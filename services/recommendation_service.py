"""
Recommendation Service for Relate (LuxStore).
Implements Market Basket Analysis via Apriori, Association Rule Mining,
Personal & Community Co-Purchase Mining, Granular Hardware & Lifestyle Compatibility Mapping,
Category-Consistent Content Similarity, and Cross-Category Collaborative Discovery.
"""

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)


class RecommenderSystem:
    def __init__(self, transactions_df, products_df=None):
        self.transactions_df = transactions_df
        self.products_df = products_df
        self.frequent_itemsets = None
        self.rules = None
        self.content_sim_matrix = None
        self.product_indices = {}
        
        if self.products_df is not None:
            self._build_content_similarity()

    def set_products_df(self, products_df):
        self.products_df = products_df
        self._build_content_similarity()

    def _build_content_similarity(self):
        """Construct TF-IDF cosine similarity matrix across product attributes."""
        if self.products_df is None or self.products_df.empty:
            return
            
        self.product_indices = {name: idx for idx, name in enumerate(self.products_df['Name'])}
        
        # Combine Category, Name, and Description
        corpus = (
            self.products_df['Category'].fillna('') + ' ' +
            self.products_df['Name'].fillna('') + ' ' +
            self.products_df['Name'].fillna('') + ' ' +
            self.products_df['Description'].fillna('')
        )
        
        tfidf = TfidfVectorizer(stop_words='english', max_features=1200)
        tfidf_matrix = tfidf.fit_transform(corpus)
        self.content_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    def _prepare_market_basket_data(self):
        """Transform transactions into one-hot basket matrix."""
        basket = (self.transactions_df
                  .groupby(['TransactionID', 'Item'])['Item']
                  .count().unstack().reset_index().fillna(0)
                  .set_index('TransactionID'))
        return basket > 0

    def train_market_basket(self, min_support=0.001, min_threshold=0.1):
        """Train Apriori and generate association rules."""
        try:
            basket_sets = self._prepare_market_basket_data()
            self.frequent_itemsets = apriori(basket_sets, min_support=min_support, use_colnames=True)
            if self.frequent_itemsets.empty:
                print("No frequent itemsets found.")
                self.rules = None
                return
            self.rules = association_rules(self.frequent_itemsets, metric="lift", min_threshold=min_threshold)
            print(f"Apriori model trained successfully. Rules found: {len(self.rules)}")
        except Exception as e:
            print("Error training Apriori model:", e)
            self.rules = None

    # --------------------------------------------------------------------------
    # GRANULAR DOMAIN & SUBCATEGORY CLASSIFICATION
    # --------------------------------------------------------------------------
    def _detect_subcategory(self, item_name, category=""):
        name_lower = str(item_name).lower()
        cat_lower = str(category).lower()
        
        # 1. Tech Devices & Accessories
        if any(k in name_lower for k in ['iphone', 'galaxy', 'oppo', 'vivo', 'realme']) and not any(k in name_lower for k in ['case', 'charger', 'stand', 'protector', 'cable', 'power bank']):
            return 'smartphone_device'
        if any(k in name_lower for k in ['case', 'screen protector', 'wall charger', 'fast charging cable', 'power bank', 'phone stand', 'airpod', 'earphone']) and ('phone' in name_lower or 'iphone' in name_lower or 'apple' in name_lower or 'charger' in name_lower or 'ear' in name_lower):
            return 'smartphone_accessory'
            
        if any(k in name_lower for k in ['macbook', 'laptop', 'zenbook', 'yoga', 'xps', 'matebook']) and not any(k in name_lower for k in ['sleeve', 'stand', 'hub', 'mouse', 'keyboard', 'cooling pad']):
            return 'laptop_device'
        if any(k in name_lower for k in ['laptop sleeve', 'laptop stand', 'multiport hub', 'wireless mouse', 'cooling pad', 'mechanical keyboard', 'foldsack no. 1 backpack', 'internal ssd']):
            return 'laptop_accessory'
            
        if any(k in name_lower for k in ['camera', 'alpha 7', 'eos r6', 'x-t5']) and not any(k in name_lower for k in ['tripod', 'sdxc', 'lens', 'battery', 'shoulder bag', 'monopod']):
            return 'camera_device'
        if any(k in name_lower for k in ['tripod', 'sdxc', 'zoom lens', 'battery pack', 'shoulder bag', 'monopod']) and ('camera' in name_lower or 'photo' in name_lower or 'lens' in name_lower or 'sdxc' in name_lower or 'tripod' in name_lower):
            return 'camera_accessory'

        # 2. Beauty & Personal Care (Category must be Beauty or name clearly cosmetic)
        if any(k in name_lower for k in ['ck one', "j'adore", 'dolce shine', 'coco noir', 'gucci bloom', 'perfume', 'eau de']):
            return 'beauty_fragrance'
        if any(k in name_lower for k in ['mascara', 'eyeshadow', 'lipstick', 'nail polish', 'powder canister', 'palette', 'powder']) and 'protein' not in name_lower:
            return 'beauty_cosmetics'
        if cat_lower == 'beauty' and any(k in name_lower for k in ['body wash', 'lotion', 'hand soap', 'shampoo']) and 'ice cream' not in name_lower:
            return 'beauty_skincare'

        # 3. Fashion Sub-domains
        if any(k in name_lower for k in ['baseball cap', 'cap']):
            return 'fashion_caps'
        if any(k in name_lower for k in ['sun glasses', 'glasses', 'sunglasses']):
            return 'fashion_sunglasses'
        if any(k in name_lower for k in ['handbag', 'bag']) and any(k in name_lower for k in ['women', 'heshe', 'prada', 'backpack']):
            return 'fashion_handbags'
        if any(k in name_lower for k in ['air jordan', 'cleats', 'future rider', 'sports sneakers', 'vibrant runners', 'high-top sneaker', 'shoes']) and not any(k in name_lower for k in ['heel', 'pump', 'slipper', 'loafer']):
            return 'fashion_sneakers'
        if any(k in name_lower for k in ['heel', 'pump', 'slipper', 'loafer']):
            return 'fashion_dress_shoes'
        if any(k in name_lower for k in ['rolex', 'longines', 'leather belt watch', 'watch gold', 'smartwatch', "wrist watch", 'ingenieur']):
            return 'fashion_watches'
        if any(k in name_lower for k in ['white gold', 'petite micropave', 'dragon station', 'pierced owl', 'earring', 'necklace', 'bracelet', 'ring']):
            return 'fashion_jewelry'
        if any(k in name_lower for k in ['joggers', 'sweatpants', 'shorts', 'crew neck t-shirt', 'black t-shirt', 'classic white tee']):
            return 'fashion_activewear'
        if any(k in name_lower for k in ['dress', 'frock', 'gown', 'skirt', 'corset']):
            return 'fashion_womens_clothing'
        if any(k in name_lower for k in ['shirt', 'tshirt', 'jacket', 'suit', 'mens casual', 'men check']):
            return 'fashion_mens_clothing'

        # 4. Home & Kitchen
        if any(k in name_lower for k in ['plant pot', 'showpiece plant']):
            return 'home_plants'
        if any(k in name_lower for k in ['pot with glass', 'pan', 'kitchen sieve', 'plate', 'lunch box', 'spoon', 'cookware', 'toaster']):
            return 'home_kitchen'
        if any(k in name_lower for k in ['bed', 'sofa', 'table lamp', 'african cherry', 'chair', 'armchair', 'furniture']):
            return 'home_furniture'

        # 5. Groceries
        if any(k in name_lower for k in ['milk', 'eggs', 'bread', 'butter', 'coffee', 'tea', 'fruit juice', 'honey jar', 'ice cream']):
            return 'groceries_breakfast'
        if any(k in name_lower for k in ['apple', 'banana', 'kiwi', 'strawberry', 'watermelon', 'orange', 'lemon', 'potatoes', 'pepper', 'cucumber']):
            return 'groceries_produce'
        if any(k in name_lower for k in ['steak', 'beef', 'chicken', 'fish', 'rice', 'oil', 'cat food', 'dog food']):
            return 'groceries_pantry'

        # Fallback to category
        return cat_lower.replace(' ', '_')

    # --------------------------------------------------------------------------
    # 0. PERSONAL CO-PURCHASE HISTORY
    # --------------------------------------------------------------------------
    def get_personal_copurchases(self, customer_id, product_name):
        """
        Finds products that THIS buyer has personally bought together with product_name
        in the same transaction basket.
        Returns list of (item_name, 'You usually buy this product with {product_name}').
        If the buyer has NEVER bought this product with another product, returns [].
        """
        if not customer_id:
            return []

        # Find transactions of THIS customer containing product_name
        user_matches = self.transactions_df[
            (self.transactions_df['CustomerID'] == customer_id) & 
            (self.transactions_df['Item'] == product_name)
        ]
        if user_matches.empty:
            return []

        user_txns = user_matches['TransactionID'].unique()
        companion_rows = self.transactions_df[
            (self.transactions_df['CustomerID'] == customer_id) &
            (self.transactions_df['TransactionID'].isin(user_txns)) &
            (self.transactions_df['Item'] != product_name)
        ]
        if companion_rows.empty:
            return []

        counts = companion_rows['Item'].value_counts()
        results = []
        for item, _ in counts.items():
            results.append((item, f"You usually buy this product with {product_name}"))
        return results

    # --------------------------------------------------------------------------
    # 1. FREQUENTLY BOUGHT TOGETHER (Apriori Market Basket + High Lift)
    # --------------------------------------------------------------------------
    def get_frequently_bought_together(self, item_name, customer_id=None, top_n=4, exclude_items=None):
        """
        1. Frequently Bought Together
        - Uses Apriori association rules (Lift > 1.0, Confidence)
        - Uses transaction co-occurrences across other accounts
        - Excludes items already shown in other rails or personal history
        - Strictly avoids random or incompatible products
        """
        seen = set(exclude_items or [])
        seen.add(item_name)
        results = []

        # Step 1: Apriori Association Rules
        if self.rules is not None and not self.rules.empty:
            # Look for rules where antecedents contains item_name
            matching_rules = self.rules[
                self.rules['antecedents'].apply(lambda ant: item_name in ant)
            ].sort_values(by=['lift', 'confidence'], ascending=[False, False])
            
            for _, r in matching_rules.iterrows():
                for con_item in r['consequents']:
                    if con_item not in seen:
                        results.append((con_item, f"Most people buy this with {item_name}"))
                        seen.add(con_item)
                        if len(results) >= top_n:
                            return results

        # Step 2: Other accounts' transaction co-purchases
        if customer_id:
            other_txns_df = self.transactions_df[self.transactions_df['CustomerID'] != customer_id]
        else:
            other_txns_df = self.transactions_df

        matching_txns = other_txns_df[other_txns_df['Item'] == item_name]['TransactionID'].unique()
        if len(matching_txns) > 0:
            companion_rows = other_txns_df[
                (other_txns_df['TransactionID'].isin(matching_txns)) &
                (~other_txns_df['Item'].isin(seen))
            ]
            counts = companion_rows['Item'].value_counts()
            for item, _ in counts.items():
                if item not in seen:
                    results.append((item, f"Most people buy this with {item_name}"))
                    seen.add(item)
                    if len(results) >= top_n:
                        return results

        # Step 3: Domain-specific companion accessory fallback if still under top_n
        if len(results) < top_n:
            acc_fallback = self.get_recommended_accessories(item_name, customer_id=customer_id, top_n=top_n - len(results), exclude_items=seen)
            for acc_item, _ in acc_fallback:
                if acc_item not in seen:
                    results.append((acc_item, f"Useful accessory for {item_name}"))
                    seen.add(acc_item)
                    if len(results) >= top_n:
                        break

        return results

    # --------------------------------------------------------------------------
    # 2. RECOMMENDED ACCESSORIES (Domain Compatibility Engine)
    # --------------------------------------------------------------------------
    def get_recommended_accessories(self, item_name, customer_id=None, top_n=6, exclude_items=None):
        """
        2. Recommended Accessories
        - Recommends essential add-ons, cables, protective gear, and peripherals
        - EXCLUDES items already in FBT or personal co-purchases!
        - Returns [] for categories without physical accessories (e.g. groceries)
        """
        seen = set(exclude_items or [])
        seen.add(item_name)
        results = []

        subcat = self._detect_subcategory(item_name)
        if self.products_df is None or self.products_df.empty:
            return []

        # Define compatible accessory target subcategories (distinct from competing alternatives)
        target_subcats = []
        if subcat == 'smartphone_device':
            target_subcats = ['smartphone_accessory']
        elif subcat == 'laptop_device':
            target_subcats = ['laptop_accessory']
        elif subcat == 'camera_device':
            target_subcats = ['camera_accessory']
        elif subcat == 'beauty_cosmetics':
            target_subcats = ['beauty_skincare']
        elif subcat == 'beauty_fragrance':
            target_subcats = ['beauty_skincare']
        elif subcat == 'fashion_sneakers':
            target_subcats = ['fashion_caps', 'fashion_activewear']
        elif subcat == 'fashion_dress_shoes':
            target_subcats = ['fashion_handbags', 'fashion_jewelry']
        elif subcat == 'fashion_watches':
            target_subcats = ['fashion_sunglasses', 'fashion_mens_clothing']
        elif subcat == 'fashion_jewelry':
            target_subcats = ['fashion_handbags', 'fashion_sunglasses']
        elif subcat == 'fashion_womens_clothing':
            target_subcats = ['fashion_handbags', 'fashion_jewelry', 'fashion_dress_shoes']
        elif subcat == 'home_plants':
            target_subcats = ['home_plants', 'home_furniture']
        elif subcat == 'home_kitchen':
            target_subcats = ['home_kitchen']
        else:
            return []

        # Find candidates matching target subcategories
        candidates = []
        for _, row in self.products_df.iterrows():
            cand_name = row['Name']
            if cand_name in seen:
                continue
            cand_subcat = self._detect_subcategory(cand_name, row['Category'])
            if cand_subcat in target_subcats:
                candidates.append(row)

        if not candidates:
            return []

        df_cand = pd.DataFrame(candidates).sort_values(by='Rating', ascending=False)
        for _, row in df_cand.iterrows():
            cand_name = row['Name']
            if cand_name not in seen:
                results.append((cand_name, f"Essential accessory for {item_name}"))
                seen.add(cand_name)
                if len(results) >= top_n:
                    break

        return results

    # --------------------------------------------------------------------------
    # 3. SIMILAR PRODUCTS (Direct Competitors in Exact Same Subcategory)
    # --------------------------------------------------------------------------
    def get_similar_products(self, item_name, top_n=6, exclude_items=None):
        """
        3. Similar Products
        Direct competing alternatives strictly within the same subcategory:
        - Laptops only match other Laptops (never bags or mice)
        - Smartphones only match other Smartphones (never cases or chargers)
        - Cameras only match other Cameras (never tripods or lenses)
        - Sneakers only match other Sneakers (never suits or sunglasses)
        - Perfumes only match other Perfumes (never shoes)
        - Watches only match other Watches
        """
        if self.products_df is None or self.products_df.empty:
            return []

        seen = set(exclude_items or [])
        seen.add(item_name)
        results = []

        item_rows = self.products_df[self.products_df['Name'] == item_name]
        category = item_rows['Category'].iloc[0] if not item_rows.empty else ''
        subcat = self._detect_subcategory(item_name, category)

        # Filter catalog strictly to the same subcategory
        same_subcat_prods = []
        for idx, row in self.products_df.iterrows():
            cand_name = row['Name']
            if cand_name in seen:
                continue
            cand_subcat = self._detect_subcategory(cand_name, row['Category'])
            if cand_subcat == subcat:
                same_subcat_prods.append((idx, cand_name, row))

        if not same_subcat_prods:
            return []

        # Rank candidates using TF-IDF cosine similarity within the filtered subcategory
        if self.content_sim_matrix is not None and item_name in self.product_indices:
            query_idx = self.product_indices[item_name]
            scored_candidates = []
            for cand_idx, cand_name, row in same_subcat_prods:
                sim_score = self.content_sim_matrix[query_idx, cand_idx]
                scored_candidates.append((cand_name, sim_score, row['Rating']))
                
            # Sort by similarity score descending, then rating
            scored_candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
            for cand_name, _, _ in scored_candidates:
                if cand_name not in seen:
                    results.append((cand_name, f"Alternative to {item_name}"))
                    seen.add(cand_name)
                    if len(results) >= top_n:
                        return results
        else:
            # Fallback: sort by rating
            same_subcat_prods.sort(key=lambda x: x[2]['Rating'], reverse=True)
            for _, cand_name, _ in same_subcat_prods:
                if cand_name not in seen:
                    results.append((cand_name, f"Similar to {item_name}"))
                    seen.add(cand_name)
                    if len(results) >= top_n:
                        return results

        return results

    # --------------------------------------------------------------------------
    # 4. YOU MAY ALSO LIKE (Cross-Category Collaborative Discovery)
    # --------------------------------------------------------------------------
    def get_you_may_also_like(self, item_name, customer_id=None, top_n=6, exclude_items=None):
        """
        4. You May Also Like
        Cross-category collaborative discovery:
        - Curated lifestyle pairings matching the shopper persona
        - ZERO repetition of items in FBT, Accessories, or Similar Products
        """
        seen = set(exclude_items or [])
        seen.add(item_name)
        results = []

        subcat = self._detect_subcategory(item_name)
        if self.products_df is None or self.products_df.empty:
            return []

        # Determine complementary lifestyle target subcategories
        if subcat in ['smartphone_device', 'laptop_device', 'camera_device', 'smartphone_accessory', 'laptop_accessory', 'camera_accessory']:
            lifestyle_targets = ['fashion_watches', 'fashion_sneakers', 'home_plants', 'beauty_fragrance']
        elif subcat in ['fashion_sneakers', 'fashion_dress_shoes', 'fashion_clothing']:
            lifestyle_targets = ['fashion_watches', 'fashion_jewelry', 'beauty_fragrance', 'smartphone_accessory']
        elif subcat in ['fashion_watches', 'fashion_jewelry']:
            lifestyle_targets = ['beauty_fragrance', 'fashion_clothing', 'fashion_sneakers', 'smartphone_accessory']
        elif subcat in ['beauty_fragrance', 'beauty_cosmetics', 'beauty_skincare']:
            lifestyle_targets = ['fashion_jewelry', 'fashion_watches', 'home_plants', 'beauty_skincare']
        elif subcat in ['home_plants', 'home_kitchen', 'home_furniture']:
            lifestyle_targets = ['home_furniture', 'home_plants', 'beauty_fragrance', 'fashion_watches']
        else:
            lifestyle_targets = ['fashion_watches', 'beauty_fragrance', 'home_plants', 'smartphone_accessory']

        # Find top-rated items matching lifestyle targets
        candidates = []
        for _, row in self.products_df.iterrows():
            cand_name = row['Name']
            if cand_name in seen:
                continue
            cand_subcat = self._detect_subcategory(cand_name, row['Category'])
            if cand_subcat in lifestyle_targets:
                candidates.append(row)

        if not candidates:
            # General top-rated discovery fallback
            df_fallback = self.products_df[~self.products_df['Name'].isin(seen)].sort_values(by='Rating', ascending=False)
            for cand_name in df_fallback['Name']:
                results.append((cand_name, f"Trending recommendation for you"))
                seen.add(cand_name)
                if len(results) >= top_n:
                    break
            return results

        df_cand = pd.DataFrame(candidates).sort_values(by='Rating', ascending=False)
        for _, row in df_cand.iterrows():
            cand_name = row['Name']
            if cand_name not in seen:
                results.append((cand_name, f"Trending with shoppers who viewed {item_name}"))
                seen.add(cand_name)
                if len(results) >= top_n:
                    break

        return results

    # --------------------------------------------------------------------------
    # BUYER'S HOME / PERSONALIZED FEED
    # --------------------------------------------------------------------------
    def get_personalized_feed(self, customer_id, top_n=20):
        """
        Builds the buyer's home feed strictly from their purchase history and transaction co-purchases.
        """
        user_txns = self.transactions_df[self.transactions_df['CustomerID'] == customer_id]
        if user_txns.empty:
            return self.get_guest_feed(top_n)

        past_items = user_txns['Item'].unique().tolist()
        recommendations = []
        seen = set()

        # Priority 1: Personal co-purchases (if buyer bought them together in past orders)
        for past_item in reversed(past_items):
            personal = self.get_personal_copurchases(customer_id, past_item)
            for item, tag in personal:
                if item not in seen:
                    recommendations.append((item, tag))
                    seen.add(item)
                    if len(recommendations) >= top_n:
                        return recommendations

        seen.update(past_items)

        # Priority 2: Other accounts' co-purchases with buyer's past items
        for past_item in reversed(past_items):
            other = self.get_frequently_bought_together(past_item, customer_id=customer_id, top_n=3, exclude_items=seen)
            for item, tag in other:
                if item not in seen:
                    recommendations.append((item, tag))
                    seen.add(item)
                    if len(recommendations) >= top_n:
                        return recommendations

        # Priority 3: Compatible accessories for devices buyer previously bought
        for past_item in reversed(past_items):
            useful = self.get_recommended_accessories(past_item, customer_id=customer_id, top_n=2, exclude_items=seen)
            for item, tag in useful:
                if item not in seen:
                    recommendations.append((item, tag))
                    seen.add(item)
                    if len(recommendations) >= top_n:
                        return recommendations

        return recommendations[:top_n]

    def get_recently_purchased(self, customer_id, top_n=10):
        """
        Returns buyer's past purchases in reverse order (separate from recommendations).
        """
        user_txns = self.transactions_df[self.transactions_df['CustomerID'] == customer_id]
        if user_txns.empty:
            return []
        past_items = user_txns['Item'].drop_duplicates().tolist()
        return list(reversed(past_items))[:top_n]

    def get_guest_feed(self, top_n=20):
        """
        Feed for guest users: finds top co-occurring pairs from actual transactions.
        Only items with real transaction co-occurrences are displayed.
        """
        item_counts = self.transactions_df['Item'].value_counts()
        top_items = item_counts.head(15).index.tolist()

        feed = []
        seen = set()

        for anchor in top_items:
            other = self.get_frequently_bought_together(anchor, customer_id=None, top_n=2, exclude_items=seen)
            for item, tag in other:
                if item not in seen:
                    feed.append((item, tag))
                    seen.add(item)
                    if len(feed) >= top_n:
                        return feed

        return feed[:top_n]


# --------------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------------
def get_product_dict_list(product_names, df_products):
    """Convert list of product names to list of product dicts."""
    res = []
    for name in product_names:
        p_row = df_products[df_products['Name'] == name]
        if not p_row.empty:
            res.append(p_row.iloc[0].to_dict())
    return res


def get_product_dict_list_with_reasons(items_with_reasons, df_products):
    """Convert list of (product_name, reason) tuples to dicts with recommendation_reason."""
    res = []
    for item, reason in items_with_reasons:
        p_row = df_products[df_products['Name'] == item]
        if not p_row.empty:
            p_dict = p_row.iloc[0].to_dict()
            p_dict['recommendation_reason'] = reason
            res.append(p_dict)
    return res
