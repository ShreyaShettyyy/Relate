from flask import Flask, render_template, request, jsonify
import pandas as pd
from recommender import RecommenderSystem

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Initialize Recommender System
try:
    df_trans = pd.read_csv('transactions.csv')
    df_prod = pd.read_csv('products.csv')
    recommender = RecommenderSystem(df_trans)
    recommender.train_market_basket(min_support=0.0005, min_threshold=0.1)
except Exception as e:
    print("Error initializing recommender:", e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metadata')
def metadata():
    customers = sorted(df_trans['CustomerID'].unique().tolist())
    products = df_prod.to_dict('records')
    return jsonify({"customers": customers, "products": products})

@app.route('/api/product_recs')
def product_recs():
    customer_id = request.args.get('customer_id', type=int)
    product = request.args.get('product')
    
    if not product:
        return jsonify({"error": "No product provided"}), 400
        
    global_recs = recommender.get_frequently_bought_with(product)
    
    personal_recs = []
    if customer_id:
        personal_recs = recommender.get_user_frequently_bought_with(customer_id, product)
        
    def get_prod_details(names):
        return df_prod[df_prod['Name'].isin(names)].to_dict('records')
        
    return jsonify({
        "global": get_prod_details(global_recs),
        "personal": get_prod_details(personal_recs)
    })

@app.route('/api/feed')
def user_feed():
    customer_id = request.args.get('customer_id', type=int)
    if not customer_id:
        return jsonify({"error": "No customer provided"}), 400
        
    feed_recs = recommender.get_user_feed_recommendations(customer_id, top_n=20)
    
    # Get user's past purchases to find their preferred categories
    user_txns = df_trans[df_trans['CustomerID'] == customer_id]
    past_items = user_txns['Item'].unique().tolist()
    past_cats = df_prod[df_prod['Name'].isin(past_items)]['Category'].unique().tolist()
    
    # Recommend other items in these categories to reach ~100 items
    category_recs = df_prod[df_prod['Category'].isin(past_cats) & ~df_prod['Name'].isin(past_items)]['Name'].tolist()
    
    final_recs = feed_recs.copy()
    for item in category_recs:
        if item not in final_recs:
            final_recs.append(item)
        if len(final_recs) >= 100:
            break
    
    # If they have no history at all (new account), show globally popular
    if not final_recs:
        final_recs = df_trans['Item'].value_counts().head(100).index.tolist()
        
    def get_prod_details(names):
        return df_prod[df_prod['Name'].isin(names)].to_dict('records')
        
    return jsonify({
        "feed": get_prod_details(final_recs)
    })

import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = 'users.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    if not email or not password: return jsonify({"error": "Missing fields"}), 400
    db = load_db()
    if email in db: return jsonify({"error": "User already exists"}), 400
    hashed_password = generate_password_hash(password)
    db[email] = {"name": name, "password": hashed_password, "cart": [], "wishlist": [], "orders": [], "customer_id": len(db) + 1101}
    save_db(db)
    return jsonify({"success": True, "user": {"email": email, "name": name, "customer_id": db[email]['customer_id']}})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    db = load_db()
    if email in db:
        user_password = db[email].get('password', '')
        # Support both hashed passwords and legacy plain-text passwords for existing users
        if check_password_hash(user_password, password) or user_password == password:
            user = db[email]
            return jsonify({"success": True, "user": {"email": email, "name": user['name'], "customer_id": user['customer_id']}})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/user/data', methods=['GET', 'POST'])
def user_data():
    email = request.args.get('email')
    if request.method == 'POST':
        email = request.json.get('email')
        
    db = load_db()
    if email not in db: return jsonify({"error": "User not found"}), 404
    
    if request.method == 'POST':
        data = request.json
        if 'cart' in data: db[email]['cart'] = data['cart']
        if 'wishlist' in data: db[email]['wishlist'] = data['wishlist']
        if 'new_order' in data:
            db[email]['orders'].append(data['new_order'])
            
            # Dynamically update the recommender dataset with the new transaction
            customer_id = db[email]['customer_id']
            txn_id = data['new_order']['id']
            new_rows = []
            for item in data['new_order']['items']:
                new_rows.append({'TransactionID': txn_id, 'CustomerID': customer_id, 'Item': item})
                
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                global df_trans, recommender
                df_trans = pd.concat([df_trans, new_df], ignore_index=True)
                recommender.transactions_df = df_trans
                
                # Append to CSV to persist across server restarts
                new_df.to_csv('transactions.csv', mode='a', header=False, index=False)
                
                # Retrain market basket model so global rules also update
                try:
                    recommender.train_market_basket(min_support=0.0005, min_threshold=0.1)
                except Exception as e:
                    print("Error retraining model:", e)
                    
        save_db(db)
        return jsonify({"success": True})
        
    return jsonify({"cart": db[email].get('cart', []), "wishlist": db[email].get('wishlist', []), "orders": db[email].get('orders', [])})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
