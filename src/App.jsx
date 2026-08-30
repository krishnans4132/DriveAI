import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import ModelComparison from './components/ModelComparison';
import SimulatorDashboard from './components/SimulatorDashboard';

function App() {
  const [view, setView] = useState('landing');

  const renderView = () => {
    if (view === 'comparison') {
      return (
        <ModelComparison
          onBack={() => setView('landing')}
          onLaunch={() => setView('simulator')}
        />
      );
    }

    if (view === 'simulator') {
      return <SimulatorDashboard onBack={() => setView('landing')} />;
    }

    return (
      <LandingPage
        onLaunch={() => setView('simulator')}
        onCompare={() => setView('comparison')}
      />
    );
  };

  return (
    <div className="app-container">
      {renderView()}
    </div>
  );
}

export default App;
