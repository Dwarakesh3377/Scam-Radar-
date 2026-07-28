import React, { useState } from 'react';
import { FaStar, FaPaperPlane } from 'react-icons/fa';
import './FeedbackCard.css';

const FeedbackCard = ({ onSubmit }) => {
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [comment, setComment] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (rating > 0) {
            onSubmit({ rating, comment });
            setSubmitted(true);
        }
    };

    if (submitted) {
        return (
            <div className="feedback-card">
                <div className="thank-you-message">
                    <h3>Thank You! 🎉</h3>
                    <p>Your feedback has been recorded. It helps us improve our service.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="feedback-card">
            <h3 className="feedback-title">Rate Your Experience</h3>
            <p className="feedback-subtitle">How satisfied are you with our scam detection service?</p>
            
            <div className="star-rating">
                {[1, 2, 3, 4, 5].map((star) => (
                    <button
                        key={star}
                        type="button"
                        className={`star-btn ${star <= (hoverRating || rating) ? 'active' : ''}`}
                        onClick={() => setRating(star)}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                    >
                        <FaStar />
                    </button>
                ))}
            </div>
            
            {/* Rating labels removed to keep it minimalist */}
            
            <form onSubmit={handleSubmit} className="feedback-form">
                <div className="form-group">
                    <label htmlFor="comment">Additional Comments (Optional)</label>
                    <textarea
                        id="comment"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="Share your thoughts, suggestions, or issues..."
                        rows="4"
                        className="comment-textarea"
                    />
                </div>
                
                <button 
                    type="submit" 
                    className="btn submit-feedback-btn"
                    disabled={rating === 0}
                >
                    <FaPaperPlane /> Submit Feedback
                </button>
            </form>
        </div>
    );
};

export default FeedbackCard;