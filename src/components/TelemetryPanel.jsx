import React from 'react';
import {
  Activity,
  BellRing,
  Coffee,
  Eye,
  Gauge,
  MapPin,
  Navigation2,
  Route,
  ScanFace,
  Timer,
} from 'lucide-react';

const formatTime = (hours) => {
  const wholeHours = Math.floor(hours);
  const minutes = Math.floor((hours - wholeHours) * 60);
  return `${wholeHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
};

const percentage = (value) => value == null ? '—' : `${(value * 100).toFixed(1)}%`;

const clamp = (value) => Math.min(100, Math.max(0, value));

const AlertQueueMonitor = ({ analysis, isIdle }) => {
  const decision = isIdle ? null : analysis?.decision;
  const alertLevel = decision?.alert_level || 'none';
  const alertRank = { none: 0, sensor_unavailable: 0, advisory: 1, warning: 2, critical: 3 }[alertLevel] || 0;
  const stages = ['Monitoring', 'Advisory', 'Warning', 'Critical'];
  const signals = [
    {
      key: 'closure',
      label: 'Continuous eye closure',
      value: decision?.continuous_eye_closure_s,
      threshold: decision?.effective_closure_warning_s,
      render: (value) => `${value.toFixed(2)}s`,
      icon: Eye,
    },
    {
      key: 'perclos',
      label: 'PERCLOS · 60 seconds',
      value: decision?.perclos_60s,
      threshold: decision?.effective_perclos_warning,
      render: (value) => `${(value * 100).toFixed(1)}%`,
      icon: ScanFace,
    },
    {
      key: 'yawns',
      label: 'Yawns · 5 minutes',
      value: decision?.yawns_5min,
      threshold: decision?.effective_yawns_for_advisory,
      render: (value) => `${Math.round(value)}`,
      icon: Activity,
    },
  ].map((signal) => ({
    ...signal,
    ratio: signal.threshold > 0 && signal.value != null
      ? signal.value / signal.threshold
      : 0,
  }));
  const leadingSignal = [...signals].sort((left, right) => right.ratio - left.ratio)[0];
  const reached = signals.some((signal) => signal.ratio >= 1);
  const nextStage = alertRank < stages.length - 1 ? stages[alertRank + 1] : 'Intervention active';

  let queueMessage = `${nextStage} is queued`;
  if (isIdle) queueMessage = 'Vehicle stopped — fatigue model is idle';
  else if (!analysis) queueMessage = 'Waiting for the first model reading';
  else if (alertLevel === 'sensor_unavailable') queueMessage = 'Face signal required before alerts can queue';
  else if (alertLevel === 'critical') queueMessage = 'Critical intervention is active';
  else if (reached) queueMessage = `${nextStage} escalation is queued`;

  return (
    <div className="alert-queue-monitor">
      <div className="queue-heading">
        <div>
          <span><BellRing size={15} /> Alert queue monitor</span>
          <strong>{queueMessage}</strong>
        </div>
        <em className={reached ? 'threshold-reached' : ''}>
          {isIdle ? 'IDLE' : reached ? 'THRESHOLD REACHED' : `${Math.round(clamp(leadingSignal.ratio * 100))}% TO TRIGGER`}
        </em>
      </div>

      <div className="alert-stage-queue" aria-label="Alert escalation queue">
        {stages.map((stage, index) => (
          <React.Fragment key={stage}>
            <div className={`queue-stage ${index < alertRank ? 'queue-stage--passed' : ''} ${index === alertRank ? 'queue-stage--active' : ''} ${index === alertRank + 1 ? 'queue-stage--next' : ''}`}>
              <span>{index + 1}</span><small>{stage}</small>
            </div>
            {index < stages.length - 1 && <i />}
          </React.Fragment>
        ))}
      </div>

      <div className="threshold-signal-list">
        {signals.map((signal) => {
          const SignalIcon = signal.icon;
          const signalReached = signal.ratio >= 1;
          return (
            <div className={`threshold-signal ${signalReached ? 'threshold-signal--reached' : ''}`} key={signal.key}>
              <div className="threshold-signal-label">
                <span><SignalIcon size={13} /> {signal.label}</span>
                <strong>
                  {signal.value == null ? '—' : signal.render(signal.value)}
                  <small> / {signal.threshold == null ? '—' : signal.render(signal.threshold)}</small>
                </strong>
              </div>
              <div className="threshold-progress"><span style={{ width: `${clamp(signal.ratio * 100)}%` }} /></div>
            </div>
          );
        })}
      </div>
      <p className="queue-footnote">Alerts fire immediately when a live adaptive threshold reaches 100%; the queue shows the next escalation stage.</p>
    </div>
  );
};

const HardcodedRouteMap = ({ isRerouting }) => (
  <div className={`route-map ${isRerouting ? 'route-map--active' : ''}`}>
    <div className="map-grid" />
    <svg viewBox="0 0 520 220" role="img" aria-label="Hardcoded demonstration route to Lakeside Rest Plaza">
      <path className="map-road map-road--secondary" d="M-10 42 C95 70 105 10 210 48 S360 92 535 55" />
      <path className="map-road map-road--secondary" d="M92 -10 C110 48 82 110 128 235" />
      <path className="map-road map-road--secondary" d="M410 -10 C380 55 440 133 392 235" />
      <path className="map-road map-road--main" d="M32 176 C115 148 160 184 228 142 S347 73 485 88" />
      <path className="map-route" d="M96 158 C162 160 184 165 228 142 S320 87 402 88" />
      <circle className="map-origin-pulse" cx="96" cy="158" r="16" />
      <circle className="map-origin" cx="96" cy="158" r="6" />
      <circle className="map-destination" cx="402" cy="88" r="8" />
    </svg>
    <div className="map-place map-place--current"><Navigation2 size={14} /><span>Demo vehicle</span></div>
    <div className="map-place map-place--rest"><Coffee size={14} /><span>Lakeside Rest Plaza</span></div>
    <div className="map-caption">
      <div><Route size={15} /><span>{isRerouting ? 'Demo route active' : 'Hardcoded offline route'}</span></div>
      <strong>{isRerouting ? '4.2 km · 6 min' : 'Rest stop ready'}</strong>
    </div>
    <span className="simulation-badge">SIMULATED NAVIGATION</span>
  </div>
);

const TelemetryPanel = ({ speed, shiftTime, isRerouting, analysis }) => {
  const isIdle = speed === 0;
  const activeAnalysis = isIdle ? null : analysis;
  const decision = activeAnalysis?.decision;
  const model = activeAnalysis?.model;
  const sensitivity = decision?.sensitivity_multiplier || 1;
  return (
    <aside className="telemetry-panel">
      <div className="telemetry-kpis">
        <div className="glass-panel telemetry-kpi">
          <span className="telemetry-kpi-icon"><Gauge size={18} /></span>
          <div><small>Simulated speed</small><strong>{speed}<em>km/h</em></strong></div>
        </div>
        <div className="glass-panel telemetry-kpi">
          <span className="telemetry-kpi-icon telemetry-kpi-icon--green"><Timer size={18} /></span>
          <div><small>Continuous drive</small><strong>{formatTime(shiftTime)}<em>hrs</em></strong></div>
        </div>
      </div>

      <div className="glass-panel risk-panel">
        <div className="panel-title-row">
          <div><span className="section-kicker">Dynamic risk engine</span><h3>Live fatigue evidence</h3></div>
          <Activity size={20} />
        </div>
        <div className="risk-readings">
          <div><span>Eye closure probability</span><strong>{percentage(model?.eye_closed_probability)}</strong></div>
          <div><span>Yawn probability</span><strong>{percentage(model?.yawn_probability)}</strong></div>
          <div><span>PERCLOS · 60 seconds</span><strong>{percentage(decision?.perclos_60s)}</strong></div>
          <div><span>Context sensitivity</span><strong>{isIdle ? 'idle' : `${sensitivity.toFixed(2)}×`}</strong></div>
        </div>
        <AlertQueueMonitor analysis={activeAnalysis} isIdle={isIdle} />
        <div className="threshold-note">
          <MapPin size={15} />
          <p>
            {isIdle
              ? 'Vehicle speed is 0 km/h. Inference and the alert queue are paused until movement begins.'
              : <>Speed and continuous-drive time lower the temporal warning duration to <b>{decision?.effective_closure_warning_s?.toFixed(2) || '—'}s</b>. Model probability thresholds stay locked.</>}
          </p>
        </div>
      </div>

      <HardcodedRouteMap isRerouting={isRerouting} />
    </aside>
  );
};

export default TelemetryPanel;
