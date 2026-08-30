import React, { useCallback, useRef, useState } from 'react';
import { ArrowLeft, ShieldCheck, Volume2, VolumeX } from 'lucide-react';
import DashcamView from './DashcamView';
import TelemetryPanel from './TelemetryPanel';
import InstructorControls from './InstructorControls';
import CoPilotModal from './CoPilotModal';
import { speakText, speechIsSupported } from '../utils/speech';

const alertCopy = {
  real: 'Fatigue evidence has crossed the speed-adjusted safety threshold.',
  yawn: 'Examiner scenario: repeated yawning suggests an early fatigue pattern.',
  microsleep: 'Examiner scenario: sustained eye closure at highway speed requires immediate action.',
};

const SimulatorDashboard = ({ onBack }) => {
  const [speed, setSpeed] = useState(0);
  const [shiftTime, setShiftTime] = useState(2);
  const [showModal, setShowModal] = useState(false);
  const [alertSource, setAlertSource] = useState('real');
  const [isRerouting, setIsRerouting] = useState(false);
  const [showBoundingBox, setShowBoundingBox] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [resetToken, setResetToken] = useState(0);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const voiceSupported = speechIsSupported();
  const lastAutomaticAlertRef = useRef(0);

  const handleAnalysis = useCallback((result) => {
    setAnalysis(result);
    const level = result?.decision?.alert_level;
    const now = Date.now();
    if ((level === 'warning' || level === 'critical') && now - lastAutomaticAlertRef.current > 12000) {
      lastAutomaticAlertRef.current = now;
      setAlertSource('real');
      setShowModal(true);
    }
  }, []);

  const runExaminerScenario = (source) => {
    setAlertSource(source);
    setSpeed(source === 'microsleep' ? 110 : 40);
    setShowBoundingBox(true);
    window.setTimeout(() => {
      setShowModal(true);
      setShowBoundingBox(false);
    }, 800);
  };

  const handleSpeedChange = (nextSpeed) => {
    setSpeed(nextSpeed);
    if (nextSpeed === 0) {
      setAnalysis(null);
      setShowModal(false);
      setIsRerouting(false);
      lastAutomaticAlertRef.current = 0;
    }
  };

  const handleReset = () => {
    setSpeed(0);
    setShiftTime(2);
    setShowModal(false);
    setIsRerouting(false);
    setShowBoundingBox(false);
    setAnalysis(null);
    lastAutomaticAlertRef.current = 0;
    setResetToken((value) => value + 1);
  };

  const enableVoiceAlerts = () => {
    const enabled = speakText('Voice alerts enabled. DriveAlert cognitive co-pilot is ready.');
    setVoiceEnabled(enabled);
  };

  return (
    <div className="simulator-layout">
      <header className="simulator-header">
        <button className="nav-back" onClick={onBack}><ArrowLeft size={17} /> Back</button>
        <div className="simulator-title">
          <span className="brand-icon"><ShieldCheck size={19} /></span>
          <div><small>DriveAlert AI</small><h2>Real-Time Safety Console</h2></div>
        </div>
        <button
          className={`voice-alert-toggle ${voiceEnabled ? 'voice-alert-toggle--active' : ''}`}
          onClick={enableVoiceAlerts}
          disabled={!voiceSupported}
          title={voiceSupported ? 'Enable and test spoken fatigue warnings' : 'Text-to-speech is unavailable in this browser'}
        >
          {voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          {voiceEnabled ? 'Voice alerts on' : voiceSupported ? 'Enable voice alerts' : 'Voice unavailable'}
        </button>
      </header>
      <DashcamView
        speed={speed}
        shiftTime={shiftTime}
        showBoundingBox={showBoundingBox}
        resetToken={resetToken}
        onAnalysis={handleAnalysis}
      />
      <TelemetryPanel speed={speed} shiftTime={shiftTime} isRerouting={isRerouting} analysis={analysis} />
      <InstructorControls
        speed={speed}
        setSpeed={handleSpeedChange}
        shiftTime={shiftTime}
        setShiftTime={setShiftTime}
        onSimulateYawn={() => runExaminerScenario('yawn')}
        onSimulateMicrosleep={() => runExaminerScenario('microsleep')}
        onReset={handleReset}
      />
      {showModal && (
        <CoPilotModal
          message={alertCopy[alertSource]}
          isRealDetection={alertSource === 'real'}
          voiceEnabled={voiceEnabled}
          onVoiceEnabled={() => setVoiceEnabled(true)}
          onAccept={() => { setIsRerouting(true); setShowModal(false); }}
          onDismiss={() => setShowModal(false)}
        />
      )}
    </div>
  );
};

export default SimulatorDashboard;
