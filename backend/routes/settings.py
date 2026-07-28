"""
Settings Routes - User Settings API
====================================
Handles user preferences and settings.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from db.mongo import mongo, users, settings

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    """Get current user's settings"""
    try:
        current_user = get_jwt_identity()
        
        # Get user preferences from user document
        if users is not None:
            user = users.find_one({'email': current_user})
            if user:
                preferences = user.get('preferences', {})
                return jsonify({
                    'theme': preferences.get('theme', 'system'),
                    'language': preferences.get('language', 'en'),
                    'notifications': preferences.get('notifications', True),
                    'auto_save': preferences.get('auto_save', True),
                    'data_collection': preferences.get('data_collection', True),
                    'risk_threshold': preferences.get('risk_threshold', 60),
                    'default_input_type': preferences.get('default_input_type', 'text')
                }), 200
        
        # Default settings
        return jsonify({
            'theme': 'system',
            'language': 'en',
            'notifications': True,
            'auto_save': True,
            'data_collection': True,
            'risk_threshold': 60,
            'default_input_type': 'text'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update current user's settings"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No settings provided'}), 400
        
        # Validate settings
        allowed_settings = {
            'theme': ['light', 'dark', 'system'],
            'language': ['en', 'ta', 'hi', 'fr', 'es', 'de', 'ja', 'zh', 'ru', 'ko'],
            'notifications': [True, False],
            'auto_save': [True, False],
            'data_collection': [True, False],
            'risk_threshold': range(0, 101),
            'default_input_type': ['text', 'url', 'email', 'company']
        }
        
        update_data = {}
        for key, value in data.items():
            if key in allowed_settings:
                if isinstance(allowed_settings[key], list):
                    if value in allowed_settings[key]:
                        update_data[f'preferences.{key}'] = value
                elif isinstance(allowed_settings[key], range):
                    if isinstance(value, int) and value in allowed_settings[key]:
                        update_data[f'preferences.{key}'] = value
        
        if not update_data:
            return jsonify({'error': 'No valid settings to update'}), 400
        
        if users is not None:
            users.update_one(
                {'email': current_user},
                {'$set': update_data}
            )
        
        return jsonify({'message': 'Settings updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/theme', methods=['PUT'])
@jwt_required()
def update_theme():
    """Quick update theme setting"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        theme = data.get('theme')
        if theme not in ['light', 'dark', 'system']:
            return jsonify({'error': 'Invalid theme. Use: light, dark, or system'}), 400
        
        if users is not None:
            users.update_one(
                {'email': current_user},
                {'$set': {'preferences.theme': theme}}
            )
        
        return jsonify({'message': f'Theme set to {theme}'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/language', methods=['PUT'])
@jwt_required()
def update_language():
    """Quick update language setting"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        language = data.get('language')
        supported = ['en', 'ta', 'hi', 'fr', 'es', 'de', 'ja', 'zh', 'ru', 'ko']
        
        if language not in supported:
            return jsonify({'error': f'Language not supported. Use: {", ".join(supported)}'}), 400
        
        if users is not None:
            users.update_one(
                {'email': current_user},
                {'$set': {'preferences.language': language}}
            )
        
        return jsonify({'message': f'Language set to {language}'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/notifications', methods=['PUT'])
@jwt_required()
def update_notifications():
    """Toggle notification settings"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        enabled = data.get('enabled', True)
        
        if users is not None:
            users.update_one(
                {'email': current_user},
                {'$set': {'preferences.notifications': bool(enabled)}}
            )
        
        status = 'enabled' if enabled else 'disabled'
        return jsonify({'message': f'Notifications {status}'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    """Export user data (GDPR compliance)"""
    try:
        current_user = get_jwt_identity()
        
        export_data = {
            'user': None,
            'analyses': [],
            'feedback': [],
            'exported_at': datetime.utcnow().isoformat()
        }
        
        if users is not None:
            user = users.find_one({'email': current_user})
            if user:
                user.pop('password', None)
                user['_id'] = str(user.get('_id', ''))
                export_data['user'] = user
        
        # Get analyses
        from db.mongo import analyses, feedback
        
        if analyses is not None:
            user_analyses = list(analyses.find({'user_email': current_user}))
            for analysis in user_analyses:
                analysis['_id'] = str(analysis['_id'])
                if 'created_at' in analysis:
                    analysis['created_at'] = analysis['created_at'].isoformat()
            export_data['analyses'] = user_analyses
        
        if feedback is not None:
            user_feedback = list(feedback.find({'user_email': current_user}))
            for fb in user_feedback:
                fb['_id'] = str(fb['_id'])
                if 'created_at' in fb:
                    fb['created_at'] = fb['created_at'].isoformat()
            export_data['feedback'] = user_feedback
        
        return jsonify(export_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Delete user account and all data"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        # Require confirmation
        if not data.get('confirm'):
            return jsonify({
                'error': 'Please confirm account deletion',
                'message': 'Set confirm: true to delete your account'
            }), 400
        
        # Delete user data
        from db.mongo import analyses, feedback
        
        if users is not None:
            users.delete_one({'email': current_user})
        
        if analyses is not None:
            analyses.delete_many({'user_email': current_user})
        
        if feedback is not None:
            feedback.delete_many({'user_email': current_user})
        
        return jsonify({
            'message': 'Account deleted successfully',
            'deleted': current_user
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500