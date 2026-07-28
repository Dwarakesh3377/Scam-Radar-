import os
# Prevent WinError 1114 / OpenMP conflict - MUST BE BEFORE ANY OTHER IMPORTS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import numpy as np
import pandas as pd
import pickle
import joblib
import re
# Heavy imports moved inside load_models to prevent blocking Flask startup
# from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

# Global variables for models
bert_model = None
bert_tokenizer = None
xlm_model = None
xlm_tokenizer = None
metadata_model = None
metadata_scaler = None
text_vectorizer = None  # TF-IDF vectorizer for text-based predictions

def load_models():
    """
    Load ML models for prediction.
    Downloads from Hugging Face Hub if local files are missing.
    """
    global bert_model, bert_tokenizer, xlm_model, xlm_tokenizer, metadata_model, metadata_scaler, text_vectorizer
    
    print("[PREDICT] Starting model loading process from Hugging Face Hub...")
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from huggingface_hub import snapshot_download
        
        # Get absolute paths relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_root = os.path.abspath(os.path.join(current_dir, '../../ml_models'))
        
        # Ensure models_root exists
        os.makedirs(models_root, exist_ok=True)
        
        # Repository name on Hugging Face Hub
        repo_id = "GOPIESWAR/scam-detector-models"
        
        # Download all models from the Hub SNAPSHOT
        # This will only download missing files and cache them
        print(f"[PREDICT] Syncing weights from {repo_id}...")
        try:
            hub_path = snapshot_download(
                repo_id=repo_id,
                local_dir=models_root,
                local_dir_use_symlinks=False
            )
            print(f"[PREDICT] Weights synced to {hub_path}")
        except Exception as e:
            print(f"[PREDICT] Snapshot download failed/using local: {e}")

        # 1. Load English BERT model
        bert_model_path = os.path.join(models_root, 'bert_model')
        if bert_model is None and os.path.exists(bert_model_path) and os.path.exists(os.path.join(bert_model_path, 'config.json')):
            try:
                print("[PREDICT] Loading BERT model into memory...")
                bert_tokenizer = AutoTokenizer.from_pretrained(bert_model_path)
                bert_model = AutoModelForSequenceClassification.from_pretrained(bert_model_path, low_cpu_mem_usage=True)
                bert_model.eval()
                print("[PREDICT] BERT model loaded successfully")
            except Exception as e:
                print(f"[PREDICT] BERT model loading failed: {e}")

        # 2. Load Multilingual XLM-RoBERTa model
        xlm_model_path = os.path.join(models_root, 'xlm_roberta_multilingual')
        if xlm_model is None and os.path.exists(xlm_model_path) and os.path.exists(os.path.join(xlm_model_path, 'config.json')):
            try:
                print("[PREDICT] Loading XLM-RoBERTa model into memory...")
                xlm_tokenizer = AutoTokenizer.from_pretrained(xlm_model_path)
                xlm_model = AutoModelForSequenceClassification.from_pretrained(xlm_model_path, low_cpu_mem_usage=True)
                xlm_model.eval()
                print("[PREDICT] XLM-RoBERTa model loaded successfully")
            except Exception as e:
                print(f"[PREDICT] XLM-RoBERTa model loading failed: {e}")
        
        # 3. Load metadata model
        metadata_path = os.path.join(models_root, 'metadata_model')
        model_file = os.path.join(metadata_path, 'model.pkl')
        scaler_file = os.path.join(metadata_path, 'scaler.pkl')
        vectorizer_file = os.path.join(metadata_path, 'vectorizer.pkl')
        
        if os.path.exists(vectorizer_file):
            try:
                with open(vectorizer_file, 'rb') as f:
                    text_vectorizer = pickle.load(f)
                print("TF-IDF vectorizer loaded successfully")
            except Exception as e:
                print(f"Error loading vectorizer: {e}")
        
        if os.path.exists(model_file):
            try:
                metadata_model = joblib.load(model_file)
                if os.path.exists(scaler_file):
                    metadata_scaler = joblib.load(scaler_file)
                print("Metadata model loaded successfully")
            except Exception as e:
                print(f"Model load failed: {e}")
            
    except Exception as e:
        print(f"Error loading models: {str(e)}")

def get_bert_prediction(text):
    """
    Get English BERT prediction
    """
    global bert_model, bert_tokenizer
    
    if bert_model is None or bert_tokenizer is None:
        return 0, 0.0
    
    try:
        inputs = bert_tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = bert_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # 0=Legit, 1=Suspicious, 2=Scam
            suspicious_prob = probs[0][1].item()
            scam_prob = probs[0][2].item()
            
            risk_score = (scam_prob * 100) + (suspicious_prob * 50)
            confidence = max(probs[0]).item()
            
            return min(100, risk_score), confidence
    except Exception as e:
        print(f"Error getting BERT prediction: {str(e)}")
        return 0, 0.0

def get_xlm_prediction(text):
    """
    Get Multilingual XLM-RoBERTa prediction
    """
    global xlm_model, xlm_tokenizer
    
    if xlm_model is None or xlm_tokenizer is None:
        return 0, 0.0
    
    try:
        inputs = xlm_tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = xlm_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            suspicious_prob = probs[0][1].item()
            scam_prob = probs[0][2].item()
            
            risk_score = (scam_prob * 100) + (suspicious_prob * 50)
            confidence = max(probs[0]).item()
            
            return min(100, risk_score), confidence
    except Exception as e:
        print(f"Error getting XLM prediction: {str(e)}")
        return 0, 0.0

def predict_with_tfidf(text):
    """Predict risk using TF-IDF features and trained model"""
    global metadata_model, text_vectorizer, metadata_scaler
    
    if metadata_model is None or text_vectorizer is None:
        return None, 0.5
    
    try:
        tfidf_features = text_vectorizer.transform([text]).toarray()
        if metadata_scaler is not None:
            tfidf_features = metadata_scaler.transform(tfidf_features)
        
        proba = metadata_model.predict_proba(tfidf_features)[0]
        predicted_class = metadata_model.predict(tfidf_features)[0]
        
        # Map class to score
        if predicted_class == 0:  # Legitimate
            risk_score = 10 + (1 - proba[0]) * 23
        elif predicted_class == 1:  # Suspicious
            risk_score = 40 + proba[2] * 26
        else:  # Scam
            risk_score = 70 + proba[2] * 30
            
        return int(round(risk_score)), round(max(proba), 2)
    except Exception as e:
        print(f"Error in TF-IDF prediction: {e}")
        return None, 0.5

def calculate_rule_based_score(features):
    """Aggressive rule-based scoring for better differentiation"""
    score = 15  # Start at very low base (Clear Legit)
    
    # 🚨 SCAM INDICATORS (Positive weights)
    if features.get('scam_financial_count', 0) > 0: score += 100  # IMMEDIATE HIGH RISK
    
    # Urgency penalty scaled by count to be more lenient on single occurrences
    urgency_count = features.get('scam_urgency_count', 0)
    if urgency_count > 1:
        score += 25
    elif urgency_count == 1:
        score += 10 # Single urgency word is barely a hint
        
    if features.get('scam_contact_count', 0) > 0: score += 20  # WhatsApp/Telegram
    if features.get('meta_is_free_email', 0): score += 20  # Gmail/Yahoo sender
    if features.get('has_suspicious_tld', 0): score += 40
    if features.get('domain_mismatch'): score += 30
    
    # ✅ LEGITIMATE INDICATORS (Negative weights - Reducing risk)
    # Corporate email bonus (Significant trust)
    if not features.get('meta_is_free_email', 0) and features.get('sender_email_length', 0) > 5:
        score -= 25 # Increased bonus
    
    # Professionalism bonus (Scaling with keywords)
    legit_kws = features.get('total_legit_keywords', 0)
    if legit_kws > 0:
        # More aggressive reduction for legit terms
        reduction = min(35, (legit_kws // 2) * 5 + 10)
        score -= reduction
    
    if features.get('is_https', 0): score -= 10 # Increased bonus
    if features.get('total_scam_keywords', 0) == 0: score -= 15
    
    return max(0, min(100, score))

def predict_risk(features, language='en'):
    """Decisive routing between English BERT and Multilingual XLM-RoBERTa"""
    try:
        # LAZY LOAD: Ensure models are loaded before prediction
        if bert_model is None or xlm_model is None:
            load_models()
        
        text = features.get('text', '')
        
        # 1. Choose Model based on Language
        ml_score, ml_conf = 0, 0.0
        if text:
            if language == 'en':
                print("[PREDICT] Routing to English BERT...")
                ml_score, ml_conf = get_bert_prediction(text)
            else:
                # Use XLM-RoBERTa for Tamil, Hindi, French, Spanish, German, Russian, Chinese, Japanese, Korean
                print(f"[PREDICT] Routing to Multilingual XLM-RoBERTa (Language: {language})...")
                ml_score, ml_conf = get_xlm_prediction(text)
                # Fallback to English BERT ONLY if XLM fails or isn't loaded
                if ml_score == 0 and ml_conf == 0:
                    ml_score, ml_conf = get_bert_prediction(text)
        
        # 2. TF-IDF Model (Baseline fallback)
        tfidf_score, tfidf_conf = 10, 0.0
        if text:
            res_score, res_conf = predict_with_tfidf(text)
            if res_score is not None:
                tfidf_score, tfidf_conf = res_score, res_conf
        
        # 3. Rule-Based Scoring
        rule_score = calculate_rule_based_score(features)
        
        print(f"DEBUG: rule_score={rule_score}, ml_score={ml_score}, tfidf_score={tfidf_score}")
        print(f"DEBUG: scam_financial_count={features.get('scam_financial_count', 0)}, scam_urgency_count={features.get('scam_urgency_count', 0)}")
        print(f"DEBUG: total_scam_keywords={features.get('total_scam_keywords', 0)}, meta_is_free_email={features.get('meta_is_free_email')}")

        # Aggregated Logic
        final_score = (rule_score * 0.5) + (ml_score * 0.3) + (tfidf_score * 0.2)
        confidence = max(ml_conf, tfidf_conf, 0.40)
        
        # 🛡️ SHORT/NUMERIC CONTENT PROTECTION
        # If input is too short or almost entirely digits, BERT/TF-IDF can be unreliable
        clean_text = re.sub(r'[\s\-\(\)\+]', '', text)
        is_mostly_numeric = len(clean_text) > 0 and (sum(c.isdigit() for c in clean_text) / len(clean_text)) > 0.6
        if len(text) < 25 or is_mostly_numeric:
            # Drop risk if no critical scam indicators (financial) are present
            if features.get('scam_financial_count', 0) == 0:
                print(f"[PREDICT] Short/Numeric content detected. Capping risk score. Length: {len(text)}")
                final_score = min(40, final_score)
                confidence = min(0.60, confidence)
            
        # 🚀 SCAM BOOSTER: CRITICAL OVERRIDES
        if features.get('scam_financial_count', 0) > 0:
            final_score = max(85, final_score)
            
        red_flag_count = 0
        if features.get('has_suspicious_tld'):
            red_flag_count += 1
        if features.get('scam_urgency_count', 0) > 0:
            red_flag_count += 1
        if features.get('domain_mismatch'):
            red_flag_count += 1
        if features.get('meta_is_free_email'):
            red_flag_count += 1
        if features.get('scam_contact_count', 0) > 0:
            red_flag_count += 1
        
        # Multiple red flags = SCAM, single red flag = SUSPICIOUS
        if red_flag_count >= 3:
            final_score = max(70, final_score)
        elif red_flag_count == 2:
            final_score = max(55, final_score)
        elif red_flag_count == 1:
            final_score = max(40, final_score)
        
        # 🛡️ LEGIT PROTECTOR
        is_very_clean = (features.get('total_scam_keywords', 0) == 0 and 
                         features.get('scam_financial_count', 0) == 0 and
                         not features.get('meta_is_free_email') and 
                         not features.get('has_suspicious_tld') and
                         not features.get('domain_mismatch'))
        
        if is_very_clean:
            final_score = min(20, final_score)
            
        # 🏢 CORPORATE PROTECTOR
        is_corporate_safe = (not features.get('meta_is_free_email') and 
                             features.get('scam_financial_count', 0) == 0 and
                             features.get('scam_urgency_count', 0) == 0)
                             
        if is_corporate_safe:
             if features.get('total_legit_keywords', 0) > 0:
                 final_score = min(20, final_score)
             else:
                 final_score = min(30, final_score)
        
        # 🚨 FINAL OVERRIDE: Payment demands are ALWAYS high risk, regardless of protectors
        if features.get('scam_financial_count', 0) > 0:
            final_score = max(80, final_score)

        import random
        final_score = max(0, min(100, final_score))
        final_confidence = max(0.35, min(0.95, confidence + random.uniform(-0.10, 0.10)))
        return int(round(final_score)), round(final_confidence, 2)
        
    except Exception as e:
        print(f"Error in predict_risk: {str(e)}")
        return 50, 0.5

# NOTE: Background loading removed to prevent OOM during Gunicorn initialization.
# Models will now lazy-load on the first analysis request.
# This prevents 137 Exit Code on Hugging Face by distributing memory load.
# loading_thread = threading.Thread(target=load_models, daemon=True)
# loading_thread.start()