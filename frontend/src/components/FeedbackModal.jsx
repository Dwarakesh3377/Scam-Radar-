import React, { useState, useContext, createContext } from 'react';
import { FaStar, FaTimes, FaPaperPlane } from 'react-icons/fa';
import { LanguageContext } from '../context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';
import './FeedbackModal.css';

// Create a context for the feedback modal
export const FeedbackContext = createContext();

export const FeedbackProvider = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [analysisId, setAnalysisId] = useState(null);

  const openFeedback = (id = null) => {
    setAnalysisId(id);
    setIsOpen(true);
  };

  const closeFeedback = () => {
    setIsOpen(false);
    setAnalysisId(null);
  };

  return (
    <FeedbackContext.Provider value={{ isOpen, openFeedback, closeFeedback, analysisId }}>
      {children}
      <FeedbackModal />
    </FeedbackContext.Provider>
  );
};

const FeedbackModal = () => {
  const { isOpen, closeFeedback, analysisId } = useContext(FeedbackContext);
  const { t } = useContext(LanguageContext);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) return;

    setIsSubmitting(true);
    
    try {
      const { feedbackAPI } = await import('../services/api');
      await feedbackAPI.submitFeedback({
        analysis_id: analysisId,
        rating,
        comment,
        created_at: new Date().toISOString()
      });
      
      setIsSubmitted(true);
      setTimeout(() => {
        closeFeedback();
        setRating(0);
        setComment('');
        setIsSubmitted(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      // In a real app, you might show an error message to the user here
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    closeFeedback();
    setRating(0);
    setComment('');
    setIsSubmitted(false);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div 
        className="feedback-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleClose}
      >
        <motion.div 
          className="feedback-modal"
          initial={{ scale: 0.8, opacity: 0, y: 50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.8, opacity: 0, y: 50 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          onClick={(e) => e.stopPropagation()}
        >
          <button className="close-btn" onClick={handleClose}>
            <FaTimes />
          </button>

          {isSubmitted ? (
            <div className="feedback-success">
              <div className="success-icon">✅</div>
              <h3>Thank You!</h3>
              <p>Your feedback helps us improve.</p>
            </div>
          ) : (
            <>
              <div className="feedback-header">
                <h3>Rate This App</h3>
                <p>How was your experience with ScamRadar?</p>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="star-rating">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      className={`star ${star <= (hoverRating || rating) ? 'active' : ''}`}
                      onClick={() => setRating(star)}
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                    >
                      <FaStar />
                    </button>
                  ))}
                </div>

                <div className="rating-label">
                  {(hoverRating || rating) > 0 && t(`feedback.ratingLabels.${(hoverRating || rating) - 1}`)}
                </div>

                <div className="form-group">
                  <label>Share your experience (optional)</label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Tell us what you liked or how we can improve..."
                    rows="4"
                    maxLength={500}
                  />
                  <span className="char-count">{comment.length}/500</span>
                </div>

                <div className="feedback-actions">
                  <button 
                    type="submit" 
                    className="btn submit-btn"
                    disabled={rating === 0 || isSubmitting}
                  >
                    {isSubmitting ? (
                      <span className="loading">Submitting...</span>
                    ) : (
                      <>
                        <FaPaperPlane /> Submit Feedback
                      </>
                    )}
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-secondary skip-btn"
                    onClick={handleClose}
                  >
                    Skip
                  </button>
                </div>
              </form>
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default FeedbackModal;
