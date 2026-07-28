"""
Pytest Configuration and Fixtures
Scam Risk Detection Application
"""
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    test_config = {
        'TESTING': True,
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'test-jwt-secret'),
        'MONGODB_URI': os.getenv('MONGODB_TEST_URI', 'mongodb://localhost:27017/scamradar_test'),
        'DATABASE_NAME': 'admin'
    }
    
    app = create_app(test_config)
    yield app


@pytest.fixture()
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Create a CLI runner for testing CLI commands."""
    return app.test_cli_runner()


@pytest.fixture()
def auth_headers(client):
    """Get authentication headers with valid JWT token."""
    # Create a test user and login
    test_user = {
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'username': 'testuser'
    }
    
    # Try to register (might already exist)
    client.post('/api/auth/register', json=test_user)
    
    # Login to get token
    response = client.post('/api/auth/login', json={
        'email': test_user['email'],
        'password': test_user['password']
    })
    
    if response.status_code == 200:
        data = response.get_json()
        token = data.get('access_token', '')
        return {'Authorization': f'Bearer {token}'}
    
    return {}


@pytest.fixture()
def sample_job_data():
    """Sample job data for testing analysis."""
    return {
        'job_description': 'Software Engineer position at Google. Requirements include 3+ years of experience in Python.',
        'company_name': 'Google LLC',
        'sender_email': 'hr@google.com',
        'contact_method': 'Email',
        'salary_offered': '₹25-40 LPA',
        'input_type': 'text'
    }


@pytest.fixture()
def sample_scam_job_data():
    """Sample scam job data for testing."""
    return {
        'job_description': 'URGENT HIRING! Earn $5000/month working from home. No experience needed. Pay $200 registration fee to start.',
        'company_name': 'Quick Money Solutions',
        'sender_email': 'jobs@gmail.com',
        'contact_method': 'WhatsApp',
        'salary_offered': '$5000/month',
        'input_type': 'text'
    }


@pytest.fixture()
def sample_feedback():
    """Sample feedback data for testing."""
    return {
        'analysis_id': 'test_analysis_001',
        'rating': 5,
        'comment': 'Very helpful analysis. Saved me from potential scam.'
    }


class MockMongoDB:
    """Mock MongoDB for testing without actual database."""
    
    def __init__(self):
        self.collections = {}
    
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection()
        return self.collections[name]


class MockCollection:
    """Mock MongoDB Collection."""
    
    def __init__(self):
        self.documents = []
        self.id_counter = 0
    
    def insert_one(self, document):
        self.id_counter += 1
        document['_id'] = str(self.id_counter)
        self.documents.append(document)
        return MockInsertResult(document['_id'])
    
    def find_one(self, query):
        for doc in self.documents:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                return doc
        return None
    
    def find(self, query=None):
        if query is None:
            return self.documents
        results = []
        for doc in self.documents:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                results.append(doc)
        return results
    
    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc:
            if '$set' in update:
                doc.update(update['$set'])
            return MockUpdateResult(1)
        return MockUpdateResult(0)
    
    def delete_one(self, query):
        for i, doc in enumerate(self.documents):
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                del self.documents[i]
                return MockDeleteResult(1)
        return MockDeleteResult(0)


class MockInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class MockUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class MockDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


@pytest.fixture()
def mock_db():
    """Create a mock database for testing."""
    return MockMongoDB()
      
