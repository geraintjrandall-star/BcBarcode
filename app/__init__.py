from flask import Flask
from .extensions import db, socketio
from .config import Config
from .routes import bp
import os

def create_app():
    # Enable instance folder
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Put DB in instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'scan_journals.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    socketio.init_app(app)

    # Register blueprint
    app.register_blueprint(bp)

    # Create DB tables if missing
    with app.app_context():
        db.create_all()

    return app