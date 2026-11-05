"""
Unit & Integration Tests for Instacart Preprocessing & Apriori Machine Learning Model.
Verifies raw datasets, preprocessed artifacts, model artifacts, and model loader queries.
"""

import unittest
from pathlib import Path
from config.config import RAW_INSTACART_DIR, PROCESSED_DATA_DIR, SAVED_MODELS_DIR
from ml.model_loader import (
    load_trained_instacart_model,
    get_instacart_recommendations,
    get_model_metadata,
)


class TestInstacartML(unittest.TestCase):
    def test_01_raw_instacart_files_exist(self):
        """Verify all 6 raw Instacart CSV files are present in data/raw/instacart/."""
        expected_files = [
            "aisles.csv",
            "departments.csv",
            "products.csv",
            "orders.csv",
            "order_products__train.csv",
            "order_products__prior.csv",
        ]
        for fname in expected_files:
            fpath = RAW_INSTACART_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing raw file: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"Raw file is empty: {fname}")

    def test_02_processed_artifacts_exist(self):
        """Verify data/processed/ contains the required preprocessed files."""
        expected_artifacts = [
            "product_frequencies.csv",
            "instacart_products_catalog.csv",
            "order_baskets.json",
            "preprocessing_metadata.json",
        ]
        for fname in expected_artifacts:
            fpath = PROCESSED_DATA_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing processed artifact: {fname}")

    def test_03_saved_model_artifacts_exist(self):
        """Verify ml/saved_models/ contains the serialized model artifacts."""
        expected_models = [
            "instacart_frequent_itemsets.pkl",
            "instacart_rules.pkl",
            "instacart_rules.csv",
            "model_metadata.json",
        ]
        for fname in expected_models:
            fpath = SAVED_MODELS_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing model artifact: {fname}")

    def test_04_model_loader(self):
        """Test model_loader successfully loads artifacts without retraining."""
        itemsets, rules, metadata = load_trained_instacart_model()
        self.assertFalse(itemsets.empty, "Frequent itemsets DataFrame should not be empty")
        self.assertFalse(rules.empty, "Association rules DataFrame should not be empty")
        self.assertIn("training_results", metadata)
        self.assertIn("evaluation", metadata)

    def test_05_instacart_recommendation_query(self):
        """Test querying recommendations for a known grocery item (e.g., Limes)."""
        recs = get_instacart_recommendations("Limes", top_n=3)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0, "Limes should have association rule recommendations")
        first_rec = recs[0]
        self.assertIn("recommended_product", first_rec)
        self.assertIn("lift", first_rec)
        self.assertIn("confidence", first_rec)
        self.assertGreater(first_rec["lift"], 1.0)


if __name__ == '__main__':
    unittest.main()

