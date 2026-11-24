"""
Voice Assistant Service for Relate (LuxStore).
Provides natural language intent matching, event/occasion product suggestions,
cart voice actions, budget filtering, and conversational shopping guidance.
"""

import re
import pandas as pd
import numpy as np


class VoiceAssistantService:
    def __init__(self, products_df):
        self.products_df = products_df
        self._build_index()

    def set_products_df(self, products_df):
        self.products_df = products_df
        self._build_index()

    def _build_index(self):
        if self.products_df is None or self.products_df.empty:
            self.products_list = []
            return
        
        clean_df = self.products_df.copy()
        clean_df['Name_clean'] = clean_df['Name'].astype(str).str.lower()
        clean_df['Category_clean'] = clean_df['Category'].astype(str).str.lower()
        clean_df['Desc_clean'] = clean_df['Description'].fillna('').astype(str).str.lower()
        
        self.clean_df = clean_df
        self.products_list = self.products_df.replace({float('nan'): None}).to_dict('records')

    # --------------------------------------------------------------------------
    # CURATED OCCASION & EVENT MAPS
    # --------------------------------------------------------------------------
    OCCASION_MAP = {
        'wedding': {
            'keywords': ['wedding', 'marriage', 'bride', 'groom', 'reception', 'engagement'],
            'search_terms': ['rolex', 'dior', 'chanel', 'white gold plated princess', 'solid gold petite', 'bracelet', 'tropical earring', 'longines'],
            'intro': "For a wedding celebration, timeless jewelry, luxury Swiss timepieces, and signature perfumes make cherished gifts."
        },
        'anniversary': {
            'keywords': ['anniversary', 'wedding anniversary'],
            'search_terms': ['rolex datejust', 'white gold plated princess', 'chanel coco noir', 'moss & fern candle', 'annibale colombo'],
            'intro': "To celebrate an anniversary, a classic Rolex watch, heirloom jewelry, or calming botanical fragrances create lasting memories."
        },
        'party': {
            'keywords': ['party', 'night out', 'club', 'celebration', 'festive', 'cocktail'],
            'search_terms': ['nike air jordan', 'calvin klein ck one', 'red lipstick', 'eyeshadow palette', 'rolex submariner', 'futuristic silver and gold'],
            'intro': "For a party or night out, stand out with designer sneakers, statement watches, and bold beauty accents."
        },
        'date': {
            'keywords': ['date', 'romantic', 'dinner date', 'valentine', 'evening date'],
            'search_terms': ['dior j\'adore', 'chanel coco noir', 'calvin klein ck one', 'rolex datejust', 'red lipstick', 'radiant citrus'],
            'intro': "For a romantic date, unforgettable fragrances like Dior J'adore and Chanel Coco Noir paired with refined accessories set the perfect mood."
        },
        'birthday': {
            'keywords': ['birthday', 'bday', 'gift', 'present', 'someone'],
            'search_terms': ['lavender dew essence', 'moss & fern candle', 'apple airpods', 'beats flex', 'anker 10000mah', 'gucci bloom'],
            'intro': "For a birthday gift, our calming botanical candles, wireless audio gear, and signature perfumes are customer favorites."
        },
        'gym_fitness': {
            'keywords': ['gym', 'fitness', 'workout', 'running', 'sports', 'exercise', 'training', 'jogging', 'marathon'],
            'search_terms': ['nike air jordan', 'puma future rider', 'sports sneakers off white', 'classic red sweatpants', 'beats flex wireless', 'apple airpods'],
            'intro': "For fitness and training, high-cushion athletic sneakers, flexible sweatpants, and sweat-resistant wireless earphones keep you energized."
        },
        'work_productivity': {
            'keywords': ['work', 'office', 'study', 'coding', 'programming', 'college', 'desk', 'productivity'],
            'search_terms': ['apple macbook pro', 'new dell xps', 'asus zenbook', 'logitech master 3s', 'foldable aluminum ergonomic laptop stand', '7-in-1 dual usb-c'],
            'intro': "For work, coding, and productivity, pro-tier laptops paired with ergonomic mice and multi-port docks maximize your efficiency."
        },
        'travel_photography': {
            'keywords': ['travel', 'trip', 'vacation', 'photography', 'photo', 'camera', 'hiking', 'outdoor', 'adventure'],
            'search_terms': ['sony alpha 7', 'canon eos r6', 'fujifilm x-t5', 'lightweight camera tripod', 'sandisk 128gb', 'anker 10000mah', 'black sun glasses'],
            'intro': "For travel and photography, mirrorless cameras with fast focus, lightweight tripods, and high-speed memory cards ensure you never miss a shot."
        },
        'home_relaxation': {
            'keywords': ['home', 'housewarming', 'relax', 'decor', 'bedroom', 'cozy', 'calm', 'peaceful', 'living room'],
            'search_terms': ['lavender dew essence', 'moss & fern candle', 'eucalyptus linen mist', 'jade stone incense', 'house showpiece plant', 'table lamp'],
            'intro': "For home serenity and relaxation, our botanical room essences, soy candles, and stone decor craft a peaceful sanctuary."
        },
        'cooking_kitchen': {
            'keywords': ['cooking', 'kitchen', 'cook', 'chef', 'baking'],
            'search_terms': ['silver pot with glass cap', 'pan', 'kitchen sieve', 'efficient 2-slice toaster', 'spoon', 'lunch box'],
            'intro': "For the culinary kitchen, non-stick cookware, stainless pots, and rapid toasters make everyday cooking delightful."
        },
        'breakfast_groceries': {
            'keywords': ['breakfast', 'grocery', 'groceries', 'food', 'morning', 'coffee', 'fruit', 'drink'],
            'search_terms': ['nescafe coffee', 'honey jar', 'juice', 'milk', 'eggs', 'apple', 'strawberry'],
            'intro': "For breakfast, premium roasted coffee, pure honey, rich juices, and fresh orchard fruits start your day right."
        }
    }

    def process_query(self, query_text, current_product=None, current_cart_ids=None):
        """
        Main query handler. Analyzes voice or text input, determines user intent,
        extracts target products / constraints, and returns a rich assistant response.
        """
        if not query_text or not query_text.strip():
            return {
                "reply": "I'm listening! You can ask for gift suggestions, search any category, or say 'Add this product to my cart'.",
                "products": [],
                "action": {"type": "none"}
            }

        q = query_text.strip().lower()
        
        # 1. Strip wake-word prefix if present
        for prefix in ['hey relate', 'hi relate', 'hello relate', 'ok relate', 'okay relate', 'relate']:
            if q.startswith(prefix):
                q = q[len(prefix):].strip(',.! ')
                break

        if not q:
            return {
                "reply": "I'm right here! What would you like to explore or purchase today?",
                "products": [],
                "action": {"type": "none"}
            }

        # 2. Check for Greetings / Identity
        if any(q.startswith(g) or q == g for g in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'who are you', 'what can you do', 'help']):
            return {
                "reply": "Hello! I am Relate AI, your voice shopping concierge. Say 'Hey Relate' anytime or ask me to recommend gifts for an event, find electronics or fashion, or say 'Add to cart'!",
                "products": self._get_featured_products(4),
                "action": {"type": "none"}
            }

        # 3. Check for Direct Cart / Navigation Actions
        # A. View Cart / Show Bag
        if any(k in q for k in ['open cart', 'view cart', 'show cart', 'my cart', 'open bag', 'show bag', 'go to cart', 'what is in my cart']):
            return {
                "reply": "Opening your shopping cart right now.",
                "products": [],
                "action": {"type": "view_cart"}
            }

        # B. Checkout / Payment
        if any(k in q for k in ['checkout', 'proceed to checkout', 'pay now', 'make payment', 'buy now', 'place order']):
            return {
                "reply": "Taking you directly to checkout.",
                "products": [],
                "action": {"type": "checkout"}
            }

        # C. Wishlist / Saved items
        if any(k in q for k in ['wishlist', 'saved items', 'saved products', 'favorites', 'my favorites']):
            return {
                "reply": "Opening your saved wishlist.",
                "products": [],
                "action": {"type": "view_wishlist"}
            }

        # D. Add to Cart Intent (Flexible regex parser)
        add_cart_match = self._parse_add_to_cart_query(q)
        if add_cart_match is not None:
            return self._handle_add_to_cart(add_cart_match, current_product)

        # 4. Check for Occasion & Event Queries
        for occ_key, occ_info in self.OCCASION_MAP.items():
            if any(re.search(r'\b' + re.escape(k) + r'\b', q) for k in occ_info['keywords']):
                matched_products = self._search_by_terms(occ_info['search_terms'], max_results=5)
                top_names = [p['Name'] for p in matched_products[:3]]
                names_speech = ", ".join(top_names)
                speech_reply = f"{occ_info['intro']} I recommend {names_speech}. Here are the best matches for you."
                return {
                    "reply": speech_reply,
                    "products": matched_products,
                    "action": {"type": "none"}
                }

        # 5. Check for Budget / Price Filters
        budget_match = re.search(r'(?:under|below|less than|within|around)\s*(?:rs\.?|inr|₹)?\s*(\d+)', q)
        max_price = int(budget_match.group(1)) if budget_match else None

        # 6. Check for Category Inquiries (e.g. "show laptops", "smartphones", "luxury watches", "shoes")
        cat_match = self._match_category(q)
        if cat_match:
            products = self._filter_by_category(cat_match, max_price=max_price)
            price_clause = f" under ₹{max_price:,}" if max_price else ""
            reply = f"Here are our top {cat_match}{price_clause}. Which one would you like to explore?"
            return {
                "reply": reply,
                "products": products[:6],
                "action": {"type": "navigate_category", "category": cat_match}
            }

        # 7. Specific Product Search by Name or Keywords
        search_results = self._search_products(q, max_price=max_price)
        if search_results:
            top_prod = search_results[0]
            price_fmt = f"₹{int(top_prod['Price']):,}" if top_prod.get('Price') else ""
            if len(search_results) == 1:
                reply = f"I found the {top_prod['Name']} for {price_fmt}. Would you like me to add it to your cart?"
            else:
                reply = f"I found {len(search_results)} items matching '{query_text}', starting with the {top_prod['Name']} for {price_fmt}. Take a look!"
            return {
                "reply": reply,
                "products": search_results[:6],
                "action": {"type": "none"}
            }

        # 8. Friendly Fallback (Never leave user hanging!)
        featured = self._get_featured_products(4)
        return {
            "reply": f"I heard '{query_text}', but couldn't find an exact match in our catalog. Here are some of our most popular recommendations across tech, fashion, and beauty!",
            "products": featured,
            "action": {"type": "none"}
        }

    # --------------------------------------------------------------------------
    # INTENT HELPERS
    # --------------------------------------------------------------------------
    def _parse_add_to_cart_query(self, q):
        """
        Parses variations of 'add [item] to cart' or 'add to cart'.
        Returns extracted item name string or '' if generic 'add to cart'.
        Returns None if not an add-to-cart intent.
        """
        # Discard informational questions asking what/how to buy
        if any(w in q for w in ['what should i buy', 'what to buy', 'should i buy', 'can i buy', 'where to buy', 'how to buy', 'what can i buy']):
            return None

        # Form 1: "add to cart [item]" or "add to bag [item]"
        m1 = re.search(r'\b(?:add|put)\s+(?:to|in)\s+(?:the\s+|my\s+)?(?:cart|bag)\s*(.*)', q)
        if m1:
            return m1.group(1).strip()

        # Form 2: "add [item] to/in cart/bag"
        m2 = re.search(r'\b(?:add|put)\s+(.+?)\s+(?:to|in)\s+(?:the\s+|my\s+)?(?:cart|bag)\b', q)
        if m2:
            return m2.group(1).strip()

        # Form 3: Direct imperative command "buy [item]" or "purchase [item]"
        if q.startswith(('buy ', 'purchase ')):
            sub = re.sub(r'^(?:buy|purchase)\s+', '', q).strip()
            if sub and not sub.startswith(('for ', 'something ', 'a gift ', 'gift ', 'me ')):
                return sub

        return None

    def _handle_add_to_cart(self, target_term, current_product=None):
        target_clean = target_term.lower().strip()

        # If user said "add this" or generic "add to cart" without specifying name
        if target_clean in ['', 'this', 'this item', 'this product', 'it', 'one']:
            if current_product:
                p_id = int(current_product.get('ID', 0))
                p_name = str(current_product.get('Name', 'this item'))
                p_price = int(current_product.get('Price', 0))
                return {
                    "reply": f"I've added {p_name} to your cart for ₹{p_price:,}! Would you like to view your cart or checkout?",
                    "products": [current_product],
                    "action": {
                        "type": "add_to_cart",
                        "product_id": p_id,
                        "product_name": p_name,
                        "price": p_price
                    }
                }
            else:
                return {
                    "reply": "Which product would you like me to add to your cart? You can say 'Add iPhone' or 'Add MacBook Pro'.",
                    "products": self._get_featured_products(4),
                    "action": {"type": "none"}
                }

        # Match specific product name
        matched = self._find_best_match(target_clean)
        if matched:
            p_id = int(matched.get('ID', 0))
            p_name = str(matched.get('Name'))
            p_price = int(matched.get('Price', 0))
            return {
                "reply": f"I've added the {p_name} to your cart for ₹{p_price:,}. Would you like to view your cart or keep browsing?",
                "products": [matched],
                "action": {
                    "type": "add_to_cart",
                    "product_id": p_id,
                    "product_name": p_name,
                    "price": p_price
                }
            }
        
        return {
            "reply": f"I couldn't find a product matching '{target_term}'. Here are some popular products you can add right now.",
            "products": self._get_featured_products(4),
            "action": {"type": "none"}
        }

    def _find_best_match(self, term):
        term_clean = term.lower().strip()
        if not term_clean or self.clean_df is None or self.clean_df.empty:
            return None

        # 1. Exact match on Name
        exact = self.clean_df[self.clean_df['Name_clean'] == term_clean]
        if not exact.empty:
            return self._to_dict(exact.iloc[0])

        # 2. Substring match on Name
        sub = self.clean_df[self.clean_df['Name_clean'].str.contains(re.escape(term_clean), regex=True, na=False)]
        if not sub.empty:
            return self._to_dict(sub.sort_values(by='Rating', ascending=False).iloc[0])

        # 3. Token overlap match
        tokens = [t for t in term_clean.split() if len(t) > 2]
        if tokens:
            best_score = 0
            best_row = None
            for _, row in self.clean_df.iterrows():
                name_words = row['Name_clean'].split()
                score = sum(2 for t in tokens if t in name_words) + sum(1 for t in tokens if any(t in w for w in name_words))
                if score > best_score:
                    best_score = score
                    best_row = row
            if best_score > 0 and best_row is not None:
                return self._to_dict(best_row)

        return None

    def _search_products(self, query, max_price=None):
        q_clean = query.lower().strip()
        tokens = [t for t in q_clean.split() if len(t) > 2 and t not in ['show', 'find', 'best', 'give', 'want', 'need', 'product', 'items', 'under', 'price', 'tell', 'about']]
        if not tokens and self.clean_df is not None:
            tokens = [t for t in q_clean.split() if len(t) > 1]

        results = []
        if self.clean_df is not None and not self.clean_df.empty:
            df = self.clean_df
            if max_price:
                df = df[df['Price'] <= max_price]

            scores = []
            for _, row in df.iterrows():
                score = 0
                for t in tokens:
                    if t in row['Name_clean']:
                        score += 3
                    if t in row['Category_clean']:
                        score += 2
                    if t in row['Desc_clean']:
                        score += 1
                scores.append(score)

            df = df.copy()
            df['Score'] = scores
            matched = df[df['Score'] > 0].sort_values(by=['Score', 'Rating'], ascending=[False, False])
            results = [self._to_dict(r) for _, r in matched.iterrows()]

        return results

    def _search_by_terms(self, terms, max_results=5):
        if self.clean_df is None or self.clean_df.empty:
            return []

        matched_rows = []
        seen_ids = set()

        for term in terms:
            term_lower = term.lower()
            matches = self.clean_df[
                self.clean_df['Name_clean'].str.contains(re.escape(term_lower), regex=True, na=False) |
                self.clean_df['Category_clean'].str.contains(re.escape(term_lower), regex=True, na=False) |
                self.clean_df['Desc_clean'].str.contains(re.escape(term_lower), regex=True, na=False)
            ]
            for _, r in matches.sort_values(by='Rating', ascending=False).iterrows():
                if r['ID'] not in seen_ids:
                    seen_ids.add(r['ID'])
                    matched_rows.append(self._to_dict(r))
                    if len(matched_rows) >= max_results:
                        return matched_rows

        return matched_rows

    def _match_category(self, q):
        cat_map = {
            'smartphones': ['smartphone', 'smartphones', 'phones', 'mobile', 'mobiles'],
            'laptops': ['laptop', 'laptops', 'notebook', 'notebooks', 'computers'],
            'fashion': ['fashion', 'clothes', 'clothing', 'shoes', 'sneakers', 'sweatpants', 'wear'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'lipsticks', 'perfumes', 'fragrances'],
            'home & kitchen': ['home', 'kitchen', 'furniture', 'cookware', 'sofas', 'lamps'],
            'groceries': ['grocery', 'groceries', 'fresh food', 'juices', 'coffee'],
            'electronics': ['electronics', 'gadgets', 'power banks'],
            'cameras': ['camera', 'cameras', 'dslr', 'dslrs', 'lenses'],
            'botanicals': ['botanical', 'botanicals', 'candles', 'incense', 'diffusers'],
            'sports accessories': ['sports', 'fitness gear', 'cleats']
        }
        for cat_name, triggers in cat_map.items():
            if any(re.search(r'\b' + re.escape(t) + r'\b', q) for t in triggers):
                if self.clean_df is not None:
                    actual = self.clean_df[self.clean_df['Category_clean'] == cat_name]
                    if not actual.empty:
                        return actual['Category'].iloc[0]
                return cat_name.title()
        return None

    def _filter_by_category(self, category, max_price=None):
        if self.clean_df is None or self.clean_df.empty:
            return []
        matches = self.clean_df[self.clean_df['Category'].str.lower() == category.lower()]
        if max_price:
            matches = matches[matches['Price'] <= max_price]
        
        # Prefer devices over accessories if category is Laptops or Smartphones
        if category.lower() in ['laptops', 'smartphones', 'cameras']:
            devices = matches[~matches['Name_clean'].str.contains(r'case|sleeve|stand|hub|mouse|keyboard|pad|cable|charger|bag|sieve|pot', regex=True)]
            if not devices.empty:
                accessories = matches[matches['Name_clean'].str.contains(r'case|sleeve|stand|hub|mouse|keyboard|pad|cable|charger|bag|sieve|pot', regex=True)]
                sorted_matches = pd.concat([devices.sort_values(by='Rating', ascending=False), accessories.sort_values(by='Rating', ascending=False)])
                return [self._to_dict(r) for _, r in sorted_matches.iterrows()]

        matches = matches.sort_values(by='Rating', ascending=False)
        return [self._to_dict(r) for _, r in matches.iterrows()]

    def _get_featured_products(self, n=4):
        if self.products_df is None or self.products_df.empty:
            return []
        sample = self.products_df.sort_values(by='Rating', ascending=False).head(n)
        return [self._to_dict(r) for _, r in sample.iterrows()]

    def _to_dict(self, row):
        item = dict(row)
        for key in ['Name_clean', 'Category_clean', 'Desc_clean', 'Score']:
            item.pop(key, None)
        item['ID'] = int(item['ID']) if 'ID' in item and not pd.isna(item['ID']) else 0
        item['Price'] = int(item['Price']) if 'Price' in item and not pd.isna(item['Price']) else 0
        item['Rating'] = float(item['Rating']) if 'Rating' in item and not pd.isna(item['Rating']) else 4.5
        item['Name'] = str(item.get('Name', ''))
        item['Category'] = str(item.get('Category', ''))
        return item
