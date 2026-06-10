# demo/test_zepiris_client.py: Unit tests for ZepIris client service.

import sys
import os
import unittest
from unittest.mock import AsyncMock, patch
import urllib.error

# Ensure project root directory is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import zepiris_client

class TestZepirisClient(unittest.IsolatedAsyncioTestCase):
    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_enroll_face(self, mock_post):
        # Setup mock response
        mock_post.return_value = '{"success": true, "id": "test-worker-001"}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.enroll_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertEqual(result, {"success": True, "id": "test-worker-001"})
        mock_post.assert_called_once_with(
            "http://mock-zepiris:8080/v1/faces/insert",
            {"id": "test-worker-001", "tenant": "123"},
            {"file": ("face.jpg", b'\x89PNG\r\n\x1a\n', "image/jpeg")}
        )

    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_verify_face_match(self, mock_post):
        # Setup mock response for search returning a match
        mock_post.return_value = '{"matches": [{"id": "test-worker-001", "score": 0.95}, {"id": "test-worker-002", "score": 0.50}]}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertTrue(result["verified"])
        self.assertEqual(result["confidence"], 0.95)
        mock_post.assert_called_once_with(
            "http://mock-zepiris:8080/v1/faces/search",
            {"tenant": "123"},
            {"file": ("face.jpg", b'\x89PNG\r\n\x1a\n', "image/jpeg")}
        )

    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_verify_face_below_threshold(self, mock_post):
        # Setup mock response for search returning match below threshold
        mock_post.return_value = '{"matches": [{"id": "test-worker-001", "score": 0.45}]}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertFalse(result["verified"])
        self.assertEqual(result["confidence"], 0.45)

    @patch("backend.services.zepiris_client._sync_multipart_post", side_effect=urllib.error.URLError("Connection refused"))
    async def test_enroll_face_connection_error(self, mock_post):
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            with self.assertRaises(RuntimeError) as context:
                await zepiris_client.enroll_face("test-worker-001", "iVBORw0KGgo=", "123")
            self.assertIn("Biometric enrollment failed to communicate with ZepIris server", str(context.exception))

    @patch("backend.services.zepiris_client._sync_multipart_post", side_effect=urllib.error.URLError("Connection refused"))
    async def test_verify_face_connection_error(self, mock_post):
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            with self.assertRaises(RuntimeError) as context:
                await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            self.assertIn("Biometric verification failed to communicate with ZepIris server", str(context.exception))

if __name__ == "__main__":
    unittest.main()
