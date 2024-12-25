from flask import Flask, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('message')
def handle_message(data):
    print('Received message: ' + data)
    socketio.send('Message received!')

if __name__ == '__main__':
    socketio.run(app, debug=True)