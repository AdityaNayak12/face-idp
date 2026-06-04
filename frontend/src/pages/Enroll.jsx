// frontend/src/pages/Enroll.jsx: Screen for capturing facial data and enrolling a new worker.

import React, { useRef, useState, useEffect } from 'react';
import { enrollWorker } from '../api';

export default function Enroll({ apiKey }) {
  const [workerId, setWorkerId] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageBase64, setImageBase64] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState(''); // 'success' or 'error'

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

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
      
      // Extract raw base64 string
      const base64 = dataUrl.split(',')[1];
      setImageBase64(base64);
    }
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    setStatusMsg('');
    setStatusType('');

    if (!workerId.trim()) {
      setStatusMsg('Please enter a Worker ID.');
      setStatusType('error');
      return;
    }

    if (!imageBase64) {
      setStatusMsg('Please capture a face photo first.');
      setStatusType('error');
      return;
    }

    setLoading(true);
    try {
      const enrolledWorkerId = workerId.trim();
      await enrollWorker(apiKey, enrolledWorkerId, imageBase64);
      setStatusMsg(`✅ Worker ${enrolledWorkerId} enrolled`);
      setStatusType('success');
      
      // Reset form inputs except worker ID for ease of use (optional, but reset here)
      setPreviewUrl(null);
      setImageBase64('');
    } catch (err) {
      setStatusMsg(`Error: ${err.message || 'Failed to enroll worker.'}`);
      setStatusType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="enroll-container">
      <div className="card enroll-card">
        <h3>Enroll New Worker</h3>
        
        <form onSubmit={handleEnroll}>
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

          {statusMsg && (
            <div className={`status-banner ${statusType === 'success' ? 'status-success' : 'status-error'}`}>
              {statusMsg}
            </div>
          )}

          <button
            id="enrollWorkerBtn"
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading || !workerId.trim() || !imageBase64}
          >
            {loading ? 'Enrolling worker...' : 'Enroll Worker'}
          </button>
        </form>
      </div>
    </div>
  );
}
