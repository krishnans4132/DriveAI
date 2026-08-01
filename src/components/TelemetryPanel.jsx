import React from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix for default marker icon in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const TelemetryPanel = ({ speed, shiftTime, isRerouting }) => {
  // Format shift time from hours (e.g., 4.5 -> 04:30)
  const formatTime = (hours) => {
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  const currentPos = [40.7128, -74.0060]; // NY
  const restStopPos = [40.7300, -73.9900]; // Nearby Rest Stop

  return (
    <div className="telemetry-panel">
      <div className="glass-panel gauge-container">
        <h3 style={{ color: 'var(--text-secondary)', marginBottom: '10px' }}>Current Speed</h3>
        <div className="speed-value">{speed} <span style={{ fontSize: '1.2rem' }}>km/h</span></div>
      </div>

      <div className="glass-panel gauge-container">
        <h3 style={{ color: 'var(--text-secondary)', marginBottom: '10px' }}>Continuous Drive Time</h3>
        <div className="speed-value" style={{ color: 'var(--accent-green)' }}>{formatTime(shiftTime)}</div>
      </div>

      <div className="glass-panel map-container" style={{ padding: 0 }}>
        <MapContainer center={currentPos} zoom={13} style={{ height: '100%', width: '100%', minHeight: '300px' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          <Marker position={currentPos}>
            <Popup>Current Location</Popup>
          </Marker>
          {isRerouting && (
            <>
              <Marker position={restStopPos}>
                <Popup>Nearest Rest Stop / Coffee</Popup>
              </Marker>
              <Polyline positions={[currentPos, restStopPos]} color="var(--accent-cyan)" weight={4} />
            </>
          )}
        </MapContainer>
      </div>
    </div>
  );
};

export default TelemetryPanel;
