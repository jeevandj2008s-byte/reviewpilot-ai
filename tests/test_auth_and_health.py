"""
ReviewPilot AI - Auth & Health Integration Test Suite
Verifies core system health, Supabase authentication endpoints,
request timing middleware, and input validation schemas.
"""
import unittest
from fastapi.testclient import TestClient

from backend.main import app

class TestAuthAndHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Verify GET /health returns 200 OK and expected payload."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "ReviewPilot")
        self.assertIn("version", data)
        self.assertIn("environment", data)
        # Verify X-Process-Time header is present and populated
        self.assertIn("x-process-time", response.headers)

    def test_02_supabase_config_endpoint(self):
        """Verify GET /api/auth/supabase/config returns status and configuration keys."""
        response = self.client.get("/api/auth/supabase/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("configured", data)
        self.assertIn("supabase_url", data)
        self.assertIn("supabase_anon_key", data)

    def test_03_supabase_signout_endpoint(self):
        """Verify POST /api/auth/supabase/signout handles token revocation gracefully."""
        response = self.client.post("/api/auth/supabase/signout")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("revoked", data)

    def test_04_supabase_signup_validation(self):
        """Verify POST /api/auth/supabase/signup validates missing email/password."""
        response = self.client.post("/api/auth/supabase/signup", json={
            "email": "",
            "password": "",
            "full_name": "Test User"
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_05_supabase_signin_validation(self):
        """Verify POST /api/auth/supabase/signin validates missing identifier/password."""
        response = self.client.post("/api/auth/supabase/signin", json={
            "identifier": "",
            "password": ""
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_06_root_index_serving(self):
        """Verify GET / serves ReviewPilot HTML landing page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ReviewPilot", response.text)

if __name__ == "__main__":
    unittest.main()
