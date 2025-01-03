from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from geo_data_handler import GeoDataHandler

app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

GEO_DATA = GeoDataHandler()
print(GEO_DATA.get_aggregated_travel_time())

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
def get_geo_data():
    print('GET /api/get-hex-geo-data')
    feature_collection = GEO_DATA.get_hex_geojson()
    socketio.emit('geo_data', feature_collection)

@socketio.on('/api/get-opnv-data')
def get_opnv_data():
    print('GET /api/get-opnv-data')
    socketio.emit('opnv_data', GEO_DATA.get_opnv_data())

@socketio.on('/api/get-aggregated-travel-time-data')
def get_aggregated_travel_time_data():
    print('GET /api/get-aggregated-travel-time-data')
    socketio.emit('aggregated_travel_time_data', GEO_DATA.get_aggregated_travel_time())

if __name__ == '__main__':
    socketio.run(app, debug=True)