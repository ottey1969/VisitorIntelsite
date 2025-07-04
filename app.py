import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    
    db.create_all()
    
    # Start auto-posting scheduler for monthly subscribers
    try:
        from auto_posting_scheduler import start_auto_posting
        start_auto_posting()
        logging.info("Auto-posting scheduler started")
    except Exception as e:
        logging.error(f"Failed to start auto-posting scheduler: {e}")
    
    # Start enhanced conversation system
    try:
        from enhanced_conversation_system import start_enhanced_system, setup_enhanced_socketio
        setup_enhanced_socketio(socketio)
        start_enhanced_system()
        logging.info("Enhanced 4-API conversation system started")
    except Exception as e:
        logging.error(f"Failed to start enhanced conversation system: {e}")
    
    # Import routes after app and db are initialized
    import routes  # noqa: F401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
