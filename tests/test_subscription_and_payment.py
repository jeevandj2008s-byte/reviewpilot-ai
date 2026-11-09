"""
ReviewPilot AI - Subscription & Direct UPI Payment Integration Tests
Verifies official plan pricing (₹299 Pro, ₹899 Enterprise),
UPI payee credentials, UTR validation, and database activation persistence.
"""
import unittest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import init_db, get_user_payments, record_payment

class TestSubscriptionAndPayment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_subscription_plans_endpoint(self):
        """Verify GET /api/subscription/plans returns ₹299 Pro and ₹899 Enterprise."""
        response = self.client.get("/api/subscription/plans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("payee_vpa"), "9741481204@axl")
        self.assertEqual(data.get("payee_name"), "ReviewPilot AI")

        plans = data.get("plans", [])
        self.assertTrue(len(plans) >= 3)

        # Verify Starter Plan
        starter = next((p for p in plans if p["id"] == "starter"), None)
        self.assertIsNotNone(starter)
        self.assertEqual(starter["price"], 0)

        # Verify Professional Plan is ₹299
        pro = next((p for p in plans if p["id"] == "professional"), None)
        self.assertIsNotNone(pro)
        self.assertEqual(pro["price"], 299)
        self.assertTrue(pro["popular"])

        # Verify Enterprise Plan is ₹899
        enterprise = next((p for p in plans if p["id"] == "enterprise"), None)
        self.assertIsNotNone(enterprise)
        self.assertEqual(enterprise["price"], 899)

    def test_02_utr_verification_endpoint(self):
        """Verify POST /api/subscription/verify-utr validates transaction references."""
        # Valid 12-digit UTR
        res_valid = self.client.post("/api/subscription/verify-utr", json={"utr": "412356789012"})
        self.assertEqual(res_valid.status_code, 200)
        self.assertTrue(res_valid.json().get("valid"))

        # Invalid format UTR
        res_invalid_format = self.client.post("/api/subscription/verify-utr", json={"utr": "inv@lid#ref!"})
        self.assertEqual(res_invalid_format.status_code, 200)
        self.assertFalse(res_invalid_format.json().get("valid"))

        # Schema constraint violation (< 4 chars)
        res_schema_err = self.client.post("/api/subscription/verify-utr", json={"utr": "12"})
        self.assertEqual(res_schema_err.status_code, 422)

    def test_03_activate_subscription_validation(self):
        """Verify POST /api/subscription/activate rejects empty/short UTR."""
        response = self.client.post("/api/subscription/activate", json={
            "plan": "professional",
            "plan_name": "Professional Plan",
            "amount": 299,
            "utr_number": "12"
        })
        self.assertEqual(response.status_code, 422)

    def test_04_activate_professional_plan(self):
        """Verify POST /api/subscription/activate confirms Pro activation with ₹299."""
        response = self.client.post("/api/subscription/activate", json={
            "plan": "professional",
            "plan_name": "Professional Plan",
            "amount": 299,
            "utr_number": "412389001122",
            "email": "testpro@reviewpilot.ai"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("plan"), "Professional")
        self.assertEqual(data.get("subscription_status"), "active")
        self.assertTrue(len(data.get("transaction_id", "")) > 0)

        # Check SQLite audit ledger
        payments = get_user_payments(email="testpro@reviewpilot.ai")
        self.assertTrue(len(payments) > 0)
        latest = payments[0]
        self.assertEqual(latest["plan"], "professional")
        self.assertEqual(latest["amount"], 299.0)
        self.assertEqual(latest["utr_number"], "412389001122")

    def test_05_activate_enterprise_plan(self):
        """Verify POST /api/subscription/activate confirms Enterprise activation with ₹899."""
        response = self.client.post("/api/subscription/activate", json={
            "plan": "enterprise",
            "plan_name": "Enterprise Plan",
            "amount": 899,
            "utr_number": "412399887766",
            "email": "testent@reviewpilot.ai"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("plan"), "Enterprise")
        self.assertEqual(data.get("subscription_status"), "active")

    def test_06_unauthenticated_history_fallback(self):
        """Verify GET /api/subscription/history handles unauthenticated guests cleanly."""
        response = self.client.get("/api/subscription/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIsInstance(data.get("payments"), list)

    def test_07_utr_sanitization_with_whitespace_and_hyphens(self):
        """Verify POST /api/subscription/verify-utr sanitizes pasted spaces and dashes."""
        res_spaced = self.client.post("/api/subscription/verify-utr", json={"utr": " 4123-5678-9012 "})
        self.assertEqual(res_spaced.status_code, 200)
        self.assertTrue(res_spaced.json().get("valid"))

    def test_08_activate_with_formatted_utr_normalizes_clean_id(self):
        """Verify POST /api/subscription/activate normalizes and stores clean alphanumeric UTR."""
        email = "formatted_utr_test@reviewpilot.ai"
        response = self.client.post("/api/subscription/activate", json={
            "plan": "professional",
            "plan_name": "Professional Plan",
            "amount": 299,
            "utr_number": " 9988-7766-5544 ",
            "email": email
        })
        self.assertEqual(response.status_code, 200)
        payments = get_user_payments(email=email)
        self.assertTrue(len(payments) > 0)
        self.assertEqual(payments[0]["utr_number"], "998877665544")

    def test_09_official_upi_payee_vpa_consistency(self):
        """Verify strict consistency of official UPI payee ID 9741481204@axl."""
        response = self.client.get("/api/subscription/plans")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("payee_vpa"), "9741481204@axl")

if __name__ == "__main__":
    unittest.main()
