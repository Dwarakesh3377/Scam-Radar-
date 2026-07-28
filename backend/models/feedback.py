from datetime import datetime
import uuid

class Feedback:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.user_email = kwargs.get('user_email', '')
        self.username = kwargs.get('username', '')
        self.rating = kwargs.get('rating', 5)
        self.comment = kwargs.get('comment', '')
        self.analysis_id = kwargs.get('analysis_id', None)
        self.category = kwargs.get('category', 'general')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.helpful_count = kwargs.get('helpful_count', 0)
        self.reported = kwargs.get('reported', False)
        self.is_verified = kwargs.get('is_verified', False)
        self.verification_notes = kwargs.get('verification_notes', '')
    
    def to_dict(self):
        """Convert feedback object to dictionary"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'username': self.username,
            'rating': self.rating,
            'comment': self.comment,
            'analysis_id': self.analysis_id,
            'category': self.category,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'helpful_count': self.helpful_count,
            'reported': self.reported,
            'is_verified': self.is_verified,
            'verification_notes': self.verification_notes
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create feedback object from dictionary"""
        return cls(**data)
    
    def update_comment(self, new_comment):
        """Update feedback comment"""
        self.comment = new_comment
        self.updated_at = datetime.utcnow()
    
    def mark_helpful(self):
        """Mark feedback as helpful"""
        self.helpful_count += 1
    
    def report(self):
        """Report feedback"""
        self.reported = True
    
    def verify(self, notes=''):
        """Verify feedback"""
        self.is_verified = True
        self.verification_notes = notes
    
    def get_star_rating(self):
        """Get star representation of rating"""
        return '★' * self.rating + '☆' * (5 - self.rating)
    
    def is_positive(self):
        """Check if feedback is positive"""
        return self.rating >= 4
    
    def is_negative(self):
        """Check if feedback is negative"""
        return self.rating <= 2