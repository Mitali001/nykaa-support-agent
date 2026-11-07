"""Smoke tests for the browser dashboard and its read-model endpoints."""
import unittest

try:
    from fastapi.testclient import TestClient
    from api.main import app
    CLIENT_AVAILABLE = True
except Exception:
    CLIENT_AVAILABLE = False


@unittest.skipUnless(CLIENT_AVAILABLE, "Install requirements.txt to test the FastAPI UI")
class DashboardApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dashboard_is_served(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nykaa Support Studio', response.text)

    def test_dashboard_data_endpoints(self):
        for path in ['/api/dashboard', '/api/orders', '/api/knowledge', '/api/evaluation', '/api/rag-report', '/api/demos', '/api/logs']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_order_detail_contains_escalation(self):
        response = self.client.get('/api/orders/NYK0001')
        self.assertEqual(response.status_code, 200)
        self.assertIn('escalation_score', response.json())

    def test_chat_api(self):
        response = self.client.post('/ask', json={'query': 'What is the return window for Beauty products?', 'session_id': 'ui-test'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['answer'])


if __name__ == '__main__':
    unittest.main()
