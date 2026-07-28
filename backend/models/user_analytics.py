from datetime import datetime, timedelta
import statistics

class UserAnalytics:
    def __init__(self, user_email, analyses=None, feedbacks=None):
        self.user_email = user_email
        self.analyses = analyses or []
        self.feedbacks = feedbacks or []
        self.generated_at = datetime.utcnow()
    
    def calculate_statistics(self):
        """Calculate user statistics"""
        stats = {
            'total_analyses': len(self.analyses),
            'scams_detected': 0,
            'suspicious_count': 0,
            'legitimate_count': 0,
            'avg_risk_score': 0,
            'analysis_timeline': [],
            'risk_distribution': {'LEGITIMATE': 0, 'SUSPICIOUS': 0, 'SCAM': 0},
            'input_type_distribution': {},
            'language_distribution': {},
            'hourly_activity': {},
            'weekly_activity': {},
            'feedback_stats': {
                'total_feedback': len(self.feedbacks),
                'avg_rating': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        }
        
        # Analysis statistics
        risk_scores = []
        for analysis in self.analyses:
            # Risk level counts
            risk_level = analysis.get('risk_level', 'UNKNOWN')
            stats['risk_distribution'][risk_level] = stats['risk_distribution'].get(risk_level, 0) + 1
            
            # Scam detection
            if risk_level == 'SCAM':
                stats['scams_detected'] += 1
            elif risk_level == 'SUSPICIOUS':
                stats['suspicious_count'] += 1
            elif risk_level == 'LEGITIMATE':
                stats['legitimate_count'] += 1
            
            # Risk scores for average
            risk_scores.append(analysis.get('risk_score', 0))
            
            # Input type distribution
            input_type = analysis.get('input_type', 'unknown')
            stats['input_type_distribution'][input_type] = stats['input_type_distribution'].get(input_type, 0) + 1
            
            # Language distribution
            language = analysis.get('language', 'unknown')
            stats['language_distribution'][language] = stats['language_distribution'].get(language, 0) + 1
            
            # Timeline data
            created_at = analysis.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                # Hourly activity
                hour = created_at.hour
                stats['hourly_activity'][hour] = stats['hourly_activity'].get(hour, 0) + 1
                
                # Weekly activity (day of week)
                weekday = created_at.strftime('%A')
                stats['weekly_activity'][weekday] = stats['weekly_activity'].get(weekday, 0) + 1
                
                # Timeline entry
                stats['analysis_timeline'].append({
                    'date': created_at.isoformat(),
                    'risk_score': analysis.get('risk_score', 0),
                    'risk_level': risk_level,
                    'input_type': input_type
                })
        
        # Calculate averages
        if risk_scores:
            stats['avg_risk_score'] = round(statistics.mean(risk_scores), 1)
        
        # Feedback statistics
        ratings = []
        for feedback in self.feedbacks:
            rating = feedback.get('rating', 0)
            ratings.append(rating)
            stats['feedback_stats']['rating_distribution'][rating] = stats['feedback_stats']['rating_distribution'].get(rating, 0) + 1
        
        if ratings:
            stats['feedback_stats']['avg_rating'] = round(statistics.mean(ratings), 1)
        
        # Sort timeline
        stats['analysis_timeline'].sort(key=lambda x: x['date'])
        
        return stats
    
    def get_recent_activity(self, days=7):
        """Get recent activity for last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_analyses = []
        recent_feedbacks = []
        
        for analysis in self.analyses:
            created_at = analysis.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            if created_at >= cutoff_date:
                recent_analyses.append(analysis)
        
        for feedback in self.feedbacks:
            created_at = feedback.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            if created_at >= cutoff_date:
                recent_feedbacks.append(feedback)
        
        return {
            'analyses': recent_analyses,
            'feedbacks': recent_feedbacks,
            'analysis_count': len(recent_analyses),
            'feedback_count': len(recent_feedbacks)
        }
    
    def get_peak_hours(self):
        """Get user's peak activity hours"""
        stats = self.calculate_statistics()
        hourly_activity = stats.get('hourly_activity', {})
        
        if not hourly_activity:
            return []
        
        # Sort hours by activity count
        sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
        
        return [{'hour': hour, 'count': count} for hour, count in sorted_hours[:3]]
    
    def get_common_input_types(self):
        """Get most common input types"""
        stats = self.calculate_statistics()
        input_dist = stats.get('input_type_distribution', {})
        
        if not input_dist:
            return []
        
        # Sort input types by frequency
        sorted_types = sorted(input_dist.items(), key=lambda x: x[1], reverse=True)
        
        return [{'type': input_type, 'count': count} for input_type, count in sorted_types]
    
    def get_risk_trend(self):
        """Get risk score trend over time"""
        timeline = self.calculate_statistics().get('analysis_timeline', [])
        
        if len(timeline) < 2:
            return {'trend': 'stable', 'change': 0}
        
        # Get first and last week averages
        first_week = timeline[:min(7, len(timeline))]
        last_week = timeline[-min(7, len(timeline)):]
        
        first_avg = statistics.mean([item['risk_score'] for item in first_week]) if first_week else 0
        last_avg = statistics.mean([item['risk_score'] for item in last_week]) if last_week else 0
        
        change = last_avg - first_avg
        
        if change > 10:
            trend = 'increasing'
        elif change < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change, 1),
            'first_week_avg': round(first_avg, 1),
            'last_week_avg': round(last_avg, 1)
        }