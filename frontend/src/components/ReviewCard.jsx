import React, { useState } from 'react';
import { FaUser, FaCalendar, FaMapMarkerAlt, FaMoneyBillWave, FaThumbsUp, FaThumbsDown, FaFlag, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';
import './ReviewCard.css';

const ReviewCard = ({ review, onUpvote, onDownvote, onReport, isVerified = false }) => {
    const [userReaction, setUserReaction] = useState(null);
    const [isReported, setIsReported] = useState(false);

    const handleUpvote = () => {
        if (userReaction !== 'upvote') {
            setUserReaction('upvote');
            if (onUpvote) onUpvote(review.id);
        }
    };

    const handleDownvote = () => {
        if (userReaction !== 'downvote') {
            setUserReaction('downvote');
            if (onDownvote) onDownvote(review.id);
        }
    };

    const handleReport = () => {
        if (!isReported) {
            setIsReported(true);
            if (onReport) onReport(review.id);
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getScamTypeColor = (scamType) => {
        const colors = {
            'registration_fee': '#ff6b6b',
            'identity_theft': '#ffa94d',
            'equipment_fee': '#51cf66',
            'processing_fee': '#339af0',
            'training_fee': '#cc5de8',
            'bank_fraud': '#ff922b',
            'phishing': '#f06595',
            'advance_fee': '#20c997'
        };
        return colors[scamType] || '#868e96';
    };

    return (
        <div className={`review-card ${isVerified ? 'verified' : ''}`}>
            {/* Header */}
            <div className="review-header">
                <div className="reviewer-info">
                    <div className="reviewer-avatar">
                        <FaUser />
                    </div>
                    <div className="reviewer-details">
                        <div className="reviewer-name">
                            Anonymous User
                            {isVerified && (
                                <span className="verified-badge">
                                    <FaCheckCircle /> Verified
                                </span>
                            )}
                        </div>
                        <div className="review-meta">
                            <span className="meta-item">
                                <FaCalendar /> {formatDate(review.report_date)}
                            </span>
                            <span className="meta-item">
                                <FaMapMarkerAlt /> {review.country}
                            </span>
                            {review.source_type && (
                                <span className="meta-item source">
                                    <FaExclamationTriangle /> {review.source_type}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                
                <div className="scam-type-tag" style={{ backgroundColor: getScamTypeColor(review.scam_type) }}>
                    {review.scam_type.replace('_', ' ').toUpperCase()}
                </div>
            </div>

            {/* Company Info */}
            <div className="company-info">
                <h4 className="company-name">{review.company_name}</h4>
                {review.loss_amount && (
                    <div className="loss-amount">
                        <FaMoneyBillWave />
                        <span>Loss: {review.loss_amount}</span>
                    </div>
                )}
            </div>

            {/* Review Text */}
            <div className="review-text">
                <p>{review.review_text}</p>
            </div>

            {/* Proof Section (if available) */}
            {review.proof_urls && review.proof_urls.length > 0 && (
                <div className="proof-section">
                    <h5>Proof of Scam:</h5>
                    <div className="proof-links">
                        {review.proof_urls.slice(0, 3).map((url, index) => (
                            <a 
                                key={index} 
                                href={url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="proof-link"
                            >
                                Evidence {index + 1}
                            </a>
                        ))}
                    </div>
                </div>
            )}

            {/* Footer with Actions */}
            <div className="review-footer">
                <div className="vote-section">
                    <button 
                        className={`vote-btn upvote ${userReaction === 'upvote' ? 'active' : ''}`}
                        onClick={handleUpvote}
                        title="Helpful"
                    >
                        <FaThumbsUp />
                        <span>{review.upvotes || 0}</span>
                    </button>
                    
                    <button 
                        className={`vote-btn downvote ${userReaction === 'downvote' ? 'active' : ''}`}
                        onClick={handleDownvote}
                        title="Not Helpful"
                    >
                        <FaThumbsDown />
                        <span>{review.downvotes || 0}</span>
                    </button>
                </div>
                
                <div className="action-section">
                    <button 
                        className={`report-btn ${isReported ? 'reported' : ''}`}
                        onClick={handleReport}
                        disabled={isReported}
                    >
                        <FaFlag />
                        <span>{isReported ? 'Reported' : 'Report'}</span>
                    </button>
                </div>
            </div>

            {/* Verification Status */}
            {review.verification_status && (
                <div className={`verification-status ${review.verification_status}`}>
                    {review.verification_status === 'confirmed' && '✅ Confirmed Scam'}
                    {review.verification_status === 'pending' && '⏳ Under Review'}
                    {review.verification_status === 'unverified' && '❓ Not Verified'}
                </div>
            )}
        </div>
    );
};

export default ReviewCard;