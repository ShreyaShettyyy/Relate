"""
Model Loader for previously trained Instacart Apriori model artifacts.
Loads frequent itemsets, association rules, and metadata from ml/saved_models/
without retraining the dataset.
"""

import json
import pickle
from pathlib import Path
import pandas as pd
from config.config import SAVED_MODELS_DIR

# Cached in-memory model artifacts
_CACHED_ITEMSETS = None
_CACHED_RULES = None
_CACHED_METADATA = None


def load_trained_instacart_model(force_reload: bool = False):
    """
    Load serialized Instacart Apriori model artifacts from disk.
    
    Returns:
        tuple: (frequent_itemsets_df, association_rules_df, metadata_dict)
    """
    global _CACHED_ITEMSETS, _CACHED_RULES, _CACHED_METADATA
    
    if not force_reload and _CACHED_RULES is not None:
        return _CACHED_ITEMSETS, _CACHED_RULES, _CACHED_METADATA
        
    itemsets_path = SAVED_MODELS_DIR / "instacart_frequent_itemsets.pkl"
    rules_path = SAVED_MODELS_DIR / "instacart_rules.pkl"
    meta_path = SAVED_MODELS_DIR / "model_metadata.json"
    
    if not rules_path.exists() or not meta_path.exists():
        raise FileNotFoundError(
            f"Trained Instacart model artifacts not found in {SAVED_MODELS_DIR}. "
            "Please run: python -m ml.train_model"
        )
        
    # Load Itemsets
    if itemsets_path.exists():
        with open(itemsets_path, "rb") as f:
            _CACHED_ITEMSETS = pickle.load(f)
    else:
        _CACHED_ITEMSETS = pd.DataFrame()
        
    # Load Rules
    with open(rules_path, "rb") as f:
        _CACHED_RULES = pickle.load(f)
        
    # Load Metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        _CACHED_METADATA = json.load(f)
        
    return _CACHED_ITEMSETS, _CACHED_RULES, _CACHED_METADATA


def get_model_metadata():
    """Retrieve training configuration and evaluation metadata for the trained model."""
    try:
        _, _, meta = load_trained_instacart_model()
        return meta
    except Exception:
        meta_path = SAVED_MODELS_DIR / "model_metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": "Model has not been trained yet. Run 'python -m ml.train_model'."}


def get_instacart_recommendations(product_name: str, top_n: int = 5) -> list:
    """
    Query the trained Instacart association rules to find companion grocery products.
    
    Args:
        product_name: Query product (e.g. 'Organic Yellow Onion', 'Limes', 'Banana')
        top_n: Number of recommended products to return
        
    Returns:
        list of dicts containing recommendation details (product, confidence, lift, support)
    """
    _, rules, _ = load_trained_instacart_model()
    if rules is None or rules.empty:
        return []
        
    query_lower = product_name.strip().lower()
    matches = []
    
    for _, row in rules.iterrows():
        antecedents = [str(x).lower() for x in row['antecedents']]
        if query_lower in antecedents or any(query_lower in ant for ant in antecedents):
            for con in row['consequents']:
                matches.append({
                    "recommended_product": str(con),
                    "confidence": round(float(row['confidence']), 4),
                    "lift": round(float(row['lift']), 2),
                    "support": round(float(row['support']), 4),
                    "relationship": f"Purchased together with {product_name} (Lift: {row['lift']:.2f})"
                })
                
    # Deduplicate and sort by lift descending
    seen = set()
    deduped = []
    for item in sorted(matches, key=lambda x: (x['lift'], x['confidence']), reverse=True):
        prod = item['recommended_product']
        if prod.lower() != query_lower and prod not in seen:
            seen.add(prod)
            deduped.append(item)
            if len(deduped) >= top_n:
                break
                
    return deduped

