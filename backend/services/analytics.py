from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics
from collections import Counter

class AnalyticsService:
    """Service for generating analytics and insights"""
    
    def __init__(self, mongo):
        self.mongo = mongo
    
    def get_user_analytics(self, user_email: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a user"""
        try:
            # Get user's analyses
            analyses = list(self.mongo.analyses.find({'user_email': user_email}))
            
            if not analyses:
                return self._get_empty_analytics()
            
            # Calculate basic stats
            total_analyses = len(analyses)
            scam_count = sum(1 for a in analyses if a['risk_level'] == 'SCAM')
            suspicious_count = sum(1 for a in analyses if a['risk_level'] == 'SUSPICIOUS')
            legitimate_count = sum(1 for a in analyses if a['risk_level'] == 'LEGITIMATE')
            
            # Calculate average risk score
            risk_scores = [a['risk_score'] for a in analyses]
            avg_risk_score = statistics.mean(risk_scores) if risk_scores else 0
            
            # Get input type distribution
            input_types = [a['input_type'] for a in analyses]
            input_type_dist = dict(Counter(input_types))
            
            # Get language distribution
            languages = [a.get('language', 'en') for a in analyses]
            language_dist = dict(Counter(languages))
            
            # Get recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_analyses = [
                a for a in analyses 
                if a['created_at'] >= thirty_days_ago
            ]
            
            # Calculate monthly trend
            monthly_trend = self._calculate_monthly_trend(analyses)
            
            # Get most common scam indicators
            scam_indicators = self._get_common_scam_indicators(analyses)
            
            # Calculate detection rate
            detection_rate = (scam_count / total_analyses * 100) if total_analyses > 0 else 0
            
            return {
                'total_analyses': total_analyses,
                'scam_count': scam_count,
                'suspicious_count': suspicious_count,
                'legitimate_count': legitimate_count,
                'avg_risk_score': round(avg_risk_score, 2),
                'detection_rate': round(detection_rate, 2),
                'input_type_distribution': input_type_dist,
                'language_distribution': language_dist,
                'recent_activity_count': len(recent_analyses),
                'monthly_trend': monthly_trend,
                'common_scam_indicators': scam_indicators,
                'risk_distribution': {
                    'LEGITIMATE': legitimate_count,
                    'SUSPICIOUS': suspicious_count,
                    'SCAM': scam_count
                }
            }
            
        except Exception as e:
            print(f"Error getting user analytics: {str(e)}")
            return self._get_empty_analytics()
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """Get global platform analytics"""
        try:
            # Get all analyses
            total_analyses = self.mongo.analyses.count_documents({})
            
            # Get risk level distribution
            scam_count = self.mongo.analyses.count_documents({'risk_level': 'SCAM'})
            suspicious_count = self.mongo.analyses.count_documents({'risk_level': 'SUSPICIOUS'})
            legitimate_count = self.mongo.analyses.count_documents({'risk_level': 'LEGITIMATE'})
            
            # Get total users
            total_users = self.mongo.users.count_documents({})
            active_users = self.mongo.users.count_documents({
                'last_login': {'$gte': datetime.utcnow() - timedelta(days=30)}
            })
            
            # Get average confidence
            pipeline = [
                {'$group': {
                    '_id': None,
                    'avg_confidence': {'$avg': '$confidence'},
                    'avg_risk_score': {'$avg': '$risk_score'}
                }}
            ]
            avg_stats = list(self.mongo.analyses.aggregate(pipeline))
            avg_confidence = avg_stats[0]['avg_confidence'] if avg_stats else 0
            avg_risk_score = avg_stats[0]['avg_risk_score'] if avg_stats else 0
            
            # Get most active languages
            language_pipeline = [
                {'$group': {'_id': '$language', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 5}
            ]
            top_languages = list(self.mongo.analyses.aggregate(language_pipeline))
            
            # Get daily activity (last 30 days)
            daily_activity = self._get_daily_activity()
            
            return {
                'total_analyses': total_analyses,
                'total_users': total_users,
                'active_users': active_users,
                'scam_count': scam_count,
                'suspicious_count': suspicious_count,
                'legitimate_count': legitimate_count,
                'avg_confidence': round(avg_confidence * 100, 2) if avg_confidence else 0,
                'avg_risk_score': round(avg_risk_score, 2),
                'top_languages': [
                    {'language': item['_id'], 'count': item['count']} 
                    for item in top_languages
                ],
                'daily_activity': daily_activity,
                'detection_rate': round((scam_count / total_analyses * 100), 2) if total_analyses > 0 else 0
            }
            
        except Exception as e:
            print(f"Error getting global analytics: {str(e)}")
            return {}
    
    def _calculate_monthly_trend(self, analyses: List[Dict]) -> List[Dict]:
        """Calculate monthly analysis trend"""
        if not analyses:
            return []
        
        # Group by month
        monthly_data = {}
        for analysis in analyses:
            date = analysis['created_at']
            month_key = f"{date.year}-{date.month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'count': 0,
                    'scams': 0,
                    'total_risk': 0
                }
            
            monthly_data[month_key]['count'] += 1
            monthly_data[month_key]['total_risk'] += analysis['risk_score']
            if analysis['risk_level'] == 'SCAM':
                monthly_data[month_key]['scams'] += 1
        
        # Convert to list and calculate averages
        trend = []
        for month, data in sorted(monthly_data.items()):
            trend.append({
                'month': month,
                'count': data['count'],
                'scams': data['scams'],
                'avg_risk_score': round(data['total_risk'] / data['count'], 2)
            })
        
        return trend[-12:]  # Last 12 months
    
    def _get_common_scam_indicators(self, analyses: List[Dict]) -> List[Dict]:
        """Get most common scam indicators"""
        scam_analyses = [a for a in analyses if a['risk_level'] == 'SCAM']
        
        if not scam_analyses:
            return []
        
        # Collect all explanations
        all_indicators = []
        for analysis in scam_analyses:
            explanations = analysis.get('explanations', [])
            all_indicators.extend(explanations)
        
        # Count occurrences
        indicator_counts = Counter(all_indicators)
        
        # Return top 5
        return [
            {'indicator': indicator, 'count': count}
            for indicator, count in indicator_counts.most_common(5)
        ]
    
    def _get_daily_activity(self) -> List[Dict]:
        """Get daily activity for last 30 days"""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {'$match': {'created_at': {'$gte': thirty_days_ago}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$created_at'},
                    'month': {'$month': '$created_at'},
                    'day': {'$dayOfMonth': '$created_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        
        results = list(self.mongo.analyses.aggregate(pipeline))
        
        return [
            {
                'date': f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}",
                'count': item['count']
            }
            for item in results
        ]
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'total_analyses': 0,
            'scam_count': 0,
            'suspicious_count': 0,
            'legitimate_count': 0,
            'avg_risk_score': 0,
            'detection_rate': 0,
            'input_type_distribution': {},
            'language_distribution': {},
            'recent_activity_count': 0,
            'monthly_trend': [],
            'common_scam_indicators': [],
            'risk_distribution': {
                'LEGITIMATE': 0,
                'SUSPICIOUS': 0,
                'SCAM': 0
            }
        }