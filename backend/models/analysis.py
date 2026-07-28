from datetime import datetime
import uuid

class Analysis:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', str(uuid.uuid4()))
        self.user_email = kwargs.get('user_email', '')
        self.input_type = kwargs.get('input_type', 'text')
        self.original_content = kwargs.get('original_content', '')
        self.processed_content = kwargs.get('processed_content', '')
        self.anonymized_content = kwargs.get('anonymized_content', '')
        self.language = kwargs.get('language', 'en')
        self.risk_score = kwargs.get('risk_score', 0.0)
        self.confidence = kwargs.get('confidence', 0.0)
        self.risk_level = kwargs.get('risk_level', 'UNKNOWN')
        self.explanations = kwargs.get('explanations', [])
        self.safety_advice = kwargs.get('safety_advice', {})
        self.metadata = kwargs.get('metadata', {})
        self.negative_reviews = kwargs.get('negative_reviews', [])
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.analysis_time = kwargs.get('analysis_time', 0.0)
        self.is_archived = kwargs.get('is_archived', False)
        self.tags = kwargs.get('tags', [])
        self.feedback_id = kwargs.get('feedback_id', None)
    
    def to_dict(self):
        """Convert analysis object to dictionary"""
        return {
            '_id': self._id,
            'user_email': self.user_email,
            'input_type': self.input_type,
            'original_content': self.original_content,
            'processed_content': self.processed_content,
            'anonymized_content': self.anonymized_content,
            'language': self.language,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'risk_level': self.risk_level,
            'explanations': self.explanations,
            'safety_advice': self.safety_advice,
            'metadata': self.metadata,
            'negative_reviews': self.negative_reviews,
            'created_at': self.created_at,
            'analysis_time': self.analysis_time,
            'is_archived': self.is_archived,
            'tags': self.tags,
            'feedback_id': self.feedback_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create analysis object from dictionary"""
        return cls(**data)
    
    def get_risk_color(self):
        """Get color based on risk score"""
        if self.risk_score <= 30:
            return '#4CAF50'  # Green
        elif self.risk_score <= 60:
            return '#FF9800'  # Orange
        else:
            return '#F44336'  # Red
    
    def get_risk_icon(self):
        """Get icon based on risk level"""
        if self.risk_level == 'LEGITIMATE':
            return '✅'
        elif self.risk_level == 'SUSPICIOUS':
            return '⚠️'
        else:
            return '❌'
    
    def get_summary(self, max_length=100):
        """Get summary of analysis"""
        content = self.original_content or self.processed_content
        if len(content) > max_length:
            return content[:max_length] + '...'
        return content
    
    def add_tag(self, tag):
        """Add tag to analysis"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag):
        """Remove tag from analysis"""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def archive(self):
        """Archive the analysis"""
        self.is_archived = True
    
    def restore(self):
        """Restore from archive"""
        self.is_archived = False