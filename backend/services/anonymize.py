"""
Anonymization Service
=====================
Mask and anonymize PII (Personally Identifiable Information).
"""

import re
import hashlib


def hash_sensitive_data(text, algorithm='sha256'):
    """
    Hash sensitive data for privacy
    """
    if not text:
        return ""
    
    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    else:
        hasher = hashlib.sha256()
    
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()[:16]


def mask_email(email):
    """
    Mask email address
    """
    if not email:
        return ""
    
    if '@' not in email:
        return hash_sensitive_data(email)
    
    username, domain = email.split('@', 1)
    
    if len(username) > 3:
        masked_username = username[:3] + '*' * (len(username) - 3)
    else:
        masked_username = '*' * len(username)
    
    return f"{masked_username}@{domain}"


def mask_phone(phone):
    """
    Mask phone number
    """
    if not phone:
        return ""
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < 4:
        return hash_sensitive_data(phone)
    
    masked = '*' * (len(digits) - 4) + digits[-4:]
    return masked


def mask_name(name):
    """
    Mask person name
    """
    if not name:
        return ""
    
    parts = name.split()
    
    if len(parts) == 0:
        return ""
    
    masked_parts = []
    for i, part in enumerate(parts):
        if i == 0 and len(part) > 1:
            masked_parts.append(part[0] + '*' * (len(part) - 1))
        else:
            masked_parts.append('*' * len(part))
    
    return ' '.join(masked_parts)


def detect_and_mask_pii_regex(text):
    """
    Detect and mask PII using regex patterns
    """
    if not text:
        return text
    
    masked_text = text
    
    # Email patterns
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    for email in emails:
        masked_email = mask_email(email)
        masked_text = masked_text.replace(email, masked_email)
    
    # Phone number patterns
    phone_patterns = [
        r'\+\d[\d\s\-\(\)]{7,}\d',
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        for phone in phones:
            masked_phone = mask_phone(phone)
            masked_text = masked_text.replace(phone, masked_phone)
    
    # Credit card patterns
    cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    ccs = re.findall(cc_pattern, text)
    for cc in ccs:
        digits = re.sub(r'\D', '', cc)
        if len(digits) >= 12:
            masked_cc = '*' * (len(digits) - 4) + digits[-4:]
            masked_text = masked_text.replace(cc, masked_cc)
    
    # SSN pattern (US)
    ssn_pattern = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
    ssns = re.findall(ssn_pattern, text)
    for ssn in ssns:
        masked_ssn = '***-**-' + re.sub(r'\D', '', ssn)[-4:]
        masked_text = masked_text.replace(ssn, masked_ssn)
    
    return masked_text


def mask_ip_address(text):
    """
    Mask IP addresses
    """
    if not text:
        return text
    
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    def mask_ipv4(match):
        ip = match.group()
        parts = ip.split('.')
        return f"{parts[0]}.{parts[1]}.***.***"
    
    masked_text = re.sub(ipv4_pattern, mask_ipv4, text)
    
    return masked_text


def anonymize_text(text, use_spacy=False):
    """
    Complete text anonymization pipeline
    """
    if not text:
        return ""
    
    text = str(text)
    
    # Step 1: Mask IP addresses
    text = mask_ip_address(text)
    
    # Step 2: Use regex patterns for masking
    text = detect_and_mask_pii_regex(text)
    
    # Step 3: Mask sensitive keywords
    sensitive_patterns = [
        r'\bpassword\s*[:=]\s*\S+',
        r'\bpin\s*[:=]\s*\d+',
        r'\bsecret\s*[:=]\s*\S+',
        r'\bkey\s*[:=]\s*\S+'
    ]
    
    for pattern in sensitive_patterns:
        text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
    
    return text


def check_pii_content(text):
    """
    Check if text contains PII and return statistics
    """
    if not text:
        return {
            'has_pii': False,
            'pii_types': [],
            'pii_count': 0,
            'masked_text': ''
        }
    
    original_text = text
    masked_text = anonymize_text(text)
    
    pii_types = set()
    pii_count = 0
    
    # Check for common PII indicators
    checks = [
        ('EMAIL', r'\S+@\S+'),
        ('PHONE', r'\+?\d[\d\s\-\(\)]{7,}\d'),
        ('CREDIT_CARD', r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        ('SSN', r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),
        ('IP', r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    ]
    
    for pii_type, pattern in checks:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        if matches:
            pii_types.add(pii_type)
            pii_count += len(matches)
    
    return {
        'has_pii': len(pii_types) > 0,
        'pii_types': list(pii_types),
        'pii_count': pii_count,
        'masked_text': masked_text,
        'original_length': len(original_text),
        'masked_length': len(masked_text)
    }