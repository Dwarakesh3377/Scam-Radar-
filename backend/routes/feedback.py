"""
Feedback Routes - User Feedback API
====================================
Handles user feedback and ratings for analyses.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from db.mongo import mongo, feedback, users, analyses

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('', methods=['POST'])
@feedback_bp.route('/', methods=['POST'])
def submit_feedback():
    """Submit feedback for an analysis"""
    try:
        # Try to get JWT identity, but don't require it
        current_user = None
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
        except Exception:
            current_user = 'anonymous'
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('analysis_id'):
            return jsonify({'error': 'analysis_id is required'}), 400
        
        if not data.get('rating') or not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Create feedback record
        feedback_record = {
            'user_email': current_user,
            'analysis_id': data['analysis_id'],
            'rating': data['rating'],
            'comment': data.get('comment', ''),
            'helpful': data.get('helpful', True),
            'accurate': data.get('accurate', True),
            'created_at': datetime.utcnow()
        }
        
        if feedback is not None:
            result = feedback.insert_one(feedback_record)
            feedback_id = str(result.inserted_id)
        else:
            feedback_id = 'no-db'
        
        # Update user analytics
        if users is not None:
            user = users.find_one({'email': current_user})
            if user:
                analytics = user.get('analytics', {})
                current_count = analytics.get('feedback_count', 0)
                current_avg = analytics.get('avg_rating', 0)
                
                new_count = current_count + 1
                new_avg = ((current_avg * current_count) + data['rating']) / new_count
                
                users.update_one(
                    {'email': current_user},
                    {'$set': {
                        'analytics.feedback_count': new_count,
                        'analytics.avg_rating': round(new_avg, 2)
                    }}
                )
        
        return jsonify({
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/analysis/<analysis_id>', methods=['GET'])
@jwt_required()
def get_feedback_for_analysis(analysis_id):
    """Get feedback for a specific analysis"""
    try:
        current_user = get_jwt_identity()
        
        if feedback is None:
            return jsonify({'feedback': None}), 200
        
        user_feedback = feedback.find_one({
            'analysis_id': analysis_id,
            'user_email': current_user
        })
        
        if user_feedback:
            user_feedback['_id'] = str(user_feedback['_id'])
            if 'created_at' in user_feedback:
                user_feedback['created_at'] = user_feedback['created_at'].isoformat()
        
        return jsonify({'feedback': user_feedback}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/my-feedback', methods=['GET'])
@jwt_required()
def get_my_feedback():
    """Get all feedback from current user"""
    try:
        current_user = get_jwt_identity()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        if feedback is None:
            return jsonify({
                'feedback': [],
                'pagination': {'page': page, 'limit': limit, 'total': 0}
            }), 200
        
        user_feedback = list(feedback.find(
            {'user_email': current_user}
        ).sort('created_at', -1).skip(skip).limit(limit))
        
        for fb in user_feedback:
            fb['_id'] = str(fb['_id'])
            if 'created_at' in fb:
                fb['created_at'] = fb['created_at'].isoformat()
        
        total = feedback.count_documents({'user_email': current_user})
        
        return jsonify({
            'feedback': user_feedback,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_feedback_stats():
    """Get feedback statistics for current user"""
    try:
        current_user = get_jwt_identity()
        
        if feedback is None:
            return jsonify({
                'total_feedback': 0,
                'avg_rating': 0,
                'helpful_count': 0,
                'accurate_count': 0
            }), 200
        
        total = feedback.count_documents({'user_email': current_user})
        
        # Calculate averages
        pipeline = [
            {'$match': {'user_email': current_user}},
            {'$group': {
                '_id': None,
                'avg_rating': {'$avg': '$rating'},
                'helpful_count': {'$sum': {'$cond': ['$helpful', 1, 0]}},
                'accurate_count': {'$sum': {'$cond': ['$accurate', 1, 0]}}
            }}
        ]
        
        result = list(feedback.aggregate(pipeline))
        
        if result:
            stats = result[0]
            return jsonify({
                'total_feedback': total,
                'avg_rating': round(stats.get('avg_rating', 0), 2),
                'helpful_count': stats.get('helpful_count', 0),
                'accurate_count': stats.get('accurate_count', 0)
            }), 200
        
        return jsonify({
            'total_feedback': 0,
            'avg_rating': 0,
            'helpful_count': 0,
            'accurate_count': 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500