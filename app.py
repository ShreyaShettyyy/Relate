from flask import Flask, render_template, request, jsonify
import pandas as pd
import time
from pathlib import Path

from config.config import (
    Config,
    PRODUCTS_FILE,
    TRANSACTIONS_FILE,
    USERS_FILE,
)
from services.auth_service import (
    load_db,
    save_db,
    register_user,
    authenticate_user,
    update_user_name,
    change_user_password,
    reset_password_with_hash,
)
from services.email_service import (
    request_password_reset_otp,
    verify_password_reset_otp,
    is_otp_verified,
    consume_verified_otp,
)
from services.recommendation_service import (
    RecommenderSystem,
    get_product_dict_list,
    get_product_dict_list_with_reasons,
)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Ensure users.json orders are synchronized into transactions.csv
def sync_user_orders_to_transactions():
    global df_trans
    if not USERS_FILE.exists() or not TRANSACTIONS_FILE.exists():
        return
    db = load_db(USERS_FILE)
    new_rows = []
    for email, u in db.items():
        cid = u.get('customer_id')
        if not cid:
            continue
        for ord in u.get('orders', []):
            oid = ord.get('id')
            items = ord.get('items', [])
            for item in items:
                exists = ((df_trans['TransactionID'] == oid) & (df_trans['CustomerID'] == cid) & (df_trans['Item'] == item)).any()
                if not exists:
                    new_rows.append({'TransactionID': oid, 'CustomerID': cid, 'Item': item})
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        df_trans = pd.concat([df_trans, new_df], ignore_index=True)
        new_df.to_csv(TRANSACTIONS_FILE, mode='a', header=False, index=False)
        print(f"Synchronized {len(new_rows)} historical user order items to transactions.csv.")

# Initialize Application Datasets and Recommender System
try:
    df_trans = pd.read_csv(TRANSACTIONS_FILE)
    df_prod = pd.read_csv(PRODUCTS_FILE)
    sync_user_orders_to_transactions()
    recommender = RecommenderSystem(df_trans, df_prod)
    recommender.train_market_basket(min_support=0.001, min_threshold=0.1)
except Exception as e:
    print("Error initializing recommender system:", e)
    df_trans = pd.DataFrame(columns=['TransactionID', 'CustomerID', 'Item'])
    df_prod = pd.DataFrame(columns=['ID', 'Name', 'Category', 'Price', 'Rating', 'Image', 'Description'])
    recommender = RecommenderSystem(df_trans, df_prod)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/metadata')
def metadata():
    customers = sorted(df_trans['CustomerID'].unique().tolist()) if not df_trans.empty else []
    products = df_prod.replace({float('nan'): None}).to_dict('records')
    categories = sorted(df_prod['Category'].dropna().unique().tolist())
    return jsonify({
        "customers": customers,
        "products": products,
        "categories": categories
    })


# ----------------- ADVANCED PRODUCT RECOMMENDATIONS -----------------
@app.route('/api/product_recs')
def product_recs():
    customer_id = request.args.get('customer_id', type=int)
    product_name = request.args.get('product')
    
    if not product_name:
        return jsonify({"error": "No product provided"}), 400

    used_items = {product_name}

    # 0. Personal Co-Purchases (If and only if buyer has personally bought product with another product)
    personal_tuples = recommender.get_personal_copurchases(customer_id, product_name)
    used_items.update(t[0] for t in personal_tuples)

    # 1. Frequently Bought Together (Apriori rules + real co-purchases from other accounts)
    fbt_tuples = recommender.get_frequently_bought_together(product_name, customer_id=customer_id, top_n=4, exclude_items=used_items)
    used_items.update(t[0] for t in fbt_tuples)
    
    # 2. Recommended Accessories (Dedicated companion accessories, excluding FBT items!)
    acc_tuples = recommender.get_recommended_accessories(product_name, customer_id=customer_id, top_n=6, exclude_items=used_items)
    used_items.update(t[0] for t in acc_tuples)
    
    # 3. Similar Products (Category-consistent alternatives)
    sim_tuples = recommender.get_similar_products(product_name, top_n=6, exclude_items=used_items)
    used_items.update(t[0] for t in sim_tuples)
    
    # 4. You May Also Like (Collaborative lifestyle discovery, zero repetition)
    yml_tuples = recommender.get_you_may_also_like(product_name, customer_id=customer_id, top_n=6, exclude_items=used_items)

    return jsonify({
        "product": product_name,
        "personal_copurchases": get_product_dict_list_with_reasons(personal_tuples, df_prod),
        "frequently_bought_together": get_product_dict_list_with_reasons(fbt_tuples, df_prod),
        "recommended_accessories": get_product_dict_list_with_reasons(acc_tuples, df_prod),
        "similar_products": get_product_dict_list_with_reasons(sim_tuples, df_prod),
        "you_may_also_like": get_product_dict_list_with_reasons(yml_tuples, df_prod)
    })


# ----------------- HOME / FEED RECOMMENDATIONS -----------------
@app.route('/api/feed')
def user_feed():
    customer_id = request.args.get('customer_id', type=int)
    
    if customer_id and not df_trans.empty and customer_id in df_trans['CustomerID'].values:
        # Personalized recommendations strictly driven by real co-purchase transactions
        raw_recs = recommender.get_personalized_feed(customer_id, top_n=24)
        recently_purchased_names = recommender.get_recently_purchased(customer_id, top_n=12)
        
        formatted_recs = get_product_dict_list_with_reasons(raw_recs, df_prod)
        recently_purchased_prods = get_product_dict_list(recently_purchased_names, df_prod)
        
        return jsonify({
            "personalized": True,
            "recommendations": formatted_recs,
            "recently_purchased": recently_purchased_prods
        })
    else:
        # Guest / Unauthenticated Feed (strictly based on co-occurrence pairs from transactions)
        raw_guest = recommender.get_guest_feed(top_n=20)
        formatted_guest = get_product_dict_list_with_reasons(raw_guest, df_prod)
        
        return jsonify({
            "personalized": False,
            "recommendations": formatted_guest,
            "recently_purchased": []
        })


# ----------------- AUTHENTICATION -----------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    
    res = register_user(name, email, password)
    status_code = res.pop("status_code", 200 if res.get("success") else 400)
    return jsonify(res), status_code


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    res = authenticate_user(email, password)
    status_code = res.pop("status_code", 200 if res.get("success") else 401)
    return jsonify(res), status_code


# ----------------- FORGOT PASSWORD VIA EMAIL OTP -----------------
@app.route('/api/auth/forgot-password/send-otp', methods=['POST'])
def send_password_reset_otp():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required."}), 400
        
    db = load_db(USERS_FILE)
    user_name = db.get(email, {}).get('name', 'Valued Customer')
    
    res = request_password_reset_otp(email, user_name)
    status_code = res.pop("status_code", 200 if res.get("success") else 400)
    return jsonify(res), status_code


@app.route('/api/auth/forgot-password/verify-otp', methods=['POST'])
def verify_otp_endpoint():
    data = request.json or {}
    email = data.get('email', '')
    otp_code = data.get('otp', '')
    
    res = verify_password_reset_otp(email, otp_code)
    status_code = res.pop("status_code", 200 if res.get("success") else 400)
    return jsonify(res), status_code


@app.route('/api/auth/forgot-password/reset-password', methods=['POST'])
def reset_password_endpoint():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    new_password = data.get('new_password', '')
    
    if not email or not new_password:
        return jsonify({"error": "Email and new password are required."}), 400
        
    if not is_otp_verified(email):
        return jsonify({"error": "Unauthorized. You must verify your code first."}), 403
        
    res = reset_password_with_hash(email, new_password)
    if res.get("success"):
        consume_verified_otp(email)
        
    status_code = res.pop("status_code", 200 if res.get("success") else 400)
    return jsonify(res), status_code


# ----------------- USER PROFILE MANAGEMENT -----------------
@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    email = request.args.get('email')
    if request.method == 'PUT':
        data = request.json or {}
        email = data.get('email')
        
    if not email:
        return jsonify({"error": "Email parameter required"}), 400
        
    db = load_db(USERS_FILE)
    email = email.strip().lower()
    if email not in db:
        return jsonify({"error": "User not found"}), 404
        
    user = db[email]
    
    if request.method == 'PUT':
        new_name = (request.json or {}).get('name', '')
        res = update_user_name(email, new_name)
        status_code = res.pop("status_code", 200 if res.get("success") else 400)
        return jsonify(res), status_code
        
    return jsonify({
        "email": email,
        "name": user['name'],
        "customer_id": user['customer_id'],
        "total_orders": len(user.get('orders', [])),
        "cart_count": len(user.get('cart', [])),
        "wishlist_count": len(user.get('wishlist', [])),
        "created_at": user.get('created_at', '2026-01-01')
    })


@app.route('/api/user/change-password', methods=['POST'])
def change_password_endpoint():
    data = request.json or {}
    email = data.get('email', '')
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    res = change_user_password(email, current_password, new_password)
    status_code = res.pop("status_code", 200 if res.get("success") else 400)
    return jsonify(res), status_code


# ----------------- USER DATA (CART, WISHLIST, ORDERS) -----------------
@app.route('/api/user/data', methods=['GET', 'POST'])
def user_data():
    email = request.args.get('email')
    if request.method == 'POST':
        email = (request.json or {}).get('email')
        
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    db = load_db(USERS_FILE)
    email = email.strip().lower()
    if email not in db:
        return jsonify({"error": "User not found"}), 404
        
    if request.method == 'POST':
        data = request.json or {}
        if 'cart' in data:
            db[email]['cart'] = data['cart']
        if 'wishlist' in data:
            db[email]['wishlist'] = data['wishlist']
            
        if 'new_order' in data:
            new_order = data['new_order']
            new_order['created_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            db[email].setdefault('orders', []).append(new_order)
            
            # Dynamically update the recommender transaction dataset
            customer_id = db[email]['customer_id']
            txn_id = new_order.get('id', int(time.time()))
            new_rows = []
            for item in new_order.get('items', []):
                new_rows.append({'TransactionID': txn_id, 'CustomerID': customer_id, 'Item': item})
                
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                global df_trans, recommender
                df_trans = pd.concat([df_trans, new_df], ignore_index=True)
                recommender.transactions_df = df_trans
                
                # Persist to transactions.csv in data/application/
                new_df.to_csv(TRANSACTIONS_FILE, mode='a', header=False, index=False)
                
                # Retrain market basket model
                try:
                    recommender.train_market_basket(min_support=0.001, min_threshold=0.1)
                except Exception as e:
                    print("Error retraining recommender:", e)
                    
        save_db(db, USERS_FILE)
        return jsonify({"success": True})
        
    return jsonify({
        "cart": db[email].get('cart', []),
        "wishlist": db[email].get('wishlist', []),
        "orders": db[email].get('orders', [])
    })


if __name__ == '__main__':
    print(f"Starting Relate (LuxStore) Server on port {Config.PORT}...")
    app.run(debug=Config.DEBUG, port=Config.PORT)
