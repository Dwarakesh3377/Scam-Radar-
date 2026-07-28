import os
import sys

# CRITICAL: These MUST be at the top to prevent WinError 1114 on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
try:
    import torch
    print(f"DEBUG: Torch initialized successfully at app startup (Version: {torch.__version__})")
except Exception as e:
    print(f"DEBUG: Torch initialization failed at app startup: {e}")

"""
Scam Risk Detection - Flask Application
========================================
Main Flask application with all routes and configurations.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    if config:
        app.config.update(config)
    
    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": os.getenv('CORS_ORIGINS', '*').split(','),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Flask configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'scam-detection-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-scam-detection-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # MongoDB configuration
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/scam_detection_db')
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please log in again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': str(error)
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Token is missing'
        }), 401
    
    # Register blueprints - Imported inside to avoid circular dependencies and ensure torch is loaded first
    from routes.auth import auth_bp
    from routes.analyze import analyze_bp
    from routes.feedback import feedback_bp
    from routes.settings import settings_bp
    from routes.reviews import reviews_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analyze_bp, url_prefix='/api/analyze')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    
    # Health check route
    @app.route('/')
    def home():
        return jsonify({
            "status": "Scam Risk Detection API is running",
            "version": "1.0.0",
            "time": datetime.utcnow().isoformat(),
            "endpoints": {
                "auth": "/api/auth",
                "analyze": "/api/analyze",
                "feedback": "/api/feedback",
                "settings": "/api/settings",
                "reviews": "/api/reviews"
            }
        })
    
    @app.before_request
    def log_request_info():
        # Only log /api/ requests to avoid health check spam if needed, but for now log all
        if request.path.startswith('/api/'):
            print(f"[RECV] {request.method} {request.path} from {request.remote_addr}")
            # print(f"Headers: {dict(request.headers)}")
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"[CRITICAL ERROR] Unhandled Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

    @app.route('/api/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "time": datetime.utcnow().isoformat()
        })
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("-" * 50)
    print(f"   SCAM RADAR - Backend API Server")
    print("-" * 50)
    print(f"   Running on: http://{host}:{port}")
    print(f"   Debug mode: {debug}")
    print("-" * 50)
    
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
