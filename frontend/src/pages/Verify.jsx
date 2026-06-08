// frontend/src/pages/Verify.jsx: Screen for capturing facial data and verifying worker identity.

import React, { useRef, useState, useEffect } from 'react';
import { verifyWorker } from '../api';

export default function Verify({ apiKey }) {
  const [workerId, setWorkerId] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageBase64, setImageBase64] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // { verified, confidence, worker_id } or null
  const [errorMsg, setErrorMsg] = useState('');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    async function startCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 480, height: 360 } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
        streamRef.current = mediaStream;
      } catch (err) {
        console.error("Camera access blocked or unavailable:", err);
      }
    }
    
    startCamera();
    
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth || 480;
      canvas.height = video.videoHeight || 360;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const dataUrl = canvas.toDataURL('image/jpeg');
      setPreviewUrl(dataUrl);
      
      const base64 = dataUrl.split(',')[1];
      setImageBase64(base64);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setResult(null);

    if (!workerId.trim()) {
      setErrorMsg('Please enter a Worker ID.');
      return;
    }

    if (!imageBase64) {
      setErrorMsg('Please capture a face photo first.');
      return;
    }

    setLoading(true);
    try {
      const response = await verifyWorker(apiKey, workerId.trim(), imageBase64);
      setResult({
        verified: response.verified,
        confidence: response.confidence,
        worker_id: response.worker_id
      });
      
      // Auto-clear result after 5 seconds
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        setResult(null);
        setPreviewUrl(null);
        setImageBase64('');
        setWorkerId('');
      }, 5000);
      
    } catch (err) {
      setErrorMsg(`Verification error: ${err.message || 'Failed to verify worker.'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verify-container">
      <div className="card verify-card">
        <h3>Verify Worker Check-in</h3>
        
        {result && (
          <div className={`result-card ${result.verified ? 'result-success' : 'result-failure'}`}>
            {result.verified ? (
              <div>
                <h2>✅ Verified</h2>
                <p className="result-detail">Worker ID: <strong>{result.worker_id}</strong></p>
                <p className="result-detail">Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong></p>
              </div>
            ) : (
              <div>
                <h2>❌ Not recognised</h2>
                <p className="result-detail">Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong></p>
              </div>
            )}
            <p className="reset-hint">Next check-in starting in 5 seconds...</p>
          </div>
        )}

        {!result && (
          <form onSubmit={handleVerify}>
            <div className="form-group">
              <label htmlFor="workerIdInput">Worker ID</label>
              <input
                id="workerIdInput"
                type="text"
                placeholder="e.g. test-worker-001"
                value={workerId}
                onChange={(e) => setWorkerId(e.target.value)}
                className="text-input"
              />
              <p className="help-text" style={{ fontSize: '0.8rem', color: '#666', marginTop: '6px', lineHeight: '1.4' }}>
                💡 <strong>Tip for mock mode:</strong> Append <code>-fail</code> or <code>-wrong</code> to the Worker ID (e.g. <code>test-worker-001-fail</code>) to simulate a biometric mismatch (wrong face) for an enrolled worker.
              </p>
            </div>

            <div className="camera-section">
              <div className="video-container">
                <video ref={videoRef} autoPlay playsInline muted className="camera-feed"></video>
              </div>
              <button type="button" className="btn btn-secondary btn-capture" onClick={handleCapture}>
                Capture
              </button>
            </div>

            <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>

            {previewUrl && (
              <div className="preview-container">
                <p className="preview-label">Snapshot Preview:</p>
                <img src={previewUrl} alt="Captured snapshot preview" className="image-preview" />
              </div>
            )}

            {errorMsg && <div className="error-message" id="verifyError">{errorMsg}</div>}

            <button
              id="verifyWorkerBtn"
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading || !workerId.trim() || !imageBase64}
            >
              {loading ? 'Verifying check-in...' : 'Check In'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
