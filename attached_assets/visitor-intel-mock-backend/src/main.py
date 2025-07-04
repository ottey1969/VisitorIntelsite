import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.live_conversation import live_conversation_bp
from src.routes.business_dashboard import business_dashboard_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(live_conversation_bp)
app.register_blueprint(business_dashboard_bp)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/health')
def health_check():
    return {"status": "healthy", "service": "Perfect Roofing Team Mock Backend"}

if __name__ == '__main__':
    print("Starting Perfect Roofing Team Mock Backend...")
    print("Available endpoints:")
    print("- GET /api/live-conversation")
    print("- GET /api/live-conversation/latest") 
    print("- GET /api-status")
    print("- POST /api/investigation")
    print("- GET /api/business/{id}/content-status")
    print("- POST /api/business/{id}/generate-content")
    print("- GET /api/business/{id}/content/{type}")
    print("- GET /api/business/{id}/content/{type}/download")
    print("- DELETE /api/business/{id}/content/{type}")
    print("- GET /api/business/{id}/showcase-url")
    print("- GET /health")
    app.run(host='0.0.0.0', port=5000, debug=True)

