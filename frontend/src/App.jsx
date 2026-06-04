// frontend/src/App.jsx: Main routing and navigation orchestrator for the face-idp frontend application.

import React, { useState } from 'react';
import Setup from './pages/Setup';
import Dashboard from './pages/Dashboard';
import Enroll from './pages/Enroll';
import Verify from './pages/Verify';

export default function App() {
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem('face_idp_api_key') || '';
  });
  const [currentPage, setCurrentPage] = useState('dashboard');

  const handleSaveKey = (key) => {
    localStorage.setItem('face_idp_api_key', key);
    setApiKey(key);
    setCurrentPage('dashboard');
  };

  const handleClearKey = () => {
    localStorage.removeItem('face_idp_api_key');
    setApiKey('');
  };

  if (!apiKey) {
    return <Setup onSaveKey={handleSaveKey} />;
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="nav-brand">face-idp</div>
        <div className="nav-menu">
          <button
            id="navDashboardBtn"
            className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}
          >
            Dashboard
          </button>
          <button
            id="navEnrollBtn"
            className={`nav-link ${currentPage === 'enroll' ? 'active' : ''}`}
            onClick={() => setCurrentPage('enroll')}
          >
            Enroll
          </button>
          <button
            id="navVerifyBtn"
            className={`nav-link ${currentPage === 'verify' ? 'active' : ''}`}
            onClick={() => setCurrentPage('verify')}
          >
            Verify
          </button>
        </div>
        <button id="clearKeyBtn" className="btn btn-secondary btn-sm" onClick={handleClearKey}>
          Clear Key
        </button>
      </nav>

      <main className="main-content">
        {currentPage === 'dashboard' && <Dashboard apiKey={apiKey} />}
        {currentPage === 'enroll' && <Enroll apiKey={apiKey} />}
        {currentPage === 'verify' && <Verify apiKey={apiKey} />}
      </main>
    </div>
  );
}
