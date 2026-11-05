"""
Machine Learning Package for Relate (LuxStore).
Houses the Instacart Market Basket Analysis preprocessing pipeline,
Apriori training engine, association rule mining, and artifact loaders.
"""

from ml.model_loader import (
    load_trained_instacart_model,
    get_instacart_recommendations,
    get_model_metadata,
)

__all__ = [
    "load_trained_instacart_model",
    "get_instacart_recommendations",
    "get_model_metadata",
]

