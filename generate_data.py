import pandas as pd
import numpy as np
import random
import urllib.request
import json
import re

def fetch_data(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def sanitize_url(url):
    if not isinstance(url, str):
        return ""
    if url.startswith('["') and url.endswith('"]'):
        try:
            parsed = json.loads(url)
            if parsed and len(parsed) > 0:
                url = parsed[0]
        except:
            pass
    # Remove any extra quotes
    url = url.strip('"').strip("'")
    return url

print("Fetching products from DummyJSON...")
try:
    data1 = fetch_data('https://dummyjson.com/products?limit=200')
    dummy_products = data1.get('products', [])
except Exception as e:
    print(f"Error fetching from DummyJSON: {e}")
    dummy_products = []

print(f"Fetched {len(dummy_products)} products from DummyJSON.")

print("Fetching products from FakeStore API...")
try:
    fakestore_products = fetch_data('https://fakestoreapi.com/products')
except Exception as e:
    print(f"Error fetching from FakeStore API: {e}")
    fakestore_products = []

print(f"Fetched {len(fakestore_products)} products from FakeStore API.")

products = []
current_id = 1

# Process DummyJSON products
for p in dummy_products:
    name = p.get('title', 'Unknown Product')
    name_lower = name.lower()
    category = str(p.get('category', 'General')).lower()
    
    # Filter out unwanted products
    if any(unwanted in name_lower for unwanted in ['beef', 'cucumber', 'chicken', 'cat food', 'glass']) or 'groceries' in category or 'vegetable' in category:
        continue

    image_url = p.get('thumbnail', '')
    if not image_url and p.get('images'):
        image_url = p['images'][0]
    
    image_url = sanitize_url(image_url)
    if not image_url or image_url.endswith('.svg') or 'placehold' in image_url:
        image_url = f"https://picsum.photos/seed/{current_id}/400/400"
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": category.capitalize().replace('-', ' '),
        "Price": int(p.get('price', 9.99) * 25),  # Lowered multiplier for realistic INR prices
        "Rating": p.get('rating', 4.0),
        "Image": image_url,
        "Description": p.get('description', '')
    })
    current_id += 1

# Process FakeStore products
for p in fakestore_products:
    image_url = sanitize_url(p.get('image', ''))
    if not image_url or image_url.endswith('.svg'):
        image_url = f"https://picsum.photos/seed/{current_id}/400/400"
    
    products.append({
        "ID": current_id,
        "Name": p.get('title', 'Unknown Product'),
        "Category": str(p.get('category', 'General')).capitalize().replace('-', ' '),
        "Price": int(p.get('price', 9.99) * 25), 
        "Rating": p.get('rating', {}).get('rate', 4.0) if isinstance(p.get('rating'), dict) else 4.0,
        "Image": image_url,
        "Description": p.get('description', '')
    })
    current_id += 1

# If we need even more, fetch from Platzi Fake Store API
if len(products) < 220:
    print("Fetching products from Platzi API...")
    try:
        platzi_products = fetch_data('https://api.escuelajs.co/api/v1/products?limit=100&offset=0')
        print(f"Fetched {len(platzi_products)} products from Platzi API.")
        
        for p in platzi_products:
            images = p.get('images', [])
            image_url = images[0] if images else ""
            image_url = sanitize_url(image_url)
            
            # Skip items without images or broken images from Platzi
            if not image_url or "any" in image_url.lower():
                continue
                
            products.append({
                "ID": current_id,
                "Name": p.get('title', 'Unknown Product'),
                "Category": str(p.get('category', {}).get('name', 'General')).capitalize().replace('-', ' '),
                "Price": int(p.get('price', 9.99) * 25), 
                "Rating": round(random.uniform(3.5, 5.0), 1),
                "Image": image_url,
                "Description": p.get('description', '')
            })
            current_id += 1
    except Exception as e:
        print(f"Failed to fetch from Platzi API: {e}")

# Remove duplicates based on Name just in case
seen_names = set()
unique_products = []
for p in products:
    if p['Name'] not in seen_names:
        seen_names.add(p['Name'])
        unique_products.append(p)

# Assign sequential IDs
for i, p in enumerate(unique_products):
    p['ID'] = i + 1

df_products = pd.DataFrame(unique_products)
df_products.to_csv("products.csv", index=False)
print(f"Total {len(df_products)} products saved to products.csv")

# Now generate transactions
print("Generating transactions...")
transactions = []
transaction_id = 1
customers = list(range(1001, 1101)) # 100 customers

categories = df_products['Category'].unique().tolist()
category_products = {cat: df_products[df_products['Category'] == cat]['ID'].tolist() for cat in categories}
all_product_ids = df_products['ID'].tolist()

for _ in range(3000): # Generating 3000 transactions for better recommendations
    cust_id = random.choice(customers)
    
    # Customer buys from a specific category or randomly
    if random.random() > 0.4 and len(categories) > 0:
        pref_cat = random.choice(categories)
        avail_products = category_products[pref_cat]
        
        if len(avail_products) > 0:
            basket_size = random.randint(1, min(4, len(avail_products)))
            basket = random.sample(avail_products, k=basket_size)
            
            # Cross-selling: 15% chance to add a product from a related category instead of purely random
            if random.random() > 0.85:
                # To prevent makeup + glass, just pick from another category somewhat safely, 
                # or just don't cross-sell wildly. We'll pick another item from the same category to keep it safe.
                if len(avail_products) > basket_size:
                    basket.append(random.choice([x for x in avail_products if x not in basket]))
        else:
            basket = random.sample(all_product_ids, k=random.randint(1, 3))
    else:
        basket = random.sample(all_product_ids, k=random.randint(1, 3))
        
    for item_id in set(basket):
        transactions.append({
            "TransactionID": transaction_id,
            "CustomerID": cust_id,
            "Item": df_products.loc[df_products['ID'] == item_id, 'Name'].values[0]
        })
    transaction_id += 1

df_transactions = pd.DataFrame(transactions)
df_transactions.to_csv("transactions.csv", index=False)
print("Data generated successfully.")
