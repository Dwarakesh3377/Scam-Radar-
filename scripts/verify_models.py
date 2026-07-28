import os
import joblib
import pickle
import warnings
import numpy as np

def verify_models():
    """
    Verify that models load without InconsistentVersionWarning and can make predictions.
    """
    models_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ml_models/metadata_model')
    
    model_file = os.path.join(models_root, 'model.pkl')
    scaler_file = os.path.join(models_root, 'scaler.pkl')
    vectorizer_file = os.path.join(models_root, 'vectorizer.pkl')
    
    print(f"Verifying models in: {models_root}")
    
    # We catch warnings to see if any are still raised
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # 1. Load Vectorizer
        with open(vectorizer_file, 'rb') as f:
            vectorizer = pickle.load(f)
        print("✓ Vectorizer loaded")
            
        # 2. Load Model
        model = joblib.load(model_file)
        print("✓ Model loaded")
            
        # 3. Load Scaler
        scaler = joblib.load(scaler_file)
        print("✓ Scaler loaded")
        
        # Check for InconsistentVersionWarning
        from sklearn.exceptions import InconsistentVersionWarning
        v_warnings = [item for item in w if issubclass(item.category, InconsistentVersionWarning)]
        
        if v_warnings:
            print(f"⚠️ Warning: Still found {len(v_warnings)} version mismatch warnings!")
            for warn in v_warnings:
                print(f"  - {warn.message}")
        else:
            print("✨ Success: No scikit-learn version mismatch warnings detected!")

    # Basic functional test
    try:
        test_text = "Urgent recruitment for Amazon. Contact HR on WhatsApp for payment details."
        tfidf_features = vectorizer.transform([test_text]).toarray()
        scaled_features = scaler.transform(tfidf_features)
        prediction = model.predict(scaled_features)
        probs = model.predict_proba(scaled_features)
        print(f"Functional Test Pass: Prediction: {prediction}, Probs: {probs}")
    except Exception as e:
        print(f"Functional Test Fail: {e}")

if __name__ == "__main__":
    verify_models()
