import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import SimulatorDashboard from './components/SimulatorDashboard';

function App() {
  const [view, setView] = useState('landing'); // 'landing' | 'simulator'

  return (
    <div className="app-container">
      {view === 'landing' ? (
        <LandingPage onLaunch={() => setView('simulator')} />
      ) : (
        <SimulatorDashboard onBack={() => setView('landing')} />
      )}
    </div>
  );
}

export default App;
