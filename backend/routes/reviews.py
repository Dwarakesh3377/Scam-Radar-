from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__)

# Path to the dataset
ROOT_DIR = Path(__file__).parent.parent
DATASET_PATH = ROOT_DIR / 'dataset' / 'negative_reviews_final 2.0.xlsx'

@reviews_bp.route('/negative', methods=['GET'])
def get_negative_reviews():
    """Get negative reviews from the dataset"""
    try:
        if not DATASET_PATH.exists():
            return jsonify({'error': 'Negative reviews dataset not found'}), 404
        
        # Load the dataset
        df = pd.read_excel(DATASET_PATH)
        
        # Assuming the reviews are in a column named 'review_text' or similar
        text_cols = [col for col in df.columns if 'text' in col.lower() or 'review' in col.lower() or 'description' in col.lower()]
        
        if not text_cols:
            return jsonify({'error': 'No review text column found in dataset'}), 500
        
        # Get the first 50 reviews
        reviews = df[text_cols[0]].dropna().astype(str).tolist()[:50]
        
        return jsonify({
            'count': len(reviews),
            'reviews': reviews
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reviews_bp.route('/company/<company_name>', methods=['GET'])
def get_company_reviews(company_name):
    """Get negative reviews for a specific company"""
    try:
        # Use our Excel loader logic to get reviews
        from utils.excel_loader import get_negative_reviews as get_excel_reviews
        reviews = get_excel_reviews(company_name=company_name, limit=10)
        
        # Also check MongoDB for any user-submitted reviews
        from db.mongo import feedback
        if feedback is not None:
            db_reviews = list(feedback.find({'company_name': company_name, 'type': 'public_review'}).sort('created_at', -1).limit(5))
            for rev in db_reviews:
                rev['_id'] = str(rev['_id'])
                reviews.append({
                    'id': f"db-{rev['_id']}",
                    'reviewer_name': 'Verified User',
                    'company_name': company_name,
                    'review_text': rev.get('comment', 'No details'),
                    'review_date': rev.get('created_at', datetime.utcnow()).isoformat() if hasattr(rev.get('created_at'), 'isoformat') else str(rev.get('created_at', '')),
                })

        return jsonify({
            'company': company_name,
            'count': len(reviews),
            'reviews': reviews
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reviews_bp.route('/', methods=['POST'])
@jwt_required()
def submit_review():
    """Submit a new review (Public review/experience)"""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        company = data.get('company_name')
        text = data.get('review_text') or data.get('comment')
        
        if not company or not text:
            return jsonify({'error': 'Company name and review text required'}), 400
            
        from db.mongo import feedback
        if feedback is None:
            return jsonify({'error': 'Database not available'}), 503
            
        review_record = {
            'user_email': current_user,
            'company_name': company,
            'comment': text,
            'rating': data.get('rating', 1),
            'type': 'public_review',
            'created_at': datetime.utcnow()
        }
        
        feedback.insert_one(review_record)
        return jsonify({'message': 'Review submitted successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500