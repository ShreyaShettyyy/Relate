"""
Unit & Integration Tests for Relate (LuxStore) Web Application & API.
Verifies all existing endpoints, authentication, user data, and multi-rail recommendations.
"""

import unittest
from app import app
from config.config import PRODUCTS_FILE, TRANSACTIONS_FILE, USERS_FILE


class TestRelateApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_index_page(self):
        """Test storefront homepage loads successfully."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Relate (LuxStore)', res.data)

    def test_02_metadata_endpoint(self):
        """Test metadata endpoint returns valid catalog & customer data."""
        res = self.client.get('/api/metadata')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('products', data)
        self.assertIn('categories', data)
        self.assertIn('customers', data)
        self.assertGreater(len(data['products']), 0)

    def test_03_guest_feed(self):
        """Test unauthenticated feed returns real transaction co-purchases."""
        res = self.client.get('/api/feed')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data['personalized'])
        self.assertIn('recommendations', data)
        self.assertGreater(len(data['recommendations']), 0)

    def test_04_authenticated_buyer_feed(self):
        """Test customer 1101 feed includes personal and community co-purchases."""
        res = self.client.get('/api/feed?customer_id=1101')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['personalized'])
        self.assertIn('recently_purchased', data)
        self.assertGreater(len(data['recently_purchased']), 0)

    def test_05_product_recommendation_rails(self):
        """Test product recommendation rails for a known product."""
        res = self.client.get('/api/product_recs?product=Calvin Klein CK One&customer_id=1101')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('frequently_bought_together', data)
        self.assertIn('recommended_accessories', data)
        self.assertIn('similar_products', data)
        self.assertIn('you_may_also_like', data)
        self.assertIn('personal_copurchases', data)

    def test_06_unpurchased_item_personal_rail_empty(self):
        """Test that unpurchased item returns empty personal_copurchases (rail hidden)."""
        res = self.client.get('/api/product_recs?product=Apple MacBook Pro&customer_id=1101')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data.get('personal_copurchases', [])), 0)

    def test_07_auth_login_validation(self):
        """Test authentication rejects invalid credentials."""
        res = self.client.post('/api/auth/login', json={'email': 'fake_nonexistent@test.com', 'password': 'wrong'})
        self.assertEqual(res.status_code, 401)


if __name__ == '__main__':
    unittest.main()

