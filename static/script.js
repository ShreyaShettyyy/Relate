document.addEventListener('DOMContentLoaded', () => {
    let allProducts = [];
    let currentCategory = 'All';
    let currentCustomer = null;
    let currentProductObj = null;

    // Fetch Data
    fetch('/api/metadata')
        .then(res => res.json())
        .then(data => {
            allProducts = data.products;
            
            // Populate Categories dynamically
            const catSet = new Set(allProducts.map(p => p.Category));
            const catList = document.getElementById('category-list');
            Array.from(catSet).sort().forEach(cat => {
                const li = document.createElement('li');
                li.setAttribute('data-cat', cat);
                li.textContent = cat;
                catList.appendChild(li);
            });
            
            bindCategoryClicks();
            renderGrid(allProducts, document.getElementById('product-grid'));
        });

    function bindCategoryClicks() {
        document.querySelectorAll('#category-list li').forEach(li => {
            li.addEventListener('click', (e) => {
                document.querySelectorAll('#category-list li').forEach(el => el.classList.remove('active-cat'));
                e.target.classList.add('active-cat');
                currentCategory = e.target.getAttribute('data-cat');
                executeSearch();
            });
        });
    }

    function generateStars(rating) {
        let starsHtml = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.floor(rating)) {
                starsHtml += '<i class="fa-solid fa-star"></i>';
            } else if (i === Math.ceil(rating) && !Number.isInteger(rating)) {
                starsHtml += '<i class="fa-solid fa-star-half-stroke"></i>';
            } else {
                starsHtml += '<i class="fa-regular fa-star"></i>';
            }
        }
        return starsHtml;
    }

    function formatPrice(price) {
        return '₹' + price.toLocaleString('en-IN');
    }

    function createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <img src="${product.Image}" alt="${product.Name}" loading="lazy" onerror="this.src='https://placehold.co/400x400/8b5cf6/ffffff?text=Image+Not+Found'">
            <div class="card-category">${product.Category}</div>
            <div class="card-title">${product.Name}</div>
            <div class="card-rating">${generateStars(product.Rating)}</div>
            <div class="card-price">${formatPrice(product.Price)}</div>
        `;
        card.addEventListener('click', () => showProductDetail(product));
        return card;
    }

    function renderGrid(products, container) {
        container.innerHTML = '';
        if (products.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align:center; padding: 2rem;">No products found.</p>';
            return;
        }
        products.forEach(p => container.appendChild(createProductCard(p)));
    }

    // Search Logic
    document.getElementById('search-btn').addEventListener('click', executeSearch);
    document.getElementById('search-input').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') executeSearch();
    });

    function executeSearch() {
        const query = document.getElementById('search-input').value.toLowerCase();
        let filtered = allProducts;
        if (currentCategory !== 'All') {
            filtered = filtered.filter(p => p.Category === currentCategory);
        }
        if (query) {
            filtered = filtered.filter(p => p.Name.toLowerCase().includes(query) || p.Description.toLowerCase().includes(query));
        }
        document.getElementById('product-detail-section').classList.add('hidden');
        document.getElementById('catalog-section').classList.remove('hidden');
        renderGrid(filtered, document.getElementById('product-grid'));
    }

    function showProductDetail(product) {
        currentProductObj = product;
        document.getElementById('catalog-section').classList.add('hidden');
        document.getElementById('product-detail-section').classList.remove('hidden');
        window.scrollTo(0, 0);
        
        document.getElementById('bread-category').textContent = product.Category;
        document.getElementById('bread-name').textContent = product.Name;
        document.getElementById('detail-image').src = product.Image;
        document.getElementById('detail-category').textContent = product.Category;
        document.getElementById('detail-title').textContent = product.Name;
        
        const ratingHtml = `${generateStars(product.Rating)} <span onclick="document.querySelector('.reviews-section').scrollIntoView({behavior: 'smooth'})" style="cursor:pointer; text-decoration:underline; color:var(--primary);">(${product.Rating} - See Reviews)</span>`;
        document.getElementById('detail-rating').innerHTML = ratingHtml;
        
        document.getElementById('detail-price').textContent = formatPrice(product.Price);
        document.getElementById('detail-desc').textContent = product.Description;
        document.getElementById('sim-cat').textContent = product.Category;
        
        // Reset wishlist icon
        const wishlistBtn = document.getElementById('wishlist-toggle');
        wishlistBtn.classList.remove('liked');
        wishlistBtn.innerHTML = '<i class="fa-regular fa-heart"></i>';
        
        const globalBlock = document.getElementById('global-recs-block');
        const personalBlock = document.getElementById('personal-recs-block');
        globalBlock.classList.add('hidden');
        personalBlock.classList.add('hidden');
        
        let url = `/api/product_recs?product=${encodeURIComponent(product.Name)}`;
        if (currentCustomer) url += `&customer_id=${currentCustomer}`;
        
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.global && data.global.length > 0) {
                    renderGrid(data.global, document.getElementById('global-recs-list'));
                    globalBlock.classList.remove('hidden');
                }
                
                if (data.personal && data.personal.length > 0) {
                    renderGrid(data.personal, document.getElementById('personal-recs-list'));
                    personalBlock.classList.remove('hidden');
                }
            });

        // Similar Category Products
        const similarProducts = allProducts.filter(p => p.Category === product.Category && p.ID !== product.ID).slice(0, 6);
        renderGrid(similarProducts, document.getElementById('similar-recs-list'));

        generateReviews(product);
    }

    function generateReviews(product) {
        const container = document.getElementById('reviews-container');
        container.innerHTML = '';
        
        const reviewTexts = [
            "Absolutely love this product! The quality is amazing and it works exactly as described. Worth every single rupee.",
            "Great purchase. The delivery was fast and the item was packaged securely. The gradients on the UI look awesome by the way!",
            "I've been using it for a week and I can highly recommend it. Will definitely buy from LuxStore again."
        ];
        
        for(let i = 1; i <= 3; i++) {
            const seed = product.ID * 10 + i;
            const rev = document.createElement('div');
            rev.className = 'review-card';
            rev.innerHTML = `
                <div class="review-header">
                    <img src="https://picsum.photos/seed/user${seed}/50/50" class="review-avatar" alt="User" onerror="this.src='https://placehold.co/50x50/8b5cf6/ffffff?text=U'">
                    <div class="review-meta">
                        <div class="review-name">Customer ${Math.floor(Math.random() * 9000 + 1000)}</div>
                        <div class="review-stars">${generateStars(product.Rating > 4.5 ? 5 : 4)}</div>
                    </div>
                </div>
                <p class="review-text">${reviewTexts[i-1]}</p>
                <div class="review-images">
                    <img src="${product.Image}" class="review-purchased-img" alt="Purchased product">
                </div>
            `;
            container.appendChild(rev);
        }
    }

    document.getElementById('back-btn').addEventListener('click', () => {
        document.getElementById('product-detail-section').classList.add('hidden');
        document.getElementById('catalog-section').classList.remove('hidden');
    });

    // Login Modal Logic
    document.getElementById('login-btn').addEventListener('click', () => {
        document.getElementById('login-modal').classList.remove('hidden');
    });
    document.getElementById('close-login').addEventListener('click', () => {
        document.getElementById('login-modal').classList.add('hidden');
    });
    document.getElementById('submit-login').addEventListener('click', () => {
        const val = document.getElementById('login-customer-id').value;
        if(val) {
            currentCustomer = val;
            document.getElementById('login-btn').classList.add('hidden');
            document.getElementById('logged-in-user').textContent = `Customer ${val}`;
            document.getElementById('logged-in-user').classList.remove('hidden');
            document.getElementById('logout-btn').classList.remove('hidden');
            document.getElementById('login-modal').classList.add('hidden');
            showToast(`Successfully logged in as Customer ${val}`);
            
            // Refresh recs if on product page
            if (currentProductObj && !document.getElementById('product-detail-section').classList.contains('hidden')) {
                showProductDetail(currentProductObj);
            }
        }
    });
    document.getElementById('logout-btn').addEventListener('click', () => {
        currentCustomer = null;
        document.getElementById('login-btn').classList.remove('hidden');
        document.getElementById('logged-in-user').classList.add('hidden');
        document.getElementById('logout-btn').classList.add('hidden');
        showToast(`Logged out successfully.`);
        if (currentProductObj && !document.getElementById('product-detail-section').classList.contains('hidden')) {
            showProductDetail(currentProductObj);
        }
    });

    // Toast Notification
    function showToast(msg) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    // Action Buttons
    document.getElementById('add-to-cart').addEventListener('click', () => showToast('Added to Cart!'));
    
    // Wishlist Toggle
    document.getElementById('wishlist-toggle').addEventListener('click', function() {
        this.classList.toggle('liked');
        if(this.classList.contains('liked')) {
            this.innerHTML = '<i class="fa-solid fa-heart"></i>';
            showToast('Added to Wishlist!');
        } else {
            this.innerHTML = '<i class="fa-regular fa-heart"></i>';
            showToast('Removed from Wishlist.');
        }
    });

    // Checkout Modal Logic
    document.getElementById('buy-now').addEventListener('click', () => {
        document.getElementById('checkout-modal').classList.remove('hidden');
        document.getElementById('checkout-item-name').textContent = currentProductObj.Name;
        document.getElementById('checkout-item-price').textContent = formatPrice(currentProductObj.Price);
        document.getElementById('checkout-total').textContent = formatPrice(currentProductObj.Price);
        document.getElementById('coupon-msg').textContent = '';
        document.getElementById('coupon-code').value = '';
        
        // Reset to UPI by default
        document.querySelector('input[value="upi"]').checked = true;
        document.getElementById('upi-options').classList.remove('hidden');
    });
    document.getElementById('close-checkout').addEventListener('click', () => {
        document.getElementById('checkout-modal').classList.add('hidden');
    });
    document.getElementById('apply-coupon').addEventListener('click', () => {
        const code = document.getElementById('coupon-code').value;
        if(code.toLowerCase() === 'lux10') {
            document.getElementById('coupon-msg').textContent = '10% Discount Applied!';
            document.getElementById('coupon-msg').style.color = 'green';
            document.getElementById('checkout-total').textContent = formatPrice(currentProductObj.Price * 0.9);
        } else {
            document.getElementById('coupon-msg').textContent = 'Invalid Coupon Code';
            document.getElementById('coupon-msg').style.color = 'red';
            setTimeout(() => document.getElementById('coupon-msg').style.color = 'green', 2000);
        }
    });
    
    // UPI selection
    let selectedUpiApp = "Google Pay";
    document.querySelectorAll('.upi-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.upi-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedUpiApp = btn.getAttribute('data-app');
            document.querySelector('input[value="upi"]').checked = true;
        });
    });
    document.querySelectorAll('input[name="payment"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if(e.target.value === 'upi') {
                document.getElementById('upi-options').classList.remove('hidden');
            } else {
                document.getElementById('upi-options').classList.add('hidden');
            }
        });
    });

    // Place Order & Tracking Flow
    document.getElementById('place-order-btn').addEventListener('click', () => {
        const paymentMethod = document.querySelector('input[name="payment"]:checked').value;
        
        document.getElementById('checkout-modal').classList.add('hidden');
        
        if (paymentMethod === 'upi') {
            document.getElementById('processing-text').textContent = `Waiting for payment on ${selectedUpiApp}...`;
        } else {
            document.getElementById('processing-text').textContent = 'Processing Payment...';
        }
        
        document.getElementById('processing-modal').classList.remove('hidden');
        
        setTimeout(() => {
            document.getElementById('processing-modal').classList.add('hidden');
            document.getElementById('order-number').textContent = Math.floor(100000 + Math.random() * 900000);
            document.getElementById('tracking-modal').classList.remove('hidden');
        }, 3000);
    });

    document.getElementById('close-tracking').addEventListener('click', () => {
        document.getElementById('tracking-modal').classList.add('hidden');
    });
});
