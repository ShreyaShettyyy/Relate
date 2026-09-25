import pandas as pd
import numpy as np
import random

products = [
    {"ID": 1, "Name": "MacBook Pro M2", "Category": "Electronics", "Price": 129999, "Rating": 4.8, "Image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400", "Description": "Supercharged by the M2 chip. Brilliant Retina display with extreme dynamic range. Powerful processing capabilities."},
    {"ID": 2, "Name": "iPhone 14 Pro", "Category": "Electronics", "Price": 119999, "Rating": 4.9, "Image": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=400", "Description": "Dynamic Island. 48MP Main camera. Always-On display. The revolutionary A16 Bionic chip powers incredible photography."},
    {"ID": 3, "Name": "Sony WH-1000XM5", "Category": "Electronics", "Price": 29999, "Rating": 4.8, "Image": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400", "Description": "Industry leading noise canceling headphones. Exceptional battery life of up to 30 hours and quick charging."},
    {"ID": 4, "Name": "Men's Cotton T-Shirt", "Category": "Clothing", "Price": 999, "Rating": 4.5, "Image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400", "Description": "100% pure cotton classic fit t-shirt. Breathable and comfortable for everyday wear. Available in multiple colors."},
    {"ID": 5, "Name": "Denim Jeans", "Category": "Clothing", "Price": 2499, "Rating": 4.6, "Image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400", "Description": "Premium stretch denim jeans. Classic 5-pocket styling and a versatile straight fit. Durable and stylish."},
    {"ID": 6, "Name": "Leather Jacket", "Category": "Clothing", "Price": 5999, "Rating": 4.8, "Image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", "Description": "Genuine leather motorcycle jacket with asymmetrical zip closure. A timeless wardrobe staple for any season."},
    {"ID": 7, "Name": "Gourmet Coffee Beans", "Category": "Food", "Price": 899, "Rating": 4.7, "Image": "https://images.unsplash.com/photo-1559525839-b184a4d698c7?w=400", "Description": "100% Arabica medium roast whole bean coffee. Sourced from sustainable farms in Colombia. Rich, chocolatey notes."},
    {"ID": 8, "Name": "Dark Chocolate Truffles", "Category": "Food", "Price": 1299, "Rating": 4.9, "Image": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400", "Description": "Assorted dark chocolate truffles with creamy ganache centers. Perfect for gifting or treating yourself."},
    {"ID": 9, "Name": "Organic Green Tea", "Category": "Food", "Price": 499, "Rating": 4.4, "Image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400", "Description": "Premium organic green tea leaves packed with antioxidants. Refreshing and soothing natural flavor."},
    {"ID": 10, "Name": "The Great Gatsby", "Category": "Books", "Price": 399, "Rating": 4.8, "Image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400", "Description": "F. Scott Fitzgerald's classic novel of the Jazz Age. A tragic story of love, wealth, and the American Dream."},
    {"ID": 11, "Name": "Atomic Habits", "Category": "Books", "Price": 699, "Rating": 4.9, "Image": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400", "Description": "An easy and proven way to build good habits and break bad ones. Master small changes for remarkable results."},
    {"ID": 12, "Name": "Scented Candle", "Category": "Home", "Price": 799, "Rating": 4.6, "Image": "https://images.unsplash.com/photo-1603006905003-be475563bc59?w=400", "Description": "Lavender and vanilla scented soy wax candle. Burns cleanly for up to 40 hours. Creates a relaxing atmosphere."},
    {"ID": 13, "Name": "Throw Blanket", "Category": "Home", "Price": 1499, "Rating": 4.7, "Image": "https://images.unsplash.com/photo-1580301762395-21ce84d00bc6?w=400", "Description": "Ultra-soft faux fur throw blanket. Adds warmth and texture to your sofa or bed. Machine washable."},
    {"ID": 14, "Name": "Ceramic Coffee Mug", "Category": "Home", "Price": 299, "Rating": 4.5, "Image": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=400", "Description": "Large 15oz ceramic mug with an ergonomic handle. Microwave and dishwasher safe. Perfect for your morning brew."},
    {"ID": 15, "Name": "Running Shoes", "Category": "Clothing", "Price": 4999, "Rating": 4.7, "Image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", "Description": "Lightweight and breathable running shoes with responsive cushioning. Engineered for maximum comfort on the track."},
    {"ID": 16, "Name": "Wireless Earbuds", "Category": "Electronics", "Price": 3999, "Rating": 4.3, "Image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400", "Description": "True wireless earbuds with deep bass and clear treble. IPX7 waterproof rating and 24-hour battery life with case."}
]

df_products = pd.DataFrame(products)
df_products.to_csv("products.csv", index=False)

transactions = []
transaction_id = 1
customers = list(range(1001, 1051))

for _ in range(1000):
    cust_id = random.choice(customers)
    basket_type = random.choice(['tech_buyer', 'clothing_buyer', 'food_buyer', 'home_buyer', 'reader', 'random'])
    
    basket = []
    if basket_type == 'tech_buyer':
        basket.append(random.choice([1, 2]))
        if random.random() > 0.4: basket.append(3)
        if random.random() > 0.5: basket.append(16)
    elif basket_type == 'clothing_buyer':
        basket.append(4)
        if random.random() > 0.3: basket.append(5)
        if random.random() > 0.5: basket.append(6)
        if random.random() > 0.7: basket.append(15)
    elif basket_type == 'food_buyer':
        basket.append(7)
        if random.random() > 0.2: basket.append(8)
        if random.random() > 0.5: basket.append(9)
        if random.random() > 0.6: basket.append(14)
    elif basket_type == 'home_buyer':
        basket.append(12)
        if random.random() > 0.3: basket.append(13)
    elif basket_type == 'reader':
        basket.append(10)
        if random.random() > 0.4: basket.append(11)
        if random.random() > 0.6: basket.append(7)
    else:
        basket = random.sample(range(1, 17), k=random.randint(1, 3))
        
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
