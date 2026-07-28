from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from .. import mongo

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_email = get_jwt_identity()
            
            # Check if user exists in database
            user = mongo.users.find_one({'email': current_user_email})
            if not user:
                return jsonify({'error': 'User not found'}), 401
                
            # Add user to request context
            request.user = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed', 'message': str(e)}), 401
    return decorated_function

def admin_required(f):
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        if request.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function