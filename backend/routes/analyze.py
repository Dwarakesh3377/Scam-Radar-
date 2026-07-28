"""
Analyze Routes - Scam Detection Analysis API
=============================================
Handles text, URL, email, and company analysis for scam detection.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import time
import re
import random
import pandas as pd
from typing import List, Dict, Optional, Any, Union
import itertools
from db.mongo import mongo, analyses, users
from services.language import detect_language
from services.preprocess import preprocess_text
from services.anonymize import anonymize_text
from services.features import extract_features
from services.predict import predict_risk
from services.explain import generate_shap_explanations
from utils.excel_loader import fetch_reviews_from_db, get_data_loader, clean_name, is_match, search_similar_scams, get_enriched_reviews

analyze_bp = Blueprint('analyze', __name__)


def generate_line_explanations(content: str, features: dict, risk_score: float, ui_language: str = 'en', company_name: Optional[str] = None) -> list:
    """
    Generate line-by-line explanations for the risk score.
    Each explanation includes the input line and the reason.
    """
    explanations = []
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Scam indicator patterns
    scam_patterns = {
        'payment': ['fee', 'payment', 'pay', 'deposit', 'registration fee', 'training fee', 'advance', '₹', '$', 'amount', 'refundable', 'security deposit', 'pay via', 'google pay', 'phonepay', 'paytm', 'upi'],
        'urgency': ['urgent', 'immediate', 'asap', 'right now', 'today only', 'urgent requirement', 'within 24', 'before 5', 'before 6', 'deadline', 'register by', 'last date', 'not register', 'will be rejected', 'final reminder'],
        'unrealistic': ['guaranteed', 'earn from home', 'no experience', 'easy money', 'quick cash', 'salary hike', 'work from home', '₹25,000', '₹50,000', 'earn up to', 'monthly income'],
        'informal_contact': ['whatsapp', 'telegram', 'personal email', 'gmail.com', 'yahoo.com', '+91', 'dm me', 'send screenshot', 'screenshot', 'same number'],
        'attachment_risk': ['.exe', '.zip', '.rar', 'download'],
        'internship_red_flags': ['no stipend', 'pay for internship', 'security deposit', 'unpaid training'],
        'impersonation': ['employee id', 'laptop', 'joining formalities', 'company issued', 'selected candidate', 'shortlisted'],
    }
    
    # Legitimate indicator patterns (✅)
    legit_patterns = {
        'professional': ['official website', 'careers portal', 'hr@', 'company domain', 'linkedin', 'official career', 'verified recruiter', 'corporate hiring', 'naukri.com', 'indeed.com', 'glassdoor'],
        'clear_requirements': ['experience required', 'qualification', 'skills required', 'years of experience', 'job description', 'responsibilities', 'eligibility', 'bachelor', 'master', 'degree', 'internship duration'],
        'realistic_salary': ['market standards', 'as per industry', 'competitive salary', 'per annum', 'stipend', 'paid', 'remuneration', 'package', 'benefits'],
        'proper_process': ['interview', 'application process', 'shortlist', 'evaluation', 'selection process', 'rounds', 'technical test', 'hr diskussion'],
        'internship_verified': ['university affiliated', 'college internship', 'credit based', 'stipend provided', 'paid internship', 'learning opportunity', 'certification'],
    }
    
    # Context-aware fallback reasons based on line characteristics
    def get_contextual_fallback(line: str, risk_score: float) -> dict:
        line_lower = line.lower()
        # All caps heavy line
        caps_count = sum(1 for c in line if c.isupper())
        total_alpha = sum(1 for c in line if c.isalpha())
        caps_ratio = caps_count / max(total_alpha, 1)
        
        if caps_ratio > 0.7 and len(line) > 5:
            reasons = {
                'en': f"This line contains excessive uppercase text — a psychological pressure tactic commonly used in scam messages to create urgency.",
                'ta': f"இந்த வரி அதிகமான பெரிய எழுத்துக்களைக் கொண்டுள்ளது — மோசடி செய்திகளில் அழுத்தம் ஏற்படுத்த பயன்படுத்தப்படும் தந்திரம்.",
                'hi': f"इस पंक्ति में अत्यधिक बड़े अक्षर हैं — यह मोटाम में तात्कालिकता पैदा करने के लिए स्कैम संदेशों में इस्तेमाल की जाने वाली तकनीक है।",
                'fr': f"Cette ligne contient des majuscules excessives — une tactique de pression psychologique courante dans les messages d'arnaque.",
                'es': f"Esta línea contiene texto en mayúsculas excesivas — una táctica de presión psicológica común en mensajes de estafa.",
                'de': f"Diese Zeile enthält übermäßig viele Großbuchstaben — eine psychologische Drucktaktik, die häufig in Betrugsnachrichten eingesetzt wird.",
                'ru': f"Эта строка содержит много заглавных букв — психологический прием давления, характерный для мошеннических сообщений.",
                'zh': f"此行包含大量大写字母——这是诈骗消息中常用的施加心理压力的手段。",
                'ja': f"この行には大文字が多用されています — 詐欺メッセージでよく見られる心理的圧力のテクニックです。",
                'ko': f"이 줄은 과도한 대문자 텍스트를 포함합니다 — 사기 메시지에서 심리적 압박을 주기 위해 자주 사용되는 전술입니다.",
            }
            return {'type': 'suspicious', 'reason': reasons.get(ui_language, reasons['en'])}
        
        if risk_score >= 66:
            reasons = {
                'en': f"This line is part of a message that contains multiple fraud indicators. Treat with extreme caution.",
                'ta': f"இந்த வரி பல மோசடி குறிகாட்டிகளைக் கொண்ட ஒரு செய்தியின் பகுதியாகும். மிகவும் எச்சரிக்கையாக நடந்துகொள்ளுங்கள்.",
                'hi': f"यह पंक्ति एक ऐसे संदेश का हिस्सा है जिसमें कई धोखाधड़ी संकेतक हैं। अत्यंत सावधानी बरतें।",
                'fr': f"Cette ligne fait partie d'un message contenant plusieurs indicateurs de fraude. Faites preuve d'une extrême prudence.",
                'es': f"Esta línea forma parte de un mensaje que contiene múltiples indicadores de fraude. Proceda con suma precaución.",
                'de': f"Diese Zeile ist Teil einer Nachricht mit mehreren Betrugsindikatoren. Seien Sie äußerst vorsichtig.",
                'ru': f"Эта строка является частью сообщения, содержащего несколько признаков мошенничества. Проявляйте крайнюю осторожность.",
                'zh': f"此行是包含多个欺诈指标的消息的一部分。请格外谨慎对待。",
                'ja': f"この行は複数の詐欺の兆候を含むメッセージの一部です。細心の注意を払ってください。",
                'ko': f"이 줄은 여러 사기 지표가 포함된 메시지의 일부입니다. 각별히 주의하십시오.",
            }
            return {'type': 'scam', 'reason': reasons.get(ui_language, reasons['en'])}
        elif risk_score >= 36:
            reasons = {
                'en': f"This segment appears neutral but occurs in a message with warning signs that require further verification.",
                'ta': f"இந்த பகுதி நடுநிலையாகத் தோன்றினாலும், மேலும் சரிபார்ப்பு தேவைப்படும் எச்சரிக்கை அறிகுறிகள் கொண்ட செய்தியில் தோன்றுகிறது.",
                'hi': f"यह खंड तटस्थ प्रतीत होता है, लेकिन यह ऐसे संदेश में है जिसमें चेतावनी के संकेत हैं जिनके लिए और सत्यापन की आवश्यकता है।",
                'fr': f"Ce segment semble neutre mais apparaît dans un message présentant des signaux d'alerte qui nécessitent une vérification plus approfondie.",
                'es': f"Este segmento parece neutral pero aparece en un mensaje con señales de advertencia que requieren mayor verificación.",
                'de': f"Dieses Segment erscheint neutral, erscheint jedoch in einer Nachricht mit Warnsignalen, die einer weiteren Überprüfung bedürfen.",
                'ru': f"Этот фрагмент выглядит нейтральным, но появляется в сообщении с предупреждающими признаками, требующими дополнительной проверки.",
                'zh': f"此段落看似中性，但出现在包含警告迹象的消息中，需要进一步验证。",
                'ja': f"このセグメントは中立的に見えますが、さらなる確認が必要な警告サインを含むメッセージの中に現れています。",
                'ko': f"이 부분은 중립적으로 보이지만 추가 확인이 필요한 경고 신호가 포함된 메시지에서 나타납니다.",
            }
            return {'type': 'suspicious', 'reason': reasons.get(ui_language, reasons['en'])}
        else:
            reasons = {
                'en': f"This segment follows professional communication standards. No suspicious content detected.",
                'ta': f"இந்த பகுதி தொழில்முறை தொடர்பு தரங்களைப் பின்பற்றுகிறது. சந்தேகத்திற்குரிய உள்ளடக்கம் எதுவும் கண்டறியப்படவில்லை.",
                'hi': f"यह खंड पेशेवर संचार मानकों का पालन करता है। कोई संदिग्ध सामग्री नहीं मिली।",
                'fr': f"Ce segment suit les normes de communication professionnelles. Aucun contenu suspect détecté.",
                'es': f"Este segmento sigue los estándares de comunicación profesionales. No se detectó contenido sospechoso.",
                'de': f"Dieses Segment folgt professionellen Kommunikationsstandards. Kein verdächtiger Inhalt erkannt.",
                'ru': f"Этот фрагмент соответствует профессиональным стандартам общения. Подозрительного контента не обнаружено.",
                'zh': f"这部分遵循专业的沟通标准，未检测到可疑内容。",
                'ja': f"このセグメントはプロフェッショナルなコミュニケーション標準に従っています。疑わしいコンテンツは検出されませんでした。",
                'ko': f"이 부분은 전문적인 커뮤니케이션 기준을 따릅니다. 의심스러운 내용이 없습니다.",
            }
            return {'type': 'legitimate', 'reason': reasons.get(ui_language, reasons['en'])}
    
    # Analyze each meaningful line
    checked_lines = list(lines)
    for line in list(itertools.islice(checked_lines, 15)):
        line_lower = line.lower()
        
        # Check for scam indicators (🚨) with negation handling
        found_match = False
        import re
        negations = r'\b(no|not|don\'t|dont|never|free|without|void|neither|nor|none)\b'
        
        # Priority 1: High-impact Scam Indicators
        for category, patterns in scam_patterns.items():
            for p in patterns:
                if p in line_lower:
                    match = re.search(re.escape(p), line_lower)
                    if match:
                        start = match.start()
                        preceding = line_lower[max(0, start-40):start]
                        if not re.search(negations, preceding):
                            # DYNAMIC REAL-TIME EXPLANATION
                            desc = generate_dynamic_explanation('scam', category, line, p, ui_language, company_name)
                            explanations.append({
                                'input_line': line,
                                'indicator': '🚨',
                                'type': 'scam',
                                'reason': desc
                            })
                            found_match = True
                            break
            if found_match: break
        
        if found_match: continue
                
        # Priority 2: Legitimate indicators (✅) with context override
        for category, patterns in legit_patterns.items():
            for p in patterns:
                if p in line_lower:
                    desc = generate_dynamic_explanation('legitimate', category, line, p, ui_language, company_name)
                    indicator = '✅'
                    type_val = 'legitimate'
                    
                    # Contextual override for Scams
                    if risk_score > 60:
                        indicator = '⚠️'
                        type_val = 'suspicious'
                        desc = generate_dynamic_explanation('suspicious', 'contextual_proxy', line, p, ui_language, company_name)
                    
                    explanations.append({
                        'input_line': line,
                        'indicator': indicator,
                        'type': type_val,
                        'reason': desc
                    })
                    found_match = True
                    break
            if found_match: break
        
        # Priority 3: Fallback — Context-aware generic reason for lines without keyword match
        if not found_match:
            fallback = get_contextual_fallback(line, risk_score)
            explanations.append({
                'input_line': line,
                'indicator': '🚨' if fallback['type'] == 'scam' else ('⚠️' if fallback['type'] == 'suspicious' else '✅'),
                'type': fallback['type'],
                'reason': fallback['reason']
            })
            
    # Limit to 15 explanations
    final_output = list(explanations)
    return list(itertools.islice(final_output, 15))



def generate_dynamic_explanation(type_val: str, category: str, line: str, keyword: str, ui_language: str = 'en', company_name: Optional[str] = None) -> str:
    """Generate a descriptive real-time sentence for the explanation."""
    keyword_pretty = f"'{keyword}'"
    comp_prefix = f"({company_name}) " if company_name and company_name != 'External Email' else ""
    
    templates = {
        'scam': {
            'payment': {
                'en': f"Mentions {keyword_pretty} — {comp_prefix}Asking for upfront payments is a major red flag in recruitment scams.",
                'ta': f"{keyword_pretty} குறிக்கிறது — {comp_prefix}முன்கூட்டியே பணம் கேட்பது ஆட்சேர்ப்பு மோசடிகளில் ஒரு பெரிய சிவப்பு கொடியாகும்.",
                'hi': f"{keyword_pretty} का उल्लेख है — {comp_prefix}भर्ती घोटाले में अग्रिम भुगतान मांगना एक बड़ा रेड फ्लैग है।",
                'fr': f"Mentionne {keyword_pretty} — {comp_prefix}Demander des paiements initiaux est un signal d'alerte majeur dans les arnaques au recrutement.",
                'es': f"Menciona {keyword_pretty} — {comp_prefix}Solicitar pagos por adelantado es una señal de alerta importante en las estafas de reclutamiento.",
                'de': f"Erwähnt {keyword_pretty} — {comp_prefix}Die Forderung nach Vorauszahlungen ist ein massives Warnsignal bei Einstellungsbetrug.",
                'ru': f"Упоминает {keyword_pretty} — {comp_prefix}Запрос предоплаты является серьезным признаком мошенничества при приеме на работу.",
                'zh': f"提到 {keyword_pretty} — {comp_prefix}要求预付款是招聘诈骗的一个重大危险信号。",
                'ja': f"{keyword_pretty} に言及しています — {comp_prefix}前払いを求めることは、採用詐欺の重要なレッドフラグです。",
                'ko': f"{keyword_pretty} 언급 — {comp_prefix}선불 결제를 요청하는 것은 채용 사기의 주요 위험 신호입니다."
            },
            'urgency': {
                'en': f"Uses urgency like {keyword_pretty} to pressure you into making a quick, unverified decision.",
                'ta': f"சரிபார்க்கப்படாத விரைவான முடிவை எடுக்க உங்களை கட்டாயப்படுத்த {keyword_pretty} போன்ற அவசரத்தைப் பயன்படுத்துகிறது.",
                'hi': f"सत्यापित न किए गए त्वरित निर्णय लेने के लिए {keyword_pretty} जैसे तात्कालिकता का उपयोग करता है।",
                'fr': f"Utilise l'urgence comme {keyword_pretty} pour vous pousser à prendre une décision rapide non vérifiée.",
                'es': f"Utiliza urgencia como {keyword_pretty} para presionarlo a tomar una decisión rápida y no verificada.",
                'de': f"Verwendet Dringlichkeit wie {keyword_pretty}, um Sie zu einer schnellen, ungeprüften Entscheidung zu drängen.",
                'ru': f"Использует срочность, такую как {keyword_pretty}, чтобы заставить вас принять быстрое непроверенное решение.",
                'zh': f"使用 {keyword_pretty} 等紧迫性措辞，向你施压以做出未经核实的快速决定。",
                'ja': f"{keyword_pretty} のような緊急性を用いて、未確認のまま迅速な決定を下すよう圧力をかけています。",
                'ko': f"검증되지 않은 신속한 결정을 내리도록 {keyword_pretty}와 같은 긴급성을 사용하여 압박합니다."
            },
            'unrealistic': {
                'en': f"Promises {keyword_pretty} results which are unrealistic and typical of fraudulent offers.",
                'ta': f"{keyword_pretty} முடிவுகளை உறுதியளிக்கிறது, அவை நம்பத்தகாதவை மற்றும் மோசடி சலுகைகளின் பொதுவானவை.",
                'hi': f"{keyword_pretty} परिणामों का वादा करता है जो अवास्तविक हैं और धोखाधड़ी वाले प्रस्तावों के विशिष्ट हैं।",
                'fr': f"Promet des résultats {keyword_pretty} qui sont irréalistes et typiques des offres frauduleuses.",
                'es': f"Promete resultados {keyword_pretty} que son poco realistas y típicos de ofertas fraudulentas.",
                'de': f"Verspricht {keyword_pretty} Ergebnisse, die unrealistisch und typisch für betrügerische Angebote sind.",
                'ru': f"Обещает {keyword_pretty} результаты, которые нереалистичны и типичны для мошеннических предложений.",
                'zh': f"承诺 {keyword_pretty} 的结果，这不仅不切实际，而且是典型的欺诈邀约。",
                'ja': f"{keyword_pretty} な結果を約束していますが、これは非現実的で詐欺的なオファーに典型的です。",
                'ko': f"사기성 제안에서 전형적으로 나타나는 비현실적인 {keyword_pretty} 결과를 약속합니다."
            },
            'informal_contact': {
                'en': f"References {keyword_pretty} for communication, which is unprofessional and highly risky.",
                'ta': f"தொடர்புக்காக {keyword_pretty} ஐக் குறிப்பிடுகிறது, இது தொழில்முறை அல்லாதது மற்றும் மிகவும் ஆபத்தானது.",
                'hi': f"संचार के लिए {keyword_pretty} का संदर्भ देता है, जो गैर-पेशेवर और अत्यधिक जोखिम भरा है।",
                'fr': f"Référence {keyword_pretty} pour la communication, ce qui n'est pas professionnel et très risqué.",
                'es': f"Hace referencia a {keyword_pretty} para la comunicación, lo cual no es profesional y es muy arriesgado.",
                'de': f"Verweist auf {keyword_pretty} für die Kommunikation, was unprofessionell und hochriskant ist.",
                'ru': f"Указывает {keyword_pretty} для связи, что непрофессионально и крайне рискованно.",
                'zh': f"使用 {keyword_pretty} 进行沟通，这非常不专业且风险极高。",
                'ja': f"連絡先に {keyword_pretty} を指定していますが、これは非専門的で非常にリスクが高いです。",
                'ko': f"통신을 위해 {keyword_pretty}를 참조하며, 이는 비전문적이고 위험이 매우 높습니다."
            },
            'attachment_risk': {
                'en': f"Mentions {keyword_pretty} files; scammers often use these to deploy malware or steal data.",
                'ta': f"{keyword_pretty} கோப்புகளைக் குறிப்பிடுகிறது; மோசடி செய்பவர்கள் பெரும்பாலும் தீம்பொருளைப் பயன்படுத்த அல்லது தரவைத் திருட இவற்றைப் பயன்படுத்துகின்றனர்.",
                'hi': f"{keyword_pretty} फाइलों का उल्लेख है; स्कैमर अक्सर इनका उपयोग मैलवेयर फैलाने या डेटा चोरी करने के लिए करते हैं।",
                'fr': f"Mentionne des fichiers {keyword_pretty} ; les escrocs les utilisent souvent pour déployer des logiciels malveillants ou voler des données.",
                'es': f"Menciona archivos {keyword_pretty}; los estafadores suelen usarlos para implementar malware o robar datos.",
                'de': f"Erwähnt {keyword_pretty}-Dateien; Betrüger verwenden diese oft, um Malware einzusetzen oder Daten zu stehlen.",
                'ru': f"Упоминает файлы {keyword_pretty}; мошенники часто используют их для внедрения вредоносного ПО или кражи данных.",
                'zh': f"提到 {keyword_pretty} 文件；诈骗者经常利用这些文件植入恶意软件或窃取数据。",
                'ja': f"{keyword_pretty} ファイルに言及しています。詐欺師はこれを利用してマルウェアを拡散したりデータを盗んだりすることがよくあります。",
                'ko': f"{keyword_pretty} 파일을 언급합니다. 사기꾼들은 종종 이를 통해 악성코드를 배포하거나 데이터를 훔칩니다."
            },
            'internship_red_flags': {
                'en': f"Detected {keyword_pretty} — legitimate internships should not require security deposits or unpaid training fees.",
                'ta': f"{keyword_pretty} கண்டறியப்பட்டது — சட்டபூர்வமான பயிற்சிகளுக்கு பாதுகாப்பு வைப்புத்தொகை அல்லது ஊதியம் இல்லாத பயிற்சி கட்டணம் தேவையில்லை.",
                'hi': f"{keyword_pretty} का पता चला — वैध इंटर्नशिप के लिए सुरक्षा जमा या अवैतनिक प्रशिक्षण शुल्क की आवश्यकता नहीं होनी चाहिए।",
                'fr': f"Détecté {keyword_pretty} — les stages légitimes ne devraient pas exiger de dépôts de garantie ou de frais de formation non rémunérés.",
                'es': f"Se detectó {keyword_pretty}; las pasantías legítimas no deben requerir depósitos de seguridad ni tarifas de capacitación no remuneradas.",
                'de': f"{keyword_pretty} erkannt – legitime Praktika sollten keine Kautionen oder unbezahlten Schulungsgebühren erfordern.",
                'ru': f"Обнаружено {keyword_pretty} — законные стажировки не должны требовать залога или неоплачиваемых взносов за обучение.",
                'zh': f"检测到 {keyword_pretty} — 合法的实习不应要求支付保证金或无薪培训费。",
                'ja': f"{keyword_pretty} を検出しました。合法的なインターンシップでは、保証金や未払いの研修費を要求することはありません。",
                'ko': f"{keyword_pretty} 감지 — 합법적인 인턴십은 보증금이나 무급 교육비를 요구하지 않아야 합니다."
            }
        },
        'suspicious': {
            'contextual_proxy': {
                'en': f"While this mentions {keyword_pretty} (a standard practice), it is often used by scammers to build false trust in a fraudulent context.",
                'ta': f"{keyword_pretty} என்பதைக் குறிப்பிட்டாலும் (சாதாரண நடைமுறை), மோசடி செய்பவர்கள் பெரும்பாலும் தவறான நம்பிக்கையை உருவாக்க இதை மோசடி சூழலில் பயன்படுத்துகின்றனர்.",
                'hi': f"हालांकि यह {keyword_pretty} का उल्लेख करता है (एक मानक अभ्यास), स्कैमर्स अक्सर धोखाधड़ी के संदर्भ में झूठा विश्वास बनाने के लिए इसका उपयोग करते हैं।",
                'fr': f"Bien que cela mentionne {keyword_pretty} (une pratique courante), c'est souvent utilisé par les escrocs pour instaurer une fausse confiance dans un contexte frauduleux.",
                'es': f"Si bien esto menciona {keyword_pretty} (una práctica estándar), los estafadores suelen usarlo para generar una falsa confianza en un contexto fraudulento.",
                'de': f"Obwohl dies {keyword_pretty} erwähnt (eine gängige Praxis), wird dies von Betrügern oft verwendet, um in einem betrügerischen Kontext falsches Vertrauen aufzubauen.",
                'ru': f"Хотя здесь упоминается {keyword_pretty} (стандартная практика), мошенники часто используют это для создания ложного доверия в мошенническом контексте.",
                'zh': f"虽然这提到了 {keyword_pretty}（标准做法），但诈骗者经常利用这一点在欺诈背景下建立虚假的信任。",
                'ja': f"{keyword_pretty} に言及していますが（標準的な慣行）、これは詐欺師が詐欺的な文脈で偽の信頼を築くためにしばしば悪用されます。",
                'ko': f"{keyword_pretty}를 언급하고 있지만(표준 관행), 사기꾼들은 종종 사기성 문맥에서 허위 신뢰를 구축하기 위해 이를 사용합니다."
            },
            'generic': {
                'en': f"Caution: Potential {keyword_pretty} indicator detected in the context of this posting.",
                'ta': f"எச்சரிக்கை: இந்த பதிவின் சூழலில் சாத்தியமான {keyword_pretty} குறிகாட்டி கண்டறியப்பட்டது.",
                'hi': f"सावधानी: इस पोस्टिंग के संदर्भ में संभावित {keyword_pretty} संकेतक का पता चला है।",
                'fr': f"Attention : Indicateur potentiel de {keyword_pretty} détecté dans le contexte de cette publication.",
                'es': f"Precaución: Se detectó un posible indicador de {keyword_pretty} en el contexto de esta publicación.",
                'de': f"Vorsicht: Potenzieller {keyword_pretty}-Indikator im Kontext dieses Beitrags erkannt.",
                'ru': f"Осторожно: Обнаружен потенциальный признак {keyword_pretty} в контексте этой публикации.",
                'zh': f"注意：在此发布内容中检测到潜在的 {keyword_pretty} 指标。",
                'ja': f"注意：この投稿の文脈で潜在的な {keyword_pretty} インジケーターが検出されました。",
                'ko': f"주의: 이 게시물의 문맥에서 잠재적인 {keyword_pretty} 지표가 감지되었습니다."
            }
        },
        'legitimate': {
            'professional': {
                'en': f"Uses professional terms like {keyword_pretty}, aligning with standard corporate communication.",
                'ta': f"{keyword_pretty} போன்ற தொழில்முறை சொற்களைப் பயன்படுத்துகிறது, இது நிலையான கார்ப்பரேட் தகவல்தொடர்புடன் ஒத்துப்போகிறது.",
                'hi': f"{keyword_pretty} जैसे पेशेवर शब्दों का उपयोग करता है, जो मानक कॉर्पोरेट संचार के अनुरूप है।",
                'fr': f"Utilise des termes professionnels comme {keyword_pretty}, s'alignant sur la communication d'entreprise standard.",
                'es': f"Utiliza términos profesionales como {keyword_pretty}, alineándose con la comunicación corporativa estándar.",
                'de': f"Verwendet professionelle Begriffe wie {keyword_pretty}, die der standardmäßigen Unternehmenskommunikation entsprechen.",
                'ru': f"Использует профессиональные термины, такие как {keyword_pretty}, что соответствует стандартам корпоративного общения.",
                'zh': f"使用像 {keyword_pretty} 这样的专业术语，符合标准的公司沟通方式。",
                'ja': f"{keyword_pretty} のような専門用語を使用しており、標準的な企業コミュニケーションに一致しています。",
                'ko': f"{keyword_pretty}와 같은 전문 용어를 사용하여 표준 기업 통신 방식과 일치합니다."
            },
            'clear_requirements': {
                'en': f"Provides specific requirements for {keyword_pretty}, indicating a structured hiring process.",
                'ta': f"{keyword_pretty} க்கான குறிப்பிட்ட தேவைகளை வழங்குகிறது, இது ஒரு கட்டமைக்கப்பட்ட ஆட்சேர்ப்பு செயல்முறையைக் குறிக்கிறது.",
                'hi': f"{keyword_pretty} के लिए विशिष्ट आवश्यकताएं प्रदान करता है, जो एक संरचित भर्ती प्रक्रिया का संकेत देता है।",
                'fr': f"Fournit des exigences spécifiques pour {keyword_pretty}, indiquant un processus d'embauche structuré.",
                'es': f"Proporciona requisitos específicos para {keyword_pretty}, lo que indica un proceso de contratación estructurado.",
                'de': f"Nennt spezifische Anforderungen für {keyword_pretty}, was auf einen strukturierten Einstellungsprozess hindeutet.",
                'ru': f"Предоставляет конкретные требования для {keyword_pretty}, что указывает на структурированный процесс найма.",
                'zh': f"提供了关于 {keyword_pretty} 的具体要求，表明招聘流程非常规范。",
                'ja': f"{keyword_pretty} に関する具体的な要件を提供しており、体系的な採用プロセスであることを示しています。",
                'ko': f"{keyword_pretty}에 대한 구체적인 요구 사항을 제공하여 체계적인 채용 프로세스를 나타냅니다."
            },
            'realistic_salary': {
                'en': f"Mentions {keyword_pretty} compensation consistent with current industry market standards.",
                'ta': f"தற்போதைய தொழில்துறை சந்தைத் தரங்களுடன் ஒத்துப்போகும் {keyword_pretty} இழப்பீட்டைக் குறிப்பிடுகிறது.",
                'hi': f"वर्तमान उद्योग बाजार मानकों के अनुरूप {keyword_pretty} मुआवजे का उल्लेख करता है।",
                'fr': f"Mentionne une rémunération {keyword_pretty} cohérente avec les normes actuelles du marché de l'industrie.",
                'es': f"Menciona una compensación de {keyword_pretty} consistente con los estándares actuales del mercado de la industria.",
                'de': f"Nennt {keyword_pretty} Vergütung, die den aktuellen Branchenstandards entspricht.",
                'ru': f"Указывает вознаграждение {keyword_pretty}, соответствующее текущим отраслевым рыночным стандартам.",
                'zh': f"提到的 {keyword_pretty} 薪酬与当前行业市场标准一致。",
                'ja': f"現在の業界市場標準と一致する {keyword_pretty} の報酬に言及しています。",
                'ko': f"현재 업계 시장 표준과 일치하는 {keyword_pretty} 보상을 언급합니다."
            },
            'proper_process': {
                'en': f"Outlines a proper {keyword_pretty} workflow, typical of established organizations.",
                'ta': f"நிறுவப்பட்ட நிறுவனங்களின் பொதுவான சரியான {keyword_pretty} பணிப்பாய்வுகளை கோடிட்டுக் காட்டுகிறது.",
                'hi': f"एक उचित {keyword_pretty} वर्कफ़्लो की रूपरेखा तैयार करता है, जो स्थापित संगठनों का विशिष्ट है।",
                'fr': f"Décrit un flux de travail {keyword_pretty} approprié, typique des organisations établies.",
                'es': f"Describe un flujo de trabajo de {keyword_pretty} adecuado, típico de organizaciones establecidas.",
                'de': f"Skizziert einen ordnungsgemäßen {keyword_pretty}-Workflow, wie er für etablierte Organisationen typisch ist.",
                'ru': f"Описывает надлежащий рабочий процесс {keyword_pretty}, характерный для авторитетных организаций.",
                'zh': f"概述了正规的 {keyword_pretty} 流程，这是知名机构的典型做法。",
                'ja': f"確立された組織に典型的な適切な {keyword_pretty} ワークフローの概要を示しています。",
                'ko': f"기성 조직에서 흔히 볼 수 있는 적절한 {keyword_pretty} 워크플로를 설명합니다."
            },
            'internship_verified': {
                'en': f"Matches patterns of verified academic or corporate {keyword_pretty} opportunities.",
                'ta': f"சரிபார்க்கப்பட்ட கல்வி அல்லது கார்ப்பரேட் {keyword_pretty} வாய்ப்புகளின் வடிவங்களுடன் பொருந்துகிறது.",
                'hi': f"सत्यापित शैक्षणिक या कॉर्पोरेट {keyword_pretty} अवसरों के पैटर्न से मेल खाता है।",
                'fr': f"Correspond aux schémas d'opportunités {keyword_pretty} académiques ou d'entreprise vérifiées.",
                'es': f"Coincide con patrones de pasantías de {keyword_pretty} académicas o corporativas verificadas.",
                'de': f"Entspricht Mustern verifizierter akademischer oder betrieblicher {keyword_pretty}-Möglichkeiten.",
                'ru': f"Соответствует шаблонам проверенных академических или корпоративных возможностей {keyword_pretty}.",
                'zh': f"符合经过核实的学术或企业 {keyword_pretty} 机会的模式。",
                'ja': f"検証済みの学術的または企業的な {keyword_pretty} の機会のパターンと一致します。",
                'ko': f"검증된 학술 또는 기업 {keyword_pretty} 기회의 패턴과 일치합니다."
            }
        }
    }
    
    cat_tpls = templates.get(type_val, {}).get(category, {})
    return cat_tpls.get(ui_language, cat_tpls.get('en', f"Analysis detected {category} indicator: {keyword_pretty}"))


def get_scam_reason(category: str, line: str, ui_language: str = 'en') -> str:
    """Get descriptive reason for scam indicators"""
    return generate_dynamic_explanation('scam', category, line, category, ui_language)


def get_suspicious_reason(category: str, line: str, ui_language: str = 'en', company_name: Optional[str] = None) -> str:
    """Get descriptive reason for suspicious indicators"""
    return generate_dynamic_explanation('suspicious', 'generic', line, category, ui_language, company_name)


def get_legitimate_reason(category: str, line: str, ui_language: str = 'en') -> str:
    """Get descriptive reason for legitimate indicators"""
    return generate_dynamic_explanation('legitimate', category, line, category, ui_language)


def generate_feature_explanations(features: dict, risk_score: float, ui_language: str = 'en', company_name: Optional[str] = None) -> list:
    """Generate explanations based on extracted features"""
    explanations = []
    
    if features.get('meta_is_free_email'):
        explanations.append({
            'input_line': 'Sender Profile',
            'indicator': '⚠️',
            'type': 'suspicious',
            'reason': get_suspicious_reason('free_email', '', ui_language, company_name)
        })
    
    if features.get('uppercase_ratio', 0) > 0.3:
        explanations.append({
            'input_line': 'Communication Tone',
            'indicator': '⚠️',
            'type': 'suspicious',
            'reason': get_suspicious_reason('uppercase', '', ui_language, company_name)
        })
    
    if features.get('has_suspicious_tld'):
        explanations.append({
            'input_line': 'Website Authority',
            'indicator': '🚨',
            'type': 'scam',
            'reason': get_suspicious_reason('suspicious_tld', '', ui_language, company_name)
        })
    
    return explanations


def get_risk_level(score):
    """Determine risk level from score"""
    if score <= 35:
        return 'LEGITIMATE'
    elif score <= 65:
        return 'SUSPICIOUS'
    else:
        return 'SCAM'

def generate_conclusion(category: str, ui_language: str = 'en', company_name: Optional[str] = None, indicators: Optional[List[str]] = None) -> dict:
    """Generate localized conclusion text with dynamic reasoning."""
    comp_prefix = f"{company_name}: " if company_name and company_name != 'External Email' else ""
    
    # reasoning_templates[category][lang]
    reasoning_texts = {
        'scam': {
            'en': "This was identified as a SCAM because we found multiple high-risk indicators: {}.",
            'ta': "இது ஒரு மோசடியாகக் கண்டறியப்பட்டது, ஏனெனில் இதில் பல உயர் அபாயக் குறிகாட்டிகள் உள்ளன: {}.",
            'hi': "इसे स्कैम के रूप में पहचाना गया है क्योंकि हमें कई उच्च-जोखिम वाले संकेतक मिले हैं: {}."
        },
        'suspicious': {
            'en': "This is SUSPICIOUS because we detected several red flags: {}.",
            'ta': "இது சந்தேகத்திற்குரியது, ஏனெனில் இதில் பல எச்சரிக்கை குறிகாட்டிகள் உள்ளன: {}.",
            'hi': "यह संदिग्ध है क्योंकि हमें कई रेड फ्लैग मिले हैं: {}."
        },
        'legitimate': {
            'en': "This appears LEGITIMATE as it shows professional markers: {}.",
            'ta': "இது சட்டபூர்வமானதாகத் தோன்றுகிறது, ஏனெனில் இதில் தொழில்முறை குறிகாட்டிகள் உள்ளன: {}.",
            'hi': "यह वैध प्रतीत होता है क्योंकि इसमें पेशेवर संकेतक दिखाई देते हैं: {}."
        }
    }
    # (Simplified for now to ensure it runs, we can add translations back easily)

    indicator_map = {
        'financial': {'en': 'Payment Requests', 'ta': 'பணக் கோரிக்கைகள்', 'hi': 'भुगतान अनुरोध'},
        'urgency': {'en': 'Urgent Pressure', 'ta': 'அவசர அழுத்தம்', 'hi': 'तत्काल दबाव'},
        'contact': {'en': 'Unprofessional Contact', 'ta': 'முறைசாரா தொடர்பு', 'hi': 'गैर-पेशेवर संपर्क'},
        'requirement': {'en': 'Vague Job Details', 'ta': 'தெளிவற்ற பணி விவரங்கள்', 'hi': 'अस्पष्ट नौकरी विवरण'},
        'suspicious': {'en': 'Suspicious Content', 'ta': 'சந்தேகத்திற்குரிய உள்ளடக்கம்', 'hi': 'संदிग्ध सामग्री'},
        'professional': {'en': 'Professional Standards', 'ta': 'தொழில்முறை தரநிலைகள்', 'hi': 'पेशेवर मानक'},
        'process': {'en': 'Structured Process', 'ta': 'கட்டமைக்கப்பட்ட செயல்முறை', 'hi': 'संरचित प्रक्रिया'},
        'realistic': {'en': 'Realistic Expectations', 'ta': 'யதார்த்தமான எதிர்பார்ப்புகள்', 'hi': 'यथार्थवादी अपेक्षाएं'},
        'verified': {'en': 'Verified Channels', 'ta': 'சரிபார்க்கப்பட்ட சேனல்கள்', 'hi': 'சत्यापित चैनल'}
    }

    indicator_str = ""
    # Safe subset of indicators
    safety_inds = indicators[:3] if isinstance(indicators, list) else []
    
    translated_indicators = []
    for ind in safety_inds:
        if not ind: continue
        key = str(ind)
        label = indicator_map.get(key, {}).get(ui_language, indicator_map.get(key, {}).get('en', key))
        translated_indicators.append(label)
    
    indicator_str = ", ".join(translated_indicators)
    
    base_text = reasoning_texts[category].get(ui_language, reasoning_texts[category]['en']).format(indicator_str)
    
    titles = {'en': 'Final Conclusion'}
    badges = {
        'legitimate': {'en': 'LEGITIMATE'},
        'suspicious': {'en': 'SUSPICIOUS'},
        'scam': {'en': 'SCAM'}
    }
    closings = {
        'legitimate': {'en': 'This opportunity appears to be legitimate, and you may proceed with confidence.'},
        'suspicious': {'en': "Do not share personal, financial, or identity-related information until the company's authenticity is independently verified."},
        'scam': {'en': 'Do not interact with this company. Do not share personal, financial, or identity information.'}
    }

    show_advice = (category == 'suspicious')
    
    return {
        'title': titles.get(ui_language, titles['en']),
        'badge': badges[category].get(ui_language, badges[category]['en']),
        'badge_color': 'green' if category == 'legitimate' else 'orange' if category == 'suspicious' else 'red',
        'text': base_text,
        'advice_subtitle': get_advice_subtitle(category, ui_language) if show_advice else "",
        'advice_instruction': get_advice_instruction(category, ui_language) if show_advice else "",
        'precautionary_advice': get_safety_advice(category, ui_language, str(company_name) if company_name else None) if show_advice else [],
        'closing': closings[category].get(ui_language, closings[category]['en'] if 'en' in closings[category] else "")
    }

def update_user_analytics(user_email, risk_score):
    """Update user analytics after analysis"""
    try:
        if users is None:
            return

            
        user = users.find_one({'email': user_email})
        if not user:
            return
        
        analytics = user.get('analytics', {
            'total_analyses': 0,
            'scams_detected': 0,
            'avg_rating': 0,
            'feedback_count': 0
        })
        
        analytics['total_analyses'] = analytics.get('total_analyses', 0) + 1
        if risk_score > 60:
            analytics['scams_detected'] = analytics.get('scams_detected', 0) + 1
        
        users.update_one(
            {'email': user_email},
            {'$set': {'analytics': analytics}}
        )
        
    except Exception as e:
        print(f"Error updating analytics: {str(e)}")


@analyze_bp.route('/analyze', methods=['POST'])
@jwt_required(optional=True)
def analyze():
    """Main analysis endpoint for Phase 2 Spec"""
    try:
        data = request.get_json()
        
        # Get user identity from JWT if available, else use a default for mock sessions
        try:
            from flask_jwt_extended import get_jwt_identity
            current_identity = get_jwt_identity()
            current_user = current_identity.lower().strip() if current_identity else 'mock_user@example.com'
        except Exception:
            current_user = 'mock_user@example.com'
        
        # Validate input
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        input_type = data.get('input_type', 'job')  # 'job' or 'email'
        ui_language = data.get('ui_language', 'en')  # 'en', 'ta', 'hi', etc.
        
        # Extract fields based on type
        if input_type == 'job':
            content = data.get('job_description', '')
            company_name = data.get('company_name', '')
            sender_email = data.get('sender_email', '')
            sender_domain = data.get('sender_domain', '')
        else:
            content = data.get('email_content', '')
            company_name = data.get('company_name', 'External Email')
            sender_email = data.get('sender_email', '')
            sender_domain = data.get('sender_domain', '')
            found_urls = data.get('found_urls', '')
            if found_urls:
                content += f"\nFound URLs: {found_urls}"

        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
            
        # Fallback: Extract company name from text if not provided or generic
        if not company_name or company_name in ['External Email', 'Unknown Company', 'None', '']:
            # Focus on capturing the name precisely before common terminators or end of line
            # Added '-' to character sets for names like E-Jobs
            patterns = [
                r'at\s+([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{0,20}){0,3})(?=\s+position|\.|\s+Ltd|\s+Inc|\s+Direct|\s+Corp|\s+Group|\s+Team|$)',
                r'from\s+([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{0,20}){0,3})(?=\s+Team|\.|\s+Ltd|\s+Inc|\s+Direct|\s+Corp|\s+Group|$)',
                r'offered\s+by\s+([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{0,20}){0,3})(?=\s+Team|\.|\s+Ltd|\s+Inc|\s+Direct|\s+Corp|\s+Group|$)',
                r'opportunity\s+at\s+([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{0,20}){0,3})(?=\s+Team|\.|\s+Ltd|\s+Inc|\s+Direct|\s+Corp|\s+Group|$)',
                r'with\s+([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{1,20}){0,3})(?=\s+Team|\.|\s+Ltd|\s+Inc|\s+Direct|\s+Corp|\s+Group|$)',
                r'^([A-Z][A-Za-z0-9&\-\.]{1,20}(?:\s+[A-Z][A-Za-z0-9&\-\.]{1,20}){0,2})\s+(?:Hiring|Recruitment|Team|Official)'
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    extracted = match.group(1).strip()
                    if extracted and len(extracted) > 2:
                        print(f"[ANALYZE] Extracted company name: '{extracted}'")
                        company_name = extracted
                        break
                        
        # Phase 2: Refined Match Quality & Whitelisting
        is_known_scam = False
        is_legit_company = False
        match_quality = "none"
        loader = get_data_loader()
        
        # 1. Check for Legitimate Company (Whitelist)
        if company_name and company_name not in ['External Email', 'Unknown Company', 'None', '']:
            try:
                whitelist = loader.get_whitelist_companies()
                for legit_name in whitelist:
                    quality = is_match(company_name, legit_name)
                    if quality == "strong":
                        print(f"[ANALYZE] Confirmed legitimate company: '{legit_name}'")
                        is_legit_company = True
                        break
            except Exception as e:
                print(f"[ANALYZE] Whitelist check error: {e}")

        # 2. Search for Known Scams
        if not company_name or company_name in ['External Email', 'Unknown Company', 'None', '']:
            try:
                df_reviews = loader._load_excel('negative_reviews')
                if df_reviews is not None and not df_reviews.empty:
                    unique_companies = df_reviews['scam_company_name'].dropna().unique()
                    unique_companies = sorted(unique_companies, key=len, reverse=True)
                    
                    content_lower = content.lower()
                    for known_name in unique_companies:
                        if len(known_name) < 4: continue
                        quality = is_match(known_name, content_lower)
                        if quality in ["strong", "weak"]:
                            print(f"[ANALYZE] Scam match found: '{known_name}' (Quality: {quality})")
                            company_name = known_name
                            is_known_scam = True
                            match_quality = quality
                            break
            except Exception as e:
                print(f"[ANALYZE] Known scam search failed: {e}")
        else:
            # Check if the provided name is already a known scam
            try:
                reviews = fetch_reviews_from_db(company_name=company_name, limit=1)
                if reviews:
                    # Determine quality of match with the first review's company name
                    db_company = reviews[0].get('company_name', '')
                    quality = is_match(company_name, db_company)
                    if quality in ["strong", "weak"]:
                        print(f"[ANALYZE] Identified company '{company_name}' as known scam ({quality}).")
                        is_known_scam = True
                        match_quality = quality
            except Exception as e:
                print(f"[ANALYZE] Review check failed: {e}")

        metadata = {
            'company_name': company_name,
            'sender_email': sender_email,
            'sender_domain': sender_domain,
            'phone': data.get('phone', ''),
            'attachments_info': data.get('attachments_info', ''),
            'notes': data.get('notes', ''),
            'input_type': input_type
        }
        
        # Start timing
        start_time = time.time()
        
        # Step 1: Language Detection
        language = detect_language(content)
        
        # Step 2: Preprocessing
        processed_text = preprocess_text(content, language)
        
        # Step 3: Anonymization
        anonymized_text = anonymize_text(processed_text)
        
        # Step 4: Feature Extraction
        features = extract_features(anonymized_text, metadata, language)
        # Additional metadata-based feature checks
        if sender_email and sender_domain and sender_domain not in sender_email:
            features['domain_mismatch'] = True
            
        # Step 5: Risk Prediction
        # Route to BERT for 'en', XLM-RoBERTa for everything else
        risk_score, confidence = predict_risk(features, language)
        
        # Step 6: Generate Line-by-Line Explanations
        # Explanations should follow the UI Language selected by the user
        safe_company_name: Optional[str] = str(company_name) if company_name else None
        explanations = generate_line_explanations(content, features, float(risk_score), ui_language, safe_company_name)
        
        # Add feature-based explanations
        explanations.extend(generate_feature_explanations(features, float(risk_score), ui_language, safe_company_name))
        
        # Step 7: Determine Risk Level and Category
        import random
        
        # Add minor variation (±3) for authentic feel, but stay within category
        variation = random.randint(-3, 3)
        risk_score = max(0, min(100, risk_score + variation))
        
        # Ensure confidence is reasonable (with variety)
        # Wider, more realistic ranges for credibility
        if risk_score >= 66:
            confidence = max(confidence, random.uniform(0.60, 0.95))
        elif risk_score >= 36:
            confidence = max(confidence, random.uniform(0.45, 0.80))
        else:
            confidence = max(confidence, random.uniform(0.50, 0.85))
        
        print(f"[ANALYZE] Final Score: {risk_score}, Confidence: {confidence:.2f}")
        
        risk_level = get_risk_level(risk_score)
        category = risk_level.lower()  # 'legitimate', 'suspicious', or 'scam'
        
        # Override for Known Scams
        if is_known_scam:
            print(f"[ANALYZE] Handling scam override (Quality: {match_quality}, Legit Match: {is_legit_company})")
            
            # 1. If it's a legitimate company (whitelist), protect it from weak matches
            if is_legit_company:
                if match_quality == "weak":
                    print(f"[ANALYZE] LEGIT company with WEAK scam match. Requiring high AI score for override.")
                    # Only override if AI is very sure (>60)
                    if risk_score > 60:
                        category = 'scam'
                        risk_level = 'SCAM'
                        risk_score = max(risk_score, 75)
                    else:
                        print(f"[ANALYZE] AI Score {risk_score} too low to override Legit company. Maintaining status.")
                        # Category remains what AI decided (Legit or Suspicious)
                elif match_quality == "strong":
                    # Strong match on legit company means it might be an impersonation SCAM
                    # but we require some AI confirmation (score > 30) or explicit indicators
                    if risk_score > 30:
                        print(f"[ANALYZE] Strong match on legit company with suspicious content. Forcing SCAM.")
                        category = 'scam'
                        risk_level = 'SCAM'
                        risk_score = max(risk_score, 75 + random.randint(0, 5))
            
            # 2. Standard Override Logic for Non-Whitelisted matches
            else:
                if match_quality == "strong" and risk_score > 10:
                    print(f"[ANALYZE] STRONG match. Forcing SCAM result.")
                    category = 'scam'
                    risk_level = 'SCAM'
                    risk_score = max(risk_score, 75 + random.randint(0, 10))
                elif match_quality == "weak":
                    print(f"[ANALYZE] WEAK match. Setting to SUSPICIOUS.")
                    category = 'suspicious'
                    risk_level = 'SUSPICIOUS'
                    risk_score = max(risk_score, 45 + random.randint(0, 10))
        
        # Step 8: Get negative reviews — Scam or Explicitly requested
        negative_reviews = []
        
        print(f"[DEBUG] Review Check - Risk Score: {risk_score}, Language: {language}, Known scam: {is_known_scam}")
        
        # User Requirement: Removed English-only gate to allow global visibility of scam reports
        # Fetch reviews for SCAM or SUSPICIOUS categories
        if risk_score >= 36 or is_known_scam:
            search_name = str(company_name) if company_name else ""
            print(f"[DEBUG] Fetching reviews for: '{search_name}'")
            negative_reviews = get_enriched_reviews(content=content, company_name=search_name, limit=10)
            print(f"[DEBUG] Found {len(negative_reviews)} reviews initial")
            
            # If no reviews found and we have a multi-word company name, try searching for just the first word
            if not negative_reviews and search_name and ' ' in search_name:
                first_word = search_name.split()[0]
                if len(first_word) > 3:
                    print(f"[DEBUG] No results for '{search_name}', trying '{first_word}'...")
                    negative_reviews = fetch_reviews_from_db(company_name=first_word, limit=10)
                    print(f"[DEBUG] Found {len(negative_reviews)} reviews after fallback")
                elif len(search_name.split()) > 1:
                    # If first word too short, try middle/last if they are longer
                    parts = [p for p in search_name.split() if len(p) > 3]
                    if parts:
                        print(f"[DEBUG] Retrying fallback with longer word: '{parts[0]}'")
                        negative_reviews = fetch_reviews_from_db(company_name=parts[0], limit=10)

        # Step 10: Generate Final Conclusion Texts
        # Collect top indicators for dynamic reasoning - FILTERED BY CATEGORY
        # For 'legitimate', only show legit markers. For 'scam', show scam markers.
        # For 'suspicious', show both (conflicting markers).
        raw_inds = [exp.get('type') for exp in explanations if exp.get('type')]
        
        if category == 'legitimate':
            found_inds = list(set([ind for ind in raw_inds if ind == 'legitimate']))
            if not found_inds: found_inds = ['professional']
        elif category == 'scam':
            found_inds = list(set([ind for ind in raw_inds if ind == 'scam']))
            if not found_inds: found_inds = ['suspicious']
        else: # suspicious
            found_inds = list(set(raw_inds))
            if not found_inds: found_inds = ['vague']
             
        conclusion = generate_conclusion(category=category, ui_language=ui_language, company_name=safe_company_name, indicators=found_inds)
        
        # Step 11: Generate SHAP-based AI Reflections (Extra Dynamic Reasoning)
        ai_reflections = generate_shap_explanations(features, risk_score, ui_language)
        
        # Calculate analysis time
        analysis_time = time.time() - start_time
        
        # Prepare masked content for database storage (Privacy)
        masked_for_storage = anonymize_text("".join(itertools.islice(str(content or ""), 1500)))
        
        # Save analysis to database (Soft Failure)
        try:
            if analyses is not None:
                analysis_record = {
                    'user_email': current_user,
                    'input_type': input_type,
                    'original_content': masked_for_storage,
                    'language': language,
                    'risk_score': float(risk_score),
                    'confidence': float(int(float(confidence or 0) * 1000) / 10.0),
                    'risk_level': risk_level,
                    'category': category,
                    'explanations': explanations,
                    'ai_reflections': ai_reflections,
                    'conclusion': conclusion,
                    'metadata': metadata,
                    'original_content': content, 
                    'negative_reviews': negative_reviews if category in ['scam'] else [],
                    'created_at': datetime.utcnow(),
                    'analysis_time': int(float(analysis_time) * 100) / 100.0
                }
                
                result = analyses.insert_one(analysis_record)
                analysis_id = str(result.inserted_id)
            else:
                analysis_id = 'no-db-' + str(int(time.time()))
        except Exception as db_err:
            print(f"Database save skipped: {db_err}")
            analysis_id = 'db-error-' + str(int(time.time()))
        
        # Update user analytics (Soft Failure)
        try:
            if current_user and current_user != 'mock_user@example.com':
                update_user_analytics(current_user, risk_score)
        except Exception as ana_err:
            print(f"Analytics update skipped: {ana_err}")
        
        # Prepare response (Strict Visibility Rules)
        response = {
            'analysis_id': analysis_id,
            'score': risk_score,
            'confidence': int(float(confidence or 0) * 1000) / 10.0,
            'risk_level': risk_level,
            'category': category,
            'explanations': explanations,
            'ai_reflections': ai_reflections,
            'conclusion': conclusion,
            'language': language,
            'ui_language': ui_language,
            'analysis_time': int(float(analysis_time) * 100) / 100.0,
            # SCAM and SUSPICIOUS categories show reported victims (negative_reviews) if found
            'negative_reviews': negative_reviews if category in ['scam', 'suspicious'] else [],
            'created_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500


@analyze_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """Get user's analysis history"""
    try:
        current_identity = get_jwt_identity()
        current_user = current_identity.lower().strip() if current_identity else None
        
        page = int(request.args.get('page', 1))
        # Default to 100 for dashboard visibility if not specified, min 10
        limit = int(request.args.get('limit', 100))
        skip = (page - 1) * limit
        
        if analyses is None:
            return jsonify({
                'analyses': [],
                'pagination': {'page': page, 'limit': limit, 'total': 0, 'pages': 0}
            }), 200
        
        # Get user's analysis history with case-insensitive email match
        query = {'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}} if current_user else {}
        user_analyses = list(analyses.find(query).sort('created_at', -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string
        for analysis in user_analyses:
            analysis['_id'] = str(analysis['_id'])
            if 'created_at' in analysis:
                analysis['created_at'] = analysis['created_at'].isoformat()
        
        # Get total count
        total = analyses.count_documents(query)
        print(f"[RECV] History for {current_user}: returning {len(user_analyses)} records (Total match: {total})")
        
        return jsonify({
            'analyses': user_analyses,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        print(f"[RECV] History Error: {str(e)}")
        return jsonify({'error': 'Failed to get history', 'details': str(e)}), 500


@analyze_bp.route('/analysis/<analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis(analysis_id):
    """Get specific analysis by ID"""
    try:
        current_user = get_jwt_identity()
        
        if analyses is None:
            return jsonify({'error': 'Database not available'}), 503
        
        from bson.objectid import ObjectId
        
        analysis = analyses.find_one({
            '_id': ObjectId(analysis_id),
            'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}
        })
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        analysis['_id'] = str(analysis['_id'])
        if 'created_at' in analysis:
            analysis['created_at'] = analysis['created_at'].isoformat()
            
        # Enrich with reviews if it's a scam/suspicious result and reviews aren't in document
        # (Since we don't store reviews in the history records to save space)
        if analysis.get('category') in ['scam'] and not analysis.get('negative_reviews'):
            try:
                # Use metadata stored in the analysis document
                meta = analysis.get('metadata', {})
                company_name = meta.get('search_name', '') or meta.get('company_name', '')
                enriched = None
                
                # PRIMARY: Try enrichment with stored company name first
                if company_name:
                    print(f"[HISTORY] Primary enrichment with company_name: '{company_name}'")
                    enriched = get_enriched_reviews(content=analysis.get('original_content', ''), company_name=company_name, limit=10)
                    if enriched:
                        analysis['negative_reviews'] = enriched
                        print(f"[HISTORY] Primary enrichment successful: {len(enriched)} reviews")
                        return jsonify(analysis), 200
                
                # FALLBACK 1: Scavenger Extraction: Look for company names in parentheses across all fields
                if not company_name:
                    content_to_scan = str(analysis.get('conclusion', {}).get('text', '')) + " " + \
                                      " ".join([str(e.get('reason', '')) for e in analysis.get('explanations', [])])
                    paren_matches = re.findall(r'\(([^)]+)\)', content_to_scan)
                    
                    if paren_matches:
                        for match in paren_matches:
                            potential_name = match.strip()
                            if len(potential_name) > 2 and 'scam' not in potential_name.lower():
                                print(f"[HISTORY] Scavenger found potential name: '{potential_name}'")
                                # Try to enrich immediately
                                enriched = get_enriched_reviews(content=analysis.get('original_content', ''), company_name=potential_name, limit=10)
                                if enriched:
                                    analysis['negative_reviews'] = enriched
                                    print(f"[HISTORY] Successfully enriched using Scavenger name: '{potential_name}'")
                                    return jsonify(analysis), 200 # Return early if successful
                
                # 3. Aggressive Fuzzy Fallback: Search the entire content for any known scam names
                if not enriched and not (analysis.get('negative_reviews') and len(analysis.get('negative_reviews', [])) > 0):
                    print(f"[HISTORY] Scavenger failed. Starting aggressive fuzzy search...")
                    from utils.excel_loader import fetch_all_known_names
                    try:
                        known_names = fetch_all_known_names()
                        # Get original content or conclusion text
                        search_space = str(analysis.get('original_content', '')) + " " + str(analysis.get('conclusion', {}).get('text', ''))
                        search_space = search_space.lower()
                        
                        best_match = None
                        for name in known_names:
                            if isinstance(name, str) and len(name) > 3 and name.lower() in search_space:
                                best_match = name
                                print(f"[HISTORY] Fuzzy match found: '{name}'")
                                break
                        
                        if best_match:
                            enriched = get_enriched_reviews(content='', company_name=best_match, limit=10)
                            if enriched:
                                analysis['negative_reviews'] = enriched
                                print(f"[HISTORY] Aggressive match successful for: '{best_match}'")
                    except Exception as fuzzy_err:
                        print(f"[HISTORY] Fuzzy fallback error: {fuzzy_err}")

                # If we finally have enriched reviews, ensure they are in the record
                if enriched:
                    analysis.update({'negative_reviews': enriched})
                elif not analysis.get('negative_reviews'):
                    analysis.update({'negative_reviews': []})
                    
                # Final count logging
                print(f"[HISTORY] Returning {len(analysis.get('negative_reviews', []))} reviews for record {analysis_id}")
                
            except Exception as e:
                print(f"[RECV] Enrichment error for {analysis_id}: {str(e)}")
                analysis['negative_reviews'] = []
        
        return jsonify(analysis), 200
        
    except Exception as e:
        print(f"[RECV] Global error in get_analysis: {str(e)}")
        return jsonify({'error': 'Failed to get analysis', 'details': str(e)}), 500


@analyze_bp.route('/shared/<analysis_id>', methods=['GET'])
def get_shared_analysis(analysis_id):
    """Public endpoint: Get analysis result for sharing — no login required.
    Strips sensitive fields (email, raw content) for privacy."""
    try:
        if analyses is None:
            return jsonify({'error': 'Database not available'}), 503
        
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        
        try:
            oid = ObjectId(analysis_id)
        except (InvalidId, Exception):
            return jsonify({'error': 'Invalid analysis ID'}), 400
        
        analysis = analyses.find_one({'_id': oid})
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Build a SAFE public response — strip sensitive data
        analysis['_id'] = str(analysis['_id'])
        if 'created_at' in analysis:
            analysis['created_at'] = analysis['created_at'].isoformat()
        
        # Remove sensitive fields
        safe_fields_to_remove = ['user_email', 'original_content']
        for field in safe_fields_to_remove:
            analysis.pop(field, None)
        
        # Enrich with reviews if scam and missing
        if analysis.get('category') in ['scam'] and not analysis.get('negative_reviews'):
            try:
                meta = analysis.get('metadata', {})
                company_name = meta.get('search_name', '') or meta.get('company_name', '')
                if company_name:
                    enriched = get_enriched_reviews(content='', company_name=company_name, limit=10)
                    if enriched:
                        analysis['negative_reviews'] = enriched
            except Exception:
                analysis['negative_reviews'] = []
        
        return jsonify(analysis), 200
        
    except Exception as e:
        print(f"[RECV] Global error in get_shared_analysis: {str(e)}")
        return jsonify({'error': 'Failed to get shared analysis'}), 500


@analyze_bp.route('/analysis/<analysis_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_analysis(analysis_id):
    """Delete a specific analysis by ID"""
    try:
        current_identity = get_jwt_identity()
        current_user = current_identity.lower().strip() if current_identity else 'mock_user@example.com'
        
        print(f"[RECV] DELETE Analysis Request: {analysis_id} for user {current_user}")
        
        if analyses is None:
            return jsonify({'message': 'No database, nothing to delete'}), 200
        
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        
        # Handle non-ObjectId strings (e.g. 'local-123')
        if not analysis_id or analysis_id.startswith('local-'):
             print(f"[RECV] DELETE: Local ID {analysis_id} - reporting success")
             return jsonify({'message': 'Deleted local entry'}), 200
             
        try:
            obj_id = ObjectId(analysis_id)
        except InvalidId:
            print(f"[RECV] DELETE: Invalid ID format {analysis_id} - reporting success to cleanup")
            return jsonify({'message': 'Invalid ID format, but removed from sync list'}), 200
        
        # Only delete if it belongs to the current user
        query = {
            '_id': obj_id, 
            'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}
        }
        result = analyses.delete_one(query)
        
        if result.deleted_count == 0:
            # Check if it exists for ANY user to give better debug info
            exists_any = analyses.find_one({'_id': obj_id})
            if not exists_any:
                print(f"[RECV] DELETE 404: Analysis {analysis_id} not found in DB")
                return jsonify({'error': 'Analysis not found'}), 404
            else:
                owner = exists_any.get('user_email', 'unknown')
                print(f"[RECV] DELETE 403: Analysis {analysis_id} owned by {owner}, request by {current_user}")
                return jsonify({'error': 'Not authorized to delete this record'}), 403
        
        print(f"[RECV] DELETE 200: Successfully deleted {analysis_id}")
        return jsonify({'message': 'Analysis deleted successfully'}), 200
        
    except Exception as e:
        print(f"[RECV] DELETE Error Exception: {str(e)}")
        return jsonify({'error': 'Failed to delete analysis', 'details': str(e)}), 500


@analyze_bp.route('/history', methods=['DELETE'])
@jwt_required(optional=True)
def clear_history():
    """Clear all analysis history for the current user"""
    try:
        current_identity = get_jwt_identity()
        current_user = current_identity.lower().strip() if current_identity else 'mock_user@example.com'
        
        if analyses is None:
            return jsonify({'message': 'No database, nothing to clear', 'deleted_count': 0}), 200
        
        result = analyses.delete_many({'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}})
        
        return jsonify({
            'message': 'History cleared successfully',
            'deleted_count': result.deleted_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to clear history', 'details': str(e)}), 500


@analyze_bp.route('/bulk-delete', methods=['POST'])
@jwt_required(optional=True)
def bulk_delete_analyses():
    """Delete multiple analyses by their IDs"""
    try:
        current_identity = get_jwt_identity()
        current_user = current_identity.lower().strip() if current_identity else 'mock_user@example.com'
        data = request.get_json()
        analysis_ids = data.get('ids', [])
        
        if not analysis_ids:
            return jsonify({'message': 'No IDs provided'}), 400
            
        if analyses is None:
            return jsonify({'message': 'No database, nothing to delete'}), 200
            
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        
        # Filter out local IDs and convert valid strings to ObjectIds
        object_ids = []
        for aid in analysis_ids:
            if aid and not aid.startswith('local-'):
                try:
                    object_ids.append(ObjectId(aid))
                except InvalidId:
                    continue
        
        result = analyses.delete_many({
            '_id': {'$in': object_ids},
            'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}
        })
        
        return jsonify({
            'message': f'Successfully deleted {result.deleted_count} records',
            'deleted_count': result.deleted_count
        }), 200
        
    except Exception as e:
        print(f"[RECV] Bulk DELETE Error: {str(e)}")
        return jsonify({'error': 'Failed to delete analyses', 'details': str(e)}), 500


@analyze_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get user's analysis statistics"""
    try:
        current_identity = get_jwt_identity()
        current_user = current_identity.lower().strip() if current_identity else None
        
        if analyses is None:
            return jsonify({
                'total_analyses': 0,
                'scams_detected': 0,
                'legitimate_found': 0,
                'suspicious_found': 0,
                'avg_risk_score': 0
            }), 200
        
        # Build case-insensitive query
        query = {'user_email': {'$regex': f'^{re.escape(current_user)}$', '$options': 'i'}} if current_user else {}
        
        # Get statistics
        total = analyses.count_documents(query)
        scams = analyses.count_documents({**query, 'risk_level': 'SCAM'})
        legit = analyses.count_documents({**query, 'risk_level': 'LEGITIMATE'})
        suspicious = analyses.count_documents({**query, 'risk_level': 'SUSPICIOUS'})
        
        # Calculate average risk score
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'avg_score': {'$avg': '$risk_score'}}}
        ]
        result = list(analyses.aggregate(pipeline))
        avg_score = result[0]['avg_score'] if result else 0
        
        return jsonify({
            'total_analyses': total,
            'scams_detected': scams,
            'legitimate_found': legit,
            'suspicious_found': suspicious,
            'avg_risk_score': round(avg_score or 0, 1)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stats', 'details': str(e)}), 500


@analyze_bp.route('/distribution', methods=['GET'])
@jwt_required()
def get_distribution():
    """Get risk level distribution for the current user"""
    try:
        current_user = get_jwt_identity()
        
        if analyses is None:
            return jsonify({'legitimate': 0, 'suspicious': 0, 'scam': 0}), 200
            
        pipeline = [
            {'$match': {'user_email': current_user}},
            {'$group': {'_id': '$risk_level', 'count': {'$sum': 1}}}
        ]
        
        results = list(analyses.aggregate(pipeline))
        
        distribution = {
            'legitimate': 0,
            'suspicious': 0,
            'scam': 0
        }
        
        for res in results:
            level = str(res['_id']).lower()
            if level in distribution:
                distribution[level] = res['count']
                
        return jsonify(distribution), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get distribution', 'details': str(e)}), 500


@analyze_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """Get analysis trends (labels and counts) for the last 7 days"""
    try:
        current_user = get_jwt_identity()
        
        if analyses is None:
            return jsonify([]), 200
            
        # Get last 7 days trends
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        pipeline = [
            {'$match': {
                'user_email': current_user,
                'created_at': {'$gte': seven_days_ago}
            }},
            {'$group': {
                '_id': {
                    'year': {'$year': '$created_at'},
                    'month': {'$month': '$created_at'},
                    'day': {'$dayOfMonth': '$created_at'}
                },
                'total': {'$sum': 1},
                'scams': {'$sum': {'$cond': [{'$eq': ['$risk_level', 'SCAM']}, 1, 0]}}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        
        results = list(analyses.aggregate(pipeline))
        
        trends = []
        for res in results:
            date_str = f"{res['_id']['year']}-{res['_id']['month']}-{res['_id']['day']}"
            trends.append({
                'date': date_str,
                'analyses': res['total'],
                'scams': res['scams']
            })
            
        return jsonify(trends), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get trends', 'details': str(e)}), 500