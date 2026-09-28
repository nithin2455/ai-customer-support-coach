import React, { useState } from 'react';
import { Star, CheckCircle, MessageSquare, Send } from 'lucide-react';
import { submitCustomerFeedback } from '../services/api';

export default function CustomerFeedbackModal({ conversationId, onSubmitSuccess }) {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [outcome, setOutcome] = useState('Resolved');
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await submitCustomerFeedback(conversationId, rating, comment, outcome);
      setSubmitted(true);
      if (onSubmitSuccess) onSubmitSuccess();
    } catch (err) {
      console.error("Error submitting feedback:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="bg-white border border-emerald-200 rounded-xl p-4 text-center space-y-1.5 shadow-xs">
        <CheckCircle className="w-7 h-7 text-emerald-600 mx-auto" />
        <h3 className="text-xs font-bold text-slate-900">Thank You for Your Feedback!</h3>
        <p className="text-[11px] text-slate-500">Your rating ({rating}/5 stars) and outcome status have been recorded.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-xs">
      <div className="flex items-center space-x-2 border-b border-slate-100 pb-2.5">
        <MessageSquare className="w-4 h-4 text-indigo-600" />
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">Support Feedback Survey</h3>
          <span className="text-[10px] text-slate-500 block">Help us evaluate your resolution experience</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3 text-xs">
        {/* Star Rating */}
        <div>
          <label className="block text-slate-700 mb-1 font-medium">Rating (1 to 5 Stars)</label>
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                type="button"
                key={star}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-0.5 focus:outline-none transition"
              >
                <Star
                  className={`w-5 h-5 ${
                    star <= (hoverRating || rating)
                      ? 'text-amber-400 fill-amber-400'
                      : 'text-slate-300'
                  }`}
                />
              </button>
            ))}
            <span className="ml-2 font-bold text-slate-700 text-xs">{rating} / 5</span>
          </div>
        </div>

        {/* Conversation Outcome Dropdown */}
        <div>
          <label className="block text-slate-700 mb-1 font-medium">Outcome Status</label>
          <select
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600 text-xs"
          >
            <option value="Resolved">Resolved (Issue completely fixed)</option>
            <option value="Partially Resolved">Partially Resolved (Pending minor follow-up)</option>
            <option value="Unresolved">Unresolved (Awaiting resolution)</option>
            <option value="Escalated">Escalated (Transferred to specialist / manager)</option>
          </select>
        </div>

        {/* Optional Comment */}
        <div>
          <label className="block text-slate-700 mb-1 font-medium">Comments</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell us about your experience or suggestions for improvement..."
            rows={2}
            className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 text-xs"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 transition shadow-xs text-xs"
        >
          <Send className="w-3.5 h-3.5" />
          <span>{isSubmitting ? 'Submitting...' : 'Submit Feedback'}</span>
        </button>
      </form>
    </div>
  );
}
