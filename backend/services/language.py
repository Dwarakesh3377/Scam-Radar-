"""
Language Detection Service
==========================
Detects language of text using langdetect with fallback.
"""

from langdetect import detect as langdetect_detect
from langdetect import DetectorFactory

# Ensure consistent results
DetectorFactory.seed = 0
try:
    from langdetect import init_profiles
    init_profiles()
except:
    pass


def detect_language(text):
    """
    Detect language of text using langdetect
    """
    if not text or len(text.strip()) < 10:
        return 'en'  # Default to English for short texts
    
    try:
        detected = langdetect_detect(text)
        
        # Map langdetect codes to our supported languages
        supported_languages = {
            'en': 'en', 'ta': 'ta', 'hi': 'hi', 'fr': 'fr',
            'es': 'es', 'de': 'de', 'ja': 'ja', 'zh-cn': 'zh',
            'zh-tw': 'zh', 'ru': 'ru', 'ko': 'ko'
        }
        
        if detected in supported_languages:
            return supported_languages[detected]
        
        # Default to English if not supported
        return 'en'
        
    except Exception as e:
        print(f"Language detection error: {str(e)}")
        return 'en'


def is_supported_language(lang_code):
    """
    Check if language code is supported
    """
    supported = ['en', 'ta', 'hi', 'fr', 'es', 'de', 'ja', 'zh', 'ru', 'ko']
    return lang_code in supported


def get_language_name(lang_code):
    """
    Get language name from code
    """
    language_names = {
        'en': 'English',
        'ta': 'Tamil',
        'hi': 'Hindi',
        'fr': 'French',
        'es': 'Spanish',
        'de': 'German',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ru': 'Russian',
        'ko': 'Korean'
    }
    return language_names.get(lang_code, 'Unknown')


def get_language_flag(lang_code):
    """
    Get flag emoji for language
    """
    flags = {
        'en': '🇺🇸',
        'ta': '🇮🇳',
        'hi': '🇮🇳',
        'fr': '🇫🇷',
        'es': '🇪🇸',
        'de': '🇩🇪',
        'ja': '🇯🇵',
        'zh': '🇨🇳',
        'ru': '🇷🇺',
        'ko': '🇰🇷'
    }
    return flags.get(lang_code, '🌐')


def detect_multilingual(text):
    """
    Detect if text contains multiple languages
    """
    if not text:
        return False
    
    # Split text into sentences
    sentences = text.split('.')
    languages = set()
    
    for sentence in sentences:
        if len(sentence.strip()) > 20:
            lang = detect_language(sentence)
            languages.add(lang)
            if len(languages) > 1:
                return True
    
    return False


def get_all_supported_languages():
    """
    Get list of all supported languages with details
    """
    return [
        {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
        {'code': 'ta', 'name': 'Tamil', 'flag': '🇮🇳'},
        {'code': 'hi', 'name': 'Hindi', 'flag': '🇮🇳'},
        {'code': 'fr', 'name': 'French', 'flag': '🇫🇷'},
        {'code': 'es', 'name': 'Spanish', 'flag': '🇪🇸'},
        {'code': 'de', 'name': 'German', 'flag': '🇩🇪'},
        {'code': 'ja', 'name': 'Japanese', 'flag': '🇯🇵'},
        {'code': 'zh', 'name': 'Chinese', 'flag': '🇨🇳'},
        {'code': 'ru', 'name': 'Russian', 'flag': '🇷🇺'},
        {'code': 'ko', 'name': 'Korean', 'flag': '🇰🇷'}
    ]