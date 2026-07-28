import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
from datetime import datetime

class Validators:
    @staticmethod
    def validate_email_address(email):
        """Validate email address format and domain"""
        if not email:
            return False, "Email is required"
        
        try:
            # Validate email format
            email_info = validate_email(email, check_deliverability=False)
            
            # Check for disposable email domains
            disposable_domains = [
                'tempmail.com', 'mailinator.com', 'guerrillamail.com',
                '10minutemail.com', 'throwawaymail.com', 'yopmail.com'
            ]
            
            domain = email_info.domain.lower()
            for disposable in disposable_domains:
                if disposable in domain:
                    return False, "Disposable email addresses are not allowed"
            
            return True, "Valid email"
            
        except EmailNotValidError as e:
            return False, str(e)
    
    @staticmethod
    def validate_phone_number(phone, country_code=None):
        """Validate phone number"""
        if not phone:
            return False, "Phone number is required"
        
        try:
            # Clean phone number
            phone = re.sub(r'[^\d+]', '', phone)
            
            # Parse phone number
            if country_code:
                parsed = phonenumbers.parse(phone, country_code)
            else:
                parsed = phonenumbers.parse(phone)
            
            # Check if valid
            if phonenumbers.is_valid_number(parsed):
                return True, "Valid phone number"
            else:
                return False, "Invalid phone number"
                
        except phonenumbers.NumberParseException as e:
            return False, str(e)
    
    @staticmethod
    def validate_url(url):
        """Validate URL format and safety"""
        if not url:
            return False, "URL is required"
        
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False, "URL must start with http:// or https://"
            
            # Check netloc (domain)
            if not parsed.netloc:
                return False, "Invalid domain"
            
            # Check for suspicious TLDs
            suspicious_tlds = ['.xyz', '.tk', '.ml', '.ga', '.cf', '.gq']
            if any(parsed.netloc.endswith(tld) for tld in suspicious_tlds):
                return True, "Valid URL (suspicious TLD detected)", True
            
            # Check for IP addresses
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            if re.match(ip_pattern, parsed.netloc):
                return True, "Valid URL (IP address detected)", True
            
            return True, "Valid URL", False
            
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        errors = []
        
        # Check length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for numbers
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "Strong password"
    
    @staticmethod
    def validate_username(username):
        """Validate username"""
        if not username:
            return False, "Username is required"
        
        # Check length
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return False, "Username must be less than 30 characters"
        
        # Check allowed characters
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            return False, "Username can only contain letters, numbers, dots, hyphens and underscores"
        
        # Check starts with letter
        if not username[0].isalpha():
            return False, "Username must start with a letter"
        
        return True, "Valid username"
    
    @staticmethod
    def validate_date(date_str, date_format='%Y-%m-%d'):
        """Validate date string"""
        if not date_str:
            return False, "Date is required"
        
        try:
            datetime.strptime(date_str, date_format)
            return True, "Valid date"
        except ValueError:
            return False, f"Date must be in format {date_format}"
    
    @staticmethod
    def validate_json_schema(data, schema):
        """Validate data against JSON schema"""
        errors = []
        
        for field, rules in schema.items():
            value = data.get(field)
            
            # Check required fields
            if rules.get('required', False) and value is None:
                errors.append(f"{field} is required")
                continue
            
            if value is None:
                continue
            
            # Check type
            expected_type = rules.get('type')
            if expected_type and not isinstance(value, expected_type):
                errors.append(f"{field} must be {expected_type.__name__}")
                continue
            
            # Check min/max for numbers
            if isinstance(value, (int, float)):
                if 'min' in rules and value < rules['min']:
                    errors.append(f"{field} must be at least {rules['min']}")
                if 'max' in rules and value > rules['max']:
                    errors.append(f"{field} must be at most {rules['max']}")
            
            # Check length for strings
            if isinstance(value, str):
                if 'min_length' in rules and len(value) < rules['min_length']:
                    errors.append(f"{field} must be at least {rules['min_length']} characters")
                if 'max_length' in rules and len(value) > rules['max_length']:
                    errors.append(f"{field} must be at most {rules['max_length']} characters")
                
                # Check pattern
                if 'pattern' in rules and not re.match(rules['pattern'], value):
                    errors.append(f"{field} does not match required pattern")
            
            # Check choices
            if 'choices' in rules and value not in rules['choices']:
                errors.append(f"{field} must be one of {', '.join(map(str, rules['choices']))}")
        
        if errors:
            return False, errors
        return True, "Valid data"
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """Validate file extension"""
        if not filename:
            return False, "Filename is required"
        
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if ext not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        return True, "Valid file extension"
    
    @staticmethod
    def validate_file_size(file_size, max_size_mb):
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"File size exceeds {max_size_mb}MB limit"
        
        return True, "Valid file size"
    
    @staticmethod
    def is_suspicious_text(text):
        """Check if text contains suspicious patterns"""
        if not text:
            return False, []
        
        suspicious_patterns = {
            'sql_injection': [
                r"(\%27)|(\')|(\-\-)",
                r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
                r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))"
            ],
            'xss': [
                r"<script.*?>.*?</script>",
                r"javascript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"onclick\s*="
            ],
            'command_injection': [
                r";\s*\w+",
                r"\|\s*\w+",
                r"&\s*\w+",
                r"`.*?`",
                r"\$\("
            ]
        }
        
        detected_patterns = []
        
        for pattern_type, patterns in suspicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_patterns.append(pattern_type)
                    break
        
        return len(detected_patterns) > 0, detected_patterns