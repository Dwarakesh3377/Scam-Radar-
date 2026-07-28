import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        print("DEBUG: Checking if Firebase is initialized...")
        # Check if already initialized
        if not firebase_admin._apps:
            print("DEBUG: Initializing Firebase Admin SDK...")
            # First try service account JSON if path exists
            cred_path_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
            
            # Determine base directory (backend folder)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            if cred_path_env:
                if os.path.isabs(cred_path_env):
                    cred_path = cred_path_env
                else:
                    # Try relative to backend dir and root dir
                    path_relative_to_backend = os.path.join(base_dir, cred_path_env)
                    path_relative_to_root = os.path.join(os.path.dirname(base_dir), cred_path_env)
                    
                    if os.path.exists(path_relative_to_backend):
                        cred_path = path_relative_to_backend
                    elif os.path.exists(path_relative_to_root):
                        cred_path = path_relative_to_root
                    else:
                        cred_path = cred_path_env # Fallback to original
            else:
                cred_path = None

            print(f"DEBUG: Final resolved cred_path: {cred_path}")
            
            if cred_path and os.path.exists(cred_path):
                print(f"DEBUG: Using service account from {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                print("DEBUG: Fallback to default credentials (no service account file found)")
                # Explicitly try to get project ID from environment
                project_id = os.getenv('FIREBASE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT') or "scam-risk-detection"
                
                try:
                    firebase_admin.initialize_app(options={'projectId': project_id})
                except ValueError as ve:
                    if "The default Firebase app already exists" in str(ve):
                        print("DEBUG: Default app already initialized by environment.")
                    else:
                        raise ve
            print(f"DEBUG: Firebase Admin SDK initialized successfully for project: {firebase_admin.get_app().project_id}")
        else:
            print("DEBUG: Firebase Admin SDK already initialized.")
        return True
    except Exception as e:
        if "The default Firebase app already exists" in str(e):
            print("DEBUG: Firebase Admin SDK already initialized (caught exception).")
            return True
        print(f"Firebase Admin initialization error: {e}")
        return False

def verify_firebase_token(id_token):
    """Verify Firebase ID Token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification error: {e}")
        return None
