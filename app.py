from flask import Flask
from extensions import db, socketio
from config import Config
from routes import bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio.init_app(app)
app.register_blueprint(bp)

with app.app_context():
    db.create_all()  # creates missing tables

if __name__ == "__main__":
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    print(f"\nApp running on:")
    print(f"  Local:   http://127.0.0.1:5000")
    print(f"  Network: http://{local_ip}:5000\n")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)# Get LAN IP