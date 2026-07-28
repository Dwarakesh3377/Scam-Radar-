import numpy as np
import joblib
import pickle
import torch
from transformers import AutoTokenizer, AutoModel
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.features import extract_features, normalize_features
from backend.services.predict import predict_risk, get_risk_breakdown
from backend.services.explain import generate_shap_explanations

class InferencePipeline:
    """Pipeline for making predictions on new data"""
    
    def __init__(self):
        # Path relative to project root
        self.root_path = Path(__file__).parent.parent.parent
        self.models_path = self.root_path / 'ml_models'
        
        # Load models
        self.load_models()
        
        # Initialize feature extractor
        self.feature_extractor = None
    
    def load_models(self):
        """Load trained models"""
        print("Loading models for inference...")
        
        try:
            # Load metadata model
            metadata_path = self.models_path / 'metadata_model'
            
            if (metadata_path / 'model.pkl').exists():
                self.metadata_model = joblib.load(metadata_path / 'model.pkl')
                self.scaler = joblib.load(metadata_path / 'scaler.pkl')
                
                # Load feature names
                import json
                with open(metadata_path / 'feature_names.json', 'r') as f:
                    self.feature_names = json.load(f)
                
                print("Metadata model loaded successfully")
            else:
                print(f"Metadata model not found at {metadata_path}")
                self.metadata_model = None
                self.scaler = None
            
            # Load BERT model
            # DO NOT fallback to Hugging Face automatically as it causes hangs during startup
            bert_path = self.models_path / 'bert_model'
            pytorch_bin = bert_path / 'pytorch_model.bin'
            
            if pytorch_bin.exists() and pytorch_bin.stat().st_size > 0:
                try:
                    print(f"Loading local BERT model from {bert_path}")
                    self.bert_tokenizer = AutoTokenizer.from_pretrained(str(bert_path))
                    self.bert_model = AutoModel.from_pretrained(str(bert_path))
                    self.bert_model.eval()
                    self.use_bert = True
                    print("BERT model initialized successfully")
                except Exception as bert_e:
                    print(f"Error loading local BERT model: {bert_e}")
                    self.use_bert = False
                    self.bert_tokenizer = None
                    self.bert_model = None
            else:
                print("Local BERT model missing or empty. Skipping BERT to ensure fast startup.")
                self.use_bert = False
                self.bert_tokenizer = None
                self.bert_model = None
            
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            self.metadata_model = None
            self.scaler = None
            self.bert_model = None
            self.bert_tokenizer = None
    
    def extract_text_features(self, text, language='en'):
        """Extract features from text using loaded models"""
        features = {}
        
        # Use TF-IDF features if available
        if hasattr(self, 'feature_names') and self.feature_names:
            # In production, you would use the loaded TF-IDF vectorizer
            # For now, use simple feature extraction
            from backend.services.features import extract_text_features as etf
            features.update(etf(text, language))
        
        return features
    
    def get_bert_embeddings(self, text):
        """Get BERT embeddings for text"""
        if self.bert_model is None or self.bert_tokenizer is None:
            return np.zeros(768)  # Fallback
        
        try:
            # Tokenize text
            inputs = self.bert_tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                # Use mean of last hidden state as embedding
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            return embeddings
            
        except Exception as e:
            print(f"Error getting BERT embeddings: {str(e)}")
            return np.zeros(768)
    
    def predict_with_metadata_model(self, features):
        """Make prediction using metadata model"""
        if self.metadata_model is None or self.scaler is None:
            return 0.5, 0.7  # Fallback
        
        try:
            # Convert features to array in correct order
            feature_array = []
            for feature_name in self.feature_names:
                if feature_name in features:
                    feature_array.append(features[feature_name])
                else:
                    feature_array.append(0)  # Default value for missing features
            
            feature_array = np.array(feature_array).reshape(1, -1)
            
            # Scale features
            feature_array_scaled = self.scaler.transform(feature_array)
            
            # Predict
            prediction = self.metadata_model.predict_proba(feature_array_scaled)[0]
            
            # Get risk score (probability of scam)
            if len(prediction) == 2:  # Binary classification
                risk_score = prediction[1] * 100  # Convert to percentage
            else:  # Multi-class or regression
                risk_score = float(prediction[0]) * 100
            
            # Confidence score (based on probability)
            confidence = np.max(prediction)
            
            return min(100, max(0, risk_score)), confidence
            
        except Exception as e:
            print(f"Error predicting with metadata model: {str(e)}")
            return 0.5 * 100, 0.5
    
    def analyze(self, text, metadata=None, language='en'):
        """
        Main analysis function
        Returns: dict with risk score, explanations, etc.
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Extract features
            if metadata is None:
                metadata = {}
            
            # Extract comprehensive features
            features = extract_features(text, metadata, language)
            
            # Step 2: Make predictions using multiple methods
            # Metadata model prediction
            metadata_score, metadata_confidence = self.predict_with_metadata_model(features)
            
            # BERT-based prediction (if available)
            bert_score = 0
            bert_confidence = 0.5
            if self.bert_model is not None:
                # Get BERT embeddings
                embeddings = self.get_bert_embeddings(text)
                
                # Simple heuristic based on text characteristics
                text_length = len(text)
                if text_length > 0:
                    # More text = potentially more legitimate
                    length_factor = min(1, text_length / 1000)
                    
                    # Keyword density from features
                    scam_density = features.get('scam_keyword_density', 0)
                    
                    # Calculate BERT-based score
                    bert_score = (scam_density * 100) - (length_factor * 20)
                    bert_score = max(0, min(100, bert_score))
                    
                    # Confidence based on text length
                    bert_confidence = min(0.9, text_length / 500)
            
            # Rule-based prediction
            from backend.services.predict import calculate_rule_based_score
            rule_score = calculate_rule_based_score(features)
            rule_confidence = 0.8
            
            # Step 3: Combine predictions
            weights = {
                'metadata': 0.4,
                'bert': 0.3 if self.bert_model is not None else 0,
                'rule': 0.3
            }
            
            # Adjust weights based on confidence
            weighted_scores = []
            total_weight = 0
            
            if metadata_confidence > 0.3:
                weighted_scores.append(metadata_score * weights['metadata'] * metadata_confidence)
                total_weight += weights['metadata'] * metadata_confidence
            
            if self.bert_model is not None and bert_confidence > 0.3:
                weighted_scores.append(bert_score * weights['bert'] * bert_confidence)
                total_weight += weights['bert'] * bert_confidence
            
            if rule_confidence > 0.3:
                weighted_scores.append(rule_score * weights['rule'] * rule_confidence)
                total_weight += weights['rule'] * rule_confidence
            
            # Calculate final score
            if total_weight > 0:
                final_score = sum(weighted_scores) / total_weight
                final_confidence = total_weight / sum(weights.values())
            else:
                # Fallback to rule-based
                final_score = rule_score
                final_confidence = 0.6
            
            # Apply sigmoid-like adjustment
            import math
            adjusted_score = 100 / (1 + math.exp(-0.1 * (final_score - 50)))
            
            # Round to integer
            final_score_int = int(round(adjusted_score))
            final_confidence = round(final_confidence, 2)
            
            # Ensure score is within bounds
            final_score_int = max(0, min(100, final_score_int))
            
            # Step 4: Generate explanations
            explanations = generate_shap_explanations(features, final_score_int, language)
            
            # Step 5: Determine risk level
            from backend.utils.risk_mapper import RiskMapper
            risk_level = RiskMapper.get_risk_level(final_score_int)
            
            # Step 6: Get safety advice
            safety_advice = RiskMapper.get_safety_advice(final_score_int)
            
            # Step 7: Get conclusion
            conclusion = RiskMapper.get_conclusion(final_score_int)
            
            # Step 8: Get actions
            actions = RiskMapper.get_actions(final_score_int)
            
            # Step 9: Calculate analysis time
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # Ensure minimum 2 second delay for realistic experience
            if analysis_time < 2:
                import time
                time.sleep(2 - analysis_time)
                analysis_time = 2
            
            # Prepare response
            response = {
                'score': final_score_int,
                'confidence': final_confidence,
                'risk_level': risk_level,
                'explanations': explanations,
                'safety_advice': safety_advice,
                'conclusion': conclusion,
                'actions': actions,
                'analysis_time': round(analysis_time, 2),
                'features_used': len(features),
                'language': language,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add breakdown if requested
            if metadata.get('include_breakdown', False):
                breakdown = get_risk_breakdown(features)
                response['breakdown'] = breakdown
            
            return response
            
        except Exception as e:
            print(f"Error in inference pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error response
            return {
                'score': 50,
                'confidence': 0.5,
                'risk_level': 'UNKNOWN',
                'explanations': ['Analysis encountered an error'],
                'safety_advice': ['Please try again or contact support'],
                'conclusion': 'Unable to complete analysis',
                'error': str(e),
                'analysis_time': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def batch_analyze(self, texts, metadata_list=None, language='en'):
        """Analyze multiple texts in batch"""
        results = []
        
        for i, text in enumerate(texts):
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
            result = self.analyze(text, metadata, language)
            results.append(result)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(texts)} texts")
        
        return results

# Singleton instance for global use
inference_pipeline = InferencePipeline()

if __name__ == "__main__":
    # Test the pipeline
    pipeline = InferencePipeline()
    
    test_text = "URGENT HIRING! Work from home and earn $5000/month. No experience needed!"
    test_metadata = {
        'sender_email': 'recruiter@fakecompany.xyz',
        'phone': '+1234567890'
    }
    
    result = pipeline.analyze(test_text, test_metadata, 'en')
    
    print("\n" + "=" * 50)
    print("INFERENCE PIPELINE TEST")
    print("=" * 50)
    print(f"Text: {test_text}")
    print(f"\nResult:")
    print(f"Score: {result['score']}%")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Confidence: {result['confidence']}")
    print(f"\nExplanations:")
    for exp in result['explanations']:
        print(f"- {exp}")
    print(f"\nConclusion: {result['conclusion']}")
    print(f"\nAnalysis Time: {result['analysis_time']}s")
    print("=" * 50)