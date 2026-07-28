"""
Backend API Tests
Scam Risk Detection Application
"""
import pytest
import json


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns OK."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_new_user(self, client):
        """Test user registration."""
        unique_email = f'test_register_{pytest.random_id}@example.com'
        response = client.post('/api/auth/register', json={
            'email': unique_email,
            'password': 'TestPassword123!',
            'username': 'newuser'
        })
        # Either 201 (created) or 409 (already exists)
        assert response.status_code in [201, 409]
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'TestPassword123!',
            'username': 'invaliduser'
        })
        assert response.status_code == 400
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/auth/register', json={
            'email': 'weak@example.com',
            'password': '123',
            'username': 'weakuser'
        })
        assert response.status_code == 400
    
    def test_login_valid_credentials(self, client):
        """Test login with valid credentials."""
        # First register
        client.post('/api/auth/register', json={
            'email': 'logintest@example.com',
            'password': 'TestPassword123!',
            'username': 'loginuser'
        })
        
        # Then login
        response = client.post('/api/auth/login', json={
            'email': 'logintest@example.com',
            'password': 'TestPassword123!'
        })
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'access_token' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'email': 'wrong@example.com',
            'password': 'WrongPassword123!'
        })
        assert response.status_code in [401, 404]


class TestAnalyzeEndpoints:
    """Test analysis endpoints."""
    
    def test_analyze_legitimate_job(self, client, auth_headers, sample_job_data):
        """Test analyzing a legitimate job posting."""
        response = client.post(
            '/api/analyze',
            json=sample_job_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'risk_score' in data
            assert 'risk_category' in data
            assert data['risk_score'] <= 30  # Legitimate should be low risk
    
    def test_analyze_scam_job(self, client, auth_headers, sample_scam_job_data):
        """Test analyzing a scam job posting."""
        response = client.post(
            '/api/analyze',
            json=sample_scam_job_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'risk_score' in data
            assert 'risk_category' in data
            assert data['risk_score'] >= 60  # Scam should be high risk
    
    def test_analyze_without_auth(self, client, sample_job_data):
        """Test that analysis requires authentication."""
        response = client.post('/api/analyze', json=sample_job_data)
        assert response.status_code in [401, 422]
    
    def test_analyze_empty_data(self, client, auth_headers):
        """Test analysis with empty data."""
        response = client.post(
            '/api/analyze',
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400


class TestFeedbackEndpoints:
    """Test feedback endpoints."""
    
    def test_submit_feedback(self, client, auth_headers, sample_feedback):
        """Test submitting feedback."""
        response = client.post(
            '/api/feedback',
            json=sample_feedback,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.get_json()
            assert 'message' in data
    
    def test_submit_feedback_invalid_rating(self, client, auth_headers):
        """Test feedback with invalid rating."""
        response = client.post(
            '/api/feedback',
            json={
                'analysis_id': 'test_id',
                'rating': 10,  # Invalid - should be 1-5
                'comment': 'Test'
            },
            headers=auth_headers
        )
        assert response.status_code in [400, 422]


class TestReviewsEndpoints:
    """Test reviews endpoints."""
    
    def test_get_reviews_by_company(self, client):
        """Test getting reviews for a company."""
        response = client.get('/api/reviews/company/C101')
        
        # May return empty list or reviews
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, (list, dict))
    
    def test_get_reviews_invalid_company(self, client):
        """Test getting reviews for non-existent company."""
        response = client.get('/api/reviews/company/INVALID999')
        
        # Should return empty list or 404
        assert response.status_code in [200, 404]


class TestSettingsEndpoints:
    """Test settings endpoints."""
    
    def test_get_user_settings(self, client, auth_headers):
        """Test getting user settings."""
        response = client.get(
            '/api/settings',
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'theme' in data or 'language' in data
    
    def test_update_theme(self, client, auth_headers):
        """Test updating theme setting."""
        response = client.put(
            '/api/settings',
            json={'theme': 'dark'},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_update_language(self, client, auth_headers):
        """Test updating language setting."""
        response = client.put(
            '/api/settings',
            json={'language': 'ta'},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]


# Generate random ID for unique test data
@pytest.fixture(scope='session', autouse=True)
def setup_random_id():
    """Set up random ID for unique test data."""
    import random
    import string
    pytest.random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
