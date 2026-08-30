import React, { useMemo, useState } from 'react';
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Check,
  Cpu,
  Database,
  Gauge,
  HardDrive,
  Layers3,
  Network,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Target,
  Trophy,
  Users,
  Zap,
} from 'lucide-react';
import {
  comparisonProtocol,
  metricDefinitions,
  models,
} from '../data/modelComparison';

const taskCopy = {
  eye: {
    eyebrow: 'Microsleep signal',
    title: 'Eye-state classification',
    description: 'Binary open-versus-closed classification using a safety-oriented threshold locked on validation data.',
  },
  mouth: {
    eyebrow: 'Fatigue signal',
    title: 'Mouth-event classification',
    description: 'Three-class not-yawn, talking and yawn recognition with a validation-locked yawn threshold.',
  },
};

function MetricBar({ label, value, modelKey }) {
  return (
    <div className="metric-bar-row">
      <div className="metric-bar-label">
        <span>{label}</span>
        <strong>{value.toFixed(2)}%</strong>
      </div>
      <div className="metric-track" aria-hidden="true">
        <span
          className={`metric-fill metric-fill--${modelKey}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function ModelIdentity({ model }) {
  const ArchitectureIcon = {
    mobilenet: Smartphone,
    efficientnet: Layers3,
    resnet: Network,
  }[model.key];

  return (
    <div className="model-identity">
      <span
        className={`model-mark model-mark--${model.key}`}
        title={`${model.name} architecture`}
        aria-hidden="true"
      >
        <ArchitectureIcon size={23} strokeWidth={2.3} />
      </span>
      <div>
        <strong>{model.name}</strong>
        <span>{model.owner}</span>
      </div>
    </div>
  );
}

const ModelComparison = ({ onBack, onLaunch }) => {
  const [activeTask, setActiveTask] = useState('eye');
  const activeMetrics = metricDefinitions[activeTask];
  const copy = taskCopy[activeTask];

  const leaders = useMemo(() => {
    const metrics = {};
    activeMetrics.forEach(([key]) => {
      metrics[key] = Math.max(...models.map((model) => model[activeTask][key]));
    });
    return metrics;
  }, [activeMetrics, activeTask]);

  return (
    <main className="comparison-page">
      <div className="comparison-orb comparison-orb--one" />
      <div className="comparison-orb comparison-orb--two" />

      <nav className="comparison-nav">
        <button className="nav-back" onClick={onBack}>
          <ArrowLeft size={18} /> Overview
        </button>
        <div className="comparison-brand">
          <span className="brand-icon"><Activity size={19} /></span>
          <span>DriveAlert <b>Research Lab</b></span>
        </div>
        <button className="nav-launch" onClick={onLaunch}>
          Live monitor <ArrowRight size={17} />
        </button>
      </nav>

      <section className="comparison-hero">
        <div className="hero-kicker"><Sparkles size={15} /> Architecture study · Experiment 03</div>
        <h1>Three architectures.<br /><span>One deployment decision.</span></h1>
        <p>
          A controlled comparison of lightweight, compound-scaled and residual
          networks for real-time driver fatigue detection.
        </p>
        <div className="protocol-row">
          {comparisonProtocol.map((item) => (
            <span key={item}><Check size={14} /> {item}</span>
          ))}
        </div>
      </section>

      <section className="decision-banner">
        <div className="decision-icon"><Zap size={25} /></div>
        <div>
          <span className="section-kicker">Deployment verdict</span>
          <h2>MobileNetV3-Small powers the live system</h2>
          <p>Near-benchmark safety metrics in a 5.8 MiB ONNX package—built for responsive webcam inference on an ordinary laptop.</p>
        </div>
        <div className="decision-stat">
          <strong>7.3×</strong>
          <span>smaller than<br />ResNet-18</span>
        </div>
      </section>

      <section className="comparison-section">
        <div className="section-heading">
          <div>
            <span className="section-kicker"><Users size={15} /> Individual contributions</span>
            <h2>Architecture ownership</h2>
          </div>
          <p>Each member trained and evaluated one architecture under the same experimental protocol.</p>
        </div>

        <div className="model-card-grid">
          {models.map((model) => (
            <article className={`model-card model-card--${model.key}`} key={model.key}>
              <div className="model-card-topline">
                <span className={`model-badge model-badge--${model.key}`}>{model.badge}</span>
                {model.key === 'mobilenet' && <ShieldCheck size={21} />}
                {model.key === 'resnet' && <Trophy size={21} />}
              </div>
              <ModelIdentity model={model} />
              <p className="model-purpose">{model.purpose}</p>
              <p className="model-why">{model.why}</p>

              <div className="model-specs">
                <div><Cpu size={16} /><span>Parameters</span><strong>{model.params.toFixed(2)}M</strong></div>
                <div><HardDrive size={16} /><span>Eye ONNX</span><strong>{model.eyeSize.toFixed(2)} MiB</strong></div>
              </div>

              <div className="model-decision">
                <Target size={17} />
                <p>{model.decision}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="comparison-section results-section">
        <div className="section-heading results-heading">
          <div>
            <span className="section-kicker"><BarChart3 size={15} /> Held-out test performance</span>
            <h2>{copy.title}</h2>
            <p>{copy.description}</p>
          </div>
          <div className="task-switcher" aria-label="Select model task">
            <button className={activeTask === 'eye' ? 'active' : ''} onClick={() => setActiveTask('eye')}>Eye model</button>
            <button className={activeTask === 'mouth' ? 'active' : ''} onClick={() => setActiveTask('mouth')}>Mouth model</button>
          </div>
        </div>

        <div className="results-layout">
          <div className="chart-panel glass-panel">
            <div className="chart-header">
              <div>
                <span>{copy.eyebrow}</span>
                <h3>Safety metric comparison</h3>
              </div>
              <span className="chart-unit">%</span>
            </div>

            {models.map((model) => (
              <div className="model-metric-group" key={model.key}>
                <ModelIdentity model={model} />
                <div className="metric-bars">
                  {activeMetrics.map(([key, label]) => (
                    <MetricBar
                      key={key}
                      label={`${label}${leaders[key] === model[activeTask][key] ? ' · best' : ''}`}
                      value={model[activeTask][key]}
                      modelKey={model.key}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          <aside className="insight-stack">
            <div className="insight-card insight-card--winner">
              <Trophy size={23} />
              <span>Metric leader</span>
              <h3>ResNet-18</h3>
              <p>{activeTask === 'eye' ? '97.88% balanced accuracy' : '96.72% yawn balanced accuracy'}</p>
            </div>
            <div className="insight-card">
              <Gauge size={23} />
              <span>Deployment leader</span>
              <h3>MobileNetV3</h3>
              <p>Smallest model with strong safety recall.</p>
            </div>
            <div className="insight-card insight-card--note">
              <Database size={22} />
              <span>Evaluation note</span>
              <p>Results use provisional weak labels and require independent human validation.</p>
            </div>
          </aside>
        </div>

        <div className="metrics-table-wrap">
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Architecture</th>
                <th>Owner</th>
                <th>Parameters</th>
                <th>ONNX</th>
                <th>Threshold</th>
                {activeMetrics.map(([, label]) => <th key={label}>{label}</th>)}
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.key}>
                  <td><span className={`table-dot table-dot--${model.key}`} />{model.name}</td>
                  <td>{model.owner}</td>
                  <td>{model.params.toFixed(2)}M</td>
                  <td>{(activeTask === 'eye' ? model.eyeSize : model.mouthSize).toFixed(2)} MiB</td>
                  <td>{model[activeTask].threshold.toFixed(3)}</td>
                  {activeMetrics.map(([key]) => <td key={key}>{model[activeTask][key].toFixed(2)}%</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="comparison-cta">
        <div>
          <span className="section-kicker">From research to the road</span>
          <h2>See the selected model in action.</h2>
          <p>Continue to the real-time fatigue monitor with simulated telemetry and cognitive co-pilot interventions.</p>
        </div>
        <button className="btn-primary" onClick={onLaunch}>
          Launch live monitor <ArrowRight size={19} />
        </button>
      </section>
    </main>
  );
};

export default ModelComparison;
