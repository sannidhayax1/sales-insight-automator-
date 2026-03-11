'use client';

import '../styles/status-message.css';

export default function StatusMessage({ message, type }) {
  if (!message) return null;

  return (
    <div className={`status-message status-${type}`}>
      <div className="status-icon">
        {type === 'success' && '✓'}
        {type === 'error' && '✕'}
        {type === 'loading' && '⏳'}
      </div>
      <p className="status-text">{message}</p>
    </div>
  );
}
