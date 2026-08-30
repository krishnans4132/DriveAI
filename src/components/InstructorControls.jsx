import React from 'react';
import { AlertTriangle, Gauge, Moon, RefreshCw, SlidersHorizontal, Timer } from 'lucide-react';

const InstructorControls = ({
  speed, setSpeed, shiftTime, setShiftTime,
  onSimulateYawn, onSimulateMicrosleep, onReset,
}) => (
  <section className="glass-panel instructor-panel">
    <div className="instructor-heading">
      <span><SlidersHorizontal size={20} /></span>
      <div><small>Examiner controls</small><strong>Context simulation</strong></div>
    </div>
    <div className="slider-container">
      <label><span><Gauge size={14} /> Vehicle speed</span><strong>{speed} km/h</strong></label>
      <input type="range" min="0" max="120" value={speed} onChange={(event) => setSpeed(Number(event.target.value))} />
    </div>
    <div className="slider-container">
      <label><span><Timer size={14} /> Drive duration</span><strong>{shiftTime.toFixed(1)} hrs</strong></label>
      <input type="range" min="0" max="10" step="0.5" value={shiftTime} onChange={(event) => setShiftTime(Number(event.target.value))} />
    </div>
    <div className="scenario-actions">
      <button className="scenario-button" onClick={onSimulateYawn}><AlertTriangle size={16} /> Demo yawn alert</button>
      <button className="scenario-button scenario-button--danger" onClick={onSimulateMicrosleep}><Moon size={16} /> Demo microsleep</button>
      <button className="reset-button" onClick={onReset} aria-label="Reset demo"><RefreshCw size={17} /></button>
    </div>
  </section>
);

export default InstructorControls;
