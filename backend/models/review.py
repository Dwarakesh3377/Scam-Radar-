from datetime import datetime
import uuid

class Review:
    def __init__(self, **kwargs):
        self.review_id = kwargs.get('review_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.user_email = kwargs.get('user_email', '')
        self.username = kwargs.get('username', '')
        self.company_name = kwargs.get('company_name', '')
        self.company_domain = kwargs.get('company_domain', '')
        self.job_title = kwargs.get('job_title', '')
        self.rating = kwargs.get('rating', 1)
        self.comment = kwargs.get('comment', '')
        self.category = kwargs.get('category', 'job_scam')
        self.evidence = kwargs.get('evidence', {'screenshots': [], 'urls': []})
        self.location = kwargs.get('location', '')
        self.date_occurred = kwargs.get('date_occurred', None)
        self.financial_loss = kwargs.get('financial_loss', 0)
        self.tags = kwargs.get('tags', [])
        self.status = kwargs.get('status', 'pending')
        self.helpful_count = kwargs.get('helpful_count', 0)
        self.reported_count = kwargs.get('reported_count', 0)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.is_verified = kwargs.get('is_verified', False)
        self.verification_notes = kwargs.get('verification_notes', '')
    
    def to_dict(self):
        """Convert review object to dictionary"""
        return {
            'review_id': self.review_id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'username': self.username,
            'company_name': self.company_name,
            'company_domain': self.company_domain,
            'job_title': self.job_title,
            'rating': self.rating,
            'comment': self.comment,
            'category': self.category,
            'evidence': self.evidence,
            'location': self.location,
            'date_occurred': self.date_occurred,
            'financial_loss': self.financial_loss,
            'tags': self.tags,
            'status': self.status,
            'helpful_count': self.helpful_count,
            'reported_count': self.reported_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_verified': self.is_verified,
            'verification_notes': self.verification_notes
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create review object from dictionary"""
        return cls(**data)
    
    def approve(self):
        """Approve the review"""
        self.status = 'approved'
        self.updated_at = datetime.utcnow()
    
    def reject(self, reason=''):
        """Reject the review"""
        self.status = 'rejected'
        self.verification_notes = reason
        self.updated_at = datetime.utcnow()
    
    def mark_helpful(self):
        """Mark review as helpful"""
        self.helpful_count += 1
    
    def report(self):
        """Report review"""
        self.reported_count += 1
        if self.reported_count >= 3:
            self.status = 'under_review'
    
    def add_evidence(self, screenshot_url=None, url=None):
        """Add evidence to review"""
        if screenshot_url:
            self.evidence['screenshots'].append(screenshot_url)
        if url:
            self.evidence['urls'].append(url)
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag):
        """Add tag to review"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def verify(self, notes=''):
        """Verify review"""
        self.is_verified = True
        self.verification_notes = notes
        self.updated_at = datetime.utcnow()
    
    def is_high_loss(self):
        """Check if financial loss is high"""
        return self.financial_loss > 1000
    
    def get_severity(self):
        """Get severity level"""
        if self.rating == 1 and self.financial_loss > 500:
            return 'critical'
        elif self.rating == 1:
            return 'high'
        elif self.rating == 2:
            return 'medium'
        else:
            return 'low'