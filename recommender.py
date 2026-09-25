import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RecommenderSystem:
    def __init__(self, transactions_df):
        self.transactions_df = transactions_df
        self.frequent_itemsets = None
        self.rules = None

    def _prepare_market_basket_data(self):
        basket = (self.transactions_df
                  .groupby(['TransactionID', 'Item'])['Item']
                  .count().unstack().reset_index().fillna(0)
                  .set_index('TransactionID'))
        
        def encode_units(x):
            if x <= 0: return 0
            if x >= 1: return 1
        
        return basket.map(encode_units)

    def train_market_basket(self, min_support=0.05, min_threshold=1.0):
        print("Training Market Basket Model...")
        basket_sets = self._prepare_market_basket_data()
        self.frequent_itemsets = apriori(basket_sets, min_support=min_support, use_colnames=True)
        if self.frequent_itemsets.empty:
            print("No frequent itemsets found.")
            return
        self.rules = association_rules(self.frequent_itemsets, metric="lift", min_threshold=min_threshold)
        print("Market Basket Model trained successfully.")

    def get_frequently_bought_with(self, item, top_n=3):
        if self.rules is None or self.rules.empty:
            return []
        
        # Find rules where item is in antecedents
        relevant_rules = self.rules[self.rules['antecedents'].apply(lambda x: item in x)]
        if relevant_rules.empty:
            return []
            
        relevant_rules = relevant_rules.sort_values(['lift', 'confidence'], ascending=[False, False]).head(top_n)
        
        recommendations = set()
        for idx, row in relevant_rules.iterrows():
            for consequent in row['consequents']:
                recommendations.add(consequent)
                
        return list(recommendations)[:top_n]

    def get_user_frequently_bought_with(self, customer_id, item, top_n=3):
        # Find transactions where THIS user bought THIS item
        user_txns = self.transactions_df[self.transactions_df['CustomerID'] == customer_id]
        txns_with_item = user_txns[user_txns['Item'] == item]['TransactionID'].unique()
        
        if len(txns_with_item) == 0:
            return []
            
        # What else did they buy in these specific transactions?
        items_in_same_txns = user_txns[user_txns['TransactionID'].isin(txns_with_item)]
        
        # Count frequencies of other items
        item_counts = items_in_same_txns[items_in_same_txns['Item'] != item]['Item'].value_counts()
        
        return item_counts.head(top_n).index.tolist()

if __name__ == "__main__":
    df = pd.read_csv('transactions.csv')
    rec = RecommenderSystem(df)
    rec.train_market_basket(min_support=0.1)
    print("Global with Bread:", rec.get_frequently_bought_with('Bread'))
    print("User 101 with Brush:", rec.get_user_frequently_bought_with(101, 'Brush'))
