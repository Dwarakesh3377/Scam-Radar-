import pandas as pd
import numpy as np
import pickle
import joblib
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import torch
from transformers import AutoTokenizer, AutoModel, Trainer, TrainingArguments
from dataset import Dataset
import warnings
warnings.filterwarnings('ignore')

class TrainingPipeline:
    """Pipeline for training scam detection models"""
    
    def __init__(self, data_path='dataset/'):
        self.data_path = data_path
        self.models_path = 'ml_models/'
        
        # Create directories
        os.makedirs(self.models_path, exist_ok=True)
        os.makedirs(os.path.join(self.models_path, 'bert_model'), exist_ok=True)
        os.makedirs(os.path.join(self.models_path, 'metadata_model'), exist_ok=True)
        
        # Initialize components
        self.tfidf_vectorizer = None
        self.metadata_model = None
        self.scaler = None
        self.bert_tokenizer = None
        self.bert_model = None
        
    def load_data(self):
        """Load training data"""
        print("Loading training data...")
        
        data = []
        labels = []
        metadata = []
        
        try:
            # Load scam data
            scam_file = os.path.join(self.data_path, 'scam_data.csv')
            if os.path.exists(scam_file):
                scam_df = pd.read_csv(scam_file)
                data.extend(scam_df['text'].tolist())
                labels.extend([1] * len(scam_df))  # 1 for scam
                metadata.extend(scam_df['metadata'].apply(eval).tolist())
            
            # Load legit data
            legit_file = os.path.join(self.data_path, 'legit_data.csv')
            if os.path.exists(legit_file):
                legit_df = pd.read_csv(legit_file)
                data.extend(legit_df['text'].tolist())
                labels.extend([0] * len(legit_df))  # 0 for legit
                metadata.extend(legit_df['metadata'].apply(eval).tolist())
            
            print(f"Loaded {len(data)} samples ({sum(labels)} scams, {len(labels)-sum(labels)} legit)")
            
            return data, labels, metadata
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return [], [], []
    
    def extract_features(self, texts, metadata_list):
        """Extract features from texts and metadata"""
        print("Extracting features...")
        
        # Text features using TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        text_features = self.tfidf_vectorizer.fit_transform(texts).toarray()
        
        # Metadata features
        meta_features = []
        for meta in metadata_list:
            features = []
            
            # Binary features
            features.append(1 if meta.get('has_urgency', False) else 0)
            features.append(1 if meta.get('has_money_mention', False) else 0)
            features.append(1 if meta.get('has_personal_info_request', False) else 0)
            
            # Numerical features
            features.append(meta.get('grammar_errors', 0))
            
            meta_features.append(features)
        
        meta_features = np.array(meta_features)
        
        # Combine features
        if len(meta_features) > 0:
            all_features = np.hstack([text_features, meta_features])
        else:
            all_features = text_features
        
        return all_features
    
    def train_metadata_model(self, X, y):
        """Train Random Forest model on metadata features"""
        print("Training metadata model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.metadata_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.metadata_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.metadata_model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Metadata Model Accuracy: {accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Legit', 'Scam']))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print("\nConfusion Matrix:")
        print(cm)
        
        return accuracy
    
    def train_bert_model(self, texts, labels):
        """Train/fine-tune BERT model for text understanding"""
        print("Preparing BERT model training...")
        
        # For now, we'll just load a pre-trained BERT model
        # In production, you would fine-tune it on your data
        
        try:
            from transformers import BertForSequenceClassification
            
            # Load pre-trained BERT model
            model_name = 'bert-base-uncased'
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = BertForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2
            )
            
            print(f"Loaded pre-trained BERT model: {model_name}")
            
            # Note: Fine-tuning code would go here
            # This requires significant computational resources
            
            return True
            
        except Exception as e:
            print(f"Error with BERT model: {str(e)}")
            print("Falling back to simpler model...")
            return False
    
    def save_models(self):
        """Save trained models"""
        print("Saving models...")
        
        # Save TF-IDF vectorizer
        if self.tfidf_vectorizer:
            vectorizer_path = os.path.join(self.models_path, 'metadata_model', 'tfidf_vectorizer.pkl')
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
        
        # Save metadata model
        if self.metadata_model:
            model_path = os.path.join(self.models_path, 'metadata_model', 'model.pkl')
            joblib.dump(self.metadata_model, model_path)
        
        # Save scaler
        if self.scaler:
            scaler_path = os.path.join(self.models_path, 'metadata_model', 'scaler.pkl')
            joblib.dump(self.scaler, scaler_path)
        
        # Save BERT model (if available)
        if self.bert_model and self.bert_tokenizer:
            bert_path = os.path.join(self.models_path, 'bert_model')
            self.bert_model.save_pretrained(bert_path)
            self.bert_tokenizer.save_pretrained(bert_path)
        
        # Save feature names
        feature_names = []
        if self.tfidf_vectorizer:
            feature_names.extend(self.tfidf_vectorizer.get_feature_names_out())
        
        # Add metadata feature names
        meta_features = ['has_urgency', 'has_money_mention', 'has_personal_info_request', 'grammar_errors']
        feature_names.extend(meta_features)
        
        features_path = os.path.join(self.models_path, 'metadata_model', 'feature_names.json')
        import json
        with open(features_path, 'w') as f:
            json.dump(feature_names, f)
        
        print("Models saved successfully!")
    
    def run_pipeline(self):
        """Run complete training pipeline"""
        print("=" * 50)
        print("SCAM DETECTION MODEL TRAINING PIPELINE")
        print("=" * 50)
        
        # Step 1: Load data
        texts, labels, metadata = self.load_data()
        
        if len(texts) == 0:
            print("No data found for training!")
            return
        
        # Step 2: Extract features
        X = self.extract_features(texts, metadata)
        y = np.array(labels)
        
        # Step 3: Train metadata model
        accuracy = self.train_metadata_model(X, y)
        
        # Step 4: Train BERT model (if enough data)
        if len(texts) >= 1000:  # Need substantial data for BERT
            self.train_bert_model(texts, labels)
        else:
            print(f"Not enough data ({len(texts)} samples) for BERT fine-tuning")
        
        # Step 5: Save models
        self.save_models()
        
        print("\n" + "=" * 50)
        print("TRAINING COMPLETE!")
        print(f"Final Model Accuracy: {accuracy:.2%}")
        print("Models saved to:", self.models_path)
        print("=" * 50)
    
    def evaluate_on_test_data(self, test_data_path='test_data.csv'):
        """Evaluate model on test data"""
        print("\nEvaluating on test data...")
        
        if not os.path.exists(test_data_path):
            print("Test data not found!")
            return
        
        # Load test data
        test_df = pd.read_csv(test_data_path)
        test_texts = test_df['text'].tolist()
        test_labels = test_df['label'].tolist()
        
        # Extract features
        X_test = self.tfidf_vectorizer.transform(test_texts).toarray()
        
        # Add metadata features if available
        if 'metadata' in test_df.columns:
            test_metadata = test_df['metadata'].apply(eval).tolist()
            meta_features = []
            for meta in test_metadata:
                features = []
                features.append(1 if meta.get('has_urgency', False) else 0)
                features.append(1 if meta.get('has_money_mention', False) else 0)
                features.append(1 if meta.get('has_personal_info_request', False) else 0)
                features.append(meta.get('grammar_errors', 0))
                meta_features.append(features)
            
            X_test = np.hstack([X_test, meta_features])
        
        # Scale features
        X_test_scaled = self.scaler.transform(X_test)
        
        # Predict
        y_pred = self.metadata_model.predict(X_test_scaled)
        
        # Evaluate
        accuracy = accuracy_score(test_labels, y_pred)
        
        print(f"Test Accuracy: {accuracy:.2%}")
        print("\nTest Classification Report:")
        print(classification_report(test_labels, y_pred, target_names=['Legit', 'Scam']))
        
        return accuracy

# Main execution
if __name__ == "__main__":
    pipeline = TrainingPipeline()
    pipeline.run_pipeline()