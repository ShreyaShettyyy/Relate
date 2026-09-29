from flask import Flask, render_template, request, jsonify
import pandas as pd
from recommender import RecommenderSystem

app = Flask(__name__)

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
        
    feed_recs = recommender.get_user_feed_recommendations(customer_id, top_n=8)
    
    def get_prod_details(names):
        return df_prod[df_prod['Name'].isin(names)].to_dict('records')
        
    return jsonify({
        "feed": get_prod_details(feed_recs)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
