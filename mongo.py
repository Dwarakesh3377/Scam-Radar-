"""
MongoDB Database Connection
===========================
Singleton pattern for MongoDB connection.
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://scam_admin:JcoyuhqOSc3HFokG@cluster0.vovujmt.mongodb.net/scam_detection_db?retryWrites=true&w=majority&appName=Cluster0')

# Create client connection with strict timeouts
try:
    print(f"Connecting to MongoDB Atlas...")
    client = MongoClient(
        MONGO_URI, 
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True
    )
    # Test connection
    client.admin.command('ping')
    print("[SUCCESS] MongoDB connection verified")
except Exception as e:
    print(f"[ERROR] MongoDB connection failed: {e}")
    client = None

# Get database instance
if client is not None:
    try:
        # Use the database specified in the URI or fallback to scam_detection_db
        db_name = client.get_database().name if client.get_default_database() else 'scam_detection_db'
        db = client.get_database(db_name)
        print(f"[SUCCESS] Connected to Database: {db.name}")
    except Exception:
        db = client.get_database('scam_detection_db')
        print(f"[INFO] Using fallback database: scam_detection_db")
    mongo = db
else:
    db = None
    mongo = None

# Collection references  
def get_collection(name):
    """Get a collection from the database"""
    if db is not None:
        return db[name]
    return None

# Initialize collections
users = get_collection('users')
analyses = get_collection('analyses')
feedback = get_collection('feedback')
reviews = get_collection('reviews')
settings = get_collection('settings')
