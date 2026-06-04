// frontend/src/pages/Dashboard.jsx: Screen displaying recent verification logs and stats.

import React, { useEffect, useState } from 'react';
import { fetchLogs } from '../api';

export default function Dashboard({ apiKey }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchLogs(apiKey);
      setLogs(data);
    } catch (err) {
      setError(err.message || 'Failed to retrieve logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [apiKey]);

  const total = logs.length;
  const verified = logs.filter(log => log.verified).length;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <button id="refreshLogsBtn" className="btn btn-secondary" onClick={loadData} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="summary-banner card">
        <p className="summary-text">
          <strong>{total}</strong> verifications total, <strong>{verified}</strong> verified.
        </p>
      </div>

      {error && <div className="error-message card">{error}</div>}

      <div className="card logs-card">
        {loading ? (
          <p className="centered-info">Loading verification logs...</p>
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <p>No verifications yet — enroll a worker to get started.</p>
          </div>
        ) : (
          <table className="logs-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Worker ID</th>
                <th>Verified</th>
                <th>Confidence Score</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>{log.worker_id}</td>
                  <td>{log.verified ? '✅' : '❌'}</td>
                  <td>{(log.confidence * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
