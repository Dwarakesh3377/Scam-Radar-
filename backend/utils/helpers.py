import re
import hashlib
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

def generate_id(prefix=''):
    """Generate a unique ID"""
    unique_id = str(uuid.uuid4()).replace('-', '')
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def sanitize_filename(filename):
    """Sanitize filename to remove unsafe characters"""
    # Remove directory traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove unsafe characters
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1)
        filename = name[:200] + '.' + ext
    
    return filename

def format_bytes(size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def generate_random_string(length=8, chars=string.ascii_letters + string.digits):
    """Generate a random string"""
    return ''.join(random.choice(chars) for _ in range(length))

def get_file_hash(file_path, algorithm='sha256'):
    """Calculate file hash"""
    hasher = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def validate_json(data):
    """Validate if data is valid JSON"""
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten a nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_list(lst, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_time_ago(dt):
    """Get human readable time ago string"""
    if not dt:
        return "Unknown time"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def mask_sensitive_data(text, mask_char='*'):
    """Mask sensitive data in text"""
    # Mask emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                 lambda m: m.group()[0] + mask_char * (len(m.group()) - 2) + m.group()[-1], text)
    
    # Mask phone numbers
    text = re.sub(r'\b\d[\d\s\-\(\)]{7,}\d\b', 
                 lambda m: mask_char * len(m.group()), text)
    
    # Mask credit cards
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                 lambda m: mask_char * len(m.group()), text)
    
    return text

def calculate_percentage(part, whole):
    """Calculate percentage safely"""
    if whole == 0:
        return 0
    return round((part / whole) * 100, 2)

def get_safe_dict_value(dict_obj, key_path, default=None):
    """Safely get value from nested dictionary"""
    keys = key_path.split('.')
    value = dict_obj
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, {})
        else:
            return default
    
    return value if value != {} else default

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def clean_html(text):
    """Clean HTML tags from text"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def generate_color_from_text(text):
    """Generate a consistent color from text"""
    hash_val = hashlib.md5(text.encode()).hexdigest()[:6]
    r = int(hash_val[0:2], 16)
    g = int(hash_val[2:4], 16)
    b = int(hash_val[4:6], 16)
    
    # Ensure not too dark or light
    if r + g + b < 150:
        r = min(255, r + 100)
        g = min(255, g + 100)
        b = min(255, b + 100)
    elif r + g + b > 600:
        r = max(0, r - 100)
        g = max(0, g - 100)
        b = max(0, b - 100)
    
    return f"#{r:02x}{g:02x}{b:02x}"