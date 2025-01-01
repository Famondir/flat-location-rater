import random
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

if __name__ == '__main__':
    socketio.run(app, debug=True)