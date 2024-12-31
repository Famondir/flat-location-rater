import random
from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import h3
from geopy.geocoders import Nominatim

app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initial map data
MAP_DATA = {
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

# geo shape data
GEO_DATA_STREETS = gpd.read_file("flask-react-app/backend/data/streets/Detailnetz-Strassenabschnitte.shp").to_crs(epsg=4326)
GEO_DATA_PLZ = gpd.read_file("flask-react-app/backend/data/PLZ/plz.shp").to_crs(epsg=4326)

geolocator = Nominatim(user_agent="flat-location-rater")

def get_street_geometry(street, plz):
    plz_shape = GEO_DATA_PLZ.query('plz == @plz')['geometry']
    street_shapes = GEO_DATA_STREETS.query('strassenna == @street')['geometry']
    selected_street_shapes = [y.iloc[0] for y in [x.intersection(plz_shape) for x in street_shapes] if not y.iloc[0].is_empty]
    street_geometry = MultiLineString(selected_street_shapes)
    return [street_geometry.__geo_interface__]

def get_coordinates(data):
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
            
            location = [geolocator.geocode(address, namedetails=True, geometry='geojson', exactly_one=True)]

            data[key]['latitude'] = location[0].latitude
            data[key]['longitude'] = location[0].longitude
            if 'street' in value and 'streetnumber' not in value and 'plz' in value:
                data[key]['geojson'] = get_street_geometry(value['street'], value['plz'])
            elif 'street' not in value and 'plz' in value:
                data[key]['geojson'] = [GEO_DATA_PLZ.query('plz == @value["plz"]')['geometry'].iloc[0].__geo_interface__]
            else:
                data[key]['geojson'] = [loc.raw['geojson'] for loc in location]
    return data

MAP_DATA['flat_positions'] = get_coordinates(MAP_DATA['flat_positions'])

@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('/api/get-map-data')
def get_map_data():
    print('GET /api/get-map-data')
    socketio.emit('map_data', MAP_DATA)

@socketio.on('/api/connect')
def handle_connect():
    print('Connected')

@socketio.on('/api/get-geo-data')
def get_geo_data():
    print('GET /api/get-geo-data')
    
    geos = []
    for flat, value in MAP_DATA['flat_positions'].items():
        if not value['is_point']:
            for geo in value['geojson']:
                if geo['type'] == 'Polygon':
                    geos.append({"type": "Feature", "properties": {"opacity": random.random()}, "geometry": geo})
                elif geo['type'] in ['LineString', 'MultiLineString']:
                    geos.append({"type": "Feature", "geometry": geo})

    feature_collection = {"type": "FeatureCollection", "features": geos}
    socketio.emit('geo_data', feature_collection)

    """ postcodes = set()
    for flat, value in MAP_DATA['flat_positions'].items():
        if not value['is_point']:
            postcodes.add(value['plz'])
    sim_geo = gpd.GeoSeries(GEO_GEO_DATA_PLZ.query('plz in @postcodes')['geometry']).simplify(tolerance=0.001)
    socketio.emit('geo_data', sim_geo.iloc[0].__geo_interface__) """

    """ hexes = [{"type": "Feature", "properties": {"opacity": random.random()}, "geometry": h3.cells_to_geo([cell])} for cell in h3.geo_to_cells(sim_geo.iloc[0], res=9)]
    feature_collection = {"type": "FeatureCollection", "features": hexes}
    socketio.emit('geo_data', feature_collection) """

if __name__ == '__main__':
    socketio.run(app, debug=True)