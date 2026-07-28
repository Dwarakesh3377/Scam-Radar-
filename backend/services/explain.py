import numpy as np
import shap 
from collections import Counter
import re

def generate_shap_explanations(features, risk_score, ui_language='en'):
    """
    Generate SHAP-based explanations for predictions
    """
    try:
        # Create a simple explainer (in production, use actual SHAP)
        explanations = []
        
        # Analyze features for explanations
        feature_importance = analyze_feature_importance(features, risk_score)
        
        # Get top contributing features
        top_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]  # Top 5 features
        
        for feature_name, importance in top_features:
            explanation = generate_feature_explanation(
                feature_name, 
                features.get(feature_name, 0),
                importance,
                ui_language
            )
            if explanation:
                explanations.append(explanation)
        
        # Add general explanations based on risk score
        general_explanations = get_general_explanations(risk_score, ui_language)
        explanations.extend(general_explanations)
        
        return explanations[:10]  # Limit to 10 explanations
        
    except Exception as e:
        print(f"Error generating SHAP explanations: {str(e)}")
        return ["Explanation generation failed"]

def analyze_feature_importance(features, risk_score):
    """
    Analyze feature importance for explanations
    """
    importance = {}
    
    # Define feature impact rules
    impact_rules = {
        'scam_urgency_count': lambda x: x * 5,
        'scam_financial_count': lambda x: x * 4,
        'has_suspicious_tld': lambda x: 25 if x > 0 else 0,
        'meta_has_suspicious_domain': lambda x: 25 if x > 0 else 0,
        'uppercase_ratio': lambda x: x * 50 if x > 0.7 else 0,
        'exclamation_count': lambda x: min(10, x * 2),
        'email_has_greeting': lambda x: -10 if x == 0 else 0,
        'meta_is_free_email': lambda x: 10 if x > 0 else 0,
        'meta_is_international': lambda x: 15 if x > 0 else 0,
        'scam_keyword_density': lambda x: x * 100,
        'total_scam_keywords': lambda x: min(30, x * 3),
        'has_url': lambda x: 15 if x > 0 else 0,
        'has_email': lambda x: 10 if x > 0 else 0,
        'has_phone': lambda x: 10 if x > 0 else 0,
        'digit_ratio': lambda x: x * 20 if x > 0.2 else 0,
        'special_char_ratio': lambda x: x * 30 if x > 0.3 else 0
    }
    
    # Calculate importance for each feature
    for feature_name, rule in impact_rules.items():
        if feature_name in features:
            value = features[feature_name]
            try:
                impact = rule(value)
                importance[feature_name] = impact
            except:
                importance[feature_name] = 0
    
    return importance

def generate_feature_explanation(feature_name, feature_value, importance, ui_language='en'):
    """
    Generate human-readable explanation for a feature
    """
    # Map feature names to explanations
    explanation_templates = {
        'scam_urgency_count': {
            'en': "Contains {count} urgency keywords (e.g., 'urgent', 'immediate')",
            'ta': "{count} அவசர முக்கிய சொற்கள் உள்ளன (எ.கா., 'அவசர', 'உடனடி')",
            'hi': "{count} अत्यावश्यक कीवर्ड शामिल हैं (जैसे, 'जरूरी', 'तत्काल')",
            'fr': "Contient {count} mots-clés d'urgence (ex: 'urgent', 'immédiat')",
            'es': "Contiene {count} palabras clave de urgencia (ej: 'urgente', 'inmediato')",
            'de': "Enthält {count} Dringlichkeits-Keywords (z. B. 'dringend', 'sofort')",
            'ru': "Содержит {count} ключевых слов срочности (например, 'срочно', 'немедленно')",
            'zh': "包含 {count} 个紧急关键词（例如：'紧急'、'立即'）",
            'ja': "{count} 個の緊急キーワードが含まれています（例：'緊急'、'至急'）",
            'ko': "{count}개의 긴급 키워드가 포함되어 있습니다 (예: '긴급', '즉시')"
        },
        'scam_financial_count': {
            'en': "Contains {count} financial keywords (e.g., 'money', 'payment')",
            'ta': "{count} நிதி முக்கிய சொற்கள் உள்ளன (எ.கா., 'பணம்', 'கட்டணம்')",
            'hi': "{count} वित्तीय कीवर्ड शामिल हैं (जैसे, 'पैसा', 'भुगतान')",
            'fr': "Contient {count} mots-clés financiers (ex: 'argent', 'paiement')",
            'es': "Contiene {count} palabras clave financieras (ej: 'dinero', 'pago')",
            'de': "Enthält {count} Finanz-Keywords (z. B. 'Geld', 'Zahlung')",
            'ru': "Содержит {count} финансовых ключевых слов (например, 'деньги', 'оплата')",
            'zh': "包含 {count} 个财务关键词（例如：'金钱'、'付款'）",
            'ja': "包含 {count} 个财务关键词（例如：'金钱'、'付款'）",
            'ko': "{count}개의 금융 키워드가 포함되어 있습니다 (예: '돈', '결제')"
        },
        'has_suspicious_tld': {
            'en': "Uses suspicious domain extension (.xyz, .tk, etc.)",
            'ta': "சந்தேகத்திற்குரிய டொமைன் நீட்டிப்பைப் பயன்படுத்துகிறது (.xyz, .tk, போன்றவை)",
            'hi': "संदिग्ध डोमेन एक्सटेंशन का उपयोग करता है (.xyz, .tk, आदि)",
            'fr': "Utilise une extension de domaine suspecte (.xyz, .tk, etc.)",
            'es': "Utiliza una extensión de dominio sospechosa (.xyz, .tk, etc.)",
            'de': "Verwendet verdächtige Domain-Endungen (.xyz, .tk usw.)",
            'ru': "Использует подозрительное расширение домена (.xyz, .tk и т. д.)",
            'zh': "使用可疑的域名后缀（.xyz、.tk 等）",
            'ja': "不審なドメイン拡張子（.xyz、.tk など）を使用しています",
            'ko': "의심스러운 도메인 확장자(.xyz, .tk 등)를 사용합니다"
        },
        'uppercase_ratio': {
            'en': "Excessive use of uppercase letters ({ratio}% of text)",
            'ta': "மேல் வரிசை எழுத்துக்களின் அதிகப்படியான பயன்பாடு ({ratio}% உரை)",
            'hi': "अपरकेस अक्षरों का अत्यधिक उपयोग ({ratio}% पाठ)",
            'fr': "Usage excessif de majuscules ({ratio}% du texte)",
            'es': "Uso excesivo de letras mayúsculas ({ratio}% del texto)",
            'de': "Übermäßiger Gebrauch von Großbuchstaben ({ratio}% des Textes)",
            'ru': "Чрезмерное использование заглавных букв ({ratio}% текста)",
            'zh': "过度使用大写字母（占文本的 {ratio}%）",
            'ja': "大文字の過剰な使用（テキストの {ratio}%）",
            'ko': "대문자의 과도한 사용 (텍스트의 {ratio}%)"
        },
        'exclamation_count': {
            'en': "Multiple exclamation marks ({count} found)",
            'ta': "பல ஆச்சரியக்குறிகள் ({count} காணப்பட்டது)",
            'hi': "कई विस्मयादिबोधक चिह्न ({count} पाए गए)",
            'fr': "Plusieurs points d'exclamation ({count} trouvés)",
            'es': "Múltiples signos de exclamación ({count} encontrados)",
            'de': "Mehrere Ausrufezeichen ({count} gefunden)",
            'ru': "Несколько восклицательных знаков (найдено {count})",
            'zh': "多个感叹号（发现 {count} 个）",
            'ja': "複数の感嘆符（{count} 個検出）",
            'ko': "여러 개의 느낌표 ({count}개 발견)"
        },
        'email_has_greeting': {
            'en': "No proper greeting in email",
            'ta': "மின்னஞ்சலில் சரியான வாழ்த்து இல்லை",
            'hi': "ईमेल में उचित अभिवादन नहीं है",
            'fr': "Pas de salutation appropriée dans l'e-mail",
            'es': "No hay un saludo adecuado en el correo electrónico",
            'de': "Keine ordnungsgemäße Begrüßung in der E-Mail",
            'ru': "В письме отсутствует надлежащее приветствие",
            'zh': "邮件中没有恰당的问候语",
            'ja': "メールに適切な挨拶がありません",
            'ko': "이메일에 적절한 인사말이 없습니다"
        },
        'meta_is_free_email': {
            'en': "Uses free email provider (Gmail, Yahoo, etc.)",
            'ta': "இலவச மின்னஞ்சல் வழங்குநரைப் பயன்படுத்துகிறது (Gmail, Yahoo, போன்றவை)",
            'hi': "मुफ्त ईमेल प्रदाता का उपयोग करता है (Gmail, Yahoo, आदि)",
            'fr': "Utilise un fournisseur d'e-mail gratuit (Gmail, Yahoo, etc.)",
            'es': "Utiliza un proveedor de correo gratuito (Gmail, Yahoo, etc.)",
            'de': "Verwendet einen kostenlosen E-Mail-Anbieter (Gmail, Yahoo usw.)",
            'ru': "Использует бесплатный почтовый сервис (Gmail, Yahoo и т. д.)",
            'zh': "使用免费电子邮件提供商（Gmail、Yahoo 等）",
            'ja': "無料のメールプロバイダー（Gmail、Yahoo など）を使用しています",
            'ko': "무료 이메일 공급자(Gmail, Yahoo 등)를 사용합니다"
        },
        'meta_is_international': {
            'en': "International contact information detected",
            'ta': "சர்வதேச தொடர்புத் தகவல் கண்டறியப்பட்டது",
            'hi': "अंतर्राष्ट्रीय संपर्क जानकारी का पता चला",
            'fr': "Informations de contact internationales détectées",
            'es': "Se detectó información de contacto internacional",
            'de': "Internationale Kontaktinformationen erkannt",
            'ru': "Обнаружена международная контактная информация",
            'zh': "检测到国际联系信息",
            'ja': "国際的な連絡先情報が検出されました",
            'ko': "국제 연락처 정보가 감지되었습니다"
        },
        'scam_keyword_density': {
            'en': "High density of scam-related keywords ({density} per word)",
            'ta': "மோசடி தொடர்பான முக்கிய சொற்களின் அதிக அடர்த்தி ({density} வார்த்தைக்கு)",
            'hi': "स्कैम-संबंधित कीवर्ड की उच्च घनत्व ({density} प्रति शब्द)",
            'fr': "Haute densité de mots-clés liés aux arnaques ({density} par mot)",
            'es': "Alta densidad de palabras clave relacionadas con estafas ({density} por palabra)",
            'de': "Hohe Dichte an scam-bezogenen Keywords ({density} pro Wort)",
            'ru': "Высокая плотность ключевых слов, связанных с мошенничеством ({density} на слово)",
            'zh': "欺诈相关关键词密度高（每单词 {density} 个）",
            'ja': "詐欺関連キーワードの高密度（1ワードあたり {density}）",
            'ko': "사기 관련 키워드의 높은 밀도 (단어당 {density}개)"
        },
        'total_scam_keywords': {
            'en': "Multiple scam indicators found ({count} total)",
            'ta': "பல மோசடி குறிகாட்டிகள் கண்டறியப்பட்டன ({count} மொத்தம்)",
            'hi': "कई स्कैम संकेतक पाए गए ({count} कुल)",
            'fr': "Plusieurs indicateurs d'arnaque trouvés ({count} au total)",
            'es': "Múltiples indicadores de estafa encontrados ({count} en total)",
            'de': "Mehrere Betrugsindikatoren gefunden ({count} insgesamt)",
            'ru': "Найдено несколько признаков мошенничества (всего {count})",
            'zh': "发现多个欺诈指标（共 {count} 个）",
            'ja': "複数の詐欺インジケーターが見つかりました（合計 {count} 個）",
            'ko': "여러 개의 사기 지표가 발견되었습니다 (총 {count}개)"
        }
    }
    
    if feature_name not in explanation_templates:
        return None
    
    # Get template for current language
    templates = explanation_templates[feature_name]
    template = templates.get(ui_language, templates['en'])
    
    # Format the explanation
    if 'count' in template:
        explanation = template.format(count=int(feature_value))
    elif 'ratio' in template:
        ratio = int(feature_value * 100)
        explanation = template.format(ratio=ratio)
    elif 'density' in template:
        density = round(feature_value, 2)
        explanation = template.format(density=density)
    else:
        explanation = template
    
    # Add impact indicator
    if importance > 0:
        impact_level = "high" if importance > 15 else "medium" if importance > 5 else "low"
        impact_text = {
            'en': f" ({impact_level} impact)",
            'ta': f" ({'அதிக' if impact_level == 'high' else 'நடுத்தர' if impact_level == 'medium' else 'குறைந்த'} தாக்கம்)",
            'hi': f" ({'उच्च' if impact_level == 'high' else 'मध्यम' if impact_level == 'medium' else 'कम'} प्रभाव)",
            'fr': f" ({'fort' if impact_level == 'high' else 'moyen' if impact_level == 'medium' else 'faible'} impact)",
            'es': f" ({'alto' if impact_level == 'high' else 'medio' if impact_level == 'medium' else 'bajo'} impacto)",
            'de': f" ({'hohe' if impact_level == 'high' else 'mittlere' if impact_level == 'medium' else 'geringe'} Auswirkung)",
            'ru': f" ({'высокое' if impact_level == 'high' else 'среднее' if impact_level == 'medium' else 'низкое'} влияние)",
            'zh': f"（{'高' if impact_level == 'high' else '中' if impact_level == 'medium' else '低'}影响）",
            'ja': f"（{'大' if impact_level == 'high' else '中' if impact_level == 'medium' else '小'}な影響）",
            'ko': f" ({'높은' if impact_level == 'high' else '중간' if impact_level == 'medium' else '낮은'} 영향)"
        }
        explanation += impact_text.get(ui_language, impact_text['en'])
    
    return explanation

def get_general_explanations(risk_score, ui_language='en'):
    """
    Get general explanations based on risk score
    """
    explanations = []
    
    if risk_score <= 30:
        templates = {
            'en': [
                "Low risk indicators detected",
                "Professional communication style",
                "Clear and legitimate job requirements",
                "Verified contact information available"
            ],
            'ta': [
                "குறைந்த அபாய குறிகாட்டிகள் கண்டறியப்பட்டன",
                "தொழில்முறை தொடர்பு நடை",
                "தெளிவான மற்றும் சட்டபூர்வமான வேலை தேவைகள்",
                "சரிபார்க்கப்பட்ட தொடர்பு தகவல் கிடைக்கிறது"
            ],
            'hi': [
                "कम जोखिम संकेतक पाए गए",
                "पेशेवर संचार शैली",
                "स्पष्ट और वैध नौकरी आवश्यकताएं",
                "सत्यापित संपर्क जानकारी उपलब्ध"
            ],
            'fr': [
                "Indicateurs de faible risque détectés",
                "Style de communication professionnel",
                "Exigences professionnelles claires et légitimes",
                "Coordonnées vérifiées disponibles"
            ],
            'es': [
                "Indicadores de bajo riesgo detectados",
                "Estilo de comunicación profesional",
                "Requisitos de trabajo claros y legítimos",
                "Información de contacto verificada disponible"
            ],
            'de': [
                "Indikatoren für geringes Risiko erkannt",
                "Professioneller Kommunikationsstil",
                "Klare und legitime Jobanforderungen",
                "Verifizierte Kontaktinformationen verfügbar"
            ],
            'ru': [
                "Обнаружены признаки низкого риска",
                "Профессиональный стиль общения",
                "Четкие и законные требования к работе",
                "Доступна проверенная контактная информация"
            ],
            'zh': [
                "检测到低风险指标",
                "专业的沟通风格",
                "清晰且合法的职位要求",
                "提供已验证的联系信息"
            ],
            'ja': [
                "低リスクのインジケーターが検出されました",
                "プロフェッショナルなコミュニケーションスタイル",
                "明確で合法的な仕事要件",
                "確認済みの連絡先情報が利用可能"
            ],
            'ko': [
                "낮은 위험 지표 감지됨",
                "전문적인 커뮤니케이션 스타일",
                "명확하고 합법적인 직무 요구 사항",
                "확인된 연락처 정보 사용 가능"
            ]
        }
    elif risk_score <= 60:
        templates = {
            'en': [
                "Mixed indicators detected - proceed with caution",
                "Some suspicious elements present",
                "Verify company information before proceeding",
                "Check for official contact channels"
            ],
            'ta': [
                "கலப்பு குறிகாட்டிகள் கண்டறியப்பட்டன - முன்னெச்சரிக்கையுடன் தொடரவும்",
                "சில சந்தேகத்திற்குரிய கூறுகள் உள்ளன",
                "தொடர்வதற்கு முன் நிறுவன தகவலைச் சரிபார்க்கவும்",
                "அதிகாரப்பூர்வ தொடர்பு சேனல்களைச் சரிபார்க்கவும்"
            ],
            'hi': [
                "मिश्रित संकेतक पाए गए - सावधानी से आगे बढ़ें",
                "कुछ संदिग्ध तत्व मौजूद हैं",
                "आगे बढ़ने से पहले कंपनी की जानकारी सत्यापित करें",
                "आधिकारिक संपर्क चैनलों की जांच करें"
            ],
            'fr': [
                "Indicateurs mixtes détectés - procédez avec prudence",
                "Certains éléments suspects sont présents",
                "Vérifiez les informations de l'entreprise avant de continuer",
                "Vérifiez les canaux de contact officiels"
            ],
            'es': [
                "Indicadores mixtos detectados - proceda con precaución",
                "Hay algunos elementos sospechosos presentes",
                "Verifique la información de la empresa antes de continuar",
                "Consulte los canales de contacto oficiales"
            ],
            'de': [
                "Gemischte Indikatoren erkannt – Vorsicht geboten",
                "Einige verdächtige Elemente vorhanden",
                "Firmeninformationen vor dem Fortfahren überprüfen",
                "Offizielle Kontaktkanäle prüfen"
            ],
            'ru': [
                "Обнаружены смешанные признаки - действуйте осторожно",
                "Присутствуют некоторые подозрительные элементы",
                "Проверьте информацию о компании перед продолжением",
                "Проверьте официальные каналы связи"
            ],
            'zh': [
                "检测到混合指标 - 请谨慎操作",
                "存在一些可疑元素",
                "在继续操作前验证公司信息",
                "检查官方联系渠道"
            ],
            'ja': [
                "混合したインジケーターが検出されました - 注意して進めてください",
                "一部の不審な要素が存在します",
                "進める前に会社情報を確認してください",
                "公式な連絡手段を確認してください"
            ],
            'ko': [
                "혼합 지표 감지됨 - 주의해서 진행하세요",
                "일부 의심스러운 요소가 있습니다",
                "진행하기 전에 회사 정보를 확인하세요",
                "공식 연락처를 확인하세요"
            ]
        }
    else:
        templates = {
            'en': [
                "High risk indicators detected - likely scam",
                "Multiple red flags present",
                "Avoid sharing personal information",
                "Do not make any payments",
                "Report this to authorities if contacted"
            ],
            'ta': [
                "அதிக அபாய குறிகாட்டிகள் கண்டறியப்பட்டன - மோசடியாக இருக்கலாம்",
                "பல சிவப்பு கொடிகள் உள்ளன",
                "தனிப்பட்ட தகவலைப் பகிர்ந்து கொள்ளாதீர்கள்",
                "எந்த கட்டணங்களையும் செய்ய வேண்டாம்",
                "தொடர்பு கொண்டால் இதை அதிகாரிகளிடம் புகாரளிக்கவும்"
            ],
            'hi': [
                "उच्च जोखिम संकेतक पाए गए - संभावित स्कैम",
                "कई रेड फ्लैग मौजूद हैं",
                "व्यक्तिगत जानकारी साझा न करें",
                "कोई भुगतान न करें",
                "यदि संपर्क किया जाए तो इसे अधिकारियों को रिपोर्ट करें"
            ],
            'fr': [
                "Indicateurs de risque élevé détectés - probablement une arnaque",
                "Plusieurs signaux d'alerte présents",
                "Évitez de partager des informations personnelles",
                "N'effectuez aucun paiement",
                "Signalez ceci aux autorités si vous êtes contacté"
            ],
            'es': [
                "Indicadores de alto riesgo detectados - probable estafa",
                "Múltiples señales de alerta presentes",
                "Evite compartir información personal",
                "No realice ningún pago",
                "Informe esto a las autoridades si lo contactan"
            ],
            'de': [
                "Indikatoren für hohes Risiko erkannt – wahrscheinlicher Betrug",
                "Mehrere Warnsignale vorhanden",
                "Vermeiden Sie die Weitergabe persönlicher Informationen",
                "Tätigen Sie keine Zahlungen",
                "Melden Sie dies den Behörden, falls Sie kontaktiert werden"
            ],
            'ru': [
                "Обнаружены признаки высокого риска - вероятное мошенничество",
                "Присутствует несколько тревожных сигналов",
                "Избегайте передачи личной информации",
                "Не производите никаких платежей",
                "Сообщите об этом властям, если с вами свяжутся"
            ],
            'zh': [
                "检测到高风险指标 - 可能是欺诈",
                "存在多个危险信号",
                "避免分享个人信息",
                "请勿进行任何支付",
                "如果对方联系您，请向有关部门举报"
            ],
            'ja': [
                "高リスクのインジケーターが検出されました - 詐欺の可能性が高いです",
                "複数のレッドフラ그が存在します",
                "個人情報の共有を避けてください",
                "いかなる支払いも行わないでください",
                "連絡があった場合は当局に報告してください"
            ],
            'ko': [
                "높은 위험 지표 감지됨 - 사기 가능성 높음",
                "여러 개의 경고 신호가 있습니다",
                "개인 정보 공유를 피하세요",
                "어떤 결제도 하지 마세요",
                "연락을 받으면 당국에 신고하세요"
            ]
        }
    
    # Get explanations for current language
    lang_templates = templates.get(ui_language, templates['en'])
    explanations.extend(lang_templates[:3])
    
    return explanations

def extract_key_phrases(text, ui_language='en'):
    """
    Extract key phrases that influenced the decision
    """
    if not text:
        return []
    
    # Scam-related phrases to look for
    scam_phrases = {
        'en': [
            r'\burgent\b.*?\bhiring\b',
            r'\bwork from home\b',
            r'\bearn\s+\$\d+',
            r'\bno experience needed\b',
            r'\bguaranteed\s+income\b',
            r'\bsend money\b',
            r'\bwire transfer\b',
            r'\bconfidential\b',
            r'\bexclusive offer\b',
            r'\blimited time\b'
        ],
        'ta': [
            r'\bஅவசர\b.*?\bநியமனம்\b',
            r'\bவீட்டிலிருந்து வேலை\b',
            r'\bசம்பாதி\s+\$\d+',
            r'\bஅனுபவம் தேவையில்லை\b',
            r'\bஉத்தரவாத வருமானம்\b'
        ],
        'hi': [
            r'\bजरूरी\b.*?\bभर्ती\b',
            r'\bघर से काम\b',
            r'\bकमाएं\s+\$\d+',
            r'\bअनुभव की आवश्यकता नहीं\b',
            r'\bगारंटीकृत आय\b'
        ],
        'fr': [
            r'\burgent\b', r'\brecrutement\b', r'\btravail à domicile\b', r'\bgagner de l\'argent\b', r'\boffre exclusive\b'
        ],
        'es': [
            r'\burgente\b', r'\breclutamiento\b', r'\btrabajo desde casa\b', r'\bganar dinero\b', r'\boferta exclusiva\b'
        ],
        'de': [
            r'\beilig\b', r'\beinstellung\b', r'\bheimarbeit\b', r'\bgeld verdienen\b', r'\bexklusives angebot\b'
        ],
        'ru': [
            r'\bсрочно\b', r'\bнайм\b', r'\bработа на дому\b', r'\bзаработать деньги\b', r'\bэксклюзивное предложение\b'
        ],
        'zh': [
            r'紧急', r'招聘', r'在家工作', r'赚钱', r'独家优惠'
        ],
        'ja': [
            r'緊急', r'採用', r'在宅勤務', r'お金を稼ぐ', r'限定オファー'
        ],
        'ko': [
            r'긴급', r'채용', r'재택 근무', r'돈을 벌다', r'독점 오퍼'
        ]
    }
    
    # Get phrases for current language
    phrases = scam_phrases.get(ui_language, scam_phrases['en'])
    key_phrases = []
    
    text_lower = text.lower()
    
    for pattern in phrases:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            key_phrases.extend(matches)
    
    # Remove duplicates but preserve order
    seen = set()
    unique_phrases = []
    for phrase in key_phrases:
        if phrase not in seen:
            seen.add(phrase)
            unique_phrases.append(phrase)
    
    return unique_phrases[:5]  # Return top 5 phrases

def generate_confidence_metrics(features, risk_score):
    """
    Generate confidence metrics for the prediction
    """
    metrics = {}
    
    # Calculate confidence based on feature quality
    quality_score = 0
    max_quality = 0
    
    # Text length contributes to confidence
    text_length = features.get('text_length', 0)
    if text_length > 100:
        quality_score += min(30, text_length / 10)
    max_quality += 30
    
    # Feature completeness
    feature_count = len([v for v in features.values() if isinstance(v, (int, float))])
    if feature_count > 10:
        quality_score += min(30, feature_count * 2)
    max_quality += 30
    
    # Keyword matches
    keyword_count = features.get('total_scam_keywords', 0)
    if keyword_count > 0:
        quality_score += min(20, keyword_count * 4)
    max_quality += 20
    
    # Metadata availability
    metadata_score = 0
    if features.get('has_email', 0) or features.get('has_phone', 0) or features.get('has_url', 0):
        metadata_score = 20
    quality_score += metadata_score
    max_quality += 20
    
    # Calculate confidence percentage
    if max_quality > 0:
        confidence = (quality_score / max_quality) * 100
    else:
        confidence = 50
    
    # Adjust confidence based on risk score extremity
    if risk_score < 20 or risk_score > 80:
        confidence = min(95, confidence + 10)  # More confident at extremes
    
    metrics['confidence'] = round(confidence, 1)
    metrics['feature_quality'] = round(quality_score, 1)
    metrics['max_quality'] = max_quality
    metrics['key_factor_count'] = len([
        k for k, v in features.items() 
        if isinstance(v, (int, float)) and abs(v) > 0.5
    ])
    
    return metrics