import math
from typing import Dict, List, Tuple

class RiskMapper:
    """Map risk scores to categories, colors, and actions"""
    
    # Risk level configurations
    RISK_LEVELS = {
        'LEGITIMATE': {
            'min': 0,
            'max': 30,
            'color': '#4CAF50',  # Green
            'icon': '✅',
            'label': 'Legitimate',
            'description': 'Safe to proceed'
        },
        'SUSPICIOUS': {
            'min': 31,
            'max': 60,
            'color': '#FF9800',  # Orange
            'icon': '⚠️',
            'label': 'Suspicious',
            'description': 'Proceed with caution'
        },
        'SCAM': {
            'min': 61,
            'max': 100,
            'color': '#F44336',  # Red
            'icon': '❌',
            'label': 'Scam',
            'description': 'Do not interact'
        }
    }
    
    # Safety advice for each risk level
    SAFETY_ADVICE = {
        'LEGITIMATE': [
            "This appears to be a legitimate opportunity",
            "Verify company details on official websites",
            "Proceed with normal application process",
            "Share only necessary information",
            "Check for recent reviews of the company"
        ],
        'SUSPICIOUS': [
            "Verify the company through multiple sources",
            "Check for official contact information",
            "Do not share sensitive personal information",
            "Look for reviews from other applicants",
            "Be cautious of requests for upfront payments",
            "Verify the sender's email domain",
            "Check if the job offer matches company's career page"
        ],
        'SCAM': [
            "DO NOT share any personal information",
            "DO NOT send money or payments",
            "DO NOT provide bank account details",
            "Report this as potential scam",
            "Warn others about this opportunity",
            "Block and ignore further communication",
            "Check our scam database for similar patterns"
        ]
    }
    
    # Final conclusions for each risk level
    CONCLUSIONS = {
        'LEGITIMATE': "✅ LEGITIMATE - Safe to apply for the job/internship. All the best for your career!",
        'SUSPICIOUS': "⚠️ SUSPICIOUS - Refer their official site but do not share any information until verified as real.",
        'SCAM': "❌ SCAM - Do not interact with them. Do not share any personal information. This is likely fraudulent."
    }
    
    # Action buttons for each risk level
    ACTIONS = {
        'LEGITIMATE': [
            {'label': 'Apply Now', 'type': 'primary', 'action': 'apply'},
            {'label': 'Save Analysis', 'type': 'secondary', 'action': 'save'},
            {'label': 'Analyze Another', 'type': 'secondary', 'action': 'new'}
        ],
        'SUSPICIOUS': [
            {'label': 'Verify First', 'type': 'warning', 'action': 'verify'},
            {'label': 'Report Issue', 'type': 'secondary', 'action': 'report'},
            {'label': 'Analyze Another', 'type': 'secondary', 'action': 'new'}
        ],
        'SCAM': [
            {'label': 'Report Scam', 'type': 'danger', 'action': 'report_scam'},
            {'label': 'View Proofs', 'type': 'warning', 'action': 'view_proofs'},
            {'label': 'Analyze Another', 'type': 'secondary', 'action': 'new'}
        ]
    }
    
    @classmethod
    def get_risk_level(cls, score: float) -> str:
        """Get risk level from score"""
        score = max(0, min(100, score))  # Clamp to 0-100
        
        for level, config in cls.RISK_LEVELS.items():
            if config['min'] <= score <= config['max']:
                return level
        
        return 'UNKNOWN'
    
    @classmethod
    def get_risk_config(cls, score: float) -> Dict:
        """Get complete risk configuration for a score"""
        level = cls.get_risk_level(score)
        config = cls.RISK_LEVELS[level].copy()
        
        # Add dynamic properties
        config['score'] = score
        config['percentage'] = int(score)
        config['level'] = level
        
        # Calculate position for gauge needle (0-180 degrees)
        # Map 0-100 score to 0-180 degrees (for half-circle gauge)
        config['needle_angle'] = (score / 100) * 180
        
        # Calculate color intensity
        intensity = min(1.0, score / 100 * 1.5)
        config['color_intensity'] = intensity
        
        return config
    
    @classmethod
    def get_safety_advice(cls, score: float, count: int = 5) -> List[str]:
        """Get safety advice for a risk score"""
        level = cls.get_risk_level(score)
        advice = cls.SAFETY_ADVICE.get(level, [])
        
        # Return specified number of advice items
        return advice[:count]
    
    @classmethod
    def get_conclusion(cls, score: float) -> str:
        """Get final conclusion for a risk score"""
        level = cls.get_risk_level(score)
        return cls.CONCLUSIONS.get(level, "Unable to determine risk level.")
    
    @classmethod
    def get_actions(cls, score: float) -> List[Dict]:
        """Get recommended actions for a risk score"""
        level = cls.get_risk_level(score)
        return cls.ACTIONS.get(level, [])
    
    @classmethod
    def get_gauge_colors(cls) -> List[Dict]:
        """Get color stops for the speedometer gauge"""
        colors = []
        
        for level, config in cls.RISK_LEVELS.items():
            colors.append({
                'color': config['color'],
                'position': config['min'] / 100,
                'label': config['label']
            })
        
        return colors
    
    @classmethod
    def get_risk_breakdown(cls, score: float, features: Dict = None) -> Dict:
        """Get detailed breakdown of risk factors"""
        level = cls.get_risk_level(score)
        breakdown = {
            'score': score,
            'level': level,
            'confidence': 'high' if abs(score - 50) > 25 else 'medium' if abs(score - 50) > 10 else 'low',
            'factors': []
        }
        
        if features:
            # Analyze features to identify key risk factors
            risk_factors = cls._analyze_features(features)
            breakdown['factors'] = risk_factors
        
        return breakdown
    
    @classmethod
    def _analyze_features(cls, features: Dict) -> List[Dict]:
        """Analyze features to identify risk factors"""
        factors = []
        
        # Urgency keywords
        urgency_count = features.get('scam_urgency_count', 0)
        if urgency_count > 0:
            factors.append({
                'type': 'urgency',
                'severity': min(3, urgency_count),
                'description': f'Contains {urgency_count} urgency keywords',
                'impact': urgency_count * 5
            })
        
        # Financial keywords
        financial_count = features.get('scam_financial_count', 0)
        if financial_count > 0:
            factors.append({
                'type': 'financial',
                'severity': min(3, financial_count),
                'description': f'Contains {financial_count} financial keywords',
                'impact': financial_count * 4
            })
        
        # Suspicious domains
        if features.get('has_suspicious_tld', 0) or features.get('meta_has_suspicious_domain', 0):
            factors.append({
                'type': 'domain',
                'severity': 3,
                'description': 'Uses suspicious domain/TLD',
                'impact': 25
            })
        
        # Free email providers
        if features.get('meta_is_free_email', 0):
            factors.append({
                'type': 'email',
                'severity': 2,
                'description': 'Uses free email provider',
                'impact': 10
            })
        
        # International contact
        if features.get('meta_is_international', 0):
            factors.append({
                'type': 'contact',
                'severity': 2,
                'description': 'International contact information',
                'impact': 15
            })
        
        # Uppercase ratio
        uppercase_ratio = features.get('uppercase_ratio', 0)
        if uppercase_ratio > 0.3:
            factors.append({
                'type': 'formatting',
                'severity': 2 if uppercase_ratio < 0.5 else 3,
                'description': f'Excessive uppercase ({int(uppercase_ratio*100)}%)',
                'impact': uppercase_ratio * 50
            })
        
        # Exclamation marks
        exclamation_count = features.get('exclamation_count', 0)
        if exclamation_count > 3:
            factors.append({
                'type': 'formatting',
                'severity': 2 if exclamation_count < 6 else 3,
                'description': f'Multiple exclamation marks ({exclamation_count})',
                'impact': min(10, exclamation_count * 2)
            })
        
        # Sort by impact
        factors.sort(key=lambda x: x['impact'], reverse=True)
        
        return factors
    
    @classmethod
    def get_negative_review_categories(cls, score: float) -> List[str]:
        """Get categories for negative reviews based on risk score"""
        level = cls.get_risk_level(score)
        
        if level == 'SCAM':
            return [
                'Financial Scam',
                'Identity Theft',
                'Phishing Attempt',
                'Fake Job Offer',
                'Upfront Payment',
                'Data Harvesting'
            ]
        elif level == 'SUSPICIOUS':
            return [
                'Unverified Company',
                'Poor Communication',
                'Vague Job Description',
                'Suspicious Requirements',
                'Privacy Concerns'
            ]
        else:
            return []
    
    @classmethod
    def get_report_categories(cls, score: float) -> List[str]:
        """Get categories for reporting based on risk score"""
        level = cls.get_risk_level(score)
        
        categories = [
            'Suspicious Job Offer',
            'Potential Scam',
            'Phishing Attempt',
            'Fake Company',
            'Privacy Violation'
        ]
        
        if level == 'SCAM':
            categories.extend([
                'Financial Fraud',
                'Identity Theft',
                'Advance Fee Fraud',
                'Data Breach'
            ])
        
        return categories
    
    @classmethod
    def calculate_confidence(cls, features: Dict, score: float) -> float:
        """Calculate confidence score for the risk assessment"""
        confidence_factors = []
        
        # Text length contributes to confidence
        text_length = features.get('text_length', 0)
        if text_length > 500:
            confidence_factors.append(0.9)
        elif text_length > 200:
            confidence_factors.append(0.7)
        elif text_length > 50:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)
        
        # Feature completeness
        feature_count = len([v for v in features.values() if isinstance(v, (int, float))])
        if feature_count > 20:
            confidence_factors.append(0.9)
        elif feature_count > 10:
            confidence_factors.append(0.7)
        elif feature_count > 5:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)
        
        # Risk score extremity (more confident at extremes)
        if score < 20 or score > 80:
            confidence_factors.append(0.9)
        elif score < 30 or score > 70:
            confidence_factors.append(0.8)
        elif score < 40 or score > 60:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.6)
        
        # Calculate average confidence
        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors)
            return round(confidence, 2)
        
        return 0.5