# Relate (LuxStore) - Intelligent Machine Learning E-Commerce Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![MLxtend](https://img.shields.io/badge/Machine%20Learning-MLxtend%20(Apriori)-orange.svg)](http://rasbt.github.io/mlxtend/)
[![Node.js](https://img.shields.io/badge/Microservice-Node.js%20Nodemailer-brightgreen.svg)](https://nodejs.org/)
[![GSAP](https://img.shields.io/badge/Frontend-GSAP%203%20Animations-yellow.svg)](https://greensock.com/gsap/)

**Relate (LuxStore)** is a full-stack e-commerce web platform and recommendation engine designed to discover authentic product relationships and deliver personalized shopping experiences based on customer purchasing patterns.

Unlike traditional stores that merely recommend recently purchased products back to the user, Relate uses **Market Basket Analysis** (via the **Apriori Algorithm**), **Association Rule Mining** (Support, Confidence, and Lift), **Accessory Compatibility Mapping**, and **TF-IDF Content Similarity** to intelligently surface genuine companion accessories, direct alternatives, and personalized discovery feeds in real time.

In addition to the core LuxStore application, this repository includes an end-to-end **Instacart Market Basket Analysis Machine Learning Pipeline** capable of preprocessing massive real-world grocery transaction datasets (over 3.4 million orders) and training production-ready Apriori association rule models.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Project Folder Structure](#project-folder-structure)
4. [Machine Learning Algorithms Used](#machine-learning-algorithms-used)
   - [Apriori Algorithm](#1-apriori-algorithm-market-basket-analysis)
   - [Association Rule Mining](#2-association-rule-mining)
   - [Support, Confidence, and Lift](#support-confidence-and-lift)
5. [Instacart Market Basket Dataset & ML Pipeline](#instacart-market-basket-dataset--ml-pipeline)
   - [Dataset Description](#instacart-dataset-description)
   - [Dataset Preprocessing Pipeline](#dataset-preprocessing-process)
   - [Model Training Process](#model-training-process)
   - [Evaluation & Validation Metrics](#model-evaluation--validation-methodology)
   - [Saved Model Artifacts](#model-artifact-locations)
6. [How the LuxStore Recommendation Engine Works](#how-the-luxstore-recommendation-engine-works)
7. [The Dedicated Product Detail Recommendation Rails](#the-dedicated-product-detail-recommendation-rails)
8. [Technology Stack](#technology-stack)
9. [Installation & Setup](#installation--setup)
10. [Execution Commands](#execution-commands)
    - [Train Instacart ML Model](#1-train-the-instacart-apriori-model)
    - [Run the Web Application](#2-run-the-relate-luxstore-web-application)
    - [Run Automated Tests](#3-run-automated-test-suites)
11. [REST API Documentation](#rest-api-documentation)
12. [License](#license)

---

## Project Overview

When a user browses an e-commerce catalog (such as viewing a smartphone, laptop, or camera), naive recommendation systems often suggest competing devices or items the customer already bought. Relate solves this:

- **When viewing a Smartphone:** Recommends screen protectors, shockproof cases, 20W fast chargers, braided USB-C cables, magnetic wireless power banks, and desktop stands.
- **When viewing a Laptop:** Recommends water-resistant laptop bags/sleeves, wireless ergonomic mice, mechanical keyboards, cooling pads, aluminum stands, and multiport USB-C hubs.
- **When viewing a Camera:** Recommends SDXC memory cards, camera shoulder bags, aluminum tripods, high-capacity battery packs, and zoom lenses.
- **Personal Purchase Patterns:** If and only if the current buyer has previously checked out items together, the system personalizes recommendations with `"You usually buy this product with {X}"`.
- **Community Purchase Patterns:** Surfaces items frequently bought together across other customer accounts (`"Most people buy this with {X}"`).
- **Separation of History & Discovery:** Recently purchased items and recommended products are kept strictly separate.

---

## Key Features

1. **Intelligent Multi-Rail Recommendation Engine**:
   - **Personal Purchase History**: Past multi-item co-purchases unique to the current user.
   - **Frequently Bought Together**: Association rules with highest Lift and Confidence, plus a 1-click **"Add All to Cart"** bundle button.
   - **Recommended Accessories**: Domain-specific compatibility mapping combined with association rule mining.
   - **Similar Products**: Competing alternatives within the same category ranked by TF-IDF cosine similarity.
   - **You May Also Like**: Cross-category collaborative discovery based on buyer lifestyle affinities.
2. **Personalized Home Discovery Feed**:
   - Tailored specifically to logged-in customers based on past order categories, unpurchased companion add-ons, and association patterns with clear justification tags.
3. **Dedicated User Profile Dashboard**:
   - Full personal account management: view/edit name, customer ID, member since date, order history, and saved wishlist.
   - Secure in-app password change with current password verification.
4. **Forgot Password via Email OTP (Nodemailer Microservice)**:
   - 3-step security wizard: Email verification $\rightarrow$ 6-digit OTP $\rightarrow$ New Password.
   - Time-limited OTP (expires in 5 minutes), maximum 5 verification attempts, and 60-second resend cooldown.
   - Dispatched securely using Node.js and Nodemailer over SMTP (with automatic dev-mode simulation logging to `logs/otp_dev_log.json`).
5. **Modern Luxury UI & GSAP Micro-Interactions**:
   - Dark luxury aesthetic with glassmorphism cards and glowing ambient accents.
   - Smooth entrance animations, hover transforms, stepper controls, slide-over cart drawer, and smart upsell checkout modal.
   - Toast notifications with progress indicators for all cart, wishlist, and order actions.
6. **Dynamic Real-Time Application Retraining**:
   - Placing an order in LuxStore appends transactions to `data/application/transactions.csv` and retrains the live Apriori model dynamically.
7. **Instacart Enterprise ML Pipeline**:
   - Separate, memory-optimized preprocessing, training, evaluation, and loading modules for large-scale grocery basket analysis.

---

## Project Folder Structure

The project follows a clean, modular structure separating configuration, datasets, machine learning pipelines, application services, static assets, and tests:

```text
ML-Project/
│
├── app.py                      # Flask Application entry point and REST API routes
├── generate_data.py            # Synthetic catalog & transaction generator for LuxStore
├── email_service.js            # Node.js Nodemailer microservice for secure OTP dispatch
│
├── config/
│   ├── __init__.py             # Config package initialization
│   └── config.py               # Centralized pathlib paths, environment variables, settings
│
├── data/
│   ├── raw/
│   │   └── instacart/          # Raw downloaded Instacart CSV datasets
│   │       ├── aisles.csv
│   │       ├── departments.csv
│   │       ├── orders.csv
│   │       ├── order_products__prior.csv
│   │       ├── order_products__train.csv
│   │       └── products.csv
│   │
│   ├── processed/              # Preprocessed ML artifacts ready for modeling
│   │   ├── instacart_products_catalog.csv
│   │   ├── product_frequencies.csv
│   │   ├── order_baskets.json
│   │   └── preprocessing_metadata.json
│   │
│   └── application/            # Application production data stores
│       ├── products.csv        # LuxStore active catalog (276 products across 10 categories)
│       ├── transactions.csv    # Transaction logs (TransactionID, CustomerID, Item)
│       └── users.json          # User accounts, hashed passwords, carts, wishlists, orders
│
├── ml/
│   ├── __init__.py             # ML package exports
│   ├── preprocessing.py        # Instacart raw data ingestion, dtype downcasting & basket grouping
│   ├── association_rules.py    # Sparse TransactionEncoder, Apriori mining & rule evaluation helpers
│   ├── train_model.py          # Apriori training pipeline, train/val evaluation & report generation
│   ├── model_loader.py         # Zero-overhead model loader and inference query interface
│   └── saved_models/           # Serialized model artifacts
│       ├── instacart_frequent_itemsets.pkl
│       ├── instacart_rules.pkl
│       ├── instacart_rules.csv
│       └── model_metadata.json
│
├── services/
│   ├── __init__.py             # Services package exports
│   ├── auth_service.py         # User registration, login verification, profile management
│   ├── recommendation_service.py # RecommenderSystem class (Apriori, Co-purchases, Accessories, TF-IDF)
│   └── email_service.py        # OTP generation, rate limiting, and Node.js microservice bridge
│
├── templates/
│   └── index.html              # Main application storefront SPA template
│
├── static/
│   ├── css/
│   │   └── style.css           # Luxury dark glassmorphism design system & responsive styling
│   ├── js/
│   │   └── script.js           # Frontend controller, GSAP animations, cart, auth, detail view
│   └── images/                 # Image assets
│
├── notebooks/
│   └── exploration.ipynb       # Jupyter notebook for exploratory data analysis
│
├── logs/
│   └── otp_dev_log.json        # Simulated OTP dispatch log for local testing
│
├── tests/
│   ├── __init__.py
│   ├── test_app.py             # Unit and integration tests for Flask routes, auth, and recommendations
│   └── test_ml.py              # Unit and integration tests for Instacart preprocessing and model loader
│
├── .env                        # Local environment variables (SMTP, Secret Keys)
├── .env.example                # Sample environment variable template
├── .gitignore                  # Git ignore rules (node_modules, venv, raw large CSVs)
├── requirements.txt            # Python dependencies (flask, pandas, mlxtend, scikit-learn, etc.)
├── package.json                # Node.js dependencies (nodemailer, dotenv)
├── package-lock.json           # Node.js lockfile
└── README.md                   # Comprehensive project documentation
```

---

## Machine Learning Algorithms Used

### 1. Apriori Algorithm (Market Basket Analysis)
The Apriori algorithm identifies frequent itemsets across transaction records by applying the **anti-monotone property**: *all subsets of a frequent itemset must also be frequent; if an itemset is infrequent, all its supersets are pruned.*

- Input: Binary transaction matrix ($TransactionID \times Item$).
- Output: Frequent itemsets with support $\ge \text{min\_support}$.

### 2. Association Rule Mining
From frequent itemsets, directional rules $A \rightarrow B$ are derived.

### Support, Confidence, and Lift

$$\text{Support}(A \rightarrow B) = \frac{\text{Count}(A \cup B)}{N}$$

$$\text{Confidence}(A \rightarrow B) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$$

$$\text{Lift}(A \rightarrow B) = \frac{\text{Confidence}(A \rightarrow B)}{\text{Support}(B)} = \frac{\text{Support}(A \cup B)}{\text{Support}(A) \times \text{Support}(B)}$$

- **$\text{Lift} > 1$**: Indicates a strong positive association. Items $A$ and $B$ are genuinely complementary and co-purchased significantly more frequently than chance.
- **$\text{Lift} = 1$**: Items $A$ and $B$ are completely independent.
- **$\text{Lift} < 1$**: Negative correlation / substitution.

### 3. TF-IDF & Cosine Similarity (Content Filtering)
Used by `get_similar_products` to match alternative products within the same category based on attribute descriptions:

$$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$

---

## Instacart Market Basket Dataset & ML Pipeline

### Instacart Dataset Description
The Instacart dataset is a widely recognized benchmark dataset for Market Basket Analysis, consisting of over 3.4 million grocery orders from more than 200,000 anonymized users.

The six CSV files located in `data/raw/instacart/` contain:
1. **`orders.csv`** (3,421,083 rows): Order metadata including `order_id`, `user_id`, `eval_set` (`prior`, `train`, `test`), `order_number`, `order_dow` (day of week), `order_hour_of_day`, and `days_since_prior_order`.
2. **`products.csv`** (49,688 rows): Product names and mappings to aisles and departments (`product_id`, `product_name`, `aisle_id`, `department_id`).
3. **`aisles.csv`** (134 rows): Aisle categories (e.g. *fresh fruits*, *packaged cheese*, *water seltzer sparkling water*).
4. **`departments.csv`** (21 rows): Top-level department categories (e.g. *produce*, *dairy eggs*, *beverages*, *bakery*).
5. **`order_products__train.csv`** (1,384,617 rows): Products purchased in each of the 131,209 `train` orders, with `add_to_cart_order` and `reordered` flags.
6. **`order_products__prior.csv`** (32,434,489 rows): Products purchased across all 3.21 million historical customer orders.

### Dataset Preprocessing Process
Implemented in `ml/preprocessing.py`:
1. **Downcasting & Missing Value Handling:** Downcasts integer IDs to `uint32`, category indices to `uint16`/`uint8`. Fills missing values in `days_since_prior_order` for first-time orders with `0.0`.
2. **Hierarchical Merging:** Enriches `products.csv` with textual aisle and department names.
3. **Partition Combination Without Duplication:** Combines all 131,209 `train` orders with a statistically representative sample of 50,000 `prior` orders (totaling over 180,000 distinct orders and 1.88 million line items) while verifying zero `order_id` collisions.
4. **Frequency Analysis & Dimensionality Optimization:** Computes frequency counts across all products. Focuses on the top 350 most active items (accounting for the vast majority of cross-order co-occurrences) to prevent combinatorial state-space explosion.
5. **Multi-Item Basket Extraction:** Groups product names by `order_id` and excludes single-item baskets (`len < 2`), yielding **121,262 multi-item transaction baskets** stored in `data/processed/order_baskets.json`.

### Model Training Process
Implemented in `ml/train_model.py`:
- **Train / Validation Split:** Shuffles and splits baskets into **80% Training (97,009 baskets)** and **20% Validation (24,253 baskets)**.
- **Sparse One-Hot Encoding:** Uses `mlxtend.preprocessing.TransactionEncoder(sparse=True)` to convert baskets into a scipy sparse matrix (`97,009 × 350`), drastically reducing memory overhead.
- **Apriori Itemset Mining:** Executes Apriori with a threshold of $\text{min\_support} = 0.008$ (0.80% of all orders), discovering **292 frequent itemsets**.
- **Association Rule Generation:** Extracts rules with $\text{min\_lift} = 1.10$ and $\text{min\_confidence} = 0.10$ (10%), generating **89 strong association rules**.

### Model Evaluation & Validation Methodology
Rather than reporting artificial accuracy metrics, the validation module evaluates rule generalizability on 10,000 unseen validation baskets:
- **Antecedent Trigger Rate:** **80.46%** of unseen validation baskets matched at least one discovered rule antecedent.
- **Rule Validation Precision (Hit Rate):** **18.71%** of triggered rule activations resulted in the consequent being present in the validation basket.
- **Mean Training Confidence:** **0.2116** (21.16%).
- **Mean Training Lift:** **1.85** (Maximum Lift: **4.38**).

#### Top Mined Instacart Association Rules
| Antecedent Product | Consequent Product | Support | Confidence | Lift | Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Limes** | **Organic Cilantro** | 1.05% | 15.99% | **4.38** | Strong complementary pairing for salsa/Mexican cooking. |
| **Organic Cilantro** | **Limes** | 1.05% | 28.84% | **4.38** | Over 28% of cilantro buyers also purchase limes. |
| **Organic Yellow Onion** | **Organic Garlic** | 0.94% | 19.41% | **4.04** | Fundamental aromatic cooking staples co-purchased together. |
| **Organic Garlic** | **Organic Yellow Onion** | 0.94% | 19.64% | **4.04** | Garlic purchases strongly predict yellow onion co-purchase. |
| **Limes** | **Large Lemon** | 1.65% | 25.03% | **2.97** | Citrus pairing with 25% purchase confidence. |

> **Limitations of MBA Evaluation:** Market Basket Analysis identifies statistical co-occurrence and directional correlation ($A \rightarrow B$). It does not establish causal directionality or substitute for supervised ground truth labels. Validation measures empirical relevance on held-out transactions.

### Model Artifact Locations
Trained artifacts are persisted in `ml/saved_models/`:
- **`instacart_frequent_itemsets.pkl`**: Serialized MLxtend frequent itemsets DataFrame.
- **`instacart_rules.pkl`**: Serialized association rules DataFrame with metrics.
- **`instacart_rules.csv`**: Exported CSV with readable antecedent and consequent strings sorted by Lift.
- **`model_metadata.json`**: Comprehensive training run configuration, timestamps, dataset parameters, evaluation statistics, and top rules.

---

## How the LuxStore Recommendation Engine Works

```
                                  [ User Browses / Purchases Product ]
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 ▼                                                                     ▼
      [ Product Detail View ]                                              [ Customer Feed / Profile ]
                 │                                                                     │
 ┌───────────────┼───────────────┬───────────────┐                             ┌───────┴───────┐
 │               │               │               │                             ▼               ▼
 ▼               ▼               ▼               ▼                     [ Personalized ]  [ Recently ]
Personal     Frequently     Recommended       Similar                     Feed Based     Purchased
Purchase     Bought         Accessories       Products                    on History     (Separate)
History      Together       (Compatibility   (TF-IDF Category                  │
(Prior User  (Cross-Account  + High Lift)     Competitors)                     ▼
 Baskets)     Apriori Rules)                                          Personal & Crowd Co-Purchases
                                                                       & Lift Association Rules
```

1. **Transaction Processing:** Historical records are converted to a sparse boolean DataFrame.
2. **Rule Generation:** `mlxtend.frequent_patterns.apriori` and `association_rules` produce rules sorted by $\text{Lift} \times \text{Confidence}$.
3. **Cross-Account Co-Purchase Mining:** The engine analyzes baskets across all user accounts in `data/application/transactions.csv`:
   - **Personal Co-Purchases (`"You usually buy this product with {X}"`):** Triggered **if and only if** the current buyer has previously purchased that exact combination of products together in a past order basket.
   - **Community Co-Purchases (`"Most people buy this with {X}"`):** Surfaces items frequently checked out in the same basket by other shopper accounts.
   - **Strict Zero-Random Guarantee:** If a product has never been purchased with another product across accounts, the engine surfaces only verified compatible hardware accessories (e.g. companion cases/cables) or hides the rail completely. Random filler items are never displayed.
4. **Filtering & Deduplication:** The currently viewed product is excluded. Already-purchased devices are pruned from feeds, while complementary accessories remain eligible.
5. **Dynamic Update:** When a user checks out, new rows are appended to `data/application/transactions.csv` and `recommender.train_market_basket()` re-computes rules immediately.

---

## The Dedicated Product Detail Recommendation Rails

| Rail Name | Algorithm Strategy | Purpose & Example |
| :--- | :--- | :--- |
| **Personal Purchase History** | Buyer's Past Multi-Item Baskets | *(Shows if and only if buyer bought together before)* Displays: *"You usually buy this product with {X}"*. |
| **Frequently Bought Together** | Apriori Association Rules ($\text{Lift} > 1$) + Basket Co-occurrence | Bundles companion items commonly checked out together across accounts: *"Most people buy this with {X}"*. Includes a 1-click **"Add All to Cart"** bundle button. |
| **Recommended Accessories** | Domain Compatibility Engine + High-Lift Association Rules | Specifically filters and ranks accessories (cases, cables, adapters, stands, bags, memory cards, mice) tailored to the active hardware. |
| **Similar Products** | TF-IDF Cosine Similarity on Category & Description + Rating Boost | Shows competing or alternative models in the same category (e.g. *MacBook Pro* $\rightarrow$ *DELL XPS 13*, *Asus Zenbook*, *Lenovo Yoga*). |
| **You May Also Like** | Cross-Category Collaborative Filtering | Recommends items explored by user cohorts with shared lifestyle patterns. |

---

## Technology Stack

- **Backend Framework:** Python 3.9+ / Flask 3.1
- **Machine Learning Libraries:** `mlxtend` 0.25, `pandas` 3.0, `scikit-learn` 1.8, `numpy` 2.4
- **Email Microservice:** Node.js v18+ / `nodemailer` 6.9 / `dotenv`
- **Frontend Architecture:** Vanilla JavaScript (ES6+), HTML5, CSS3 Glassmorphism
- **Animations:** GSAP 3.12 (GreenSock Animation Platform) & ScrollTrigger
- **Typography & Icons:** Google Fonts (*Outfit*, *Plus Jakarta Sans*), Font Awesome 6
- **Data Stores:** `data/application/products.csv`, `data/application/transactions.csv`, `data/application/users.json`

---

## Installation & Setup

### Prerequisites
- **Python 3.9+** (Tested on Python 3.14)
- **Node.js 18+** (with npm)
- **Git**

### 1. Python Virtual Environment & Dependencies
On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Node.js & Nodemailer Setup
Install Node.js dependencies:
```bash
npm install
```

### 3. Environment Variable Configuration
Create a `.env` file in the project root:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_specific_password
EMAIL_FROM="Relate LuxStore" <no-reply@luxstore.com>

FLASK_ENV=development
SECRET_KEY=luxstore-ml-secure-key-2026
```
> [!NOTE]
> If SMTP credentials are not configured, the Node.js email service automatically simulates email dispatch and logs OTP codes to `logs/otp_dev_log.json` and the console for seamless local testing.

---

## Execution Commands

### 1. Train the Instacart Apriori Model
To run the full preprocessing pipeline and train the Apriori model on the Instacart dataset:
```bash
# Run preprocessing standalone (optional)
python -m ml.preprocessing

# Train the Apriori model and evaluate rules
python -m ml.train_model
```

### 2. Run the Relate (LuxStore) Web Application
Start the Flask server:
```bash
python app.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

Demo Accounts:
- `15shreyashetty@gmail.com` (Password: `0613`, Customer ID: `#1101`)
- `k@gmain.com` (Password: `0613`, Customer ID: `#1102`)

### 3. Run Automated Test Suites
Run all unit and integration tests covering the web application, APIs, and the ML pipeline:
```bash
python -m unittest discover tests
```

---

## REST API Documentation

### 1. Catalog & Metadata
- **`GET /api/metadata`**
  - Returns: `{ "customers": [...], "products": [...], "categories": [...] }`

### 2. Multi-Rail Recommendations
- **`GET /api/product_recs?product={product_name}&customer_id={id}`**
  - Returns:
    ```json
    {
      "product": "iPhone 13 Pro",
      "personal_copurchases": [ ... ],
      "frequently_bought_together": [ ... ],
      "recommended_accessories": [ ... ],
      "similar_products": [ ... ],
      "you_may_also_like": [ ... ]
    }
    ```

### 3. Home Discovery Feed
- **`GET /api/feed?customer_id={id}`**
  - Returns personalized items with justification reasons and past purchase history:
    ```json
    {
      "personalized": true,
      "recommendations": [
        { "Name": "...", "recommendation_reason": "You usually buy this product with...", ... }
      ],
      "recently_purchased": [ ... ]
    }
    ```

### 4. Authentication
- **`POST /api/auth/register`**
  - Body: `{ "name": "...", "email": "...", "password": "..." }`
- **`POST /api/auth/login`**
  - Body: `{ "email": "...", "password": "..." }`

### 5. Forgot Password via OTP
- **`POST /api/auth/forgot-password/send-otp`**
  - Body: `{ "email": "..." }`
- **`POST /api/auth/forgot-password/verify-otp`**
  - Body: `{ "email": "...", "otp": "123456" }`
- **`POST /api/auth/forgot-password/reset-password`**
  - Body: `{ "email": "...", "new_password": "..." }`

### 6. User Profile Management
- **`GET /api/user/profile?email={email}`**
  - Returns profile summary, order count, and customer ID.
- **`PUT /api/user/profile`**
  - Body: `{ "email": "...", "name": "New Name" }`
- **`POST /api/user/change-password`**
  - Body: `{ "email": "...", "current_password": "...", "new_password": "..." }`

### 7. Cart, Wishlist & Orders
- **`GET /api/user/data?email={email}`**
  - Returns user's cart, wishlist, and order history.
- **`POST /api/user/data`**
  - Body: `{ "email": "...", "cart": [...], "wishlist": [...], "new_order": { ... } }`
  - Appends new transactions to `data/application/transactions.csv` and dynamically retrains the model.

---

## License
This project is open-source and available under the [ISC License](LICENSE).
