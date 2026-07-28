import os
import joblib
import pickle
import warnings
from sklearn.exceptions import InconsistentVersionWarning

# Suppress the warning during this specific process so we can load and re-save
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

def re_save_models():
    """
    Load models that were saved with an older sklearn version and re-save them
    to suppress InconsistentVersionWarning in the current environment.
    """
    models_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ml_models/metadata_model')
    
    model_file = os.path.join(models_root, 'model.pkl')
    scaler_file = os.path.join(models_root, 'scaler.pkl')
    vectorizer_file = os.path.join(models_root, 'vectorizer.pkl')
    
    print(f"Checking models in: {models_root}")
    
    # 1. Re-save Vectorizer (Pickle)
    if os.path.exists(vectorizer_file):
        try:
            with open(vectorizer_file, 'rb') as f:
                vectorizer = pickle.load(f)
            with open(vectorizer_file, 'wb') as f:
                pickle.dump(vectorizer, f)
            print("Successfully re-saved vectorizer.pkl")
        except Exception as e:
            print(f"Failed to re-save vectorizer: {e}")
            
    # 2. Re-save Model (Joblib)
    if os.path.exists(model_file):
        try:
            model = joblib.load(model_file)
            joblib.dump(model, model_file)
            print("Successfully re-saved model.pkl")
        except Exception as e:
            print(f"Failed to re-save model: {e}")
            
    # 3. Re-save Scaler (Joblib)
    if os.path.exists(scaler_file):
        try:
            scaler = joblib.load(scaler_file)
            joblib.dump(scaler, scaler_file)
            print("Successfully re-saved scaler.pkl")
        except Exception as e:
            print(f"Failed to re-save scaler: {e}")

if __name__ == "__main__":
    re_save_models()
