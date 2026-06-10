// frontend/src/api.js: API functions for interacting with the face-idp FastAPI backend.

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorMsg = `Error: ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data && data.detail) {
        errorMsg = data.detail;
      }
    } catch (_) {
      // Use general status message if not JSON
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export async function enrollWorker(apiKey, workerId, imageBase64) {
  const response = await fetch(`${BASE_URL}/enroll`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      worker_id: workerId,
      org_api_key: apiKey,
      image_base64: imageBase64
    })
  });
  return handleResponse(response);
}

export async function verifyWorker(apiKey, workerId, imageBase64) {
  const response = await fetch(`${BASE_URL}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      worker_id: workerId,
      org_api_key: apiKey,
      image_base64: imageBase64
    })
  });
  return handleResponse(response);
}

export async function fetchLogs(apiKey) {
  const response = await fetch(`${BASE_URL}/logs?api_key=${encodeURIComponent(apiKey)}`, {
    method: 'GET'
  });
  return handleResponse(response);
}

export async function healthCheck() {
  const response = await fetch(`${BASE_URL}/health`, {
    method: 'GET'
  });
  return handleResponse(response);
}
