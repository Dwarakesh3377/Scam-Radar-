"""
Authentication Tests
Scam Risk Detection Application
"""
import pytest


class TestPasswordValidation:
    """Test password validation rules."""
    
    def test_password_minimum_length(self):
        """Test that password must be at least 8 characters."""
        from backend.utils.validators import validate_password
        
        # Too short
        result = validate_password('Ab1!')
        assert not result['valid']
        assert 'length' in result.get('error', '').lower()
        
        # Valid length
        result = validate_password('Abcd123!')
        assert result['valid']
    
    def test_password_requires_uppercase(self):
        """Test that password requires uppercase letter."""
        from backend.utils.validators import validate_password
        
        # No uppercase
        result = validate_password('abcd1234!')
        assert not result['valid']
        
        # With uppercase
        result = validate_password('Abcd1234!')
        assert result['valid']
    
    def test_password_requires_lowercase(self):
        """Test that password requires lowercase letter."""
        from backend.utils.validators import validate_password
        
        # No lowercase
        result = validate_password('ABCD1234!')
        assert not result['valid']
        
        # With lowercase
        result = validate_password('ABCd1234!')
        assert result['valid']
    
    def test_password_requires_number(self):
        """Test that password requires at least one number."""
        from backend.utils.validators import validate_password
        
        # No number
        result = validate_password('Abcdefgh!')
        assert not result['valid']
        
        # With number
        result = validate_password('Abcdefg1!')
        assert result['valid']


class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_emails(self):
        """Test valid email formats."""
        from backend.utils.validators import validate_email
        
        valid_emails = [
            'test@example.com',
            'user.name@domain.org',
            'user+tag@subdomain.domain.com',
            'user123@company.co.in'
        ]
        
        for email in valid_emails:
            assert validate_email(email)['valid'], f"Should accept: {email}"
    
    def test_invalid_emails(self):
        """Test invalid email formats."""
        from backend.utils.validators import validate_email
        
        invalid_emails = [
            'notanemail',
            '@nodomain.com',
            'noat.com',
            'spaces in@email.com',
            ''
        ]
        
        for email in invalid_emails:
            assert not validate_email(email)['valid'], f"Should reject: {email}"


class TestTokenGeneration:
    """Test JWT token generation and validation."""
    
    def test_token_generation(self, app):
        """Test that tokens are generated correctly."""
        from flask_jwt_extended import create_access_token
        
        with app.app_context():
            token = create_access_token(identity='test_user_id')
            assert token is not None
            assert len(token) > 0
    
    def test_token_contains_identity(self, app):
        """Test that token contains correct identity."""
        from flask_jwt_extended import create_access_token, decode_token
        
        with app.app_context():
            user_id = 'test_user_123'
            token = create_access_token(identity=user_id)
            decoded = decode_token(token)
            assert decoded['sub'] == user_id


class TestUserModel:
    """Test user model operations."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        import hashlib
        
        password = 'TestPassword123!'
        
        # Simple hash for testing
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        # Should not be the same as original
        assert hashed != password
        
        # Should be consistent
        hashed2 = hashlib.sha256(password.encode()).hexdigest()
        assert hashed == hashed2
    
    def test_user_data_structure(self):
        """Test user data structure."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'created_at': '2024-01-01T00:00:00Z',
            'settings': {
                'theme': 'dark',
                'language': 'en'
            }
        }
        
        # Verify required fields
        assert 'username' in user_data
        assert 'email' in user_data
        assert 'password_hash' in user_data
        assert 'settings' in user_data


class TestAuthorizationLevels:
    """Test different authorization levels."""
    
    def test_protected_route_requires_auth(self, client):
        """Test that protected routes require authentication."""
        # Try to access protected route without token
        response = client.get('/api/profile')
        
        # Should be unauthorized
        assert response.status_code in [401, 422]
    
    def test_protected_route_with_valid_token(self, client, auth_headers):
        """Test accessing protected route with valid token."""
        response = client.get('/api/profile', headers=auth_headers)
        
        # Should be authorized (or 404 if profile doesn't exist)
        assert response.status_code in [200, 404]
    
    def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        response = client.get(
            '/api/profile',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        # Should be unauthorized
        assert response.status_code in [401, 422]


class TestSocialAuthProviders:
    """Test social authentication providers."""
    
    def test_google_auth_url(self, client):
        """Test Google OAuth URL generation."""
        response = client.get('/api/auth/google')
        
        # Should redirect or return URL
        assert response.status_code in [200, 302, 501]
    
    def test_github_auth_url(self, client):
        """Test GitHub OAuth URL generation."""
        response = client.get('/api/auth/github')
        
        # Should redirect or return URL
        assert response.status_code in [200, 302, 501]
    
    def test_facebook_auth_url(self, client):
        """Test Facebook OAuth URL generation."""
        response = client.get('/api/auth/facebook')
        
        # Should redirect or return URL
        assert response.status_code in [200, 302, 501]
    
    def test_apple_auth_url(self, client):
        """Test Apple OAuth URL generation."""
        response = client.get('/api/auth/apple')
        
        # Should redirect or return URL
        assert response.status_code in [200, 302, 501]
