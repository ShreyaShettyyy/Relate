import pandas as pd
import numpy as np
import random
import urllib.request
import json
from config.config import PRODUCTS_FILE, TRANSACTIONS_FILE

def fetch_data(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def sanitize_url(url):
    if not isinstance(url, str):
        return None
    if url.startswith('["') and url.endswith('"]'):
        try:
            parsed = json.loads(url)
            if parsed and len(parsed) > 0:
                url = parsed[0]
        except:
            pass
    url = url.strip('"').strip("'").strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        return None
    bad_keywords = ['.svg', 'placehold', 'any', 'google.com', 'gogole.com', 'martinez.net']
    if any(k in url.lower() for k in bad_keywords):
        return None
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

def map_category(cat):
    cat = str(cat).lower()
    if 'grocery' in cat or 'groceries' in cat: return 'Groceries'
    if 'beauty' in cat or 'skin' in cat or 'fragrance' in cat: return 'Beauty'
    if 'smartphone' in cat or 'mobile' in cat or 'phone' in cat: return 'Smartphones'
    if 'laptop' in cat or 'computer' in cat: return 'Laptops'
    if 'camera' in cat: return 'Cameras'
    if 'electronics' in cat or 'tablet' in cat: return 'Electronics'
    if 'dress' in cat or 'womens' in cat or 'clothing' in cat or 'shirt' in cat or 'shoe' in cat or 'watch' in cat: return 'Fashion'
    if 'kitchen' in cat or 'home' in cat or 'furniture' in cat: return 'Home & Kitchen'
    return 'Electronics'

def is_garbage_product(name, cat):
    name = str(name).lower()
    cat = str(cat).lower()
    if 'title' in name and any(char.isdigit() for char in name): return True
    if 'new' in name and 'name' in name: return True
    if 'updated' in cat or 'miscellaneous' in cat: return True
    if name == 'string' or name == 'unknown product': return True
    if len(name) > 12 and ' ' not in name: return True
    return False

for p in dummy_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', 'General')
    if is_garbage_product(name, cat): continue

    image_list = []
    if p.get('thumbnail'):
        url = sanitize_url(p.get('thumbnail'))
        if url: image_list.append(url)
    for img in p.get('images', []):
        url = sanitize_url(img)
        if url and url not in image_list: image_list.append(url)
    if not image_list: continue
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85),
        "Rating": float(p.get('rating', round(random.uniform(3.5, 5.0), 1))),
        "Image": ",".join(image_list[:3]),
        "Description": p.get('description', '')[:100]
    })
    current_id += 1

for p in fakestore_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', 'General')
    if is_garbage_product(name, cat): continue
    
    image_url = sanitize_url(p.get('image', ''))
    if not image_url: continue
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85), 
        "Rating": p.get('rating', {}).get('rate', 4.0) if isinstance(p.get('rating'), dict) else 4.0,
        "Image": image_url,
        "Description": p.get('description', '')[:100]
    })
    current_id += 1

for p in platzi_products:
    name = p.get('title', 'Unknown Product')
    cat = p.get('category', {}).get('name', 'General')
    if is_garbage_product(name, cat): continue
        
    image_list = []
    for img in p.get('images', []):
        url = sanitize_url(img)
        if url and url not in image_list: image_list.append(url)
    if not image_list: continue
    
    products.append({
        "ID": current_id,
        "Name": name,
        "Category": map_category(cat),
        "Price": int(p.get('price', 9.99) * 85), 
        "Rating": round(random.uniform(3.5, 5.0), 1),
        "Image": ",".join(image_list[:3]),
        "Description": p.get('description', 'High quality premium product.')[:100]
    })
    current_id += 1

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
df_products.to_csv(PRODUCTS_FILE, index=False)
print(f"Total {len(df_products)} products saved to {PRODUCTS_FILE}")

# Generate realistic domain-clustered transactions
print("Generating realistic domain-clustered transactions...")
from services.auth_service import load_db
from config.config import USERS_FILE

# Domain clusters for realistic market basket associations
SMARTPHONE_DEVICES = [
    'iPhone 13 Pro', 'iPhone X', 'iPhone 6', 'iPhone 5s',
    'Samsung Galaxy S10', 'Samsung Galaxy S8', 'Samsung Galaxy S7',
    'Oppo F19 Pro Plus', 'Oppo A57', 'Oppo K1',
    'Vivo S1', 'Vivo V9', 'Vivo X21',
    'Realme C35', 'Realme X', 'Realme XT'
]

SMARTPHONE_ACCESSORIES = [
    'Shockproof Crystal Clear Phone Case',
    'Ultra-Clear Tempered Glass Screen Protector',
    '20W Fast USB-C Wall Charger Adapter',
    'Braided USB-C to Lightning Fast Charging Cable',
    'Anker 10000mAh Magnetic Wireless Power Bank',
    'Adjustable Aluminum Desktop Phone Stand',
    'Apple Airpower Wireless Charger',
    'Apple iPhone Charger',
    'Apple MagSafe Battery Pack',
    'iPhone 12 Silicone Case with MagSafe Plum',
    'Apple Airpods',
    'Beats Flex Wireless Earphones'
]

LAPTOP_DEVICES = [
    'Apple MacBook Pro 14 Inch Space Grey',
    'Asus Zenbook Pro Dual Screen Laptop',
    'New DELL XPS 13 9300 Laptop',
    'Sleek Modern Laptop with Ambient Lighting',
    'Sleek Modern Laptop for Professionals',
    'Huawei Matebook X Pro',
    'Lenovo Yoga 920'
]

LAPTOP_ACCESSORIES = [
    'Water-Resistant Slim Laptop Sleeve & Bag',
    'Logitech Master 3S Ergonomic Wireless Mouse',
    'Ergonomic Low-Profile Mechanical Keyboard',
    'RGB Dual-Fan Laptop Cooling Pad',
    'Foldable Aluminum Ergonomic Laptop Stand',
    '7-in-1 Dual USB-C Multiport Hub Adapter',
    'Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops',
    'SanDisk SSD PLUS 1TB Internal SSD - SATA III 6 Gb/s',
    'WD 2TB Elements Portable External Hard Drive - USB 3.0 '
]

CAMERA_DEVICES = [
    'Sony Alpha 7 IV Full-Frame Mirrorless Camera',
    'Canon EOS R6 Mark II Mirrorless Camera',
    'Fujifilm X-T5 Mirrorless Digital Camera'
]

CAMERA_ACCESSORIES = [
    'Professional 24-70mm f/2.8 Full-Frame Zoom Lens',
    'SanDisk 128GB Extreme PRO SDXC Memory Card',
    'Professional Lightweight Camera Tripod with Ball Head',
    'Rechargeable High-Capacity Camera Battery Pack',
    'Padded DSLR Camera Shoulder Bag with Rain Cover',
    'Monopod',
    'Selfie Stick Monopod'
]

COSMETICS = [
    'Essence Mascara Lash Princess',
    'Eyeshadow Palette with Mirror',
    'Powder Canister',
    'Red Lipstick',
    'Red Nail Polish'
]

FRAGRANCES = [
    'Calvin Klein CK One',
    "Dior J'adore",
    'Dolce Shine Eau de',
    'Chanel Coco Noir Eau De',
    'Gucci Bloom Eau de',
    'Radiant Citrus Eau de Parfum'
]

BATH_BODY = [
    'Olay Ultra Moisture Shea Butter Body Wash',
    'Vaseline Men Body and Face Lotion',
    'Attitude Super Leaves Hand Soap'
]

SNEAKERS = [
    'Nike Air Jordan 1 Red And Black',
    'Nike Baseball Cleats',
    'Sports Sneakers Off White & Red',
    'Sports Sneakers Off White Red',
    'Puma Future Rider Trainers',
    'Vibrant Runners: Bold Orange & Blue Sneakers',
    'Futuristic Silver and Gold High-Top Sneaker'
]

ACTIVEWEAR = [
    'Classic Red Sweatpants',
    'Classic White Crew Neck T-Shirt',
    'Classic Black T-Shirt',
    'Gigabyte Aorus Men Tshirt',
    'Classic Black Baseball Cap'
]

WATCHES = [
    'Rolex Cellini Moonphase',
    'Rolex Cellini Date Black Dial',
    'Rolex Datejust',
    'Rolex Datejust Women',
    'Rolex Submariner Watch',
    'Longines Master Collection',
    'Brown Leather Belt Watch',
    'Watch Gold for Women'
]

WATCH_COMPANIONS = [
    'Black Sun Glasses',
    'Classic Sun Glasses',
    'Man Plaid Shirt',
    'Blue & Black Check Shirt',
    'Men Check Shirt'
]

JEWELRY = [
    'White Gold Plated Princess',
    'Solid Gold Petite Micropave ',
    "John Hardy Women's Legends Naga Gold & Silver Dragon Station Chain Bracelet",
    'Pierced Owl Rose Gold Plated Stainless Steel Double',
    'Tropical Earring'
]

PLANTS_HOME = [
    'Plant Pot',
    'House Showpiece Plant',
    'Table Lamp',
    'Annibale Colombo Bed',
    'Annibale Colombo Sofa',
    'Bedside Table African Cherry',
    'Sleek Modern Leather Sofa',
    'Modern Elegance Teal Armchair'
]

KITCHEN = [
    'Silver Pot With Glass Cap',
    'Kitchen Sieve',
    'Plate',
    'Lunch Box',
    'Spoon',
    'Pan',
    'Efficient 2-Slice Toaster'
]

GROCERIES_BREAKFAST = [
    'Milk', 'Eggs', 'Honey Jar', 'Juice', 'Nescafe Coffee', 'Ice Cream'
]

GROCERIES_PRODUCE = [
    'Apple', 'Banana', 'Kiwi', 'Strawberry', 'Lemon', 'Potatoes', 'Green Bell Pepper', 'Cucumber'
]

# Helper to filter to only items present in current product catalog
catalog_names = set(df_products['Name'].unique())
def filter_catalog(items):
    return [x for x in items if x in catalog_names]

CLUSTERS = [
    (filter_catalog(SMARTPHONE_DEVICES), filter_catalog(SMARTPHONE_ACCESSORIES), (1, 3), 450),
    (filter_catalog(LAPTOP_DEVICES), filter_catalog(LAPTOP_ACCESSORIES), (1, 3), 400),
    (filter_catalog(CAMERA_DEVICES), filter_catalog(CAMERA_ACCESSORIES), (1, 3), 300),
    (filter_catalog(COSMETICS), filter_catalog(COSMETICS), (2, 4), 300),
    (filter_catalog(FRAGRANCES), filter_catalog(FRAGRANCES + BATH_BODY + ['Red Nail Polish', 'Red Lipstick']), (1, 2), 250),
    (filter_catalog(SNEAKERS), filter_catalog(ACTIVEWEAR + SNEAKERS), (1, 2), 300),
    (filter_catalog(WATCHES), filter_catalog(WATCH_COMPANIONS + WATCHES), (1, 2), 250),
    (filter_catalog(JEWELRY), filter_catalog(JEWELRY), (1, 2), 200),
    (filter_catalog(['Plant Pot']), filter_catalog(['House Showpiece Plant', 'Table Lamp', 'Bedside Table African Cherry']), (1, 2), 150),
    (filter_catalog(KITCHEN), filter_catalog(KITCHEN), (2, 3), 200),
    (filter_catalog(GROCERIES_BREAKFAST), filter_catalog(GROCERIES_BREAKFAST), (2, 3), 200),
    (filter_catalog(GROCERIES_PRODUCE), filter_catalog(GROCERIES_PRODUCE), (2, 3), 200),
    (filter_catalog(LAPTOP_DEVICES), filter_catalog(SMARTPHONE_DEVICES + ['Sleek Smartwatch with Vibrant Display', 'Apple Watch Series 4 Gold']), (1, 2), 200),
]

random.seed(42)
customers = list(range(1001, 1101))
transactions = []
txn_id = 1

for anchors, pool, count_range, num_txns in CLUSTERS:
    if not anchors or not pool:
        continue
    for _ in range(num_txns):
        cust_id = random.choice(customers)
        anchor = random.choice(anchors)
        k = random.randint(count_range[0], min(count_range[1], len(pool)))
        companions = random.sample([p for p in pool if p != anchor], k=min(k, len([p for p in pool if p != anchor])))
        basket = [anchor] + companions
        for item in set(basket):
            transactions.append({
                "TransactionID": txn_id,
                "CustomerID": cust_id,
                "Item": item
            })
        txn_id += 1

# Preserve historical user orders from users.json if file exists
try:
    db = load_db(USERS_FILE)
    for email, u in db.items():
        cid = u.get('customer_id')
        if not cid:
            continue
        for ord in u.get('orders', []):
            oid = ord.get('id', txn_id)
            items = ord.get('items', [])
            for item in items:
                transactions.append({
                    "TransactionID": oid,
                    "CustomerID": cid,
                    "Item": item
                })
except Exception as e:
    print(f"Notice: historical orders sync skipped ({e})")

df_trans = pd.DataFrame(transactions)
df_trans.to_csv(TRANSACTIONS_FILE, index=False)
print(f"Generated {len(df_trans)} realistic transaction records across {df_trans['TransactionID'].nunique()} baskets.")
print(f"Transactions saved to {TRANSACTIONS_FILE}.")
