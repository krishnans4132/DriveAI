import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import DashcamView from './DashcamView';
import TelemetryPanel from './TelemetryPanel';
import InstructorControls from './InstructorControls';
import CoPilotModal from './CoPilotModal';

const SimulatorDashboard = ({ onBack }) => {
  const [speed, setSpeed] = useState(80);
  const [shiftTime, setShiftTime] = useState(2.0); // 2 hours
  const [showModal, setShowModal] = useState(false);
  const [isRerouting, setIsRerouting] = useState(false);
  const [showBoundingBox, setShowBoundingBox] = useState(false);

  // Map speed (0-120) to playback rate (0.5 to 2.0)
  const playbackRate = Math.max(0.5, speed / 60);

  const handleSimulateYawn = () => {
    // Usually triggers at lower speed or higher drive time
    setSpeed(40);
    setShowBoundingBox(true);
    setTimeout(() => {
      setShowModal(true);
      setShowBoundingBox(false);
    }, 1500);
  };

  const handleSimulateMicrosleep = () => {
    // Urgent trigger
    setSpeed(110);
    setShowBoundingBox(true);
    setTimeout(() => {
      setShowModal(true);
      setShowBoundingBox(false);
    }, 1500);
  };

  const handleReset = () => {
    setSpeed(80);
    setShiftTime(2.0);
    setShowModal(false);
    setIsRerouting(false);
    setShowBoundingBox(false);
  };

  const handleAcceptReroute = () => {
    setIsRerouting(true);
    setShowModal(false);
  };

  const handleDismiss = () => {
    setShowModal(false);
    // In a real app, this might start a countdown to an emergency alarm
    alert("Emergency escalation timer started! (3s)");
  };

  return (
    <div className="simulator-layout">
      <header className="header">
        <button className="btn-outline" onClick={onBack} style={{ border: 'none' }}>
          <ArrowLeft size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} /> 
          Back to Home
        </button>
        <h2>Live Simulator Dashboard</h2>
        <div style={{ width: '100px' }}></div> {/* Spacer for flex centering */}
      </header>

      <DashcamView 
        playbackRate={playbackRate} 
        showBoundingBox={showBoundingBox} 
      />
      
      <TelemetryPanel 
        speed={speed} 
        shiftTime={shiftTime} 
        isRerouting={isRerouting} 
      />
      
      <InstructorControls 
        speed={speed} setSpeed={setSpeed}
        shiftTime={shiftTime} setShiftTime={setShiftTime}
        onSimulateYawn={handleSimulateYawn}
        onSimulateMicrosleep={handleSimulateMicrosleep}
        onReset={handleReset}
      />

      {showModal && (
        <CoPilotModal 
          onAccept={handleAcceptReroute}
          onDismiss={handleDismiss}
        />
      )}
    </div>
  );
};

export default SimulatorDashboard;
