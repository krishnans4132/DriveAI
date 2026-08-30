import React, { useEffect } from 'react';
import { Coffee, Navigation, ShieldAlert, Volume2, X } from 'lucide-react';
import { speakText } from '../utils/speech';

const CoPilotModal = ({ message, isRealDetection, voiceEnabled, onVoiceEnabled, onAccept, onDismiss }) => {
  const spokenMessage = `${message} A safe rest stop is ready. Would you like to reroute?`;
  useEffect(() => {
    if (voiceEnabled) speakText(spokenMessage);
    return () => window.speechSynthesis?.cancel();
  }, [spokenMessage]);

  const playVoiceAlert = () => {
    if (voiceEnabled) {
      speakText(spokenMessage);
    } else {
      onVoiceEnabled?.();
      speakText(spokenMessage);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Fatigue intervention">
      <div className="modal-content">
        <button className="modal-close" onClick={onDismiss} aria-label="Close"><X size={18} /></button>
        <div className="modal-alert-icon"><ShieldAlert size={30} /></div>
        <span className="modal-eyebrow">{isRealDetection ? 'LIVE MODEL INTERVENTION' : 'EXAMINER SCENARIO'}</span>
        <h2>It is time for a safe break.</h2>
        <p>{message}</p>
        <button className="speech-chip" onClick={playVoiceAlert}>
          <Volume2 size={15} /> {voiceEnabled ? 'Replay voice warning' : 'Play and enable voice warning'}
        </button>
        <div className="rest-stop-card">
          <span><Coffee size={21} /></span>
          <div><small>Recommended stop</small><strong>Lakeside Rest Plaza</strong><p>4.2 km away · approximately 6 minutes</p></div>
        </div>
        <div className="modal-actions">
          <button className="btn-primary" onClick={onAccept}><Navigation size={18} /> Start safe reroute</button>
          <button className="btn-outline" onClick={onDismiss}>Continue monitoring</button>
        </div>
        <small className="modal-disclaimer">Demonstration support system — the driver remains responsible for stopping safely.</small>
      </div>
    </div>
  );
};

export default CoPilotModal;
