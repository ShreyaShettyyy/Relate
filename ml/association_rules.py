"""
Association Rule Mining Module for Market Basket Analysis.
Provides sparse transaction matrix encoding, Apriori frequent itemset discovery,
association rule generation, ranking, and validation evaluation.
"""

import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


def build_sparse_basket_matrix(baskets: list):
    """
    Convert a list of product baskets into a memory-efficient Pandas Sparse DataFrame.
    
    Args:
        baskets: List of lists, e.g. [['Banana', 'Milk'], ['Bread', 'Butter']]
        
    Returns:
        tuple: (df_sparse, feature_names)
    """
    te = TransactionEncoder()
    sparse_matrix = te.fit(baskets).transform(baskets, sparse=True)
    df_sparse = pd.DataFrame.sparse.from_spmatrix(sparse_matrix, columns=te.columns_)
    return df_sparse, te.columns_


def mine_frequent_itemsets(df_sparse, min_support: float = 0.01):
    """
    Run Apriori algorithm on sparse DataFrame to find all itemsets with support >= min_support.
    """
    frequent_itemsets = apriori(df_sparse, min_support=min_support, use_colnames=True)
    return frequent_itemsets


def extract_association_rules(frequent_itemsets, metric: str = "lift", min_threshold: float = 1.1):
    """
    Generate association rules from frequent itemsets using the specified metric and threshold.
    """
    if frequent_itemsets is None or frequent_itemsets.empty:
        return pd.DataFrame()
    rules = association_rules(frequent_itemsets, metric=metric, min_threshold=min_threshold)
    return rules


def format_rules_for_export(rules_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a clean, serializable copy of the rules DataFrame with frozensets converted to readable strings.
    """
    if rules_df is None or rules_df.empty:
        return pd.DataFrame()
    
    export_df = rules_df.copy()
    export_df['antecedents_str'] = export_df['antecedents'].apply(lambda x: ', '.join(sorted(list(x))))
    export_df['consequents_str'] = export_df['consequents'].apply(lambda x: ', '.join(sorted(list(x))))
    export_df['antecedent_len'] = export_df['antecedents'].apply(len)
    export_df['consequent_len'] = export_df['consequents'].apply(len)
    
    # Sort by composite importance: Lift * Confidence * Support
    export_df['score'] = export_df['lift'] * export_df['confidence'] * export_df['support']
    export_df = export_df.sort_values(by=['lift', 'confidence', 'support'], ascending=[False, False, False])
    return export_df


def evaluate_rules_on_validation_baskets(rules_df: pd.DataFrame, validation_baskets: list, max_eval: int = 5000) -> dict:
    """
    Evaluate discovered association rules against unseen validation baskets.
    
    Measures:
    1. Antecedent Trigger Rate: Fraction of validation baskets containing at least one rule antecedent.
    2. Precision / Success Rate: Fraction of triggered rule instances where the consequent was also in the basket.
    3. Average Confidence & Lift across evaluated rules.
    """
    if rules_df is None or rules_df.empty or not validation_baskets:
        return {
            "validation_baskets_tested": 0,
            "antecedent_match_rate": 0.0,
            "rule_precision": 0.0,
            "note": "No rules or validation baskets available."
        }
    
    eval_baskets = validation_baskets[:max_eval]
    basket_sets = [set(b) for b in eval_baskets]
    
    # Pre-parse rules into (set(antecedent), set(consequent), confidence, lift)
    rule_tuples = []
    for _, row in rules_df.iterrows():
        rule_tuples.append((
            set(row['antecedents']),
            set(row['consequents']),
            row['confidence'],
            row['lift']
        ))
        
    baskets_triggered = 0
    total_antecedent_triggers = 0
    successful_predictions = 0
    
    for b_set in basket_sets:
        has_trigger = False
        for ant, con, conf, lift in rule_tuples:
            if ant.issubset(b_set):
                has_trigger = True
                total_antecedent_triggers += 1
                if con.issubset(b_set):
                    successful_predictions += 1
        if has_trigger:
            baskets_triggered += 1
            
    antecedent_match_rate = baskets_triggered / len(eval_baskets) if eval_baskets else 0.0
    precision = successful_predictions / total_antecedent_triggers if total_antecedent_triggers > 0 else 0.0
    
    return {
        "validation_baskets_tested": len(eval_baskets),
        "baskets_triggered": baskets_triggered,
        "antecedent_trigger_rate": round(antecedent_match_rate * 100, 2),
        "total_rule_activations": total_antecedent_triggers,
        "successful_consequent_predictions": successful_predictions,
        "rule_validation_precision": round(precision * 100, 2),
        "mean_training_confidence": round(float(rules_df['confidence'].mean()), 4),
        "mean_training_lift": round(float(rules_df['lift'].mean()), 4),
        "max_lift": round(float(rules_df['lift'].max()), 4),
    }

