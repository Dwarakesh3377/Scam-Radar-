"""
ML Logic Unit Tests
====================
Tests for feature extraction and model prediction.
"""
import pytest
import numpy as np
from services.predict import predict_with_tfidf, predict_risk

def test_tfidf_prediction():
    """Test TF-IDF prediction with various inputs"""
    # Scam text
    scam_text = "Urgent! Pay money to get this job. No interview needed."
    score, confidence = predict_with_tfidf(scam_text)
    if score is not None:
        assert score > 50
        assert confidence > 0.5
        
    # Legitimate text
    legit_text = "This is a standard Software Engineer position at a reputable company. Requirements include Python and SQL."
    score, confidence = predict_with_tfidf(legit_text)
    if score is not None:
        assert score < 50

def test_predict_risk_integration():
    """Test the main predict_risk function"""
    features = {
        'text': 'Urgent recruitment! Pay 5000 for registration.',
        'scam_keyword_density': 0.8
    }
    score, confidence = predict_risk(features)
    assert score > 50
    assert confidence > 0.7
