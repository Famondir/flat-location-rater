from flask import Flask, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initial map data
MAP_DATA = {
    'center': [52.510885, 13.3989367],  # Berlin
    'zoom': 11,
    'poi_positions': {
        'HTW Berlin': {'latitude': 52.4563126, 'longitude': 13.5294627},
        'BHT Berlin': {'latitude': 52.54386247486057, 'longitude': 13.354034184240273}
    },
    'flat_positions':  {
        'Berliner Rechnungshof': {'latitude': 52.524121062023426, 'longitude': 13.352456193718531}
    }
}

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
    # socketio.emit('map_data', MAP_DATA)

if __name__ == '__main__':
    socketio.run(app, debug=True)