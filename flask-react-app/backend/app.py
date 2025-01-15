from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from geo_data_handler import GeoDataHandler

app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

GEO_DATA = GeoDataHandler()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('/api/connect')
def handle_connect():
    print('Connected')

@socketio.on('/api/get-map-data')
def get_map_data():
    print('GET /api/get-map-data')
    socketio.emit('map_data', GEO_DATA.get_map_data())

@socketio.on('/api/get-geo-data')
def get_geo_data():
    print('GET /api/get-geo-data')
    feature_collection = GEO_DATA.get_geojson()
    socketio.emit('geo_data', feature_collection)

@socketio.on('/api/get-hex-geo-data')
def get_geo_data(flat):
    print('GET /api/get-hex-geo-data')
    feature_collection = GEO_DATA.get_hex_geojson(flat)
    socketio.emit('hex_geo_data', feature_collection)

@socketio.on('/api/get-opnv-data')
def get_opnv_data():
    print('GET /api/get-opnv-data')
    socketio.emit('opnv_data', GEO_DATA.get_opnv_data())

@socketio.on('/api/get-aggregated-travel-time-data')
def get_aggregated_travel_time_data():
    print('GET /api/get-aggregated-travel-time-data')
    socketio.emit('aggregated_travel_time_data', GEO_DATA.get_aggregated_travel_time())

@socketio.on('/api/get-flat-locations')
def get_flat_locations():
    print('/api/get-flat-locations')
    socketio.emit('flat_locations', GEO_DATA.get_flat_locations())

@socketio.on('/api/delete-flat')
def delete_flat(flat):
    print('/api/delete-flat')
    GEO_DATA.delete_flat(flat)
    socketio.emit('flat_locations', GEO_DATA.get_flat_locations())
    socketio.emit('map_data', GEO_DATA.get_map_data())
    socketio.emit('aggregated_travel_time_data', GEO_DATA.get_aggregated_travel_time())
    feature_collection = GEO_DATA.get_geojson()
    socketio.emit('geo_data', feature_collection)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)