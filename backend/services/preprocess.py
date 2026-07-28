"""
Text Preprocessing Service
==========================
Clean and preprocess text for analysis.
"""

import re
import string


# Download NLTK data (will be done on first import)
def ensure_nltk_data():
    """Ensure NLTK data is downloaded"""
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
    except:
        pass


# Try to set up NLTK
ensure_nltk_data()


def clean_text(text, language='en'):
    """
    Clean and normalize text
    """
    if not text:
        return ""
    
    # Convert to string
    text = str(text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '[URL]', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    
    # Remove phone numbers
    text = re.sub(r'\+?\d[\d\s\-\(\)]{7,}\d', '[PHONE]', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?\-]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def tokenize_text(text, language='en'):
    """
    Tokenize text into words
    """
    if not text:
        return []
    
    # Clean text first
    text = clean_text(text, language)
    
    # Simple tokenization by splitting on whitespace
    tokens = text.split()
    
    return tokens


def remove_stopwords(tokens, language='en'):
    """
    Remove stopwords from tokens
    """
    try:
        from nltk.corpus import stopwords
        lang_map = {
            'en': 'english',
            'fr': 'french',
            'es': 'spanish',
            'de': 'german'
        }
        nltk_lang = lang_map.get(language, 'english')
        stop_words = set(stopwords.words(nltk_lang))
    except:
        # Fallback stopwords
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about',
                      'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'between', 'under', 'again', 'further', 'then',
                      'once', 'here', 'there', 'when', 'where', 'why', 'how',
                      'all', 'each', 'few', 'more', 'most', 'other', 'some',
                      'such', 'only', 'own', 'same', 'so',
                      'than', 'too', 'very', 's', 't', 'just', 'now'}
    
    # CRITICAL: Always preserve negations for scam detection
    negation_words = {'no', 'not', 'nor', 'neither', 'don', 'dont', 'none', 'without', 'never'}
    stop_words = stop_words - negation_words

    # Add custom stopwords
    custom_stopwords = {
        'http', 'https', 'www', 'com', 'org', 'net', 'html',
        '[url]', '[email]', '[phone]', '...', '..'
    }
    stop_words.update(custom_stopwords)
    
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    return filtered_tokens


def preprocess_text(text, language='en'):
    """
    Complete text preprocessing pipeline
    """
    if not text:
        return ""
    
    # Step 1: Clean text
    cleaned = clean_text(text, language)
    
    # Step 2: Tokenize
    tokens = tokenize_text(cleaned, language)
    
    # Step 3: Remove stopwords
    tokens = remove_stopwords(tokens, language)
    
    # Step 4: Remove duplicates but preserve order
    seen = set()
    unique_tokens = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    # Join back to string
    processed_text = ' '.join(unique_tokens)
    
    return processed_text


def extract_entities(text, language='en'):
    """
    Extract named entities using regex patterns
    """
    if not text:
        return {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'emails': [],
            'urls': []
        }
    
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': [],
        'money': [],
        'emails': [],
        'urls': []
    }
    
    # Extract emails
    emails = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
    entities['emails'] = list(set(emails))
    
    # Extract URLs
    urls = re.findall(r'https?://\S+|www\.\S+', text)
    entities['urls'] = list(set(urls))
    
    # Extract money amounts
    money = re.findall(r'\$[\d,]+(?:\.\d{2})?|\d+\s*(?:dollars|usd|euros|eur|pounds|gbp)', text, re.IGNORECASE)
    entities['money'] = list(set(money))
    
    # Extract dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, text, re.IGNORECASE)
        entities['dates'].extend(dates)
    entities['dates'] = list(set(entities['dates']))
    
    return entities


def calculate_text_metrics(text):
    """
    Calculate various text metrics
    """
    if not text:
        return {
            'word_count': 0,
            'sentence_count': 0,
            'avg_word_length': 0,
            'readability_score': 0,
            'spam_keywords': 0
        }
    
    # Word count
    words = text.split()
    word_count = len(words)
    
    # Sentence count
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    sentence_count = len(sentences) or 1
    
    # Average word length
    if word_count > 0:
        avg_word_length = sum(len(word) for word in words) / word_count
    else:
        avg_word_length = 0
    
    # Readability score (simple version)
    if sentence_count > 0 and word_count > 0:
        readability = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * avg_word_length
    else:
        readability = 0
    
    # Spam keyword detection
    spam_keywords = [
        'urgent', 'immediate', 'guaranteed', 'free', 'winner', 'prize',
        'congratulations', 'click', 'limited', 'offer', 'discount',
        'credit', 'loan', 'investment', 'profit', 'earn', 'money',
        'work from home', 'no experience', 'apply now', 'limited time'
    ]
    
    spam_count = 0
    text_lower = text.lower()
    for keyword in spam_keywords:
        if keyword in text_lower:
            spam_count += 1
    
    return {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_word_length': round(avg_word_length, 2),
        'readability_score': round(readability, 2),
        'spam_keywords': spam_count
    }