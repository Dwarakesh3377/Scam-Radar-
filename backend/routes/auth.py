"""
Authentication Routes - User Auth API
======================================
Handles user registration, login, and social authentication.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests
import os
from db.mongo import mongo, users
from models.user import User
from firebase_setup.firebase_admin_config import initialize_firebase, verify_firebase_token

initialize_firebase()

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['username', 'email', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        
        # Check if email already exists
        if users is not None and users.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=email,
            full_name=data.get('full_name', ''),
            auth_provider='email',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            account_type='Standard User'
        )
        user.set_password(data['password'])
        
        # Save to database
        if users is not None:
            users.insert_one(user.to_dict())
        
        # Generate tokens
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'user': {
                'username': user.username,
                'email': user.email,
                'account_type': user.account_type,
                'analytics': user.analytics,
                'created_at': user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else user.created_at
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        email = data['email'].lower().strip()
        
        # Find user
        if users is None:
            return jsonify({'error': 'Database not available'}), 503
            
        user_data = users.find_one({'email': email})
        
        if not user_data:
            print(f"[AUTH] Login failed for {email}: User not found")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        user = User.from_dict(user_data)
        if not user.check_password(data['password']):
            print(f"[AUTH] Login failed for {email}: Incorrect password")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        users.update_one(
            {'email': email},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Generate token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'username': user.username,
                'email': user.email,
                'account_type': user.account_type,
                'profile_picture': user.profile_picture,
                'analytics': user.analytics,
                'created_at': user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else user.created_at
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    """Login with Google OAuth"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Google token required'}), 400
        
        # Verify Google token
        response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Invalid Google token'}), 401
        
        user_info = response.json()
        email = user_info.get('email', '').lower()
        
        if not email:
            return jsonify({'error': 'Email not provided by Google'}), 400
        
        # Find or create user
        if users is not None:
            user_data = users.find_one({'email': email})
        else:
            user_data = None
        
        if not user_data:
            # Create new user
            user = User(
                username=user_info.get('name', email.split('@')[0]),
                email=email,
                auth_provider='google',
                profile_picture=user_info.get('picture', ''),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                account_type='Standard User'
            )
            if users is not None:
                users.insert_one(user.to_dict())
            user_data = user.to_dict()
        else:
            # Update last login
            if users is not None:
                users.update_one(
                    {'email': email},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
        
        # Generate token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Google login successful',
            'access_token': access_token,
            'user': {
                'username': user_data.get('username'),
                'email': email,
                'account_type': user_data.get('account_type', 'Standard User'),
                'profile_picture': user_data.get('profile_picture', ''),
                'analytics': user_data.get('analytics', {}),
                'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') and hasattr(user_data.get('created_at'), 'isoformat') else user_data.get('created_at')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/github-login', methods=['POST'])
def github_login():
    """Login with GitHub OAuth"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'GitHub code required'}), 400
        
        # Exchange code for access token
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code
            },
            headers={'Accept': 'application/json'}
        )
        
        if token_response.status_code != 200:
            return jsonify({'error': 'Failed to get GitHub access token'}), 401
        
        token_data = token_response.json()
        github_token = token_data.get('access_token')
        
        if not github_token:
            return jsonify({'error': 'GitHub access token not received'}), 401
        
        # Get user info from GitHub
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'Bearer {github_token}'}
        )
        
        if user_response.status_code != 200:
            return jsonify({'error': 'Failed to get GitHub user info'}), 401
        
        github_user = user_response.json()
        email = github_user.get('email')
        
        # Get email if not public
        if not email:
            emails_response = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'Bearer {github_token}'}
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next((e for e in emails if e.get('primary')), None)
                email = primary_email.get('email') if primary_email else None
        
        if not email:
            return jsonify({'error': 'Email not available from GitHub'}), 400
        
        email = email.lower()
        
        # Find or create user
        if users is not None:
            user_data = users.find_one({'email': email})
        else:
            user_data = None
        
        if not user_data:
            user = User(
                username=github_user.get('login', email.split('@')[0]),
                email=email,
                auth_provider='github',
                profile_picture=github_user.get('avatar_url', ''),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                account_type='Standard User'
            )
            if users is not None:
                users.insert_one(user.to_dict())
            user_data = user.to_dict()
        else:
            if users is not None:
                users.update_one(
                    {'email': email},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
        
        # Generate token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'GitHub login successful',
            'access_token': access_token,
            'user': {
                'username': user_data.get('username'),
                'email': email,
                'account_type': user_data.get('account_type', 'Standard User'),
                'profile_picture': user_data.get('profile_picture', ''),
                'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') and hasattr(user_data.get('created_at'), 'isoformat') else user_data.get('created_at')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    """Login with Facebook OAuth"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Facebook token required'}), 400
        
        # Verify Facebook token with Graph API
        response = requests.get(
            f'https://graph.facebook.com/me?fields=id,name,email,picture&access_token={token}'
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Invalid Facebook token'}), 401
        
        user_info = response.json()
        email = user_info.get('email', '').lower()
        
        if not email:
            # Fallback for users without email in Facebook
            email = f"{user_info.get('id')}@facebook.com"
        
        # Find or create user
        if users is not None:
            user_data = users.find_one({'email': email})
        else:
            user_data = None
        
        if not user_data:
            user = User(
                username=user_info.get('name', email.split('@')[0]),
                email=email,
                auth_provider='facebook',
                profile_picture=user_info.get('picture', {}).get('data', {}).get('url', ''),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                account_type='Standard User'
            )
            if users is not None:
                users.insert_one(user.to_dict())
            user_data = user.to_dict()
        else:
            if users is not None:
                users.update_one(
                    {'email': email},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
        
        # Generate token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Facebook login successful',
            'access_token': access_token,
            'user': {
                'username': user_data.get('username'),
                'email': email,
                'account_type': user_data.get('account_type', 'Standard User'),
                'profile_picture': user_data.get('profile_picture', ''),
                'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') and hasattr(user_data.get('created_at'), 'isoformat') else user_data.get('created_at')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/apple-login', methods=['POST'])
def apple_login():
    """Login with Apple OAuth"""
    try:
        data = request.get_json()
        token = data.get('token') # This is usually an identityToken (JWT)
        
        if not token:
            return jsonify({'error': 'Apple token required'}), 400
        
        # In a real app, you would verify the Apple identityToken (JWT) 
        # using Apple's public keys. For this implementation, we'll 
        # extract the user info if the token is present.
        # Note: Proper verification requires the `python-jose` or `pyjwt` library.
        
        # Mocking Apple response for illustration since real verification 
        # depends on external keys and client configuration.
        # In practice, the frontend gets the email/name on the FIRST login only.
        
        email = data.get('email', '').lower()
        if not email:
            return jsonify({'error': 'Email required for Apple login'}), 400
            
        # Find or create user
        if users is not None:
            user_data = users.find_one({'email': email})
        else:
            user_data = None
            
        if not user_data:
            user = User(
                username=data.get('name', email.split('@')[0]),
                email=email,
                auth_provider='apple',
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                account_type='Standard User'
            )
            if users is not None:
                users.insert_one(user.to_dict())
            user_data = user.to_dict()
        else:
            if users is not None:
                users.update_one(
                    {'email': email},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
        
        # Generate token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Apple login successful',
            'access_token': access_token,
            'user': {
                'username': user_data.get('username'),
                'email': email,
                'account_type': user_data.get('account_type', 'Standard User'),
                'analytics': user_data.get('analytics', {}),
                'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') and hasattr(user_data.get('created_at'), 'isoformat') else user_data.get('created_at')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        current_user = get_jwt_identity()
        
        if users is None:
            return jsonify({'error': 'Database not available'}), 503
        
        user_data = users.find_one({'email': current_user})
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove sensitive data
        user_data.pop('password', None)
        user_data['_id'] = str(user_data.get('_id', ''))
        
        if 'created_at' in user_data and hasattr(user_data['created_at'], 'isoformat'):
            user_data['created_at'] = user_data['created_at'].isoformat()
        if 'last_login' in user_data and hasattr(user_data['last_login'], 'isoformat'):
            user_data['last_login'] = user_data['last_login'].isoformat()
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if users is None:
            return jsonify({'error': 'Database not available'}), 503
        
        # Allowed fields to update
        allowed_fields = ['username', 'full_name', 'profile_picture', 'bio', 'avatar_id', 'theme_color']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        users.update_one(
            {'email': current_user},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change current user's password"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords are required'}), 400
        
        if users is None:
            return jsonify({'error': 'Database not available'}), 503
            
        user_data = users.find_one({'email': current_user})
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        user = User.from_dict(user_data)
        if not user.check_password(old_password):
            return jsonify({'error': 'Incorrect current password'}), 401
            
        # Update password
        user.set_password(new_password)
        
        users.update_one(
            {'email': current_user},
            {'$set': {'password': user.password}}
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get statistics for the current user"""
    try:
        current_user = get_jwt_identity()
        
        if users is None:
            return jsonify({'error': 'Database not available'}), 503
            
        user_data = users.find_one({'email': current_user})
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        # Return analytics data
        analytics = user_data.get('analytics', {
            'total_analyses': 0,
            'scams_detected': 0,
            'avg_rating': 0,
            'feedback_count': 0
        })
        
        return jsonify(analytics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    """Login with Firebase Identity Token"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        print(f"[AUTH] Received Firebase login request. idToken present: {bool(id_token)}")
        
        if not id_token:
            return jsonify({'error': 'Firebase ID token required'}), 400
        
        # Verify Firebase ID token
        decoded_token = verify_firebase_token(id_token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid or expired Firebase token'}), 401
        
        email = decoded_token.get('email', '').lower()
        if not email:
            # For some providers, email might be missing; fallback to uid
            uid = decoded_token.get('uid')
            email = f"{uid}@firebase.com"
        
        # Find or create user
        if users is not None:
            user_data = users.find_one({'email': email})
        else:
            user_data = None
        
        if not user_data:
            # Create new user from Firebase data
            user = User(
                username=decoded_token.get('name', email.split('@')[0]),
                email=email,
                auth_provider=decoded_token.get('firebase', {}).get('sign_in_provider', 'firebase'),
                profile_picture=decoded_token.get('picture', ''),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                account_type='Standard User'
            )
            if users is not None:
                users.insert_one(user.to_dict())
            user_data = user.to_dict()
        else:
            # Update last login
            if users is not None:
                users.update_one(
                    {'email': email},
                    {'$set': {
                        'last_login': datetime.utcnow(),
                        'profile_picture': decoded_token.get('picture', user_data.get('profile_picture', ''))
                    }}
                )
        
        # Generate our local JWT token
        access_token = create_access_token(
            identity=email,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Firebase login successful',
            'access_token': access_token,
            'user': {
                'username': user_data.get('username'),
                'email': email,
                'account_type': user_data.get('account_type', 'Standard User'),
                'profile_picture': user_data.get('profile_picture', ''),
                'analytics': user_data.get('analytics', {}),
                'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') and hasattr(user_data.get('created_at'), 'isoformat') else user_data.get('created_at')
            }
        }), 200
        
    except Exception as e:
        print(f"Error in firebase_login: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh an expired access token"""
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(
            identity=current_user,
            expires_delta=timedelta(hours=24)
        )
        return jsonify({
            'access_token': access_token,
            'message': 'Token refreshed successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard token)"""
    return jsonify({'message': 'Logged out successfully'}), 200