from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', str(uuid.uuid4()))
        self.username = kwargs.get('username', '')
        self.email = kwargs.get('email', '')
        self.password = kwargs.get('password', '')
        self.full_name = kwargs.get('full_name', '')
        self.account_type = kwargs.get('account_type', 'Standard User')
        self.role = kwargs.get('role', 'user')
        self.auth_provider = kwargs.get('auth_provider', 'email')
        self.profile_picture = kwargs.get('profile_picture', '')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.last_login = kwargs.get('last_login', datetime.utcnow())
        self.is_active = kwargs.get('is_active', True)
        self.deleted_at = kwargs.get('deleted_at', None)
        self.bio = kwargs.get('bio', '')
        self.avatar_id = kwargs.get('avatar_id', 'lion')  # Default avatar
        self.theme_color = kwargs.get('theme_color', 'Cyan')
        
        
        # Preferences
        self.preferences = kwargs.get('preferences', {
            'theme': 'system',
            'language': 'en',
            'notifications': True,
            'auto_save': True,
            'data_collection': True,
            'risk_threshold': 60,
            'default_input_type': 'text'
        })
        
        # Analytics
        self.analytics = kwargs.get('analytics', {
            'total_analyses': 0,
            'scams_detected': 0,
            'avg_rating': 0,
            'feedback_count': 0
        })
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'full_name': self.full_name,
            'account_type': self.account_type,
            'role': self.role,
            'auth_provider': self.auth_provider,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active,
            'deleted_at': self.deleted_at,
            'bio': self.bio,
            'avatar_id': self.avatar_id,
            'theme_color': self.theme_color,
            'preferences': self.preferences,
            'analytics': self.analytics
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create user object from dictionary"""
        return cls(**data)
    
    def update_preferences(self, **kwargs):
        """Update user preferences"""
        for key, value in kwargs.items():
            if key in self.preferences:
                self.preferences[key] = value
    
    def update_analytics(self, **kwargs):
        """Update user analytics"""
        for key, value in kwargs.items():
            if key in self.analytics:
                self.analytics[key] = value
    
    def increment_analyses(self):
        """Increment total analyses count"""
        self.analytics['total_analyses'] = self.analytics.get('total_analyses', 0) + 1
    
    def increment_scams_detected(self):
        """Increment scams detected count"""
        self.analytics['scams_detected'] = self.analytics.get('scams_detected', 0) + 1
    
    def update_rating(self, new_rating):
        """Update average rating"""
        current_rating = self.analytics.get('avg_rating', 0)
        current_count = self.analytics.get('feedback_count', 0)
        
        if current_count == 0:
            self.analytics['avg_rating'] = new_rating
        else:
            total_rating = current_rating * current_count + new_rating
            self.analytics['avg_rating'] = total_rating / (current_count + 1)
        
        self.analytics['feedback_count'] = current_count + 1