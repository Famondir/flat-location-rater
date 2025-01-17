from datetime import datetime
import random
import geopandas as gpd
from shapely.geometry import MultiLineString, Polygon, shape
import h3
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
from asynch_requesting import AsyncRequest
import jmespath
import json
import sqlite3
from contextlib import closing
import re
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
import time
import logging

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
        self.coord_table_name = "address_coordinates"

        self.initiate_database()
        
        # self.fredy_db_path = "C:/Users/schae/OneDrive - Berliner Hochschule für Technik/Data Science/3. Semester/Urban Technologies/db/listings.db"
        self.fredy_db_path = "C:/Users/Simon/Documents/GitHub/fredy/db/listings.db"
        self.fredy_table_name = "listing"
        self.fredy_flats = pd.DataFrame()
        
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
                'Flat 5': {'plz': '12557'},
            }
        }
        
        self.flat_number = len(self.MAP_DATA['flat_positions']) + 1

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
        self.GEO_DATA_OPNV = gpd.read_file("flask-react-app/backend/data/OPNV/Strecken/OPNV Bahnstrecken.shp").to_crs(epsg=4326)
        self.GEO_DATA_OPNV = self.GEO_DATA_OPNV.query('Bahn_Typ_k not in ["T", "B", "R"]')
        self.GEO_DATA_OPNV_STOPS = gpd.read_file("flask-react-app/backend/data/OPNV/Stationen/OPNV Stationen.shp").to_crs(epsg=4326)
        self.GEO_DATA_OPNV_STOPS = self.GEO_DATA_OPNV_STOPS.query('Bahn_Typ_k not in ["T", "B", "R"]')
        self.GEO_DATA_OPNV_STOPS = (self.GEO_DATA_OPNV_STOPS
            .to_crs(epsg=25833)  # Project to meters (Berlin)
            .assign(geometry=lambda x: x.geometry.buffer(50, resolution=64))  # 100m radius, 32 segments
            .to_crs(epsg=4326)  # Back to WGS84
        )

        self.geolocator = Nominatim(user_agent="flat-location-rater")

        self.set_coordinates_and_travel_time_for_map_data()
        # print(pd.DataFrame.from_dict(self.MAP_DATA['flat_positions'], orient='index'))

    def load_flats_from_fredy(self, number_of_flats = 5):
        new_flats_df = self.get_flats_from_fredy(number_of_flats)
        new_flats_df = new_flats_df.drop(self.fredy_flats.index, errors='ignore', axis=0)
        # print(new_flats_df)

        for _, row in new_flats_df.iterrows():
            if row['plz'] != None and row['street'] != None and row['streetnumber'] != None:
                dictionary = dict()
                dictionary['plz'] = row['plz']
                if row['street'] != '':
                    dictionary['street'] = row['street']
                if row['streetnumber'] != '':
                    dictionary['streetnumber'] = row['streetnumber']
                self.MAP_DATA['flat_positions'][f'Flat {self.flat_number}'] = dictionary
                self.flat_number += 1
            else:
                print(row)
        
        self.fredy_flats = pd.concat([self.fredy_flats, new_flats_df])
        self.set_coordinates_and_travel_time_for_map_data()

    def set_coordinates_and_travel_time_for_map_data(self):
        self.MAP_DATA['flat_positions'] = self.get_coordinates(
        self.aggregate_identical_flats(self.MAP_DATA['flat_positions'])
        )

        self.TRAVEL_TIME_DATA = self.get_travel_time()

    def aggregate_identical_flats(self, flat_positions):
        flats_to_delete = set()
        new_entries = {}
        
        # Compare all pairs
        for key1, val1 in flat_positions.items():
            if key1 in flats_to_delete:
                continue
            for key2, val2 in flat_positions.items():
                if key1 >= key2 or key2 in flats_to_delete:
                    continue
                if val1 == val2:
                    # Create combined entry
                    new_key = f"{key1}+{key2}"
                    new_entries[new_key] = val1
                    flats_to_delete.add(key1)
                    flats_to_delete.add(key2)
        
        # Remove old entries and add new ones
        for key in flats_to_delete:
            del flat_positions[key]
        flat_positions.update(new_entries)
        
        return flat_positions

    def get_opnv_data(self):
        return(pd.concat([self.GEO_DATA_OPNV, self.GEO_DATA_OPNV_STOPS]).__geo_interface__)

    def get_street_geometry(self, street, plz):
        plz_shape = self.GEO_DATA_PLZ.query('plz == @plz')['geometry']
        street_shapes = self.GEO_DATA_STREETS.query('strassenna == @street')['geometry']
        selected_street_shapes = [y.iloc[0] for y in [x.intersection(plz_shape) for x in street_shapes] if not y.iloc[0].is_empty]
        street_geometry = MultiLineString(selected_street_shapes)
        return [street_geometry.__geo_interface__]
    
    def geocode_with_retry(self, address, max_retries=3, timeout=3):
        for attempt in range(max_retries):
            try:
                return self.geolocator.geocode(
                    address, 
                    namedetails=True, 
                    geometry='geojson', 
                    exactly_one=True,
                    timeout=timeout
                )
            except (GeocoderUnavailable, GeocoderTimedOut) as e:
                if attempt == max_retries - 1:
                    logging.error(f"Geocoding failed after {max_retries} attempts: {str(e)}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def get_coordinates(self, data):
        df_coordinates = self.retriev_stored_coordinates()
        # print(df_coordinates)
    
        for key, value in data.items():
            if 'latitude' in value and 'longitude' in value and 'plz' not in value:
                data[key]['is_point'] = True
            else:
                street = ''
                streetnumber = ''
                plz = ''
                latitude = 0
                longitude = 0

                if 'street' in value and 'streetnumber' in value and 'plz' in value:
                    street = value['street']
                    streetnumber = value['streetnumber']
                    plz = value['plz']
                    address = {'postalcode': plz, 'country': 'Germany', 'street': street+' '+streetnumber}
                    data[key]['is_point'] = True
                elif 'street' in value and 'streetnumber' not in value and 'plz' in value:
                    street = value['street']
                    plz = value['plz']
                    address = {'postalcode': plz, 'country': 'Germany', 'street': street}
                    data[key]['is_point'] = False
                elif 'street' not in value and 'plz' in value:
                    plz = value['plz']
                    address = {'postalcode': plz, 'country': 'Germany'}
                    data[key]['is_point'] = False
                
                # location = [self.geolocator.geocode(address, namedetails=True, geometry='geojson', exactly_one=True)]

                result = df_coordinates.query('street == @street and streetnumber == @streetnumber and plz == @plz')
                if len(result) > 0:
                    latitude = result['latitude'].values[0]
                    longitude = result['longitude'].values[0]
                else:
                    # location = [self.geolocator.geocode(address, namedetails=True, geometry='geojson', exactly_one=True)]
                    location = [self.geocode_with_retry(address)]
                    if location[0] is None:
                        return None

                    latitude = location[0].latitude
                    longitude = location[0].longitude
                    self.store_adress_coordinate_pair((street, streetnumber, plz, latitude, longitude))
                    time.sleep(1.5)

                data[key]['latitude'] = latitude
                data[key]['longitude'] = longitude
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
                    point = {'type': 'Point', 'coordinates': [longitude, latitude]}
                    data[key]['geojson'] = [point]
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
    
    def get_flat_locations(self):
        return self.MAP_DATA['flat_positions']
    
    def delete_flat(self, flat):
        del self.MAP_DATA['flat_positions'][flat['name']]
        self.TRAVEL_TIME_DATA = self.get_travel_time()
        return

    def get_aggregated_travel_time(self):
        df = (
            self.TRAVEL_TIME_DATA
            .groupby(['flat', 'geojson_hex'], as_index=False)
            .agg({'seconds': ['sum']})
            .pipe(lambda x: x.set_axis(['flat', 'geojson_hex', 'sum'], axis=1))
            .groupby('flat', as_index=False)
            .agg({'sum': ['median', 'min', 'std']})
            .pipe(lambda x: x.set_axis(['flat', 'median', 'min', 'std'], axis=1))
            .pipe(lambda x: x.sort_values('median', ascending=True))
            .fillna(0)
        )
        return(df.to_dict(orient='records'))
    
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
    
    def get_hex_geojson(self, flat):
        # postcodes = set()
        geos = []

        df = self.TRAVEL_TIME_DATA[self.TRAVEL_TIME_DATA['is_point'] == 'False']
        df = df.query('flat == @flat["flat"]').groupby('geojson_hex').agg({'seconds': 'sum'}).reset_index()
        min, max = df.agg({'seconds': ['min', 'max']})['seconds']

        for idx, row in df.iterrows():
            feature = {"type": "Feature", "properties": {"scale": 1-(row['seconds']-min)/(max-min)*0.9999, "travelTime": row['seconds'], "hex": row['geojson_hex']}, "geometry": h3.cells_to_geo([row['geojson_hex']])}
            geos.append(feature)

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

                cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.coord_table_name} (
                    street TEXT,
                    streetnumber TEXT,
                    plz TEXT,
                    latitude INTEGER,
                    longitude INTEGER
                )
                """)
                connection.commit()
    
    def store_adress_coordinate_pair(self, data):
        with closing(sqlite3.connect(self.db_name)) as connection:
            with closing(connection.cursor()) as cursor:
                # print(data)
                cursor.execute(f"INSERT INTO {self.coord_table_name} (street, streetnumber, plz, latitude, longitude) VALUES (?, ?, ?, ?, ?)", data)
                connection.commit()

    def retriev_stored_coordinates(self):
        with closing(sqlite3.connect(self.db_name)) as connection:
            # Get existing addresses and coordinates from database
            return(pd.read_sql_query(f'select * from {self.coord_table_name}', connection))

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
                count_none = 0
                for request in request_results:
                    # print(request['response'])
                    if request['response'] is not None:
                        data = json.loads(request['response'])

                        arrival = jmespath.search('journeys[0].legs[-1].arrival', data)
                        departure = jmespath.search('journeys[0].legs[0].departure', data)
                        
                        if arrival is not None:
                            travel_time = datetime.fromisoformat(arrival)-datetime.fromisoformat(departure)
                            cursor.execute(f"INSERT INTO {self.table_name} (url, seconds) VALUES (?, ?)", (request['url'], travel_time.total_seconds()))
                        else:
                            # print(request['response'])
                            count_none += 1
                    else:
                        count_none += 1

                print(f"There have been {count_none} None responses from the server.")
                connection.commit()
                
    def get_flats_from_fredy(self, number_of_flats = 5):
        with closing(sqlite3.connect(self.fredy_db_path)) as connection:
            with closing(connection.cursor()) as cursor:
                
                df = pd.read_sql_query(f'select * from {self.fredy_table_name}', connection).tail(number_of_flats)
                df['plz'] = df['address'].transform(lambda x: re.search("[0-9]{5}", x)[0])
                df['street'] = df['address'].transform(lambda x: (x.replace('Berlin', '').split(','))[0] if x.count(',') == 2 else '')
                df['streetnumber'] = df['street'].transform(lambda x: re.search(r'\d+', x).group() if re.search(r'\d+', x) else '')
                df['street'] = df['street'].transform(lambda x: re.sub(r'\d+', '', x).strip().replace('str.', 'straße').replace('Str.', 'Straße'))
        
                return(df[['plz', 'street', 'streetnumber']])
            
if __name__ == "__main__":
    GEO_DATA = GeoDataHandler()