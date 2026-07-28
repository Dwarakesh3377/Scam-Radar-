from flask import request, jsonify
import re
import os
from functools import wraps
import bleach

class SecurityMiddleware:
    # Blacklists
    malicious_ips = set()
    suspicious_user_agents = set()
    
    @staticmethod
    def load_blacklists():
        """Load IP and User-Agent blacklists from security files"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            security_dir = os.path.abspath(os.path.join(current_dir, '../security'))
            
            # Load IPs
            ip_file = os.path.join(security_dir, 'malicious-ips.txt')
            if os.path.exists(ip_file):
                with open(ip_file, 'r') as f:
                    SecurityMiddleware.malicious_ips = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
            
            # Load User Agents
            ua_file = os.path.join(security_dir, 'suspicious-user-agents.txt')
            if os.path.exists(ua_file):
                with open(ua_file, 'r') as f:
                    SecurityMiddleware.suspicious_user_agents = set(line.strip().lower() for line in f if line.strip() and not line.startswith('#'))
            
            print(f"Loaded {len(SecurityMiddleware.malicious_ips)} malicious IPs and {len(SecurityMiddleware.suspicious_user_agents)} suspicious User-Agents.")
        except Exception as e:
            print(f"Error loading blacklists: {e}")

    @staticmethod
    def is_blocked(request):
        """Check if request should be blocked based on blacklists"""
        # Check IP
        ip = request.remote_addr
        if ip in SecurityMiddleware.malicious_ips:
            return True, "IP blocked"
            
        # Check User Agent
        ua = request.headers.get('User-Agent', '').lower()
        for pattern in SecurityMiddleware.suspicious_user_agents:
            if pattern in ua:
                return True, "Suspicious User-Agent blocked"
                
        return False, None

    @staticmethod
    def sanitize_input(data):
        """Sanitize user input to prevent XSS"""
        if isinstance(data, str):
            # Remove script tags and dangerous HTML
            data = bleach.clean(data, tags=[], attributes={}, strip=True)
            # Escape special characters
            data = data.replace('<', '&lt;').replace('>', '&gt;')
            data = data.replace('"', '&quot;').replace("'", '&#x27;')
        return data
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        pattern = r'^(https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/.*)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def check_sql_injection(text):
        """Check for SQL injection patterns"""
        sql_patterns = [
            r'(\%27)|(\')|(\-\-)',  # SQL comments
            r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',  # SQL meta characters
            r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',  # 'or' keyword
            r'((\%27)|(\'))union',  # union keyword
            r'exec(\s|\+)+(s|x)p\w+',  # exec stored procedures
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

# Initialize blacklists on module load
SecurityMiddleware.load_blacklists()

def sanitize_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check blacklists first
        blocked, reason = SecurityMiddleware.is_blocked(request)
        if blocked:
            return jsonify({'error': 'Security blocked', 'message': reason}), 403

        # Sanitize GET parameters
        if request.args:
            for key in request.args:
                request.args[key] = SecurityMiddleware.sanitize_input(request.args[key])
        
        # Sanitize POST data
        if request.is_json:
            data = request.get_json()
            if data:
                sanitized_data = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        sanitized_data[key] = SecurityMiddleware.sanitize_input(value)
                    else:
                        sanitized_data[key] = value
                # We need to update request.json safely
                # In Flask, we might need to overwrite the internal json data if we want it to persist
                # but usually decorators just pass it along.
                # However, many routes access request.json directly.
                request._cached_json = (sanitized_data, sanitized_data)
        
        # Sanitize form data
        if request.form:
            for key in request.form:
                request.form[key] = SecurityMiddleware.sanitize_input(request.form[key])
        
        return f(*args, **kwargs)
    return decorated_function
