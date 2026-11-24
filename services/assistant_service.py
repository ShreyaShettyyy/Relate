"""
Voice Assistant Service for Relate (LuxStore).
Provides natural language intent matching, event/occasion product suggestions,
cart voice actions, budget filtering, and conversational shopping guidance.
"""

import re
import pandas as pd
import numpy as np


class VoiceAssistantService:
    def __init__(self, products_df, recommender=None):
        self.products_df = products_df
        self.recommender = recommender
        self._build_index()

    def set_products_df(self, products_df):
        self.products_df = products_df
        self._build_index()

    def set_recommender(self, recommender):
        self.recommender = recommender

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

    STOP_WORDS = {
        'show', 'me', 'some', 'products', 'product', 'item', 'items', 'for', 'example',
        'like', 'any', 'good', 'best', 'give', 'want', 'need', 'tell', 'about', 'can',
        'you', 'please', 'display', 'view', 'look', 'what', 'are', 'the', 'have', 'recommend',
        'suggest', 'explore', 'find', 'which', 'with', 'a', 'an', 'in', 'of', 'on', 'to',
        'and', 'or', 'is', 'it', 'at', 'by', 'as', 'also', 'all', 'so', 'that', 'this',
        'these', 'those', 'from', 'into', 'up', 'down', 'out', 'off', 'over', 'under',
        'then', 'here', 'there', 'when', 'where', 'why', 'how', 'both', 'each', 'few',
        'more', 'most', 'other', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'than', 'too', 'very', 's', 't', 'will', 'just', 'should', 'now', 'hey', 'relate'
    }

    def process_query(self, query_text, current_product=None, current_cart_ids=None, last_recommended_product=None, customer_id=None):
        """
        Main query handler. Analyzes voice or text input, determines user intent,
        extracts target products / constraints, and returns a rich assistant response.
        """
        if not query_text or not query_text.strip():
            return {
                "reply": "I'm listening! You can ask for dresses, shoes, laptops, smartphones, or say 'Add this to my cart'.",
                "products": [],
                "action": {"type": "none"}
            }

        q = query_text.strip().lower()
        
        # 1. Strip wake-word prefix if present (including common speech-to-text misrecognitions)
        for prefix in ['hey relate', 'hi relate', 'hello relate', 'ok relate', 'okay relate', 'relate', 'hey reality', 'hey relay', 'hey re late']:
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
                "reply": "Hello! I am Relate AI, your voice shopping concierge. Say 'Hey Relate' anytime or ask me to show dresses, smartphones, or say 'Order this product'!",
                "products": self._get_featured_products(4),
                "action": {"type": "none"}
            }

        # 3. Check for Direct Cart, Order & Navigation Actions
        # A. Order / Checkout / "view cart and order the product"
        order_match = self._parse_order_query(q)
        if order_match is not None:
            return self._handle_order(
                order_match,
                current_product=current_product,
                current_cart_ids=current_cart_ids,
                last_recommended_product=last_recommended_product,
                customer_id=customer_id
            )

        # B. View Cart / Show Bag
        if any(k in q for k in ['open cart', 'view cart', 'show cart', 'my cart', 'open bag', 'show bag', 'go to cart', 'what is in my cart']):
            return {
                "reply": "Opening your shopping cart right now.",
                "products": [],
                "action": {"type": "view_cart"}
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
            return self._handle_add_to_cart(
                add_cart_match,
                current_product=current_product,
                last_recommended_product=last_recommended_product,
                customer_id=customer_id
            )

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

        # 5.5 Check for Focused Product Sub-categories (Shoes, Watches, Perfumes, Speakers, Headphones)
        focused = self._check_focused_item_query(q, max_price=max_price)
        if focused:
            return focused

        # 6. Check for Category Inquiries (e.g. "show laptops", "smartphones")
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

        # 8. Friendly Fallback (Strict precision: never suggest random products!)
        return {
            "reply": f"I couldn't find any products matching '{query_text}' in our catalog. You can ask for dresses, sarees, suits, handbags, jewelry, smartphones, laptops, shoes, perfumes, or watches.",
            "products": [],
            "action": {"type": "none"}
        }

    # --------------------------------------------------------------------------
    # INTENT HELPERS
    # --------------------------------------------------------------------------
    def _get_companion_products(self, product_name, customer_id=None, top_n=3):
        """
        Retrieves products frequently bought together or co-purchased by other users
        or the same user via Apriori association rules and co-purchase analytics.
        """
        if self.recommender is None or self.clean_df is None or self.clean_df.empty:
            return []

        used_names = {str(product_name).strip()}
        companion_list = []

        # 1. Personal co-purchases (same buyer past history)
        if customer_id:
            try:
                personal = self.recommender.get_personal_copurchases(customer_id, product_name)
                for name, reason in personal:
                    if name not in used_names:
                        used_names.add(name)
                        companion_list.append((name, reason or f"You usually buy this with {product_name}"))
                        if len(companion_list) >= top_n:
                            break
            except Exception:
                pass

        # 2. Frequently bought together (Apriori rules & community co-purchases from other users)
        if len(companion_list) < top_n:
            try:
                fbt = self.recommender.get_frequently_bought_together(product_name, customer_id=customer_id, top_n=top_n, exclude_items=used_names)
                for name, reason in fbt:
                    if name not in used_names:
                        used_names.add(name)
                        companion_list.append((name, reason or f"Most people usually buy this with {product_name}"))
                        if len(companion_list) >= top_n:
                            break
            except Exception:
                pass

        # 3. Recommended companion accessories
        if len(companion_list) < top_n:
            try:
                acc = self.recommender.get_recommended_accessories(product_name, customer_id=customer_id, top_n=top_n, exclude_items=used_names)
                for name, reason in acc:
                    if name not in used_names:
                        used_names.add(name)
                        companion_list.append((name, reason or f"Recommended accessory for {product_name}"))
                        if len(companion_list) >= top_n:
                            break
            except Exception:
                pass

        results = []
        for name, reason in companion_list:
            row = self.clean_df[self.clean_df['Name'] == name]
            if not row.empty:
                d = self._to_dict(row.iloc[0])
                d['recommendation_reason'] = reason
                results.append(d)
        return results

    def _check_focused_item_query(self, q, max_price=None):
        """
        Catches queries for specific product sub-types (e.g. 'shoes', 'dresses', 'watches', 'perfumes', 'cameras')
        so they do not get swallowed by overly broad top-level category defaults.
        """
        if self.clean_df is None or self.clean_df.empty:
            return None

        # A. Footwear / Shoes
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['shoes', 'shoe', 'sneakers', 'sneaker', 'trainers', 'footwear', 'cleats', 'loafers', 'sandals', 'heels']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'shoe|sneaker|jordan|rider|cleat|heel|loafer|suede casual|sandals', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by='Rating', ascending=False).iterrows()]
                return {
                    "reply": "Here are our top footwear styles and designer sneakers. Which pair would you like to explore?",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # B. Luxury Watches
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['watches', 'watch', 'rolex', 'timepiece', 'timepieces']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'rolex|watch|longines', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iterrows()]
                return {
                    "reply": "Here are our luxury Swiss timepieces and master collection watches.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # C. Fragrances / Perfumes
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['perfume', 'perfumes', 'fragrance', 'fragrances', 'cologne', 'scent']):
            matches = self.clean_df[
                ((self.clean_df['Category_clean'] == 'beauty') & (self.clean_df['Name_clean'].str.contains(r'dior|chanel|ck one|gucci bloom|dolce|perfume|eau de|fragrance', regex=True))) |
                (self.clean_df['Name_clean'].str.contains(r'radiant citrus', regex=True))
            ]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by='Rating', ascending=False).iterrows()]
                return {
                    "reply": "Here are our signature designer perfumes and luxury fragrances.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # D. Dresses, Evening Gowns & Indian Festive Wear (Sarees & Lehengas)
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['dresses', 'dress', 'gown', 'gowns', 'saree', 'sarees', 'lehenga', 'lehengas', 'frock', 'frocks', 'maxi', 'slip dress', 'ballgown', 'evening dress']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'dress|gown|saree|lehenga|frock|slip', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iterrows()]
                return {
                    "reply": "Here are our designer dresses, silk evening gowns, and festive ethnic collections. Which one would you like to explore?",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # E. Tailored Suits, Blazers & Tuxedos
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['suit', 'suits', 'blazer', 'blazers', 'tuxedo', 'tuxedos', 'bandhgala', 'formal suit']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'tuxedo|suit|blazer|bandhgala', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iterrows()]
                return {
                    "reply": "Here are our tailored Italian wool suits, slim-fit blazers, and royal festive jackets.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # F. Luxury Handbags & Totes
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['handbag', 'handbags', 'bag', 'bags', 'tote', 'totes', 'purse', 'purses', 'crossbody']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'handbag|tote|crossbody|purse|carry-on|luggage', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iterrows()]
                return {
                    "reply": "Here are our Italian leather handbags, crossbody bags, and luxury totes.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # G. Fine Diamond & Gold Jewelry
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['jewelry', 'jewellery', 'necklace', 'necklaces', 'earring', 'earrings', 'bracelet', 'bracelets', 'diamond', 'diamonds', 'gold necklace']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'necklace|earring|bracelet|pendant|diamond|gold', regex=True) & ~self.clean_df['Name_clean'].str.contains(r'watch', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iterrows()]
                return {
                    "reply": "Here are our certified diamond necklaces, halo earrings, and 18K gold tennis bracelets.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # H. Audio / Speakers
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['speakers', 'speaker', 'smart speaker', 'sound system', 'echo']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'echo|homepod|speaker', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by='Rating', ascending=False).iterrows()]
                return {
                    "reply": "Here are our premium smart speakers and home audio systems.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        # I. Headphones / Earbuds
        if any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in ['headphones', 'headphone', 'earphones', 'earphone', 'earbuds', 'airpods', 'beats']):
            matches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'airpods|beats|headphone|earbud', regex=True)]
            if max_price:
                matches = matches[matches['Price'] <= max_price]
            if not matches.empty:
                results = [self._to_dict(r) for _, r in matches.sort_values(by='Rating', ascending=False).iterrows()]
                return {
                    "reply": "Here are our top wireless headphones, studio over-ears, and noise-cancelling earbuds.",
                    "products": results[:6],
                    "action": {"type": "none"}
                }

        return None

    def _parse_order_query(self, q):
        """
        Parses variations of 'order the product', 'view cart and order the product', 'order [item]'.
        Returns extracted item name string, 'view_cart_and_order', 'this', or None.
        """
        q_clean = q.strip('.,!? ')

        # Explicit 'view cart and order'
        if any(p in q_clean for p in ['view cart and order', 'view cart and checkout', 'view cart and place order', 'open cart and order', 'open cart and checkout', 'show cart and order', 'show cart and checkout']):
            return 'view_cart_and_order'

        # Generic order commands
        generic_orders = [
            'order the product', 'order a product', 'order product', 'order this product',
            'order this', 'order it', 'place order', 'place the order', 'place my order',
            'order now', 'buy now', 'buy this now', 'buy the product now', 'purchase now',
            'proceed to checkout', 'checkout', 'go to checkout', 'complete order', 'finish order'
        ]
        if q_clean in generic_orders:
            return 'this'

        # "order [item]" e.g. "order iphone 13 pro", "order midnight silk evening gown"
        m1 = re.search(r'^(?:please\s+|can\s+you\s+)?(?:order|place\s+order\s+for|buy\s+now)\s+(.+)$', q_clean)
        if m1:
            item = m1.group(1).strip()
            if item in ['it', 'this', 'product', 'the product', 'a product', 'item']:
                return 'this'
            return item

        # "order the [item]" or "order this [item]"
        m2 = re.search(r'^(?:order|buy)\s+(?:the\s+|this\s+)?(.+?)\s+now$', q_clean)
        if m2:
            item = m2.group(1).strip()
            return 'this' if item in ['it', 'this', 'product', 'item'] else item

        return None

    def _handle_order(self, target_term, current_product=None, current_cart_ids=None, last_recommended_product=None, customer_id=None):
        target_clean = str(target_term).lower().strip()

        # Case 1: "view cart and order"
        if target_clean == 'view_cart_and_order':
            return {
                "reply": "Here is your cart! Taking you straight to checkout to complete your order.",
                "products": [],
                "action": {
                    "type": "checkout",
                    "show_cart": True
                }
            }

        active_candidate = current_product or last_recommended_product

        # Case 2: Generic "order the product" / "order this" / "place order"
        if target_clean in ['', 'this', 'product', 'the product', 'it']:
            if active_candidate:
                p_id = int(active_candidate.get('ID', 0))
                p_name = str(active_candidate.get('Name', 'this item'))
                p_price = int(active_candidate.get('Price', 0))
                companion = self._get_companion_products(p_name, customer_id=customer_id)
                
                if companion:
                    top_names = " and ".join(c['Name'] for c in companion[:2])
                    reply = f"I've added {p_name} to your cart for ₹{p_price:,} and brought you to checkout to place your order! Shoppers also frequently buy {top_names} with this."
                else:
                    reply = f"I've added {p_name} to your cart for ₹{p_price:,} and brought you directly to checkout to complete your order!"

                return {
                    "reply": reply,
                    "products": [active_candidate],
                    "companion_products": companion,
                    "action": {
                        "type": "checkout",
                        "product_id": p_id,
                        "product_name": p_name,
                        "price": p_price
                    }
                }
            elif current_cart_ids and len(current_cart_ids) > 0:
                return {
                    "reply": "Taking you directly to checkout to review and complete your order!",
                    "products": [],
                    "action": {
                        "type": "checkout"
                    }
                }
            else:
                return {
                    "reply": "Your shopping cart is currently empty. Please tell me which product you'd like to order, or select one from our collection!",
                    "products": [],
                    "action": {"type": "none"}
                }

        # Case 3: Specific product order e.g. "order midnight silk evening gown"
        matched = self._find_best_match(target_clean)
        if matched:
            p_id = int(matched.get('ID', 0))
            p_name = str(matched.get('Name'))
            p_price = int(matched.get('Price', 0))
            companion = self._get_companion_products(p_name, customer_id=customer_id)
            
            if companion:
                top_names = " and ".join(c['Name'] for c in companion[:2])
                reply = f"I've added the {p_name} to your cart for ₹{p_price:,} and brought you to checkout to place your order! Customers also frequently purchase {top_names} with this."
            else:
                reply = f"I've added the {p_name} to your cart for ₹{p_price:,} and brought you straight to checkout to complete your order!"

            return {
                "reply": reply,
                "products": [matched],
                "companion_products": companion,
                "action": {
                    "type": "checkout",
                    "product_id": p_id,
                    "product_name": p_name,
                    "price": p_price
                }
            }

        return {
            "reply": f"I couldn't find a product matching '{target_term}' in our catalog. You can ask for dresses, sarees, suits, handbags, jewelry, smartphones, laptops, shoes, or perfumes.",
            "products": [],
            "action": {"type": "none"}
        }

    def _parse_add_to_cart_query(self, q):
        """
        Parses variations of 'add [item] to cart' or 'add to cart'.
        Returns extracted item name string or 'this' if generic 'add to cart'.
        Returns None if not an add-to-cart intent.
        """
        # Discard informational questions asking what/how to buy
        if any(w in q for w in ['what should i buy', 'what to buy', 'should i buy', 'can i buy', 'where to buy', 'how to buy', 'what can i buy']):
            return None

        q_clean = q.strip('.,!? ')

        # Explicit generic commands
        generic_phrases = [
            'add to cart', 'add to bag', 'add this', 'add this to cart', 'add this to bag',
            'add it', 'add it to cart', 'add it to bag', 'buy this', 'buy it',
            'add product to cart', 'add a product to cart', 'add a product to the cart',
            'add the product to cart', 'add the product to the cart', 'add product to the cart',
            'put this in cart', 'put it in cart', 'put product in cart'
        ]
        if q_clean in generic_phrases:
            return 'this'

        # Form 0: "can you add [item] to cart", "please add [item] to cart", "i want to add [item] to cart"
        m0 = re.search(r'^(?:can\s+you\s+|could\s+you\s+|please\s+|kindly\s+|i\s+want\s+to\s+|i\s+would\s+like\s+to\s+)?(?:add|put)\s+(.+?)\s+(?:to|in|into)\s+(?:the\s+|my\s+)?(?:cart|bag)\b', q_clean)
        if m0:
            item = m0.group(1).strip()
            if item in ['it', 'this', 'product', 'the product', 'a product', 'item', 'this item']:
                return 'this'
            return item

        # Form 1: "add to cart [item]" or "add to bag [item]"
        m1 = re.search(r'\b(?:add|put)\s+(?:to|in)\s+(?:the\s+|my\s+)?(?:cart|bag)\s+(.+)$', q_clean)
        if m1:
            item = m1.group(1).strip()
            return 'this' if item in ['it', 'this', 'product', 'item'] else item

        # Form 2: "add [item] to/in cart/bag"
        m2 = re.search(r'\b(?:add|put)\s+(.+?)\s+(?:to|in)\s+(?:the\s+|my\s+)?(?:cart|bag)\b', q_clean)
        if m2:
            item = m2.group(1).strip()
            return 'this' if item in ['it', 'this', 'product', 'item'] else item

        # Form 3: Direct imperative command "buy [item]" or "purchase [item]"
        if q_clean.startswith(('buy ', 'purchase ')):
            sub = re.sub(r'^(?:buy|purchase)\s+', '', q_clean).strip()
            if sub and not sub.startswith(('for ', 'something ', 'a gift ', 'gift ', 'me ')):
                return 'this' if sub in ['it', 'this', 'product', 'item'] else sub

        # Form 4: Direct imperative command "add [item]" (e.g. "add iphone 13 pro", "add macbook", "add airpods")
        m4 = re.search(r'^\s*add\s+(.+)$', q_clean)
        if m4:
            sub = m4.group(1).strip()
            if sub and not sub.startswith(('more', 'another', 'something', 'filter', 'to cart', 'to bag')):
                return 'this' if sub in ['it', 'this', 'product', 'item', 'a product', 'the product'] else sub

        return None

    def _handle_add_to_cart(self, target_term, current_product=None, last_recommended_product=None, customer_id=None):
        target_clean = target_term.lower().strip()
        generic_terms = {
            '', 'this', 'this item', 'this product', 'it', 'one', 'a product', 'the product',
            'product', 'products', 'item', 'items', 'that', 'that product', 'that item'
        }

        target_is_generic = target_clean in generic_terms
        active_candidate = current_product or last_recommended_product

        # If user gave a generic "add to cart" command and we have an active candidate
        if target_is_generic:
            if active_candidate:
                p_id = int(active_candidate.get('ID', 0))
                p_name = str(active_candidate.get('Name', 'this item'))
                p_price = int(active_candidate.get('Price', 0))
                companion = self._get_companion_products(p_name, customer_id=customer_id)
                
                if companion:
                    top_names = " and ".join(c['Name'] for c in companion[:2])
                    reply = f"I have added {p_name} to your cart for ₹{p_price:,}! Shoppers also frequently buy {top_names} with this. Here are companion recommendations for you."
                else:
                    reply = f"I have added {p_name} to your cart for ₹{p_price:,}! Would you like to view your cart or checkout?"

                return {
                    "reply": reply,
                    "products": [active_candidate],
                    "companion_products": companion,
                    "action": {
                        "type": "add_to_cart",
                        "product_id": p_id,
                        "product_name": p_name,
                        "price": p_price
                    }
                }
            else:
                return {
                    "reply": "Which product would you like to add to your cart? Please say a product name, such as 'Midnight Silk Evening Gown' or 'iPhone 13 Pro'.",
                    "products": [],
                    "action": {"type": "none"}
                }

        # Match specific product name or category concept
        matched = self._find_best_match(target_clean)
        if matched:
            p_id = int(matched.get('ID', 0))
            p_name = str(matched.get('Name'))
            p_price = int(matched.get('Price', 0))
            companion = self._get_companion_products(p_name, customer_id=customer_id)
            
            if companion:
                top_names = " and ".join(c['Name'] for c in companion[:2])
                reply = f"I have added the {p_name} to your cart for ₹{p_price:,}! Customers also frequently purchase {top_names} with this. Take a look below!"
            else:
                reply = f"I have added the {p_name} to your cart for ₹{p_price:,}. Would you like to view your cart or keep shopping?"

            return {
                "reply": reply,
                "products": [matched],
                "companion_products": companion,
                "action": {
                    "type": "add_to_cart",
                    "product_id": p_id,
                    "product_name": p_name,
                    "price": p_price
                }
            }
        
        return {
            "reply": f"I couldn't find a product matching '{target_term}'. You can search for dresses, smartphones, laptops, shoes, perfumes, or watches.",
            "products": [],
            "action": {"type": "none"}
        }
    def _find_best_match(self, term):
        term_clean = term.lower().strip()
        if term_clean.startswith(('the ', 'a ', 'an ')):
            term_clean = re.sub(r'^(?:the|a|an)\s+', '', term_clean).strip()

        if not term_clean or self.clean_df is None or self.clean_df.empty:
            return None

        # 0. Direct match: Exact name match
        exact = self.clean_df[self.clean_df['Name_clean'] == term_clean]
        if not exact.empty:
            return self._to_dict(exact.iloc[0])

        # Multi-word specific product match (e.g. "midnight silk evening gown", "banarasi silk saree", "emerald satin slip dress")
        if len(term_clean.split()) >= 2:
            sub = self.clean_df[self.clean_df['Name_clean'].str.contains(re.escape(term_clean), regex=True, na=False)]
            if not sub.empty:
                return self._to_dict(sub.sort_values(by=['Rating', 'Price'], ascending=[False, False]).iloc[0])

            contained = self.clean_df[self.clean_df['Name_clean'].apply(lambda n: len(n) >= 5 and n in term_clean)]
            if not contained.empty:
                return self._to_dict(contained.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 1. iPhone matches (device vs accessory)
        if 'iphone' in term_clean and not any(acc in term_clean for acc in ['charger', 'case', 'cable', 'cover', 'protector', 'battery', 'lamp', 'adapter']):
            iphones = self.clean_df[
                (self.clean_df['Name_clean'].str.contains('iphone', na=False)) &
                (~self.clean_df['Name_clean'].str.contains(r'case|charger|cable|protector|battery|lamp|adapter', regex=True))
            ]
            if not iphones.empty:
                for model in ['13 pro', '13', 'x', '6', '5s']:
                    if model in term_clean:
                        m = iphones[iphones['Name_clean'].str.contains(model, na=False)]
                        if not m.empty:
                            return self._to_dict(m.sort_values(by='Price', ascending=False).iloc[0])
                # Default to flagship
                return self._to_dict(iphones.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 2. General Smartphone matches
        if term_clean in ['smartphone', 'smartphones', 'smart phone', 'smart phones', 'phone', 'phones', 'mobile', 'mobiles']:
            phones = self.clean_df[(self.clean_df['Category'] == 'Smartphones') & (~self.clean_df['Name_clean'].str.contains(r'case|charger|cable|protector|stand|holder|power bank|pedestal|monopod|stick|battery|airpods|beats|lamp', regex=True))]
            if not phones.empty:
                return self._to_dict(phones.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 3. Laptop / MacBook matches
        if 'macbook' in term_clean or 'laptop' in term_clean:
            if not any(acc in term_clean for acc in ['sleeve', 'case', 'bag', 'stand', 'cooler', 'cooling', 'mouse', 'pad', 'hub', 'adapter']):
                laptops = self.clean_df[
                    (self.clean_df['Category'] == 'Laptops') &
                    (~self.clean_df['Name_clean'].str.contains(r'sleeve|case|bag|stand|cooler|cooling|mouse|pad|hub|adapter|backpack', regex=True))
                ]
                if not laptops.empty:
                    if 'macbook' in term_clean:
                        macs = laptops[laptops['Name_clean'].str.contains('macbook', na=False)]
                        if not macs.empty:
                            return self._to_dict(macs.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])
                    if 'dell' in term_clean or 'xps' in term_clean:
                        dells = laptops[laptops['Name_clean'].str.contains('dell|xps', na=False)]
                        if not dells.empty:
                            return self._to_dict(dells.iloc[0])
                    if 'zenbook' in term_clean or 'asus' in term_clean:
                        asuss = laptops[laptops['Name_clean'].str.contains('zenbook|asus', na=False)]
                        if not asuss.empty:
                            return self._to_dict(asuss.iloc[0])
                    return self._to_dict(laptops.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 4. Dresses / Evening Gowns / Ethnic Festive Wear
        if any(w in term_clean for w in ['dress', 'dresses', 'gown', 'gowns', 'saree', 'sarees', 'lehenga', 'lehengas', 'frock']):
            dresses = self.clean_df[self.clean_df['Name_clean'].str.contains(r'dress|gown|saree|lehenga|frock', regex=True)]
            if not dresses.empty:
                if 'silk' in term_clean or 'evening' in term_clean or 'gown' in term_clean:
                    m = dresses[dresses['Name_clean'].str.contains('silk|evening|gown', na=False)]
                    if not m.empty:
                        return self._to_dict(m.sort_values(by=['Rating', 'Price'], ascending=[False, False]).iloc[0])
                if 'saree' in term_clean:
                    m = dresses[dresses['Name_clean'].str.contains('saree', na=False)]
                    if not m.empty:
                        return self._to_dict(m.sort_values(by=['Rating', 'Price'], ascending=[False, False]).iloc[0])
                if 'lehenga' in term_clean:
                    m = dresses[dresses['Name_clean'].str.contains('lehenga', na=False)]
                    if not m.empty:
                        return self._to_dict(m.sort_values(by=['Rating', 'Price'], ascending=[False, False]).iloc[0])
                if 'satin' in term_clean or 'slip' in term_clean:
                    m = dresses[dresses['Name_clean'].str.contains('satin|slip', na=False)]
                    if not m.empty:
                        return self._to_dict(m.sort_values(by=['Rating', 'Price'], ascending=[False, False]).iloc[0])
                return self._to_dict(dresses.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 5. Tailored Suits / Blazers / Tuxedos
        if any(w in term_clean for w in ['suit', 'suits', 'blazer', 'blazers', 'tuxedo', 'tuxedos', 'bandhgala']):
            suits = self.clean_df[self.clean_df['Name_clean'].str.contains(r'tuxedo|suit|blazer|bandhgala', regex=True)]
            if not suits.empty:
                if 'tuxedo' in term_clean:
                    m = suits[suits['Name_clean'].str.contains('tuxedo', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                if 'blazer' in term_clean:
                    m = suits[suits['Name_clean'].str.contains('blazer', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                if 'bandhgala' in term_clean:
                    m = suits[suits['Name_clean'].str.contains('bandhgala', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                return self._to_dict(suits.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 6. Luxury Handbags / Totes
        if any(w in term_clean for w in ['handbag', 'handbags', 'tote', 'totes', 'purse', 'crossbody']):
            bags = self.clean_df[self.clean_df['Name_clean'].str.contains(r'handbag|tote|crossbody|purse', regex=True)]
            if not bags.empty:
                return self._to_dict(bags.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 7. Fine Jewelry / Diamond / Gold
        if any(w in term_clean for w in ['jewelry', 'jewellery', 'necklace', 'earring', 'earrings', 'bracelet', 'diamond']):
            jewels = self.clean_df[self.clean_df['Name_clean'].str.contains(r'necklace|earring|bracelet|diamond', regex=True) & ~self.clean_df['Name_clean'].str.contains(r'watch', regex=True)]
            if not jewels.empty:
                return self._to_dict(jewels.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 8. Shoes / Sneakers matches
        if any(w in term_clean for w in ['shoe', 'shoes', 'sneaker', 'sneakers', 'trainer', 'trainers', 'cleat', 'cleats', 'footwear', 'heel', 'loafers']):
            shoes = self.clean_df[self.clean_df['Name_clean'].str.contains(r'shoe|sneaker|jordan|rider|cleat|heel|loafer|suede casual', regex=True)]
            if not shoes.empty:
                if 'jordan' in term_clean or 'nike' in term_clean:
                    m = shoes[shoes['Name_clean'].str.contains('jordan|nike', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                if 'puma' in term_clean:
                    m = shoes[shoes['Name_clean'].str.contains('puma', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                return self._to_dict(shoes.sort_values(by='Rating', ascending=False).iloc[0])

        # 9. Watches / Rolex matches
        if any(w in term_clean for w in ['watch', 'watches', 'rolex', 'timepiece']):
            watches = self.clean_df[self.clean_df['Name_clean'].str.contains(r'rolex|watch', regex=True)]
            if not watches.empty:
                if 'submariner' in term_clean:
                    m = watches[watches['Name_clean'].str.contains('submariner', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                if 'datejust' in term_clean:
                    m = watches[watches['Name_clean'].str.contains('datejust', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                if 'cellini' in term_clean:
                    m = watches[watches['Name_clean'].str.contains('cellini', na=False)]
                    if not m.empty:
                        return self._to_dict(m.iloc[0])
                return self._to_dict(watches.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 10. Camera matches
        if any(w in term_clean for w in ['camera', 'cameras', 'dslr']):
            if not any(acc in term_clean for acc in ['tripod', 'bag', 'card', 'battery', 'lens']):
                cams = self.clean_df[(self.clean_df['Category'] == 'Cameras') & (~self.clean_df['Name_clean'].str.contains(r'card|tripod|bag|battery|pedestal|lens', regex=True))]
                if not cams.empty:
                    if 'sony' in term_clean:
                        m = cams[cams['Name_clean'].str.contains('sony', na=False)]
                        if not m.empty:
                            return self._to_dict(m.iloc[0])
                    if 'canon' in term_clean:
                        m = cams[cams['Name_clean'].str.contains('canon', na=False)]
                        if not m.empty:
                            return self._to_dict(m.iloc[0])
                    if 'fujifilm' in term_clean:
                        m = cams[cams['Name_clean'].str.contains('fujifilm', na=False)]
                        if not m.empty:
                            return self._to_dict(m.iloc[0])
                    return self._to_dict(cams.sort_values(by=['Price', 'Rating'], ascending=[False, False]).iloc[0])

        # 11. Exact match on Name
        exact = self.clean_df[self.clean_df['Name_clean'] == term_clean]
        if not exact.empty:
            return self._to_dict(exact.iloc[0])

        # 12. Substring match on Name
        sub = self.clean_df[self.clean_df['Name_clean'].str.contains(re.escape(term_clean), regex=True, na=False)]
        if not sub.empty:
            return self._to_dict(sub.sort_values(by='Rating', ascending=False).iloc[0])

        # 13. Token overlap match (excluding stop words)
        tokens = [t for t in term_clean.split() if len(t) > 2 and t not in self.STOP_WORDS]
        if tokens:
            best_score = 0
            best_row = None
            for _, row in self.clean_df.iterrows():
                name_words = row['Name_clean'].split()
                score = sum(3 for t in tokens if t in name_words) + sum(1 for t in tokens if any(t in w for w in name_words))
                if score > best_score:
                    best_score = score
                    best_row = row
            if best_score > 0 and best_row is not None:
                return self._to_dict(best_row)

        return None

    def _search_products(self, query, max_price=None):
        q_clean = query.lower().strip()
        tokens = [t for t in q_clean.split() if len(t) > 2 and t not in self.STOP_WORDS]
        if not tokens and self.clean_df is not None:
            tokens = [t for t in q_clean.split() if len(t) > 1 and t not in self.STOP_WORDS]

        if not tokens:
            return []

        results = []
        if self.clean_df is not None and not self.clean_df.empty:
            df = self.clean_df
            if max_price:
                df = df[df['Price'] <= max_price]

            scores = []
            for _, row in df.iterrows():
                score = 0
                name_clean = row['Name_clean']
                cat_clean = row['Category_clean']
                desc_clean = row['Desc_clean']
                
                for t in tokens:
                    # Exact word boundary matching for high accuracy
                    if re.search(rf'\b{re.escape(t)}\b', name_clean):
                        score += 6
                    elif len(t) >= 4 and t in name_clean:
                        score += 3

                    if re.search(rf'\b{re.escape(t)}\b', cat_clean):
                        score += 4
                    elif len(t) >= 4 and t in cat_clean:
                        score += 2

                    if re.search(rf'\b{re.escape(t)}\b', desc_clean):
                        score += 1
                scores.append(score)

            df = df.copy()
            df['Score'] = scores
            # Require at least a strong match (score >= 3) so random tokens don't falsely match
            matched = df[df['Score'] >= 3].sort_values(by=['Score', 'Rating'], ascending=[False, False])
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
            'smartphones': ['smart phone', 'smart phones', 'smartphone', 'smartphones', 'phone', 'phones', 'mobile', 'mobiles', 'cellphone', 'cellphones', 'android', 'iphone', 'handset', 'handsets'],
            'laptops': ['laptop', 'laptops', 'notebook', 'notebooks', 'computers', 'computer', 'macbook'],
            'fashion': ['fashion', 'clothes', 'clothing', 'shoes', 'sneakers', 'sweatpants', 'wear', 'dress', 'dresses', 'shirt', 'shirts', 'jeans', 'jacket', 'jackets', 'watch', 'watches', 'sunglasses'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'lipsticks', 'lipstick', 'perfumes', 'perfume', 'fragrances', 'fragrance', 'cologne'],
            'home & kitchen': ['home', 'kitchen', 'furniture', 'cookware', 'sofas', 'sofa', 'beds', 'bed', 'lamps', 'lamp', 'living', 'chair', 'chairs'],
            'groceries': ['grocery', 'groceries', 'fresh food', 'juices', 'juice', 'coffee', 'fruits', 'food', 'apothecary'],
            'electronics': ['electronics', 'gadget', 'gadgets', 'power banks', 'power bank', 'speaker', 'speakers', 'tablet', 'tablets', 'ipad'],
            'cameras': ['camera', 'cameras', 'dslr', 'dslrs', 'lenses', 'lens', 'tripod', 'tripods'],
            'botanicals': ['botanical', 'botanicals', 'candle', 'candles', 'incense', 'diffusers', 'diffuser', 'mist', 'essence'],
            'sports accessories': ['sports', 'sport', 'fitness gear', 'fitness', 'cleats', 'gym', 'workout'],
            'vehicles & outdoors': ['vehicle', 'vehicles', 'bike', 'bikes', 'bicycle', 'bicycles', 'motorcycle', 'motorcycles', 'scooter', 'scooters']
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
        
        # When user asks for Smartphones, prioritize actual phone handsets (exclude cases/cables/chargers from top results)
        if category.lower() == 'smartphones':
            handsets = matches[~matches['Name_clean'].str.contains(r'case|charger|cable|protector|stand|holder|power bank|pedestal|monopod|stick|battery|airpods|beats|lamp', regex=True)]
            accessories = matches[matches['Name_clean'].str.contains(r'case|charger|cable|protector|stand|holder|power bank|pedestal|monopod|stick|battery|airpods|beats|lamp', regex=True)]
            sorted_matches = pd.concat([handsets.sort_values(by=['Price', 'Rating'], ascending=[False, False]), accessories.sort_values(by='Rating', ascending=False)])
            return [self._to_dict(r) for _, r in sorted_matches.iterrows()]

        # When user asks for Laptops, prioritize actual laptops (exclude backpacks/sleeves from top results)
        if category.lower() == 'laptops':
            devices = matches[~matches['Name_clean'].str.contains(r'backpack|bag|sleeve|case|stand|mouse', regex=True)]
            accessories = matches[matches['Name_clean'].str.contains(r'backpack|bag|sleeve|case|stand|mouse', regex=True)]
            sorted_matches = pd.concat([devices.sort_values(by=['Price', 'Rating'], ascending=[False, False]), accessories.sort_values(by='Rating', ascending=False)])
            return [self._to_dict(r) for _, r in sorted_matches.iterrows()]

        # When user asks for Cameras, prioritize actual cameras (exclude SD cards/bags/tripods from top results)
        if category.lower() == 'cameras':
            devices = matches[~matches['Name_clean'].str.contains(r'card|tripod|bag|battery|pedestal', regex=True)]
            accessories = matches[matches['Name_clean'].str.contains(r'card|tripod|bag|battery|pedestal', regex=True)]
            sorted_matches = pd.concat([devices.sort_values(by=['Price', 'Rating'], ascending=[False, False]), accessories.sort_values(by='Rating', ascending=False)])
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
