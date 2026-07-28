#!/usr/bin/env python3
"""
Scam Risk Detection - Application Runner
=========================================
This script provides a simple way to run the application.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add backend to path
ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / 'backend'
FRONTEND_DIR = ROOT_DIR / 'frontend'

# Detect Virtual Environment
VENV_PYTHON = ROOT_DIR / 'venv' / 'Scripts' / 'python.exe'
PY_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

if VENV_PYTHON.exists():
    print(f"DEBUG: Using Virtual Environment: {VENV_PYTHON}")
else:
    print(f"DEBUG: Using Global Python: {sys.executable}")

sys.path.insert(0, str(BACKEND_DIR))


def kill_port(port=5000):
    """Kill process running on a specific port."""
    try:
        if os.name == 'nt':  # Windows
            # Find PID using netstat
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode()
            for line in output.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    print(f"Killing ghost process {pid} on port {port}...")
                    subprocess.run(['taskkill', '/F', '/PID', pid], shell=True, capture_output=True)
        else:  # Linux/Mac
            subprocess.run(['fuser', '-k', f'{port}/tcp'], shell=True, capture_output=True)
    except:
        pass


def check_mongodb():
    """Check if MongoDB is running."""
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / '.env')
    mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://scam_admin:KbPi3SE928SM7LZA@cluster1.qn2bqyb.mongodb.net/?appName=Cluster1')
    
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        print(f"Connected to MongoDB: {mongo_uri}")
        return True
    except Exception as e:
        print(f"Error: MongoDB connection failed: {e}")
        print("   Please check your connection or MONGO_URI in .env")
        return False


def run_backend(debug=True):
    """Run the Flask backend server."""
    print("\nStarting Backend Server...")
    os.chdir(BACKEND_DIR)
    
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / '.env')
    
    from app import app
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    kill_port(port)
    print(f"   Backend running at: http://localhost:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


def run_frontend():
    """Run the React frontend development server."""
    print("\nStarting Frontend Server...")
    os.chdir(FRONTEND_DIR)
    subprocess.run(['npm', 'run', 'dev'], shell=True)


def run_both():
    """Run both backend and frontend in separate processes."""
    kill_port(5000)
    kill_port(5173)
    # Check MongoDB first
    if not check_mongodb():
        sys.exit(1)
    
    # Start backend
    print("\nStarting Backend Server...")
    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = str(BACKEND_DIR)
    backend_env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    # Run backend as a subprocess
    backend_process = subprocess.Popen(
        [PY_EXE, 'app.py'],
        cwd=BACKEND_DIR,
        env=backend_env
    )
    
    # Wait for backend to be ready by polling health endpoint
    print("Waiting for backend to be ready (this may take a moment)...")
    import time
    import requests
    
    max_retries = 30
    retry_count = 0
    backend_ready = False
    
    while retry_count < max_retries:
        try:
            response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
            if response.status_code == 200:
                print("Backend is READY!")
                backend_ready = True
                break
        except:
            pass
        
        retry_count += 1
        time.sleep(1)
        if retry_count % 5 == 0:
            print(f"   Still waiting... ({retry_count}/{max_retries})")
            
    if not backend_ready:
        print("\nWARNING: Backend did not respond in time. Proceeding anyway, but login might fail initially.")
    
    # Start frontend
    print("\nStarting Frontend Server...")
    os.chdir(FRONTEND_DIR)
    try:
        subprocess.run(['npm', 'run', 'dev'], shell=True)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        backend_process.terminate()
        backend_process.wait()


def install_dependencies():
    """Install all dependencies."""
    print("\nInstalling Backend Dependencies...")
    os.chdir(BACKEND_DIR)
    subprocess.run([PY_EXE, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    print("\nInstalling Frontend Dependencies...")
    os.chdir(FRONTEND_DIR)
    subprocess.run(['npm', 'install'], shell=True)
    
    print("\nAll dependencies installed!")


def main():
    parser = argparse.ArgumentParser(
        description='Scam Risk Detection - Application Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --backend     # Run backend only
  python run.py --frontend    # Run frontend only
  python run.py --both        # Run both (default)
  python run.py --install     # Install dependencies
        """
    )
    
    parser.add_argument('--backend', action='store_true', help='Run backend server only')
    parser.add_argument('--frontend', action='store_true', help='Run frontend server only')
    parser.add_argument('--both', action='store_true', help='Run both servers (default)')
    parser.add_argument('--install', action='store_true', help='Install all dependencies')
    parser.add_argument('--check', action='store_true', help='Check prerequisites')
    parser.add_argument('--debug', action='store_true', default=True, help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("SCAM RADAR - AI-Powered Scam Detection")
    print("=" * 50)
    
    if args.install:
        install_dependencies()
        return
    
    if args.check:
        check_mongodb()
        return
    
    if args.backend:
        if check_mongodb():
            run_backend(debug=args.debug)
    elif args.frontend:
        run_frontend()
    else:
        # Default: run both
        run_both()


if __name__ == '__main__':
    main()
