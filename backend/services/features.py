import re
import numpy as np
import pandas as pd
from collections import Counter
import urllib.parse
from .preprocess import preprocess_text, extract_entities, calculate_text_metrics
from .language import detect_language

# Scam indicator keywords (Multilingual)
SCAM_KEYWORDS = {
    'urgency': [
        'urgent', 'immediate', 'asap', 'right away', 'hurry', 'limited time', 'act now', 'final reminder', '24 hours',
        'तुरंत', 'जल्द', 'शीघ्र', 'अभी', 'अंतिम', 'सीमित समय', # Hindi
        'உடனடியாக', 'அவசரம்', 'இப்போதே', 'கடைசி', 'நேரம் குறைவு', # Tamil
        'urgente', 'inmediato', 'ahora', 'tiempo limitado', 'último aviso', # Spanish
        'urgent', 'immédiat', 'dépêchez-vous', 'temps limité', # French
        'sofort', 'eilig', 'jetzt', 'begrenzte zeit', # German
        'срочно', 'немедленно', 'сейчас', 'ограниченное время', # Russian
        '紧急', '立即', '马上', '最后机会', '限时', # Chinese
        '緊急', '今すぐ', '直ちに', '期間限定', # Japanese
        '긴급', '즉시', '지금', '마지막 기회' # Korean
    ],
    'financial': [
        'money', 'cash', 'pay', 'payment', 'transfer', 'wire', 'bitcoin', 'crypto', 'paypal', 'security deposit', 
        'registration fee', 'google pay', 'phonepe', 'bank transfer', 'refundable', 'rupees', 'inr', 'fees', 'deposit',
        'पैसे', 'भुगतान', 'पंजीकरण शुल्क', 'जमा', 'बैंक ट्रांसफर', 'रिफंडेबल', # Hindi
        'பணம்', 'கட்டணம்', 'பதிவு கட்டணம்', 'வங்கி மாற்றம்', 'முன்பணம்', # Tamil
        'dinero', 'pago', 'transferencia', 'depósito', 'tarifa de registro', # Spanish
        'argent', 'paiement', 'virement', 'dépôt de garantie', 'frais', # French
        'geld', 'zahlung', 'überweisung', 'kaution', 'gebühren', # German
        'деньги', 'оплата', 'перевод', 'депозит', 'регистрационный взнос', # Russian
        '钱', '支付', '转账', '押金', '注册费', # Chinese
        'お金', '支払い', '振込', 'デポジット', '登録料', # Japanese
        '돈', '결제', '이체', '보증금', '등록비' # Korean
    ],
    'opportunity': [
        'earn', 'income', 'profit', 'guaranteed', 'risk-free', 'no risk', 'get rich', 'work from home', 'part time',
        'कमाएं', 'आय', 'लाभ', 'गारंटी', 'घर बैठे काम', # Hindi
        'சம்பாதிக்க', 'வருமானம்', 'உத்தரவாதம்', 'வீட்டிலிருந்தே வேலை', # Tamil
        'ganar', 'ingresos', 'beneficios', 'garantizado', 'trabajo desde casa', # Spanish
        'gagner', 'revenu', 'profit', 'garanti', 'travail à domicile', # French
        'verdienen', 'einkommen', 'profit', 'garantiert', 'homeoffice', # German
        'заработать', 'доход', 'прибыль', 'гарантировано', 'работа на дому', # Russian
        '赚', '收入', '利润', '有保障', '居家办公', # Chinese
        '稼ぐ', '収入', '利益', '保証', '在宅勤務', # Japanese
        '수익', '소득', '이익', '보장', '재택근무' # Korean
    ],
    'requirement': [
        'no experience', 'no skills', 'anyone can', 'easy work', 'simple job', 'data entry',
        'कोई अनुभव नहीं', 'आसान काम', 'डाटा एंट्री', # Hindi
        'அனுபவம் தேவையில்லை', 'எளிதான வேலை', 'டேட்டா என்ட்ரி', # Tamil
        'sin experiencia', 'sin habilidades', 'trabajo fácil', # Spanish
        'sans expérience', 'travail facile', # French
        'keine erfahrung', 'einfache arbeit', # German
        'без опыта', 'простая работа', # Russian
        '无需经验', '任何人都行', '简单工作', # Chinese
        '未経験', '誰でも', '簡単な仕事', # Japanese
        '경력 무관', '누구나', '쉬운 일' # Korean
    ],
    'contact': [
        'whatsapp', 'telegram', 'signal', 'wire', 'skype', 'email only', 'message me',
        'व्हाट्सएप', 'टेलीग्राम', 'संदेश', # Hindi
        'வாட்ஸ்அப்', 'டெலிகிராம்', # Tamil
        'contacto', 'mensaje', # Spanish
        'contactez-moi', 'message', # French
        'kontakt', 'nachricht', # German
        'связаться', 'сообщение', # Russian
        '联系', '私信', # Chinese
        '連絡', 'メッセージ', # Japanese
        '연락', '메시지' # Korean
    ],
    'suspicious': [
        'confidential', 'secret', 'exclusive', 'private', 'hidden', 'underground', 'training fee', 'processing fee',
        'गोपनीय', 'गुप्त', 'प्रशिक्षण शुल्क', # Hindi
        'ரகசியம்', 'பயிற்சி கட்டணம்', # Tamil
        'confidencial', 'secreto', 'tarifa de procesamiento', # Spanish
        'confidentiel', 'secret', 'frais de formation', # French
        'vertraulich', 'geheim', 'bearbeitungsgebühr', # German
        'конфиденциально', 'секретно', 'плата за обучение', # Russian
        '机密', '秘密', '培训费', # Chinese
        '機密', '秘密', '研修費', # Japanese
        '기밀', '비밀', '교육비' # Korean
    ]
}

# Legitimate indicator keywords (Multilingual)
LEGIT_KEYWORDS = {
    'professional': [
        'official website', 'careers portal', 'linkedin', 'corporate', 'established', 'hiring for', 'position at',
        'equal opportunity employer', 'diversity and inclusion', 'benefits include', 'health insurance', 'retirement plan',
        'professional development', 'career growth', 'reports to', 'collaborative environment', 'company culture',
        'आधिकारिक वेबसाइट', 'कॉर्पोरेट', 'समान अवसर नियोक्ता', # Hindi
        'அதிகாரப்பூர்வ இணையதளம்', # Tamil
        'sitio oficial', 'corporativo', 'empleador de igualdad de oportunidades', # Spanish
        'site officiel', 'entreprise', 'employeur garantissant l\'égalité des chances', # French
        'offizielle website', 'unternehmen', 'chancengleichheit', # German
        'официальный сайт', 'корпоративный', 'равные возможности', # Russian
        '官方网站', '企业', '平等机会', # Chinese
        '公式サイト', '企業', '機会均等', # Japanese
        '공식 홈페이지', '기업', '평등한 기회' # Korean
    ],
    'requirements': [
        'experience required', 'qualification', 'skills required', 'years of experience', 'job description', 'eligibility',
        'responsibilities', 'key requirements', 'preferred qualifications', 'background check', 'authorized to work',
        'योग्यता', 'कौशल', 'अनुभव आवश्यक', 'जिम्मेदारियां', # Hindi
        'தகுதி', 'அனுபவம் தேவை', # Tamil
        'experiencia requerida', 'calificación', 'responsabilidades', # Spanish
        'expérience requise', 'qualification', 'responsabilités', # French
        'erfahrung erforderlich', 'qualifikation', 'verantwortlichkeiten', # German
        'требуется опыт', 'квалификация', 'обязанности', # Russian
        '需要经验', '任职资格', '职责', # Chinese
        '要経験', '資格', '責任', # Japanese
        '경력 필요', '자격 요건', '책임' # Korean
    ],
    'salary': [
        'market standards', 'as per industry', 'competitive salary', 'per annum',
        'बाजार मानकों', 'प्रति वर्ष', # Hindi
        'சந்தை தரம்', # Tamil
        'estándares de mercado', # Spanish
        'normes du marché', # French
        'marktstandard', # German
        'рыночные стандарты', # Russian
        '市场标准', # Chinese
        '市場基準', # Japanese
        '시장 기준' # Korean
    ],
    'process': [
        'interview', 'application process', 'shortlist', 'evaluation', 'recruitment', 'technical interview', 'teams',
        'साक्षात्कार', 'भर्ती', 'मूल्यांकन', # Hindi
        'நேர்காணல்', 'தேர்வு', # Tamil
        'entrevista', 'reclutamiento', # Spanish
        'entretien', 'recrutement', # French
        'vorstellungsgespräch', 'einstellung', # German
        'интервью', 'набор', # Russian
        '面试', '招聘', # Chinese
        '面接', '採用', # Japanese
        '면접', '채용' # Korean
    ],
    'internship': [
        'affiliated', 'university', 'stipend provided', 'paid internship', 'certificate', 'duration',
        'इंटर्नशिप', 'विश्वविद्यालय', # Hindi
        'பயிற்சி', 'பல்கலைக்கழகம்', # Tamil
        'pasantía', 'universidad', # Spanish
        'stage', 'université', # French
        'praktikum', 'universität', # German
        'стажировка', 'университет', # Russian
        '实习', '大学', # Chinese
        'インターン', '大学', # Japanese
        '인턴십', '대학교' # Korean
    ]
}

def extract_text_features(text, language='en'):
    """
    Extract features from text content
    """
    if not text:
        return {}
    
    text = str(text)
    features = {}
    
    # Basic text metrics
    metrics = calculate_text_metrics(text)
    features.update(metrics)
    
    # Length features
    features['text_length'] = len(text)
    features['word_count'] = len(text.split())
    features['char_count'] = len(text.replace(' ', ''))
    
    # Uppercase ratio
    uppercase_chars = sum(1 for c in text if c.isupper())
    features['uppercase_ratio'] = uppercase_chars / max(len(text), 1)
    
    # Exclamation/question marks
    features['exclamation_count'] = text.count('!')
    features['question_count'] = text.count('?')
    
    # Numeric content
    digits = sum(c.isdigit() for c in text)
    features['digit_ratio'] = digits / max(len(text), 1)
    
    # Special characters
    special_chars = sum(not c.isalnum() and not c.isspace() for c in text)
    features['special_char_ratio'] = special_chars / max(len(text), 1)
    
    # Spam keyword detection (with negation handling)
    text_lower = text.lower()
    scam_keyword_counts = {}
    total_scam_keywords = 0
    
    # Common negation words to ignore high-risk terms
    negations = r'\b(no|not|don\'t|never|free|without|void|neither|nor)\b'
    
    for category, keywords in SCAM_KEYWORDS.items():
        count = 0
        for kw in keywords:
            # Check if keyword exists but is NOT preceded by a negation word (approx 3 words before)
            # Find all instances of the keyword
            for match in re.finditer(re.escape(kw), text_lower):
                start = match.start()
                # Check preceding 50 characters for negation words
                preceding = text_lower[max(0, start-50):start]
                if not re.search(negations, preceding):
                    count += 1
        
        scam_keyword_counts[f'scam_{category}_count'] = count
        total_scam_keywords += count
    
    # Legitimate keyword detection
    legit_keyword_counts = {}
    total_legit_keywords = 0
    for category, keywords in LEGIT_KEYWORDS.items():
        count = 0
        for kw in keywords:
            count += len(re.findall(re.escape(kw), text_lower))
        legit_keyword_counts[f'legit_{category}_count'] = count
        total_legit_keywords += count
    
    features.update(scam_keyword_counts)
    features.update(legit_keyword_counts)
    features['total_scam_keywords'] = total_scam_keywords
    features['total_legit_keywords'] = total_legit_keywords
    features['scam_keyword_density'] = total_scam_keywords / max(len(text.split()), 1)
    features['legit_keyword_density'] = total_legit_keywords / max(len(text.split()), 1)
    
    # Email and URL features
    email_count = len(re.findall(r'\S+@\S+', text))
    url_count = len(re.findall(r'https?://\S+|www\.\S+', text))
    
    features['email_count'] = email_count
    features['url_count'] = url_count
    features['has_email'] = 1 if email_count > 0 else 0
    features['has_url'] = 1 if url_count > 0 else 0
    
    # Phone number detection
    phone_patterns = [
        r'\+\d[\d\s\-\(\)]{7,}\d',
        r'\b\d[\d\s\-\(\)]{7,}\d\b'
    ]
    phone_count = 0
    for pattern in phone_patterns:
        phone_count += len(re.findall(pattern, text))
    
    features['phone_count'] = phone_count
    features['has_phone'] = 1 if phone_count > 0 else 0
    
    # Grammar and spelling (simple heuristic)
    common_words = ['the', 'and', 'you', 'that', 'for', 'with', 'this', 'have', 'from']
    uncommon_ratio = sum(1 for word in text_lower.split() if word not in common_words) / max(len(text.split()), 1)
    features['uncommon_word_ratio'] = uncommon_ratio
    
    # Readability features
    sentences = text.split('.')
    features['avg_sentence_length'] = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    features['sentence_count'] = len(sentences)
    
    # Entity features
    entities = extract_entities(text, language)
    features['person_count'] = len(entities['persons'])
    features['organization_count'] = len(entities['organizations'])
    features['location_count'] = len(entities['locations'])
    
    return features

def extract_url_features(url):
    """
    Extract features from URL
    """
    if not url:
        return {}
    
    features = {}
    
    try:
        parsed = urllib.parse.urlparse(url)
        
        # URL length features
        features['url_length'] = len(url)
        features['domain_length'] = len(parsed.netloc)
        features['path_length'] = len(parsed.path)
        
        # Suspicious TLDs
        suspicious_tlds = ['.xyz', '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.loan', '.win']
        features['has_suspicious_tld'] = 1 if any(parsed.netloc.endswith(tld) for tld in suspicious_tlds) else 0
        
        # IP address in URL
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        features['has_ip_address'] = 1 if re.search(ip_pattern, parsed.netloc) else 0
        
        # Subdomain count
        subdomains = parsed.netloc.split('.')
        features['subdomain_count'] = len(subdomains) - 2  # Subtract domain and TLD
        
        # HTTPS
        features['is_https'] = 1 if parsed.scheme == 'https' else 0
        
        # Special characters in domain
        special_chars = sum(not c.isalnum() and c != '.' and c != '-' for c in parsed.netloc)
        features['domain_special_chars'] = special_chars
        
        # Numerical characters in domain
        numerical_chars = sum(c.isdigit() for c in parsed.netloc)
        features['domain_numerical_chars'] = numerical_chars
        
        # Shortened URL detection
        shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 't.co']
        features['is_shortened'] = 1 if any(shortener in parsed.netloc for shortener in shorteners) else 0
        
    except:
        # If URL parsing fails, use basic features
        features['url_length'] = len(url)
        features['has_suspicious_tld'] = 0
        features['is_https'] = 0
    
    return features

def extract_email_features(email):
    """
    Extract features from email content
    """
    if not email:
        return {}
    
    features = {}
    
    # Basic email features
    features['email_length'] = len(email)
    
    # Greeting detection
    greetings = ['dear', 'hello', 'hi', 'greetings', 'good morning', 'good afternoon']
    features['has_greeting'] = 1 if any(greet in email.lower()[:100] for greet in greetings) else 0
    
    # Signature detection
    signatures = ['regards', 'sincerely', 'best', 'thank you', 'thanks', 'cheers']
    features['has_signature'] = 1 if any(sig in email.lower()[-200:] for sig in signatures) else 0
    
    # Subject line features (if present)
    if 'subject:' in email.lower():
        subject_start = email.lower().find('subject:')
        subject_end = email.find('\n', subject_start)
        if subject_end > subject_start:
            subject = email[subject_start:subject_end]
            features['subject_length'] = len(subject)
            features['subject_has_urgency'] = 1 if any(word in subject.lower() for word in SCAM_KEYWORDS['urgency']) else 0
    
    # Attachment mention
    attachment_keywords = ['attachment', 'attached', 'enclosed', 'file attached', 'document']
    features['mentions_attachment'] = 1 if any(keyword in email.lower() for keyword in attachment_keywords) else 0
    
    # Request for action
    action_keywords = ['click here', 'click below', 'download', 'open', 'reply', 'respond']
    features['requests_action'] = 1 if any(keyword in email.lower() for keyword in action_keywords) else 0
    
    return features

def extract_metadata_features(metadata):
    """
    Extract features from metadata
    """
    if not metadata:
        return {}
    
    features = {}
    
    # Sender email features
    sender_email = metadata.get('sender_email', '')
    if sender_email:
        features['sender_email_length'] = len(sender_email)
        
        # Free email providers
        free_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        features['is_free_email'] = 1 if any(provider in sender_email.lower() for provider in free_providers) else 0
        
        # Suspicious domains
        suspicious_domains = ['.xyz', '.tk', '.ml', '.ga', '.cf']
        features['has_suspicious_domain'] = 1 if any(sender_email.endswith(domain) for domain in suspicious_domains) else 0
    
    # Phone number features
    phone = metadata.get('phone', '')
    if phone:
        features['phone_length'] = len(phone)
        
        # International numbers
        features['is_international'] = 1 if phone.startswith('+') else 0
        
        # Suspicious country codes
        suspicious_codes = ['+234', '+44', '+91', '+1']  # Nigeria, UK, India, US/Canada
        features['has_suspicious_code'] = 1 if any(phone.startswith(code) for code in suspicious_codes) else 0
    
    # Timestamp features
    timestamp = metadata.get('timestamp', '')
    if timestamp:
        try:
            # Check if timestamp is recent
            import datetime
            ts_dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.datetime.utcnow()
            hours_diff = (now - ts_dt).total_seconds() / 3600
            features['hours_since_submission'] = hours_diff
        except:
            features['hours_since_submission'] = 0
    
    return features

def extract_features(text, metadata=None, language='en'):
    """
    Main feature extraction function
    """
    if metadata is None:
        metadata = {}
    
    # Detect language if not provided
    if not language:
        from .language import detect_language
        language = detect_language(text)
    
    # Extract all features
    features = {}
    features['text'] = text  # Add raw text for model prediction fallback
    
    # Text features
    text_features = extract_text_features(text, language)
    features.update(text_features)
    
    # URL features (if text contains URL)
    url_pattern = r'https?://\S+|www\.\S+'
    urls = re.findall(url_pattern, text)
    if urls:
        url_features = extract_url_features(urls[0])  # Use first URL
        features.update({f'url_{k}': v for k, v in url_features.items()})
    
    # Email features (if text looks like email)
    if '@' in text and ('subject:' in text.lower() or 'dear' in text.lower()):
        email_features = extract_email_features(text)
        features.update({f'email_{k}': v for k, v in email_features.items()})
    
    # Metadata features
    if metadata:
        metadata_features = extract_metadata_features(metadata)
        features.update({f'meta_{k}': v for k, v in metadata_features.items()})
    
    # Language feature
    features['language'] = language
    
    # Add feature indices
    for i, (key, value) in enumerate(list(features.items())):
        features[f'feature_{i}'] = value
    
    return features

def normalize_features(features):
    """
    Normalize feature values to [0, 1] range
    """
    normalized = {}
    
    # Define normalization ranges for known features
    normalization_ranges = {
        'text_length': (0, 10000),
        'word_count': (0, 2000),
        'scam_keyword_density': (0, 0.5),
        'uppercase_ratio': (0, 1),
        'digit_ratio': (0, 1),
        'url_length': (0, 200),
        'email_length': (0, 10000)
    }
    
    for key, value in features.items():
        if isinstance(value, (int, float)):
            if key in normalization_ranges:
                min_val, max_val = normalization_ranges[key]
                if max_val > min_val:
                    normalized_val = (value - min_val) / (max_val - min_val)
                    normalized_val = max(0, min(1, normalized_val))  # Clip to [0, 1]
                    normalized[key] = normalized_val
                else:
                    normalized[key] = 0
            else:
                # Simple normalization for unknown features
                if abs(value) > 1:
                    normalized[key] = min(1, value / 100)
                else:
                    normalized[key] = value
        else:
            normalized[key] = value
    
    return normalized

def get_feature_names():
    """
    Get list of all feature names
    """
    # This should match the features extracted above
    base_features = [
        'text_length', 'word_count', 'char_count', 'uppercase_ratio',
        'exclamation_count', 'question_count', 'digit_ratio',
        'special_char_ratio', 'total_scam_keywords', 'scam_keyword_density',
        'email_count', 'url_count', 'has_email', 'has_url',
        'phone_count', 'has_phone', 'uncommon_word_ratio',
        'avg_sentence_length', 'sentence_count',
        'person_count', 'organization_count', 'location_count'
    ]
    
    scam_keyword_features = [f'scam_{category}_count' for category in SCAM_KEYWORDS.keys()]
    
    url_features = [
        'url_length', 'domain_length', 'path_length', 'has_suspicious_tld',
        'has_ip_address', 'subdomain_count', 'is_https',
        'domain_special_chars', 'domain_numerical_chars', 'is_shortened'
    ]
    
    email_features = [
        'email_length', 'has_greeting', 'has_signature',
        'subject_length', 'subject_has_urgency',
        'mentions_attachment', 'requests_action'
    ]
    
    metadata_features = [
        'sender_email_length', 'is_free_email', 'has_suspicious_domain',
        'phone_length', 'is_international', 'has_suspicious_code',
        'hours_since_submission'
    ]
    
    all_features = (base_features + scam_keyword_features + 
                   ['url_' + f for f in url_features] +
                   ['email_' + f for f in email_features] +
                   ['meta_' + f for f in metadata_features] +
                   ['language'])
    
    return all_features