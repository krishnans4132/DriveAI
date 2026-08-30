import React, { useEffect, useRef, useState } from 'react';
import { Camera, CameraOff, Cpu, Eye, PauseCircle, ScanFace, Wifi, WifiOff } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';
const SESSION_ID = `drivealert-${Math.random().toString(36).slice(2)}`;
const probability = (value) => value == null ? '—' : `${(value * 100).toFixed(1)}%`;

const DashcamView = ({ speed, shiftTime, showBoundingBox, resetToken, onAnalysis }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const busyRef = useRef(false);
  const idleRef = useRef(false);
  const telemetryRef = useRef({ speed, shiftTime });
  const analysisCallbackRef = useRef(onAnalysis);
  const [cameraState, setCameraState] = useState('requesting');
  const [apiState, setApiState] = useState('checking');
  const [analysis, setAnalysis] = useState(null);
  const [cameraError, setCameraError] = useState('');

  useEffect(() => { telemetryRef.current = { speed, shiftTime }; }, [speed, shiftTime]);
  useEffect(() => { analysisCallbackRef.current = onAnalysis; }, [onAnalysis]);

  useEffect(() => {
    if (speed === 0) {
      setAnalysis(null);
      analysisCallbackRef.current?.(null);
      if (!idleRef.current) {
        idleRef.current = true;
        fetch(`${API_URL}/api/session/reset`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: SESSION_ID }),
        }).catch(() => {});
      }
    } else {
      idleRef.current = false;
    }
  }, [speed]);

  useEffect(() => {
    let active = true;
    const startCamera = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraState('unsupported');
        setCameraError('This browser does not support webcam access.');
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 960 }, height: { ideal: 720 }, facingMode: 'user' },
          audio: false,
        });
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        videoRef.current.srcObject = stream;
        setCameraState('live');
      } catch (error) {
        setCameraState('denied');
        setCameraError(error?.name === 'NotAllowedError'
          ? 'Camera permission was denied. Allow camera access and reload the page.'
          : 'The webcam could not be opened. Check that another app is not using it.');
      }
    };
    startCamera();
    return () => {
      active = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/status`)
      .then((response) => {
        if (!response.ok) throw new Error('Backend unavailable');
        return response.json();
      })
      .then(() => !cancelled && setApiState('online'))
      .catch(() => !cancelled && setApiState('offline'));
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/api/session/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: SESSION_ID }),
    }).catch(() => {});
    setAnalysis(null);
  }, [resetToken]);

  useEffect(() => {
    if (cameraState !== 'live') return undefined;
    const analyzeFrame = async () => {
      const current = telemetryRef.current;
      if (current.speed === 0) return;
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (busyRef.current || !video || !canvas || video.readyState < 2) return;
      busyRef.current = true;
      try {
        const width = 640;
        const height = Math.round(width * (video.videoHeight || 480) / (video.videoWidth || 640));
        canvas.width = width;
        canvas.height = height;
        canvas.getContext('2d', { alpha: false }).drawImage(video, 0, 0, width, height);
        const response = await fetch(`${API_URL}/api/analyze_frame`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: SESSION_ID,
            frame: canvas.toDataURL('image/jpeg', 0.72),
            speed_kph: current.speed,
            continuous_drive_minutes: current.shiftTime * 60,
          }),
        });
        if (!response.ok) throw new Error(`Inference request failed (${response.status})`);
        const result = await response.json();
        if (telemetryRef.current.speed === 0) return;
        setApiState('online');
        setAnalysis(result);
        analysisCallbackRef.current?.(result);
      } catch (error) {
        setApiState('offline');
      } finally {
        busyRef.current = false;
      }
    };
    analyzeFrame();
    const interval = window.setInterval(analyzeFrame, 700);
    return () => window.clearInterval(interval);
  }, [cameraState]);

  const boxStyle = (box) => box ? {
    left: `${(1 - box.x - box.width) * 100}%`,
    top: `${box.y * 100}%`,
    width: `${box.width * 100}%`,
    height: `${box.height * 100}%`,
  } : undefined;
  const isIdle = speed === 0;
  const level = isIdle ? 'idle' : analysis?.decision?.alert_level || (apiState === 'offline' ? 'offline' : 'waiting');

  return (
    <section className={`dashcam-container dashcam-container--${level}`}>
      <video ref={videoRef} className="dashcam-video" autoPlay muted playsInline />
      <canvas ref={canvasRef} hidden />
      {cameraState !== 'live' && (
        <div className="camera-empty-state">
          {cameraState === 'requesting' ? <Camera size={38} /> : <CameraOff size={38} />}
          <h3>{cameraState === 'requesting' ? 'Connecting to driver camera' : 'Camera unavailable'}</h3>
          <p>{cameraError || 'Approve the webcam permission to begin real-time monitoring.'}</p>
        </div>
      )}
      {isIdle && cameraState === 'live' && (
        <div className="model-idle-overlay">
          <PauseCircle size={30} />
          <strong>Fatigue model idle</strong>
          <span>Monitoring starts when the vehicle begins moving.</span>
        </div>
      )}
      {analysis?.eye_box && <div className="vision-box vision-box--eye" style={boxStyle(analysis.eye_box)}><span>eyes</span></div>}
      {analysis?.mouth_box && <div className="vision-box vision-box--mouth" style={boxStyle(analysis.mouth_box)}><span>mouth</span></div>}
      {showBoundingBox && <div className="vision-box vision-box--demo"><span>examiner scenario</span></div>}
      <div className="camera-topbar">
        <div className="live-chip"><span /> LIVE DRIVER CAMERA</div>
        <div className={`connection-chip connection-chip--${isIdle ? 'idle' : apiState}`}>
          {isIdle ? <PauseCircle size={14} /> : apiState === 'online' ? <Wifi size={14} /> : <WifiOff size={14} />}
          {isIdle ? 'MODEL IDLE · VEHICLE STOPPED' : apiState === 'online' ? 'MODEL CONNECTED' : apiState === 'checking' ? 'CONNECTING' : 'START LOCAL API'}
        </div>
      </div>
      <div className="vision-hud">
        <div className="hud-model">
          <span className="hud-icon"><Cpu size={18} /></span>
          <div><small>Deployed model</small><strong>MobileNetV3-Small</strong></div>
        </div>
        <div className="hud-reading">
          <Eye size={16} /><div><small>Eye closed</small><strong>{isIdle ? 'idle' : probability(analysis?.model?.eye_closed_probability)}</strong></div>
        </div>
        <div className="hud-reading">
          <ScanFace size={16} /><div><small>Mouth state</small><strong>{isIdle ? 'idle' : analysis?.model?.mouth_state?.replace('_', ' ') || 'waiting'}</strong></div>
        </div>
        <div className={`hud-alert hud-alert--${level}`}>
          <small>Risk status</small><strong>{level.replace('_', ' ')}</strong>
        </div>
      </div>
    </section>
  );
};

export default DashcamView;
