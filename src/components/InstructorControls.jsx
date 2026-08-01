import React from 'react';
import { Settings, RefreshCw, AlertTriangle, Moon } from 'lucide-react';

const InstructorControls = ({ 
  speed, setSpeed, 
  shiftTime, setShiftTime,
  onSimulateYawn,
  onSimulateMicrosleep,
  onReset 
}) => {
  return (
    <div className="glass-panel instructor-panel">
      <div className="controls-group">
        <Settings size={24} color="var(--accent-cyan)" />
        <div className="slider-container">
          <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Vehicle Speed: {speed} km/h
          </label>
          <input 
            type="range" 
            min="0" max="120" 
            value={speed} 
            onChange={(e) => setSpeed(Number(e.target.value))} 
          />
        </div>

        <div className="slider-container" style={{ marginLeft: '20px' }}>
          <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Drive Time: {shiftTime.toFixed(1)} Hours
          </label>
          <input 
            type="range" 
            min="0" max="10" step="0.5"
            value={shiftTime} 
            onChange={(e) => setShiftTime(Number(e.target.value))} 
          />
        </div>
      </div>

      <div className="controls-group">
        <button className="btn-outline" onClick={onSimulateYawn}>
          <AlertTriangle size={18} /> Simulate Yawn (Low Spd)
        </button>
        <button className="btn-danger" onClick={onSimulateMicrosleep}>
          <Moon size={18} /> Simulate Microsleep (High Spd)
        </button>
        <button className="btn-outline" onClick={onReset} style={{ borderColor: 'var(--text-secondary)', color: 'var(--text-secondary)' }}>
          <RefreshCw size={18} /> Reset State
        </button>
      </div>
    </div>
  );
};

export default InstructorControls;
