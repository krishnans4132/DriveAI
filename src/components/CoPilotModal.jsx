import React, { useEffect } from 'react';
import { Navigation } from 'lucide-react';

const CoPilotModal = ({ onAccept, onDismiss }) => {
  
  useEffect(() => {
    // Text-to-Speech logic
    if ('speechSynthesis' in window) {
      const msg = new SpeechSynthesisUtterance();
      msg.text = "Early fatigue detected. Would you like to reroute to the nearest rest area for coffee?";
      msg.rate = 1;
      msg.pitch = 1;
      window.speechSynthesis.speak(msg);
    }

    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    }
  }, []);

  return (
    <div className="modal-overlay">
      <div className="glass-panel modal-content">
        <h2>⚠️ Fatigue Alert Triggered</h2>
        <p style={{ fontSize: '1.2rem', marginBottom: '20px' }}>
          "Early fatigue detected. Would you like to reroute to the nearest rest area for coffee?"
        </p>
        <div className="modal-actions">
          <button className="btn-primary" onClick={onAccept}>
            <Navigation size={18} /> Yes, Reroute
          </button>
          <button className="btn-outline" onClick={onDismiss} style={{ borderColor: 'var(--text-secondary)', color: 'var(--text-secondary)' }}>
            Dismiss (Emergency Timer)
          </button>
        </div>
      </div>
    </div>
  );
};

export default CoPilotModal;
