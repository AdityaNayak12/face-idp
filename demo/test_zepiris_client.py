# demo/test_zepiris_client.py: Unit tests for ZepIris client service.

import sys
import os
import unittest
from unittest.mock import AsyncMock, patch

# Ensure project root directory is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import zepiris_client

class TestZepirisClient(unittest.IsolatedAsyncioTestCase):
    @patch("httpx.AsyncClient.post")
    async def test_enroll_face(self, mock_post):
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.json = lambda: {"success": True, "id": "test-worker-001"}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.enroll_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertEqual(result, {"success": True, "id": "test-worker-001"})
        mock_post.assert_called_once()
        # Verify form data and multipart file arguments
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://mock-zepiris:8080/v1/faces/insert")
        self.assertEqual(kwargs["data"], {"id": "test-worker-001", "tenant": "123"})
        self.assertIn("file", kwargs["files"])

    @patch("httpx.AsyncClient.post")
    async def test_verify_face_match(self, mock_post):
        # Setup mock response for search returning a match
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "matches": [
                {"id": "test-worker-001", "score": 0.95},
                {"id": "test-worker-002", "score": 0.50}
            ]
        }
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertTrue(result["verified"])
        self.assertEqual(result["confidence"], 0.95)

    @patch("httpx.AsyncClient.post")
    async def test_verify_face_below_threshold(self, mock_post):
        # Setup mock response for search returning match below threshold
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "matches": [
                {"id": "test-worker-001", "score": 0.45}
            ]
        }
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertFalse(result["verified"])
        self.assertEqual(result["confidence"], 0.45)

if __name__ == "__main__":
    unittest.main()
