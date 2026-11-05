"""
Instacart Dataset Preprocessing Pipeline for Market Basket Analysis.
Loads the 6 raw Instacart CSVs, handles missing values and types,
merges product/aisle/department hierarchies, combines train and prior order records,
performs product frequency analysis, and exports transaction baskets to data/processed/.
"""

import json
import time
from pathlib import Path
import pandas as pd
import numpy as np

from config.config import RAW_INSTACART_DIR, PROCESSED_DATA_DIR


def load_raw_datasets():
    """
    Load all six raw Instacart CSV files using memory-optimized dtypes.
    
    Files:
    1. aisles.csv
    2. departments.csv
    3. products.csv
    4. orders.csv
    5. order_products__train.csv
    6. order_products__prior.csv
    """
    print("[1/5] Loading raw Instacart CSV files...")
    start_time = time.time()
    
    aisles_path = RAW_INSTACART_DIR / "aisles.csv"
    departments_path = RAW_INSTACART_DIR / "departments.csv"
    products_path = RAW_INSTACART_DIR / "products.csv"
    orders_path = RAW_INSTACART_DIR / "orders.csv"
    train_path = RAW_INSTACART_DIR / "order_products__train.csv"
    prior_path = RAW_INSTACART_DIR / "order_products__prior.csv"
    
    # 1. Aisles
    df_aisles = pd.read_csv(aisles_path, dtype={'aisle_id': np.uint16, 'aisle': 'category'})
    
    # 2. Departments
    df_departments = pd.read_csv(departments_path, dtype={'department_id': np.uint8, 'department': 'category'})
    
    # 3. Products
    df_products = pd.read_csv(
        products_path,
        dtype={
            'product_id': np.uint32,
            'product_name': str,
            'aisle_id': np.uint16,
            'department_id': np.uint8
        }
    )
    
    # 4. Orders
    df_orders = pd.read_csv(
        orders_path,
        dtype={
            'order_id': np.uint32,
            'user_id': np.uint32,
            'eval_set': 'category',
            'order_number': np.uint16,
            'order_dow': np.uint8,
            'order_hour_of_day': np.uint8,
            'days_since_prior_order': np.float32
        }
    )
    
    # Handle missing values: first orders have NaN for days_since_prior_order
    df_orders['days_since_prior_order'] = df_orders['days_since_prior_order'].fillna(0.0).astype(np.float32)
    
    # 5. Train order products (131,209 orders, ~1.38M records)
    df_train_lines = pd.read_csv(
        train_path,
        dtype={
            'order_id': np.uint32,
            'product_id': np.uint32,
            'add_to_cart_order': np.uint8,
            'reordered': np.uint8
        }
    )
    
    load_duration = round(time.time() - start_time, 2)
    print(f"Loaded aisles ({len(df_aisles)}), departments ({len(df_departments)}), "
          f"products ({len(df_products)}), orders ({len(df_orders)}), "
          f"train lines ({len(df_train_lines)}) in {load_duration}s.")
          
    return {
        "aisles": df_aisles,
        "departments": df_departments,
        "products": df_products,
        "orders": df_orders,
        "train_lines": df_train_lines,
        "prior_path": prior_path
    }


def merge_and_enrich_products(df_products, df_aisles, df_departments):
    """Merge products with aisles and departments to form a complete catalog."""
    print("[2/5] Merging product catalog with aisles and departments...")
    enriched = df_products.merge(df_aisles, on='aisle_id', how='left')
    enriched = enriched.merge(df_departments, on='department_id', how='left')
    return enriched


def combine_orders_and_extract_baskets(raw_data, sample_prior_orders=50000, top_products_limit=500):
    """
    Combine train and prior order records without order duplication.
    Extracts transaction baskets filtered to the top most frequent products
    and multi-item baskets (basket length >= 2) for Market Basket Analysis.
    """
    print("[3/5] Combining train and sample prior order records...")
    df_train_lines = raw_data['train_lines']
    prior_path = raw_data['prior_path']
    df_products = raw_data['products']
    
    # Build fast lookup dictionary: product_id -> product_name
    product_map = dict(zip(df_products['product_id'], df_products['product_name']))
    
    # Use all train orders (~131,209 orders)
    combined_lines = [df_train_lines]
    
    # Sample additional representative orders from prior (~50,000 orders) chunk-by-chunk for memory safety
    if sample_prior_orders and sample_prior_orders > 0 and prior_path.exists():
        print(f"Sampling up to {sample_prior_orders} orders from order_products__prior.csv...")
        chunks = []
        rows_target = sample_prior_orders * 10  # ~10 items per basket on average
        
        for chunk in pd.read_csv(
            prior_path,
            chunksize=250000,
            dtype={'order_id': np.uint32, 'product_id': np.uint32, 'add_to_cart_order': np.uint8, 'reordered': np.uint8}
        ):
            chunks.append(chunk)
            if sum(len(c) for c in chunks) >= rows_target:
                break
                
        if chunks:
            sample_prior = pd.concat(chunks, ignore_index=True)
            # Ensure no order_id collisions with train
            train_order_ids = set(df_train_lines['order_id'].unique())
            sample_prior = sample_prior[~sample_prior['order_id'].isin(train_order_ids)]
            # Restrict to desired unique order count
            unique_sampled_orders = sample_prior['order_id'].unique()[:sample_prior_orders]
            sample_prior = sample_prior[sample_prior['order_id'].isin(unique_sampled_orders)]
            combined_lines.append(sample_prior)
            print(f"Added {len(sample_prior)} lines from {len(unique_sampled_orders)} prior orders.")
            
    df_all_lines = pd.concat(combined_lines, ignore_index=True)
    
    # Deduplicate exact line items if any
    initial_len = len(df_all_lines)
    df_all_lines = df_all_lines.drop_duplicates(subset=['order_id', 'product_id'])
    duplicates_removed = initial_len - len(df_all_lines)
    
    total_orders = df_all_lines['order_id'].nunique()
    total_records = len(df_all_lines)
    print(f"Total combined order lines: {total_records} across {total_orders} unique orders (duplicates dropped: {duplicates_removed}).")
    
    # Frequency analysis
    print(f"[4/5] Performing product frequency analysis (filtering to top {top_products_limit} products)...")
    product_counts = df_all_lines['product_id'].value_counts()
    
    top_pids = set(product_counts.head(top_products_limit).index)
    filtered_lines = df_all_lines[df_all_lines['product_id'].isin(top_pids)]
    
    # Group products by order_id
    grouped_baskets = filtered_lines.groupby('order_id')['product_id'].apply(list)
    
    # Convert product_ids to names and retain only multi-item baskets (len >= 2)
    named_baskets = []
    for b in grouped_baskets:
        if len(b) >= 2:
            named_basket = [product_map[pid] for pid in b if pid in product_map]
            if len(named_basket) >= 2:
                named_baskets.append(named_basket)
                
    print(f"Generated {len(named_baskets)} valid multi-item baskets for Apriori modeling.")
    
    # Frequency DataFrame
    freq_data = []
    for pid, count in product_counts.head(top_products_limit).items():
        name = product_map.get(pid, f"Product {pid}")
        support = round(count / total_orders, 5)
        freq_data.append({
            "product_id": int(pid),
            "product_name": name,
            "order_count": int(count),
            "sample_support": float(support)
        })
    df_frequencies = pd.DataFrame(freq_data)
    
    return named_baskets, df_frequencies, {
        "total_combined_records": total_records,
        "total_unique_orders": total_orders,
        "duplicates_removed": duplicates_removed,
        "top_products_evaluated": top_products_limit,
        "multi_item_baskets_count": len(named_baskets),
    }


def save_processed_artifacts(named_baskets, df_frequencies, df_enriched_catalog, stats):
    """Save processed datasets and metadata to data/processed/."""
    print("[5/5] Saving processed artifacts to data/processed/...")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Product Frequencies
    freq_csv_path = PROCESSED_DATA_DIR / "product_frequencies.csv"
    df_frequencies.to_csv(freq_csv_path, index=False)
    
    # 2. Enriched Instacart Products Catalog
    catalog_path = PROCESSED_DATA_DIR / "instacart_products_catalog.csv"
    df_enriched_catalog.to_csv(catalog_path, index=False)
    
    # 3. Transaction Baskets (Compressed JSON)
    baskets_path = PROCESSED_DATA_DIR / "order_baskets.json"
    with open(baskets_path, "w", encoding="utf-8") as f:
        json.dump(named_baskets, f)
        
    # 4. Preprocessing Metadata
    meta_path = PROCESSED_DATA_DIR / "preprocessing_metadata.json"
    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": "Instacart Market Basket Analysis",
        "raw_data_dir": str(RAW_INSTACART_DIR),
        "processed_data_dir": str(PROCESSED_DATA_DIR),
        "statistics": stats,
        "top_5_products": df_frequencies.head(5).to_dict(orient="records"),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Artifacts successfully written to {PROCESSED_DATA_DIR}:")
    print(f" - {freq_csv_path.name}")
    print(f" - {catalog_path.name}")
    print(f" - {baskets_path.name} ({len(named_baskets)} baskets)")
    print(f" - {meta_path.name}")
    return metadata


def run_preprocessing_pipeline(sample_prior_orders=50000, top_products_limit=350):
    """Execute complete data preprocessing pipeline."""
    print("=" * 70)
    print("STARTING INSTACART DATASET PREPROCESSING PIPELINE")
    print("=" * 70)
    t0 = time.time()
    
    raw = load_raw_datasets()
    enriched_catalog = merge_and_enrich_products(raw['products'], raw['aisles'], raw['departments'])
    named_baskets, df_freq, stats = combine_orders_and_extract_baskets(
        raw,
        sample_prior_orders=sample_prior_orders,
        top_products_limit=top_products_limit
    )
    meta = save_processed_artifacts(named_baskets, df_freq, enriched_catalog, stats)
    
    total_time = round(time.time() - t0, 2)
    print("=" * 70)
    print(f"PREPROCESSING COMPLETED SUCCESSFULLY in {total_time}s.")
    print("=" * 70)
    return named_baskets, df_freq, meta


if __name__ == "__main__":
    run_preprocessing_pipeline()

