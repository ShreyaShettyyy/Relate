"""
Instacart Apriori Market Basket Analysis Model Training.
Trains an Apriori model on processed Instacart transaction baskets,
generates frequent itemsets and association rules (Support, Confidence, Lift),
performs train/validation evaluation, and saves serialized artifacts to ml/saved_models/.

Execution command:
    python -m ml.train_model
"""

import json
import time
import pickle
import random
from pathlib import Path
import pandas as pd
import numpy as np

from config.config import PROCESSED_DATA_DIR, SAVED_MODELS_DIR
from ml.preprocessing import run_preprocessing_pipeline
from ml.association_rules import (
    build_sparse_basket_matrix,
    mine_frequent_itemsets,
    extract_association_rules,
    format_rules_for_export,
    evaluate_rules_on_validation_baskets,
)


def load_or_generate_baskets():
    """Load preprocessed transaction baskets or trigger preprocessing pipeline if missing."""
    baskets_file = PROCESSED_DATA_DIR / "order_baskets.json"
    freq_file = PROCESSED_DATA_DIR / "product_frequencies.csv"
    
    if not baskets_file.exists() or not freq_file.exists():
        print("Processed baskets not found. Launching preprocessing pipeline...")
        baskets, df_freq, _ = run_preprocessing_pipeline()
        return baskets, df_freq
        
    print(f"Loading processed transaction baskets from {baskets_file}...")
    with open(baskets_file, "r", encoding="utf-8") as f:
        baskets = json.load(f)
        
    df_freq = pd.read_csv(freq_file)
    print(f"Loaded {len(baskets)} transaction baskets and {len(df_freq)} product frequency records.")
    return baskets, df_freq


def train_instacart_apriori(
    min_support: float = 0.008,
    min_confidence: float = 0.10,
    min_lift: float = 1.10,
    train_split_ratio: float = 0.80,
    random_seed: int = 42
):
    """
    Train and evaluate the Apriori Association Rule model on the Instacart dataset.
    """
    total_start_time = time.time()
    print("=" * 80)
    print("INSTACART APRIORI MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 80)
    
    # 1. Load Data
    baskets, df_freq = load_or_generate_baskets()
    total_baskets_count = len(baskets)
    unique_products_in_baskets = len(set(p for b in baskets for p in b))
    
    # 2. Train / Validation Split
    print(f"\n[Split] Splitting {total_baskets_count} baskets into {int(train_split_ratio*100)}% Train and {int((1-train_split_ratio)*100)}% Validation...")
    random.seed(random_seed)
    shuffled_baskets = list(baskets)
    random.shuffle(shuffled_baskets)
    
    split_idx = int(len(shuffled_baskets) * train_split_ratio)
    train_baskets = shuffled_baskets[:split_idx]
    val_baskets = shuffled_baskets[split_idx:]
    print(f"Train Baskets: {len(train_baskets)} | Validation Baskets: {len(val_baskets)}")
    
    # 3. Build Sparse Transaction Representation
    print("\n[Encoding] Building memory-efficient sparse transaction matrix for training baskets...")
    t_enc_start = time.time()
    df_train_sparse, feature_columns = build_sparse_basket_matrix(train_baskets)
    enc_duration = round(time.time() - t_enc_start, 2)
    print(f"Sparse Matrix Created: {df_train_sparse.shape[0]} transactions × {df_train_sparse.shape[1]} items ({enc_duration}s).")
    
    # 4. Apriori Frequent Itemsets
    print(f"\n[Apriori] Mining frequent itemsets with min_support = {min_support} ({min_support*100:.2f}% of orders)...")
    t_apriori_start = time.time()
    frequent_itemsets = mine_frequent_itemsets(df_train_sparse, min_support=min_support)
    apriori_duration = round(time.time() - t_apriori_start, 2)
    total_itemsets = len(frequent_itemsets)
    print(f"Discovered {total_itemsets} frequent itemsets in {apriori_duration}s.")
    
    if frequent_itemsets.empty:
        raise ValueError("No frequent itemsets met the minimum support threshold. Try lowering min_support.")
        
    # 5. Association Rule Extraction
    print(f"\n[Rules] Extracting association rules with min_lift = {min_lift} and min_confidence = {min_confidence}...")
    t_rules_start = time.time()
    raw_rules = extract_association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
    
    # Filter by confidence threshold
    rules = raw_rules[raw_rules['confidence'] >= min_confidence].copy()
    rules_duration = round(time.time() - t_rules_start, 2)
    total_rules = len(rules)
    print(f"Extracted {total_rules} strong association rules in {rules_duration}s.")
    
    # 6. Evaluation on Validation Set
    print("\n[Evaluation] Validating association rules against unseen validation baskets...")
    t_eval_start = time.time()
    eval_metrics = evaluate_rules_on_validation_baskets(rules, val_baskets, max_eval=10000)
    eval_duration = round(time.time() - t_eval_start, 2)
    print(f"Validation completed in {eval_duration}s.")
    print(f" - Validation Baskets Tested: {eval_metrics['validation_baskets_tested']}")
    print(f" - Antecedent Trigger Rate: {eval_metrics['antecedent_trigger_rate']}% of baskets matched a rule")
    print(f" - Consequent Hit Precision: {eval_metrics['rule_validation_precision']}%")
    print(f" - Mean Training Confidence: {eval_metrics['mean_training_confidence']}")
    print(f" - Mean Training Lift: {eval_metrics['mean_training_lift']} (Max: {eval_metrics['max_lift']})")
    
    # 7. Format and Save Artifacts
    print(f"\n[Persistence] Saving model artifacts and metadata to {SAVED_MODELS_DIR}...")
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    formatted_rules = format_rules_for_export(rules)
    
    # Artifact paths
    itemsets_pkl_path = SAVED_MODELS_DIR / "instacart_frequent_itemsets.pkl"
    rules_pkl_path = SAVED_MODELS_DIR / "instacart_rules.pkl"
    rules_csv_path = SAVED_MODELS_DIR / "instacart_rules.csv"
    meta_json_path = SAVED_MODELS_DIR / "model_metadata.json"
    
    # Save pickles
    with open(itemsets_pkl_path, "wb") as f:
        pickle.dump(frequent_itemsets, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    with open(rules_pkl_path, "wb") as f:
        pickle.dump(rules, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    # Save human-readable CSV of ranked rules
    formatted_rules.to_csv(rules_csv_path, index=False)
    
    total_training_duration = round(time.time() - total_start_time, 2)
    
    # Save comprehensive metadata
    model_metadata = {
        "model_name": "Instacart Apriori Market Basket Analysis",
        "algorithm": "Apriori & Association Rule Mining (MLxtend)",
        "training_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "training_duration_seconds": total_training_duration,
        "parameters": {
            "min_support": min_support,
            "min_confidence": min_confidence,
            "min_lift": min_lift,
            "train_split_ratio": train_split_ratio,
            "random_seed": random_seed
        },
        "dataset_statistics": {
            "total_baskets": total_baskets_count,
            "train_baskets": len(train_baskets),
            "validation_baskets": len(val_baskets),
            "unique_products": unique_products_in_baskets,
            "sparse_matrix_shape": list(df_train_sparse.shape)
        },
        "training_results": {
            "frequent_itemsets_count": total_itemsets,
            "association_rules_count": total_rules,
            "top_rules": formatted_rules[['antecedents_str', 'consequents_str', 'support', 'confidence', 'lift']].head(10).to_dict(orient="records")
        },
        "evaluation": eval_metrics,
        "evaluation_methodology_and_limitations": (
            "Market Basket Analysis discovers directional co-occurrence patterns (if Antecedent -> Consequent). "
            "Unlike supervised classification with accuracy/F1-scores, association rules measure statistical dependence: "
            "Support P(A & B), Confidence P(B|A), and Lift P(B|A)/P(B). "
            "Validation evaluates whether Antecedent conditions trigger on unseen baskets and if Consequents co-occur. "
            "Limitations include sensitivity to support thresholds and inability to detect causal substitution effects."
        ),
        "artifact_files": {
            "frequent_itemsets_pkl": str(itemsets_pkl_path.name),
            "association_rules_pkl": str(rules_pkl_path.name),
            "association_rules_csv": str(rules_csv_path.name),
            "metadata_json": str(meta_json_path.name)
        }
    }
    
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=4)
        
    # 8. Print Formal Training Report
    print("\n" + "=" * 80)
    print("                     INSTACART MODEL TRAINING REPORT")
    print("=" * 80)
    print(f" Total Orders Processed : {total_baskets_count:,} multi-item baskets")
    print(f" Total Unique Products  : {unique_products_in_baskets:,}")
    print(f" Total Transactions     : {len(train_baskets):,} training baskets ({len(val_baskets):,} validation)")
    print(f" Total Frequent Itemsets: {total_itemsets:,}")
    print(f" Total Association Rules: {total_rules:,}")
    print(f" Minimum Support        : {min_support} ({min_support*100:.2f}%)")
    print(f" Minimum Confidence     : {min_confidence} ({min_confidence*100:.2f}%)")
    print(f" Minimum Lift Threshold : {min_lift}")
    print(f" Validation Precision   : {eval_metrics['rule_validation_precision']}%")
    print(f" Total Training Duration: {total_training_duration} seconds")
    print(f" Model Output Location  : {SAVED_MODELS_DIR}")
    print("=" * 80)
    
    print("\n[Top 5 Mined Association Rules by Lift]:")
    for idx, r in enumerate(formatted_rules.head(5).itertuples(), 1):
        print(f" {idx}. [{r.antecedents_str}]  ===>  [{r.consequents_str}]")
        print(f"    Support: {r.support:.4f} | Confidence: {r.confidence:.4f} | Lift: {r.lift:.2f}")
    print("=" * 80 + "\n")
    
    return model_metadata


if __name__ == "__main__":
    train_instacart_apriori()

