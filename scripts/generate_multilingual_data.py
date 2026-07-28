import pandas as pd
import os

def generate_multilingual_sample():
    data = [
        # Hindi (Scam)
        {"text": "आपको घर बैठे ₹५०,००० कमाने का मौका। तुरंत व्हाट्सएप करें।", "label": "scam", "language": "hi"},
        {"text": "पंजीकरण शुल्क ₹५०० अनिवार्य है।", "label": "scam", "language": "hi"},
        # Hindi (Legit)
        {"text": "इन्फोसिस में सॉफ्टवेयर इंजीनियर की भर्ती। आधिकारिक वेबसाइट पर आवेदन करें।", "label": "legitimate", "language": "hi"},
        
        # Tamil (Scam)
        {"text": "வீட்டில் இருந்தே மாதம் ₹60,000 சம்பாதிக்கலாம். முன்பணம் தேவை.", "label": "scam", "language": "ta"},
        # Tamil (Legit)
        {"text": "டாடா கன்சல்டன்சி சர்வீசஸ் நிறுவனத்தில் வேலை வாய்ப்பு. தகுதியுள்ளவர்கள் விண்ணப்பிக்கவும்.", "label": "legitimate", "language": "ta"},
        
        # Spanish (Scam)
        {"text": "Gana 3000€ al mes trabajando desde casa. Envía un mensaje por Telegram ahora.", "label": "scam", "language": "es"},
        {"text": "Se requiere pago de depósito de seguridad para comenzar la capacitación.", "label": "scam", "language": "es"},
        # Spanish (Legit)
        {"text": "Oportunidad de empleo en Amazon España. Aplique a través del portal de carreras oficial.", "label": "legitimate", "language": "es"},
        
        # French (Scam)
        {"text": "Gagnez 2000€ par semaine. Aucune expérience requise. Contactez-nous sur WhatsApp.", "label": "scam", "language": "fr"},
        # French (Legit)
        {"text": "Poste de développeur chez Ubisoft Paris. Veuillez consulter notre site officiel pour postuler.", "label": "legitimate", "language": "fr"}
    ]
    
    df = pd.DataFrame(data)
    
    dataset_dir = "d:/scam-risk-detection2/dataset"
    os.makedirs(dataset_dir, exist_ok=True)
    
    output_path = os.path.join(dataset_dir, "multilingual_sample_v1.xlsx")
    df.to_excel(output_path, index=False)
    print(f"Sample data generated at: {output_path}")

if __name__ == "__main__":
    generate_multilingual_sample()
