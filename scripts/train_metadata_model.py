import os
import pandas as pd
import numpy as np
import joblib
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def train_metadata_model():
    dataset_dir = 'dataset'
    models_dir = 'ml_models/metadata_model'
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Define files and their labels
    # 0 = Legitimate, 1 = Suspicious, 2 = Scam
    data_sources = [
        ('legitimate_jobs_final 2.0.xlsx', 0),
        ('legitimate_internships_final 2.0.xlsx', 0),
        ('suspicious_jobs_final 2.0.xlsx', 1),
        ('suspicious_internships_final 2.0.xlsx', 1),
        ('scam_jobs_final 2.0.xlsx', 2),
        ('scam_internships_final 2.0.xlsx', 2)
    ]
    
    all_rows = []
    
    print("Loading datasets...")
    for filename, label in data_sources:
        path = os.path.join(dataset_dir, filename)
        if not os.path.exists(path):
            print(f"Warning: File {path} not found. Skipping.")
            continue
            
        try:
            df = pd.read_excel(path)
            # Find the most relevant text column (description or review_text)
            text_col = None
            for col in ['description', 'review_text', 'job_description']:
                if col in df.columns:
                    text_col = col
                    break
            
            if text_col:
                texts = df[text_col].astype(str).tolist()
                for t in texts:
                    if len(t.strip()) > 10: # Only use non-empty descriptions
                        all_rows.append({'text': t, 'label': label})
                print(f"Loaded {len(texts)} rows from {filename}")
            else:
                print(f"Warning: No valid text column found in {filename}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    if not all_rows:
        print("No data found to train on!")
        return
        
    df_combined = pd.DataFrame(all_rows)
    print(f"Total dataset size: {len(df_combined)}")
    print(df_combined['label'].value_counts())
    
    # 2. TF-IDF Vectorization
    print("Vectorizing text...")
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
    X = vectorizer.fit_transform(df_combined['text']).toarray()
    y = df_combined['label'].values
    
    # 3. Scaling (Metadata model in predict.py expects a scaler)
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    # 5. Training Random Forest
    print("Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # 6. Evaluation
    print("Evaluation Results:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # 7. Save Models
    print(f"Saving models to {models_dir}...")
    
    # Predict.py loads vectorizer.pkl with pickle
    with open(os.path.join(models_dir, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(vectorizer, f)
        
    # Predict.py loads model.pkl and scaler.pkl with joblib
    joblib.dump(model, os.path.join(models_dir, 'model.pkl'))
    joblib.dump(scaler, os.path.join(models_dir, 'scaler.pkl'))
    
    print("Training complete! Models saved and ready for scikit-learn 1.8.0")

if __name__ == "__main__":
    train_metadata_model()
