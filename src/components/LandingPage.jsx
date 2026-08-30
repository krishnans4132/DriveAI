import React from 'react';
import { ShieldAlert, BrainCircuit, Activity, Globe, BarChart3 } from 'lucide-react';

const LandingPage = ({ onLaunch, onCompare }) => {
  return (
    <div style={{ paddingBottom: '60px' }}>
      <header className="landing-hero">
        <h1>DriveAlert AI</h1>
        <p>Real-Time Driver Fatigue and Microsleep Detection for Commercial Transport Safety</p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onLaunch}>
            <span>🚗</span> Launch Live Simulator
          </button>
          <button className="btn-outline hero-compare-button" onClick={onCompare}>
            <BarChart3 size={19} /> Explore Model Comparison
          </button>
        </div>
      </header>

      <section style={{ maxWidth: '800px', margin: '0 auto 60px', padding: '0 20px' }}>
        <div className="glass-panel" style={{ textAlign: 'center' }}>
          <ShieldAlert size={48} color="var(--accent-red)" style={{ marginBottom: '20px' }} />
          <h2 style={{ marginBottom: '15px' }}>The Silent Hazard</h2>
          <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            Commercial transport driver fatigue and microsleeps are leading causes of fatal highway accidents. 
            Traditional hardware-heavy infrared monitoring systems are expensive, intrusive, and often fail under 
            variable lighting or driver occlusion (e.g., glasses). DriveAlert AI leverages software-first, 
            context-aware edge computing to detect early fatigue indicators and proactively intervene.
          </p>
        </div>
      </section>

      <section className="novelties-grid">
        <div className="glass-panel novelty-card">
          <h3><BrainCircuit size={24} /> Cognitive Co-Pilot</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Verbal text-to-speech intervention and automatic rest-stop navigation upon fatigue detection, 
            preventing accidents before they happen.
          </p>
        </div>
        
        <div className="glass-panel novelty-card">
          <h3><Activity size={24} /> Velocity-Context Filter</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Dynamic adjustment of eye-closure thresholds based on vehicle speed. Low speeds trigger silent UI warnings, 
            while highway speeds trigger instant emergency alarms.
          </p>
        </div>

        <div className="glass-panel novelty-card">
          <h3><Globe size={24} /> Dynamic Shift Scaling</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            Automatic multiplier on fatigue sensitivity based on continuous hours driven. As the shift lengthens, 
            the system becomes more vigilant.
          </p>
        </div>
      </section>

      <section style={{ maxWidth: '800px', margin: '0 auto', padding: '0 20px', textAlign: 'center' }}>
        <div className="glass-panel">
          <h3 style={{ color: 'var(--accent-green)', marginBottom: '15px' }}>SDG Alignment & Research</h3>
          <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            Aligned with <strong>SDG 3 (Good Health & Well-being)</strong> and <strong>SDG 11 (Sustainable Cities)</strong>. 
            Our model bridges critical research gaps by focusing on low-light vision, glasses occlusion via robust datasets (YawDD, UTA-RLDD, DDD), 
            and early-stage non-invasive interventions.
          </p>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
