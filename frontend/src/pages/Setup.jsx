// frontend/src/pages/Setup.jsx: Screen for initial API key configuration and backend validation.

import React, { useState } from 'react';
import { healthCheck } from '../api';

export default function Setup({ onSaveKey }) {
  const [keyInput, setKeyInput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!keyInput.trim()) {
      setError('API key cannot be empty.');
      return;
    }

    setLoading(true);
    try {
      await healthCheck();
      onSaveKey(keyInput.trim());
    } catch (err) {
      setError('Backend not reachable — is the server running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-container">
      <div className="card setup-card">
        <h2>Face-IDP Setup</h2>
        <p className="subtitle">Please configure your Organization API Key to authenticate requests.</p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="apiKeyInput">API Key</label>
            <input
              id="apiKeyInput"
              type="text"
              placeholder="Enter your API Key"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              disabled={loading}
              className="text-input"
            />
          </div>
          
          {error && <div className="error-message" id="setupError">{error}</div>}
          
          <button id="saveKeyBtn" type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Connecting...' : 'Save & continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
