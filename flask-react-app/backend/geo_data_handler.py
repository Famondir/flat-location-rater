from datetime import datetime
import random
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Polygon, shape
import h3
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
from asynch_requesting import AsyncRequest
import jmespath
import json
import sqlite3
from contextlib import closing

def get_time_string(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = (total_seconds % 60)
    return(f'{int(hours)} h {int(minutes)} min {int(seconds)} s')

class GeoDataHandler:
    def __init__(self):
        # Define database name and table schema
        self.db_name = "flask-react-app/backend/flat_location_rater.db"
        self.table_name = "url_travel_time"

        # Initial map data
        self.MAP_DATA = {
            'center': [52.510885, 13.3989367],  # Berlin
            'zoom': 11,
            'poi_positions': {
                'HTW Berlin': {'latitude': 52.4563126, 'longitude': 13.5294627},
                'BHT Berlin': {'latitude': 52.54386247486057, 'longitude': 13.354034184240273},
                'Berliner Rechnungshof': {'latitude': 52.524121062023426, 'longitude': 13.352456193718531}
            },
            'flat_positions':  {
                'Flat 1': {'latitude': 52.510885, 'longitude': 13.3989367},
                'Flat 2': {'plz': '12557'},
                'Flat 3': {'street': 'Karl-Marx-Allee', 'streetnumber': '1', 'plz': '10178'},
                'Flat 4': {'street': 'Jungfernstieg', 'plz': '12207'},
            }
        }
        
        # Initial route data
        self.ROUTE_DATA = {
            1: {'poi': 'HTW Berlin', 'day': 'Monday', 'time': '09:00', 'direction': 'to'},
            2: {'poi': 'HTW Berlin', 'day': 'Monday', 'time': '17:00', 'direction': 'from'},
            3: {'poi': 'BHT Berlin', 'day': 'Tuesday', 'time': '09:00', 'direction': 'to'},
            4: {'poi': 'BHT Berlin', 'day': 'Tuesday', 'time': '15:00', 'direction': 'from'},
            5: {'poi': 'Berliner Rechnungshof', 'day': 'Sunday', 'time': '13:00', 'direction': 'to'}
        }

        # geo shape data
        self.GEO_DATA_STREETS = gpd.read_file("flask-react-app/backend/data/streets/Detailnetz-Strassenabschnitte.shp").to_crs(epsg=4326)
        self.GEO_DATA_PLZ = gpd.read_file("flask-react-app/backend/data/PLZ/plz.shp").to_crs(epsg=4326)

        self.geolocator = Nominatim(user_agent="flat-location-rater")

        self.MAP_DATA['flat_positions'] = self.get_coordinates(self.MAP_DATA['flat_positions'])

        self.TRAVEL_TIME_DATA = self.get_travel_time()

    def get_street_geometry(self, street, plz):
        plz_shape = self.GEO_DATA_PLZ.query('plz == @plz')['geometry']
        street_shapes = self.GEO_DATA_STREETS.query('strassenna == @street')['geometry']
        selected_street_shapes = [y.iloc[0] for y in [x.intersection(plz_shape) for x in street_shapes] if not y.iloc[0].is_empty]
        street_geometry = MultiLineString(selected_street_shapes)
        return [street_geometry.__geo_interface__]

    def get_coordinates(self, data):
        for key, value in data.items():
            if 'latitude' in value and 'longitude' in value:
                data[key]['is_point'] = True
            else:
                if 'street' in value and 'streetnumber' in value and 'plz' in value:
                    address = {'postalcode': value['plz'], 'country': 'Germany', 'street': value['street']+' '+value['streetnumber']}
                    data[key]['is_point'] = True
                elif 'street' in value and 'streetnumber' not in value and 'plz' in value:
                    address = {'postalcode': value['plz'], 'country': 'Germany', 'street': value['street']}
                    data[key]['is_point'] = False
                elif 'street' not in value and 'plz' in value:
                    address = {'postalcode': value['plz'], 'country': 'Germany'}
                    data[key]['is_point'] = False
                
                location = [self.geolocator.geocode(address, namedetails=True, geometry='geojson', exactly_one=True)]

                data[key]['latitude'] = location[0].latitude
                data[key]['longitude'] = location[0].longitude
                if 'street' in value and 'streetnumber' not in value and 'plz' in value:
                    geo = self.get_street_geometry(value['street'], value['plz'])
                    data[key]['geojson'] = geo
                    data[key]['geojson_hex'] = self.get_hexes_for_streets(shape(geo[0]))
                    data[key]['geojson_hex_coordinates'] = [h3.cell_to_latlng(hex) for hex in data[key]['geojson_hex']]
                elif 'street' not in value and 'plz' in value:
                    geo = self.GEO_DATA_PLZ.query('plz == @value["plz"]')['geometry'].iloc[0].__geo_interface__
                    data[key]['geojson'] = [geo]
                    data[key]['geojson_hex'] = h3.geo_to_cells(geo, res=9)
                    data[key]['geojson_hex_coordinates'] = [h3.cell_to_latlng(hex) for hex in data[key]['geojson_hex']]
                else:
                    data[key]['geojson'] = [loc.raw['geojson'] for loc in location]
        return data
    
    def get_map_data(self):
        return self.MAP_DATA
    
    def get_travel_time(self):
        flats = pd.DataFrame.from_dict(self.MAP_DATA['flat_positions'], orient='index').\
            reset_index().rename(columns={"index": "flat"}).\
                explode(['geojson_hex', 'geojson_hex_coordinates']).\
                    assign(latitude = lambda x: np.where(x.geojson_hex_coordinates.isnull(), x.latitude, x.geojson_hex_coordinates.str[0]), longitude = lambda x: np.where(x.geojson_hex_coordinates.isnull(), x.longitude, x.geojson_hex_coordinates.str[1]))
        poi = pd.DataFrame.from_dict(self.MAP_DATA['poi_positions'], orient='index').reset_index().rename(columns={"index": "poi"})
        fxp = pd.merge(flats, poi, how="cross")
        df_routes = pd.DataFrame.from_dict(self.ROUTE_DATA, orient='index')
        df_url = pd.merge(fxp, df_routes, on="poi").astype(str).assign(
            url = lambda x: "https://v6.bvg.transport.rest/journeys?from.latitude="+np.where(x.direction == "to", ""+x.latitude_x, ""+x.latitude_y)+"&from.longitude="+np.where(x.direction == "to", x.longitude_x, x.longitude_y)+"&from.address="+x.flat+"&to.latitude="+np.where(x.direction == "to", x.latitude_y, x.latitude_x)+"&to.longitude="+np.where(x.direction == "to", x.longitude_y, x.longitude_x)+"&to.address="+x.poi+"&"+np.where(x.direction == "to", "arrival=next+"+x.day+"+"+x.time,"departure=next+"+x.day+"+"+x.time)+"&results=1"
        )
        df_url['url'] = df_url['url'].str.replace(' ', '+')

        existing_urls = self.retrieve_stored_urls()

        # Filter DataFrame for new URLs only
        new_urls_df = df_url[~df_url['url'].isin(existing_urls)]

        # Only request if new URLs exist
        if not new_urls_df.empty:
            print(f'Requesting {len(new_urls_df['url'])} new urls')
            async_request = AsyncRequest(new_urls_df['url'].tolist())
            async_request.get_requests()

            # Save new results to database
            self.store_travel_time(async_request.results)

        df_travel_times = df_url.merge(self.retrieve_stored_travel_time(), on='url')
        # print(df_travel_times.query('flat == "Flat 2"'))

        return(df_travel_times)
    
    def get_aggregated_travel_time(self):
        df_travel_times_aggregated = self.TRAVEL_TIME_DATA.groupby('flat').agg({'seconds': ['sum' ,'median', 'std']})
        return(df_travel_times_aggregated)
    
    def get_geojson(self):
        postcodes = set()
        geos = []
        for flat, value in self.MAP_DATA['flat_positions'].items():
            if not value['is_point']:
                for geo in value['geojson']:
                    if geo['type'] == 'Polygon':
                        if 'street' not in value and 'plz' in value:
                            if value['plz'] not in postcodes:
                                geos.append({"type": "Feature", "properties": {"opacity": random.random()}, "geometry": geo})
                                postcodes.add(value['plz'])
                        else:
                            print('WARNING: Should this be reached?')
                            geos.append({"type": "Feature", "properties": {"opacity": random.random()}, "geometry": geo})
                    elif geo['type'] in ['LineString', 'MultiLineString']:
                        geos.append({"type": "Feature", "geometry": geo})

        feature_collection = {"type": "FeatureCollection", "features": geos}
        return(feature_collection)
    
    def get_hex_geojson(self):
        postcodes = set()
        geos = []
        for flat, value in self.MAP_DATA['flat_positions'].items():
            if not value['is_point']:
                for geo in value['geojson']:
                    if geo['type'] == 'Polygon':
                        if 'street' not in value and 'plz' in value:
                            if value['plz'] not in postcodes:
                                hexes = [{"type": "Feature", "properties": {"opacity": random.random()}, "geometry": h3.cells_to_geo([cell])} for cell in value['geojson_hex']]
                                for hex in hexes:
                                    geos.append(hex)
                                postcodes.add(value['plz'])
                        else:
                            print('WARNING: Should this be reached?')
                            geos.append({"type": "Feature", "properties": {"opacity": random.random()}, "geometry": geo})
                    elif geo['type'] in ['LineString', 'MultiLineString']:
                        hexes = [{"type": "Feature", "properties": {"opacity": random.random()}, "geometry": h3.cells_to_geo([cell])} for cell in value['geojson_hex']]
                        for hex in hexes:
                            geos.append(hex)

        feature_collection = {"type": "FeatureCollection", "features": geos}
        return(feature_collection)

    def get_hexes_for_streets(self, multiline, buffer_distance=0.0003, resolution=11):
        def multilinestring_to_polygon(multiline, buffer_distance=0.0005):
            # Create buffer around the multilinestring
            buffered = multiline.buffer(buffer_distance)

            # Ensure it's a polygon and simplify
            polygon = Polygon(buffered.exterior)
            simplified = polygon.simplify(tolerance=0.0001)
            return simplified

        return h3.geo_to_cells(multilinestring_to_polygon(multiline, buffer_distance), res = resolution)

    def initiate_database(self):
        # Connect to the SQLite database (creates it if it doesn't exist)
        with closing(sqlite3.connect(self.db_name)) as connection:
            with closing(connection.cursor()) as cursor:
        
                # Create the table if it does not exist
                cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    url TEXT,
                    seconds INTEGER
                )
                """)
                connection.commit()

    def retrieve_stored_urls(self):
        with closing(sqlite3.connect(self.db_name)) as connection:
            with closing(connection.cursor()) as cursor:
                # Get existing URLs from database
                cursor.execute(f"SELECT url FROM {self.table_name}")
                existing_urls = [row[0] for row in cursor.fetchall()]
        
                return(existing_urls)
            
    def retrieve_stored_travel_time(self):
        with closing(sqlite3.connect(self.db_name)) as connection:
            return(pd.read_sql_query(f'select * from {self.table_name}', connection))
            
    def store_travel_time(self, request_results):
        with closing(sqlite3.connect(self.db_name)) as connection:
            with closing(connection.cursor()) as cursor:
                for request in request_results:
                    data = json.loads(request['response'])

                    arrival = jmespath.search('journeys[0].legs[-1].arrival', data)
                    departure = jmespath.search('journeys[0].legs[0].departure', data)
                    
                    if arrival is not None:
                        travel_time = datetime.fromisoformat(arrival)-datetime.fromisoformat(departure)
                        cursor.execute(f"INSERT INTO {self.table_name} (url, seconds) VALUES (?, ?)", (request['url'], travel_time.total_seconds()))
                    else:
                        print(request['url'])
                
                connection.commit()