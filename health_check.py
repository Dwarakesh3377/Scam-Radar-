import os
import sys

def check_project():
    results = []
    
    # 1. Backend Check
    print("Checking Backend...")
    backend_path = 'backend/app.py'
    if os.path.exists(backend_path):
        results.append("✅ Backend (app.py) exists.")
    else:
        results.append("❌ Backend (app.py) MISSING.")

    # 2. Frontend Check
    print("Checking Frontend...")
    frontend_path = 'frontend/src/App.jsx'
    if os.path.exists(frontend_path):
        results.append("✅ Frontend (App.jsx) exists.")
    else:
        results.append("❌ Frontend (App.jsx) MISSING.")

    # 3. ML Models Check
    print("Checking ML Models...")
    models = [
        'ml_models/bert_model/model.safetensors',
        'ml_models/xlm_roberta_multilingual/model.safetensors',
        'ml_models/metadata_model/model.pkl'
    ]
    for m in models:
        if os.path.exists(m):
            results.append(f"✅ Model found: {m}")
        else:
            results.append(f"❌ Model MISSING: {m}")

    # 4. Dataset Check
    print("Checking Datasets...")
    if os.path.exists('dataset'):
        results.append("✅ Dataset directory exists.")
    else:
        results.append("❌ Dataset directory MISSING.")

    print("\n--- FINAL STATUS ---")
    for r in results:
        print(r)

if __name__ == "__main__":
    check_project()
