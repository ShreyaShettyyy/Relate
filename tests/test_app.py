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

    def test_08_cross_user_copurchase_and_useful_accessories(self):
        """Test cross-user co-purchase logic and useful accessories without random recommendations."""
        res = self.client.get('/api/product_recs?product=iPhone 13 Pro&customer_id=1102')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('frequently_bought_together', data)
        self.assertIn('recommended_accessories', data)
        # Verify useful accessories exist for mobile devices (e.g. cases/chargers)
        acc_names = [x['Name'] for x in data['recommended_accessories']]
        self.assertTrue(any('Case' in n or 'Charger' in n or 'Screen' in n or 'Stand' in n for n in acc_names))

    def test_09_voice_assistant_add_to_cart(self):
        """Test voice assistant parses add-to-cart query and returns structured action."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Hey Relate, add iPhone 13 Pro to cart'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('reply', data)
        self.assertEqual(data['action']['type'], 'add_to_cart')
        self.assertEqual(data['action']['product_id'], 123)

    def test_10_voice_assistant_event_suggestion(self):
        """Test voice assistant provides occasion-specific product recommendations."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Suggest a gift for a wedding'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('reply', data)
        self.assertGreater(len(data['products']), 0)
        # Should include luxury items like Rolex or jewelry
        names = [p['Name'] for p in data['products']]
        self.assertTrue(any('Rolex' in n or 'Gold' in n or 'Diamond' in n or 'Perfume' in n for n in names))

    def test_11_voice_assistant_navigation_action(self):
        """Test voice assistant handles cart and checkout navigation queries."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Show my cart'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['action']['type'], 'view_cart')

    def test_12_voice_assistant_dresses_collection(self):
        """Test voice assistant returns luxury dress and ethnic collections without unrelated items."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Show me luxury evening dresses'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(len(data.get('products', [])), 0)
        # Verify returned products are relevant garments (dresses, gowns, lehengas, sarees)
        for p in data['products']:
            self.assertIn(p['Category'], ['Fashion', 'Womens Dresses'])
            self.assertTrue(any(w in p['Name'].lower() for w in ['dress', 'gown', 'lehenga', 'saree', 'slip']))

    def test_13_voice_assistant_view_cart_and_order(self):
        """Test voice assistant executes 'view cart and order the product' by displaying cart and triggering checkout."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'View cart and order the product'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['action']['type'], 'checkout')
        self.assertTrue(data['action'].get('show_cart'))

    def test_14_voice_assistant_strict_non_random_matches(self):
        """Test voice assistant strictly avoids random suggestions when a query has no matching product."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Show me alien spaceship and laser blaster'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        # Must return empty products list, never random products
        self.assertEqual(len(data.get('products', [])), 0)

    def test_15_voice_assistant_companion_recommendations_on_cart_add(self):
        """Test voice assistant returns co-purchased companion recommendations when adding an item to cart."""
        res = self.client.post('/api/assistant/chat', json={
            'query': 'Add Midnight Silk Evening Gown to cart',
            'customer_id': 1104
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['action']['type'], 'add_to_cart')
        self.assertEqual(data['action']['product_id'], 277)
        self.assertIn('companion_products', data)
        self.assertGreater(len(data['companion_products']), 0)
        comp_names = [c['Name'] for c in data['companion_products']]
        # Should recommend pairing jewelry or accessories
        self.assertTrue(any('Bracelet' in n or 'Diamond' in n or 'Necklace' in n or 'Bag' in n for n in comp_names))


if __name__ == '__main__':
    unittest.main()

