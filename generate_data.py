import pandas as pd
import numpy as np
import random
import urllib.request
import json

def fetch_data(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def sanitize_url(url, fallback_seed):
    if not isinstance(url, str):
        return f"https://picsum.photos/seed/{fallback_seed}/400/400"
    if url.startswith('["') and url.endswith('"]'):
        try:
            parsed = json.loads(url)
            if parsed and len(parsed) > 0:
                url = parsed[0]
        except:
            pass
    url = url.strip('"').strip("'")
    if not url or url.endswith('.svg') or 'placehold' in url.lower() or 'any' in url.lower():
        return f"https://picsum.photos/seed/{fallback_seed}/400/400"
    return url

print("Fetching products from DummyJSON...")
try:
    data1 = fetch_data('https://dummyjson.com/products?limit=0')
    dummy_products = data1.get('products', [])
except Exception as e:
    print(f"Error fetching from DummyJSON: {e}")
    dummy_products = []

print("Fetching products from FakeStore API...")
try:
    fakestore_products = fetch_data('https://fakestoreapi.com/products')
except Exception as e:
    print(f"Error fetching from FakeStore API: {e}")
    fakestore_products = []

print("Fetching products from Platzi API...")
try:
    platzi_products = fetch_data('https://api.escuelajs.co/api/v1/products?limit=250&offset=0')
except Exception as e:
    print(f"Error fetching from Platzi API: {e}")
    platzi_products = []

products = []
current_id = 1

# Helper to normalize categories for UI
def map_category(cat):
    cat = str(cat).lower()
    if 'grocery' in cat or 'groceries' in cat: return 'Groceries'
    if 'beauty' in cat or 'skin' in cat or 'fragrance' in cat: return 'Beauty'
    if 'smartphone' in cat or 'mobile' in cat or 'phone' in cat: return 'Smartphones'
    if 'laptops' in cat or 'electronics' in cat or 'computer' in cat or 'tablet' in cat: return 'Electronics'
    if 'dress' in cat or 'womens' in cat or 'clothing' in cat or 'shirt' in cat: return 'Fashion'
    if 'kitchen' in cat or 'home' in cat or 'furniture' in cat: return 'Home & Kitchen'
    return cat.capitalize().replace('-', ' ')

def is_garbage_product(name, cat):
    name = str(name).lower()
    cat = str(cat).lower()
    if 'title' in name and any(char.isdigit() for char in name): return True
    if 'new' in name and 'name' in name: return True
    if 'updated' in cat or 'miscellaneous' in cat: return True
    if name == 'string' or name == 'unknown product': return True
    return False

for p in dummy_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', 'General')
    
    if is_garbage_product(name, cat): continue

    image_url = p.get('thumbnail', '')
    if not image_url and p.get('images'):
        image_url = p['images'][0]
    
    image_url = sanitize_url(image_url, current_id)
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85),
        "Rating": float(p.get('rating', round(random.uniform(3.5, 5.0), 1))),
        "Image": image_url,
        "Description": p.get('description', '')[:100]
    })
    current_id += 1

for p in fakestore_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', 'General')
    if is_garbage_product(name, cat): continue
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85), 
        "Rating": p.get('rating', {}).get('rate', 4.0) if isinstance(p.get('rating'), dict) else 4.0,
        "Image": sanitize_url(p.get('image', ''), current_id),
        "Description": p.get('description', '')[:100]
    })
    current_id += 1

for p in platzi_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', {}).get('name', 'General')
    if is_garbage_product(name, cat): continue
        
    images = p.get('images', [])
    image_url = images[0] if images else ""
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85), 
        "Rating": round(random.uniform(3.5, 5.0), 1),
        "Image": sanitize_url(image_url, current_id),
        "Description": p.get('description', 'High quality premium product.')[:100]
    })
    current_id += 1

# Generate extra Groceries and Beauty if lacking
grocery_items = ["Organic Bananas", "Whole Wheat Bread", "Almond Milk", "Farm Fresh Eggs", "Green Apples", "Basmati Rice", "Olive Oil", "Pasta", "Tomato Ketchup", "Green Tea Bags", "Dark Chocolate", "Peanut Butter"]
beauty_items = ["Matte Lipstick", "Hydrating Face Cream", "Vitamin C Serum", "Exfoliating Scrub", "Rose Water Toner", "SPF 50 Sunscreen", "Liquid Eyeliner", "Volumizing Mascara"]

def add_synthetic(items, cat):
    global current_id
    for item in items:
        products.append({
            "ID": current_id, "Name": item, "Category": cat,
            "Price": random.randint(150, 1200), "Rating": round(random.uniform(4.0, 5.0), 1),
            "Image": f"https://picsum.photos/seed/{current_id}/400/400",
            "Description": f"Premium quality {item.lower()} for your daily needs."
        })
        current_id += 1

add_synthetic(grocery_items, 'Groceries')
add_synthetic(beauty_items, 'Beauty')

# Remove duplicates based on Name
seen_names = set()
unique_products = []
for p in products:
    if p['Name'] not in seen_names:
        seen_names.add(p['Name'])
        unique_products.append(p)

for i, p in enumerate(unique_products):
    p['ID'] = i + 1

df_products = pd.DataFrame(unique_products)
df_products.to_csv("products.csv", index=False)
print(f"Total {len(df_products)} products saved to products.csv")

# Generate transactions
print("Generating transactions...")
transactions = []
transaction_id = 1
customers = list(range(1001, 1101))

categories = df_products['Category'].unique().tolist()
category_products = {cat: df_products[df_products['Category'] == cat]['ID'].tolist() for cat in categories}
all_product_ids = df_products['ID'].tolist()

for _ in range(3000):
    cust_id = random.choice(customers)
    if random.random() > 0.3 and len(categories) > 0:
        pref_cat = random.choice(categories)
        avail_products = category_products.get(pref_cat, [])
        if len(avail_products) > 0:
            basket_size = random.randint(1, min(4, len(avail_products)))
            basket = random.sample(avail_products, k=basket_size)
            if random.random() > 0.8 and len(avail_products) > basket_size:
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

pd.DataFrame(transactions).to_csv("transactions.csv", index=False)
print("Data generated successfully.")
