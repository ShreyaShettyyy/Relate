document.addEventListener('DOMContentLoaded', () => {
    let allProducts = [];
    let currentCategory = 'All';
    let currentUser = null;
    let currentProductObj = null;
    let cart = [];
    let wishlist = [];
    let orders = [];
    let checkoutMode = 'direct';
    let checkoutTotalAmt = 0;

    function navigateTo(sectionId, push = true) {
        document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
        document.getElementById(sectionId).classList.remove('hidden');
        window.scrollTo(0, 0);
        if (push) {
            history.pushState({ section: sectionId }, '', `#${sectionId}`);
        }
    }

    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.section) {
            navigateTo(e.state.section, false);
        } else {
            navigateTo('catalog-section', false);
        }
    });
    history.replaceState({ section: 'catalog-section' }, '', '#catalog-section');

    const flipCategories = [
        { name: "Top Offers", img: "https://img.icons8.com/color/96/000000/discount--v1.png", cat: "All" },
        { name: "Mobiles", img: "https://img.icons8.com/color/96/000000/smartphone--v1.png", cat: "Smartphones" },
        { name: "Electronics", img: "https://img.icons8.com/color/96/000000/tv.png", cat: "Electronics" },
        { name: "Fashion", img: "https://img.icons8.com/color/96/000000/t-shirt.png", cat: "Fashion" },
        { name: "Beauty", img: "https://img.icons8.com/color/96/000000/cosmetic-brush.png", cat: "Beauty" },
        { name: "Home", img: "https://img.icons8.com/color/96/000000/sofa.png", cat: "Home & Kitchen" },
        { name: "Grocery", img: "https://img.icons8.com/color/96/000000/shopping-cart.png", cat: "Groceries" }
    ];

    // Fetch Data
    fetch('/api/metadata')
        .then(res => res.json())
        .then(data => {
            allProducts = data.products;
            
            const catList = document.getElementById('flipkart-category-list');
            flipCategories.forEach(c => {
                const div = document.createElement('div');
                div.className = 'flip-cat-item';
                div.innerHTML = `<img src="${c.img}"><span>${c.name}</span>`;
                div.addEventListener('click', () => {
                    currentCategory = c.cat;
                    executeSearch();
                });
                catList.appendChild(div);
            });
            
            // Mix Top Rated and Deals to the front for guests
            const topRated = [...allProducts].sort((a,b) => b.Rating - a.Rating).slice(0, 10);
            const deals = [...allProducts].sort(() => 0.5 - Math.random()).slice(0, 10);
            
            const combinedFront = [...topRated, ...deals];
            const frontIds = new Set(combinedFront.map(p => p.ID));
            const rest = allProducts.filter(p => !frontIds.has(p.ID));
            
            currentFeedList = [...combinedFront, ...rest];
            renderGrid(currentFeedList, document.getElementById('product-grid'));
        });

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
            <img src="${product.Image}" alt="${product.Name}" loading="lazy" onerror="this.onerror=null; this.src='https://picsum.photos/seed/${product.ID}/400/400'">
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

    document.getElementById('search-btn').addEventListener('click', executeSearch);
    document.getElementById('search-input').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') executeSearch();
    });

    let currentFeedList = [];

    function executeSearch() {
        if (currentFeedList.length === 0) currentFeedList = allProducts;
        const query = document.getElementById('search-input').value.toLowerCase();
        let filtered = currentFeedList;
        if (currentCategory !== 'All') {
            filtered = filtered.filter(p => p.Category === currentCategory || p.Category.includes(currentCategory));
        }
        if (query) {
            filtered = filtered.filter(p => p.Name.toLowerCase().includes(query) || p.Description.toLowerCase().includes(query));
        }
        navigateTo('catalog-section');
        renderGrid(filtered, document.getElementById('product-grid'));
    }

    function showProductDetail(product) {
        currentProductObj = product;
        navigateTo('product-detail-section');
        
        document.getElementById('bread-category').textContent = product.Category;
        document.getElementById('bread-name').textContent = product.Name;
        document.getElementById('detail-image').src = product.Image;
        document.getElementById('detail-title').textContent = product.Name;
        
        // Thumbnails
        const thumbContainer = document.getElementById('detail-thumbnails');
        thumbContainer.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const img = document.createElement('img');
            let imgSrc = product.Image;
            if (i > 0) {
                imgSrc = `https://picsum.photos/seed/${product.ID * 10 + i}/400/400`;
            }
            img.src = imgSrc;
            img.onerror = () => { img.src = `https://placehold.co/400x400/eeeeee/333333?text=View+${i+1}`; };
            img.style.cssText = 'width: 60px; height: 60px; object-fit: contain; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; padding: 4px;';
            if (i === 0) img.style.borderColor = '#2874f0';
            img.addEventListener('click', () => {
                document.getElementById('detail-image').src = imgSrc;
                Array.from(thumbContainer.children).forEach(c => c.style.borderColor = '#ddd');
                img.style.borderColor = '#2874f0';
            });
            thumbContainer.appendChild(img);
        }

        // Mock Product Highlights
        const highlights = document.getElementById('product-highlights');
        highlights.innerHTML = `
            <li><strong>Category:</strong> ${product.Category}</li>
            <li><strong>Base Material:</strong> Premium Quality</li>
            <li><strong>Occasion:</strong> Everyday & Festive</li>
            <li><strong>Color:</strong> Multi-variant</li>
            <li><strong>Rating:</strong> ${product.Rating} out of 5</li>
        `;
        
        const ratingHtml = `${generateStars(product.Rating)} <span onclick="document.querySelector('.reviews-section').scrollIntoView({behavior: 'smooth'})" style="cursor:pointer; text-decoration:underline; color:var(--primary);">(${product.Rating} - See Reviews)</span>`;
        document.getElementById('detail-rating').innerHTML = ratingHtml;
        
        document.getElementById('detail-price').textContent = formatPrice(product.Price);
        document.getElementById('detail-desc').textContent = product.Description;
        
        const wishlistBtn = document.getElementById('wishlist-toggle');
        if (wishlist.includes(product.ID)) {
            wishlistBtn.classList.add('liked');
            wishlistBtn.innerHTML = '<i class="fa-solid fa-heart"></i>';
        } else {
            wishlistBtn.classList.remove('liked');
            wishlistBtn.innerHTML = '<i class="fa-regular fa-heart"></i>';
        }
        
        const globalBlock = document.getElementById('global-recs-block');
        const personalBlock = document.getElementById('personal-recs-block');
        globalBlock.classList.add('hidden');
        personalBlock.classList.add('hidden');
        
        let url = `/api/product_recs?product=${encodeURIComponent(product.Name)}`;
        if (currentUser) url += `&customer_id=${currentUser.customer_id}`;
        
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
        
        const indianNames = ["Aarav", "Neha", "Rohan", "Priya", "Vikram", "Anjali", "Kabir", "Meera", "Rahul", "Shruti"];
        const indianLastNames = ["Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta"];
        
        for(let i = 1; i <= 3; i++) {
            const seed = product.ID * 10 + i;
            const reviewerName = indianNames[seed % indianNames.length] + " " + indianLastNames[seed % 6];
            const rev = document.createElement('div');
            rev.className = 'review-card';
            rev.innerHTML = `
                <div class="review-header">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(reviewerName)}&background=random" class="review-avatar" alt="User">
                    <div class="review-meta">
                        <div class="review-name">${reviewerName}</div>
                        <div class="review-stars">${generateStars(product.Rating > 4.5 ? 5 : 4)}</div>
                    </div>
                </div>
                <p class="review-text">${reviewTexts[i-1]}</p>
            `;
            container.appendChild(rev);
        }
    }

    // Removed manual back button logic to rely entirely on browser Back (popstate)

    // ---------------- AUTH LOGIC ----------------
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            document.getElementById('auth-page').classList.remove('hidden');
        });
    }

    const closeAuthBtn = document.getElementById('close-auth');
    if (closeAuthBtn) {
        closeAuthBtn.addEventListener('click', () => {
            document.getElementById('auth-page').classList.add('hidden');
        });
    }

    document.getElementById('show-register').addEventListener('click', () => {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    });
    
    document.getElementById('show-login').addEventListener('click', () => {
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    });

    document.getElementById('auth-login-btn').addEventListener('click', () => {
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        
        fetch('/api/auth/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                handleLoginSuccess(data.user);
            } else {
                showToast("Invalid credentials");
            }
        });
    });

    document.getElementById('auth-register-btn').addEventListener('click', () => {
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;
        
        if(password !== confirm) {
            showToast("Passwords do not match");
            return;
        }
        
        fetch('/api/auth/register', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("Account created! Please login.");
                document.getElementById('reg-name').value = '';
                document.getElementById('reg-email').value = '';
                document.getElementById('reg-password').value = '';
                document.getElementById('reg-confirm').value = '';
                document.getElementById('register-form').classList.add('hidden');
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('auth-email').value = email;
            } else {
                showToast(data.error);
            }
        });
    });

    function handleLoginSuccess(user) {
        currentUser = user;
        document.getElementById('auth-page').classList.add('hidden');
        document.getElementById('logged-in-user').textContent = `Hi, ${user.name}`;
        document.getElementById('logged-in-user').classList.remove('hidden');
        document.getElementById('logout-btn').classList.remove('hidden');
        if (document.getElementById('login-btn')) document.getElementById('login-btn').classList.add('hidden');
        showToast("Logged in successfully!");
        
        // Fetch User Data (cart, wishlist, orders)
        fetch(`/api/user/data?email=${encodeURIComponent(user.email)}`)
            .then(res => res.json())
            .then(data => {
                cart = data.cart || [];
                wishlist = data.wishlist || [];
                orders = data.orders || [];
                loadUserFeed(user.customer_id);
            });
    }

    document.getElementById('logout-btn').addEventListener('click', () => {
        currentUser = null;
        cart = []; wishlist = []; orders = [];
        currentFeedList = allProducts;
        document.getElementById('logged-in-user').classList.add('hidden');
        document.getElementById('logout-btn').classList.add('hidden');
        if (document.getElementById('login-btn')) document.getElementById('login-btn').classList.remove('hidden');
        navigateTo('catalog-section');
        executeSearch();
        showToast("Logged out");
    });

    function syncUserData(extraData = {}) {
        if (!currentUser) return;
        const payload = { email: currentUser.email, cart, wishlist, ...extraData };
        fetch('/api/user/data', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    }

    function loadUserFeed(customerId) {
        fetch(`/api/feed?customer_id=${customerId}`)
            .then(res => res.json())
            .then(data => {
                if (data.feed && data.feed.length > 0) {
                    const topRated = [...allProducts].sort((a,b) => b.Rating - a.Rating).slice(0, 5);
                    const deals = [...allProducts].sort(() => 0.5 - Math.random()).slice(0, 5);
                    const combinedFront = [...deals, ...topRated, ...data.feed];
                    
                    const feedIds = new Set(combinedFront.map(p => p.ID));
                    const restProducts = allProducts.filter(p => !feedIds.has(p.ID));
                    currentFeedList = [...combinedFront, ...restProducts];
                    executeSearch(); // re-render main grid with the updated order
                }
            })
            .catch(err => console.error("Error loading feed:", err));
    }

    // ---------------- CART, WISHLIST, ORDERS LOGIC ----------------
    function showToast(msg) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    document.getElementById('add-to-cart').addEventListener('click', () => {
        cart.push(currentProductObj.ID);
        syncUserData();
        showToast('Added to Cart!');
    });
    
    document.getElementById('wishlist-toggle').addEventListener('click', function() {
        this.classList.toggle('liked');
        if(this.classList.contains('liked')) {
            this.innerHTML = '<i class="fa-solid fa-heart"></i>';
            if (!wishlist.includes(currentProductObj.ID)) wishlist.push(currentProductObj.ID);
            showToast('Added to Wishlist!');
        } else {
            this.innerHTML = '<i class="fa-regular fa-heart"></i>';
            wishlist = wishlist.filter(id => id !== currentProductObj.ID);
            showToast('Removed from Wishlist.');
        }
        syncUserData();
    });

    document.getElementById('nav-cart').addEventListener('click', () => {
        const container = document.getElementById('cart-items');
        container.innerHTML = '';
        let total = 0;
        
        if (cart.length === 0) {
            container.innerHTML = '<p>Your cart is empty.</p>';
            document.getElementById('checkout-cart-btn').classList.add('hidden');
        } else {
            document.getElementById('checkout-cart-btn').classList.remove('hidden');
            cart.forEach((id, index) => {
                const prod = allProducts.find(p => p.ID === id);
                if (prod) {
                    total += prod.Price;
                    const el = document.createElement('div');
                    el.className = 'cart-item-row';
                    el.innerHTML = `
                        <img src="${prod.Image}">
                        <div class="cart-item-info">
                            <div>${prod.Name}</div>
                            <div style="color:var(--primary); font-weight:bold;">${formatPrice(prod.Price)}</div>
                        </div>
                        <button class="cart-remove-btn" data-index="${index}">Remove</button>
                    `;
                    container.appendChild(el);
                }
            });
        }
        checkoutTotalAmt = total;
        document.getElementById('cart-total-price').textContent = formatPrice(total);
        
        document.querySelectorAll('.cart-remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.target.getAttribute('data-index'));
                cart.splice(idx, 1);
                syncUserData();
                document.getElementById('nav-cart').click(); // re-render
            });
        });
        
        document.getElementById('cart-modal').classList.remove('hidden');
    });

    document.getElementById('nav-wishlist').addEventListener('click', () => {
        const container = document.getElementById('wishlist-items');
        container.innerHTML = '';
        if (wishlist.length === 0) {
            container.innerHTML = '<p>Your wishlist is empty.</p>';
        } else {
            const wishlistProds = wishlist.map(id => allProducts.find(p => p.ID === id)).filter(Boolean);
            wishlistProds.forEach(prod => {
                const el = document.createElement('div');
                el.className = 'cart-item-row';
                el.innerHTML = `
                    <img src="${prod.Image}">
                    <div class="cart-item-info">
                        <div>${prod.Name}</div>
                        <div style="color:var(--primary); font-weight:bold;">${formatPrice(prod.Price)}</div>
                    </div>
                `;
                el.style.cursor = 'pointer';
                el.addEventListener('click', () => {
                    document.getElementById('wishlist-modal').classList.add('hidden');
                    showProductDetail(prod);
                });
                container.appendChild(el);
            });
        }
        document.getElementById('wishlist-modal').classList.remove('hidden');
    });

    document.getElementById('nav-orders').addEventListener('click', () => {
        navigateTo('orders-section');

        const container = document.getElementById('orders-page-list');
        container.innerHTML = '';
        if (orders.length === 0) {
            container.innerHTML = '<p>No past purchases found.</p>';
        } else {
            orders.slice().reverse().forEach(order => {
                const orderCard = document.createElement('div');
                orderCard.className = 'glass-effect';
                orderCard.style.padding = '1.5rem';
                orderCard.style.marginBottom = '1.5rem';
                orderCard.style.borderRadius = '12px';
                
                let itemsHtml = '';
                order.items.forEach(itemName => {
                    let prod = allProducts.find(p => p.Name === itemName);
                    if (!prod) {
                        prod = {
                            Name: itemName,
                            Image: 'https://placehold.co/100x100/1e1e1e/878787?text=Unavailable',
                            Description: 'This product is no longer available in the catalog.',
                            Price: 0,
                            ID: Math.floor(Math.random() * 10000)
                        };
                    }
                    itemsHtml += `
                        <div style="display:flex; gap:15px; margin-top:1rem; padding-bottom:1rem; border-bottom:1px solid var(--border);">
                            <img src="${prod.Image}" style="width:100px; height:100px; object-fit:cover; border-radius:8px;">
                            <div style="flex:1;">
                                <div style="font-weight:bold; font-size:1.1rem;">${prod.Name}</div>
                                <div style="color:var(--text-muted); font-size:0.9rem; margin:0.5rem 0;">${prod.Description.substring(0, 80)}...</div>
                                <div style="color:var(--primary); font-weight:bold;">${formatPrice(prod.Price)}</div>
                            </div>
                            <div style="flex:1;">
                                <strong>Leave a Review</strong><br>
                                <div style="color:#fbbf24; margin:0.5rem 0; cursor:pointer;" onclick="this.innerHTML='<i class=\\'fa-solid fa-star\\'></i><i class=\\'fa-solid fa-star\\'></i><i class=\\'fa-solid fa-star\\'></i><i class=\\'fa-solid fa-star\\'></i><i class=\\'fa-solid fa-star\\'></i>'">
                                    <i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i>
                                </div>
                                <textarea placeholder="Write your feedback..." style="width:100%; padding:0.8rem; border-radius:8px; border:1px solid var(--border); background:rgba(255,255,255,0.05); color:var(--text-main); font-family: inherit; resize: vertical; min-height: 60px; margin-bottom: 0.5rem;"></textarea>
                                <div style="margin-bottom: 1rem; color: #212121; font-size: 0.85rem;">
                                    <label for="review-img-${order.id}-${prod.ID}" style="cursor: pointer; display: flex; align-items: center; gap: 5px; color: var(--primary); font-weight: bold;">
                                        <i class="fa-solid fa-camera"></i> Add Image (Optional)
                                    </label>
                                    <input type="file" id="review-img-${order.id}-${prod.ID}" accept="image/*" style="display: none;" onchange="
                                        const file = this.files[0];
                                        if (file) {
                                            const reader = new FileReader();
                                            reader.onload = function(e) {
                                                let previewContainer = document.getElementById('preview-container-${order.id}-${prod.ID}');
                                                if (!previewContainer) {
                                                    previewContainer = document.createElement('div');
                                                    previewContainer.id = 'preview-container-${order.id}-${prod.ID}';
                                                    previewContainer.style.marginTop = '10px';
                                                    document.getElementById('review-img-${order.id}-${prod.ID}').parentNode.appendChild(previewContainer);
                                                }
                                                previewContainer.innerHTML = '<img src=\\'' + e.target.result + '\\' style=\\'width:60px; height:60px; object-fit:cover; border-radius:4px; border:1px solid #ddd;\\'>';
                                            }
                                            reader.readAsDataURL(file);
                                        }
                                    ">
                                </div>
                                <button style="padding: 0.5rem 1.5rem; border-radius: 20px; border: none; background: var(--primary); color: white; cursor: pointer; font-weight: bold; font-size: 0.85rem; margin-top: 0.5rem; transition: 0.3s; width: max-content;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'" onclick="this.textContent='Thank you!'; this.style.background='#10b981';">Submit Review</button>
                            </div>
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">Order #${order.id}</div>
                    `;
                });

                orderCard.innerHTML = `
                    <div style="display:flex; justify-content:flex-end; border-bottom:2px solid var(--border); padding-bottom:0.5rem;">
                        <div style="font-weight:bold; color:var(--primary); font-size:1.2rem;">Total: ${formatPrice(order.total)}</div>
                    </div>
                    ${itemsHtml}
                `;
                container.appendChild(orderCard);
            });
        }
    });

    document.getElementById('close-cart').addEventListener('click', () => document.getElementById('cart-modal').classList.add('hidden'));
    document.getElementById('close-wishlist').addEventListener('click', () => document.getElementById('wishlist-modal').classList.add('hidden'));

    let upsellGlobalProduct = null;
    let upsellPersonalProduct = null;
    let upsellSelectedItems = [];

    document.getElementById('buy-now').addEventListener('click', () => {
        upsellGlobalProduct = null;
        upsellPersonalProduct = null;
        upsellSelectedItems = [currentProductObj];

        const globalRecsContainer = document.getElementById('global-recs-list');
        const personalRecsContainer = document.getElementById('personal-recs-list');

        if (!globalRecsContainer.parentElement.classList.contains('hidden') && globalRecsContainer.firstChild) {
            const recName = globalRecsContainer.firstChild.querySelector('.card-title').textContent;
            upsellGlobalProduct = allProducts.find(p => p.Name === recName);
        }
        
        if (!personalRecsContainer.parentElement.classList.contains('hidden') && personalRecsContainer.firstChild) {
            const recName = personalRecsContainer.firstChild.querySelector('.card-title').textContent;
            upsellPersonalProduct = allProducts.find(p => p.Name === recName);
        }

        if (!upsellGlobalProduct && !upsellPersonalProduct) {
            const similarProd = allProducts.find(p => p.Category === currentProductObj.Category && p.ID !== currentProductObj.ID);
            if (similarProd) {
                upsellGlobalProduct = similarProd;
            } else {
                proceedToCheckout(currentProductObj, [currentProductObj]);
                return;
            }
        }

        showUpsellPage();
    });

    function createUpsellItemHTML(prod, isChecked, type) {
        return `
            <img src="${prod.Image}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
            <div style="flex: 1;">
                <div style="font-weight: bold; font-size: 1.1rem;">${prod.Name}</div>
                <div style="color: var(--primary); font-weight: bold;">${formatPrice(prod.Price)}</div>
            </div>
            <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: bold; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
                <input type="checkbox" class="upsell-checkbox" data-type="${type}" ${isChecked ? 'checked' : ''} style="transform: scale(1.5);">
                Add to Cart
            </label>
        `;
    }

    function showUpsellPage() {
        navigateTo('upsell-section');

        const pBlock = document.getElementById('upsell-personal-block');
        const pItem = document.getElementById('upsell-personal-item');
        if (upsellPersonalProduct) {
            pBlock.classList.remove('hidden');
            pItem.innerHTML = createUpsellItemHTML(upsellPersonalProduct, true, 'personal');
            if(!upsellSelectedItems.includes(upsellPersonalProduct)) upsellSelectedItems.push(upsellPersonalProduct);
        } else {
            pBlock.classList.add('hidden');
        }

        const gBlock = document.getElementById('upsell-global-block');
        const gItem = document.getElementById('upsell-global-item');
        if (upsellGlobalProduct && upsellGlobalProduct !== upsellPersonalProduct) {
            gBlock.classList.remove('hidden');
            gItem.innerHTML = createUpsellItemHTML(upsellGlobalProduct, !upsellPersonalProduct, 'global');
            if(!upsellPersonalProduct && !upsellSelectedItems.includes(upsellGlobalProduct)) upsellSelectedItems.push(upsellGlobalProduct);
        } else {
            gBlock.classList.add('hidden');
        }
        
        document.querySelectorAll('.upsell-checkbox').forEach(chk => {
            chk.addEventListener('change', (e) => {
                const prod = e.target.getAttribute('data-type') === 'personal' ? upsellPersonalProduct : upsellGlobalProduct;
                if (e.target.checked) {
                    if (!upsellSelectedItems.includes(prod)) upsellSelectedItems.push(prod);
                } else {
                    upsellSelectedItems = upsellSelectedItems.filter(p => p !== prod);
                }
            });
        });
    }

    document.getElementById('upsell-accept-btn').addEventListener('click', () => {
        document.getElementById('upsell-section').classList.add('hidden');
        proceedToCheckout(currentProductObj, upsellSelectedItems);
    });

    document.getElementById('upsell-skip-btn').addEventListener('click', () => {
        document.getElementById('upsell-section').classList.add('hidden');
        proceedToCheckout(currentProductObj, [currentProductObj]);
    });

    let checkoutItemsList = [];
    function proceedToCheckout(mainProduct, items) {
        checkoutMode = 'direct';
        checkoutItemsList = items;
        checkoutTotalAmt = items.reduce((sum, item) => sum + item.Price, 0);
        
        navigateTo('checkout-section');
        
        if (items.length > 1) {
            document.getElementById('checkout-item-name').textContent = `${mainProduct.Name} + ${items.length - 1} Item(s)`;
        } else {
            document.getElementById('checkout-item-name').textContent = mainProduct.Name;
        }
        
        document.getElementById('checkout-item-price').textContent = formatPrice(checkoutTotalAmt);
        document.getElementById('checkout-total').textContent = formatPrice(checkoutTotalAmt);
        resetCheckoutForm();
    }

    document.getElementById('checkout-cart-btn').addEventListener('click', () => {
        checkoutMode = 'cart';
        checkoutItemsList = cart.map(id => allProducts.find(p => p.ID === id)).filter(Boolean);
        document.getElementById('cart-modal').classList.add('hidden');
        
        navigateTo('checkout-section');
        
        document.getElementById('checkout-item-name').textContent = `${cart.length} Items`;
        document.getElementById('checkout-item-price').textContent = formatPrice(checkoutTotalAmt);
        document.getElementById('checkout-total').textContent = formatPrice(checkoutTotalAmt);
        resetCheckoutForm();
    });

    function resetCheckoutForm() {
        document.getElementById('coupon-msg').textContent = '';
        document.getElementById('coupon-code').value = '';
        document.querySelector('input[value="upi"]').checked = true;
        document.getElementById('upi-options').classList.remove('hidden');
        
        // Fill saved address if any locally (optional enhancement)
        const savedAddr = localStorage.getItem('luxstore_addr');
        if (savedAddr) {
            const addrObj = JSON.parse(savedAddr);
            document.getElementById('ship-name').value = addrObj.name;
            document.getElementById('ship-street').value = addrObj.street;
            document.getElementById('ship-city').value = addrObj.city;
            document.getElementById('ship-pin').value = addrObj.pin;
        }
    }

    // close-checkout removed as checkout is now a full page

    document.getElementById('apply-coupon').addEventListener('click', () => {
        const code = document.getElementById('coupon-code').value;
        if(code.toLowerCase() === 'lux10') {
            document.getElementById('coupon-msg').textContent = '10% Discount Applied!';
            document.getElementById('coupon-msg').style.color = 'green';
            checkoutTotalAmt = checkoutTotalAmt * 0.9;
            document.getElementById('checkout-total').textContent = formatPrice(checkoutTotalAmt);
        } else {
            document.getElementById('coupon-msg').textContent = 'Invalid Coupon Code';
            document.getElementById('coupon-msg').style.color = 'red';
            setTimeout(() => document.getElementById('coupon-msg').style.color = 'green', 2000);
        }
    });
    
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

    document.getElementById('place-order-btn').addEventListener('click', () => {
        // Save address to local storage
        localStorage.setItem('luxstore_addr', JSON.stringify({
            name: document.getElementById('ship-name') ? document.getElementById('ship-name').value : '',
            street: document.getElementById('ship-street') ? document.getElementById('ship-street').value : '',
            city: document.getElementById('ship-city') ? document.getElementById('ship-city').value : '',
            pin: document.getElementById('ship-pin') ? document.getElementById('ship-pin').value : ''
        }));

        const paymentMethod = document.querySelector('input[name="payment"]:checked').value;
        document.getElementById('checkout-section').classList.add('hidden');
        
        document.getElementById('payment-amount').textContent = formatPrice(checkoutTotalAmt);
        
        // Mock specific logos & PIN UI
        const logoEl = document.getElementById('payment-app-logo');
        const pinContainer = document.getElementById('pin-container');
        const submitPinBtn = document.getElementById('submit-pin-btn');
        const spinner = document.getElementById('payment-spinner');
        const upiInput = document.getElementById('upi-pin-input');
        
        upiInput.value = '';
        spinner.classList.add('hidden');
        submitPinBtn.classList.remove('hidden');
        submitPinBtn.textContent = 'Submit & Pay';
        
        if (paymentMethod === 'upi') {
            document.getElementById('processing-text').textContent = `Enter UPI PIN`;
            
            logoEl.classList.remove('hidden');
            pinContainer.classList.remove('hidden');
            
            if (selectedUpiApp === 'Google Pay') logoEl.src = 'https://upload.wikimedia.org/wikipedia/commons/f/f2/Google_Pay_Logo.svg';
            else if (selectedUpiApp === 'PhonePe') logoEl.src = 'https://upload.wikimedia.org/wikipedia/commons/7/71/PhonePe_Logo.svg';
            else if (selectedUpiApp === 'Paytm') logoEl.src = 'https://upload.wikimedia.org/wikipedia/commons/4/42/Paytm_logo.png';
            
        } else {
            document.getElementById('processing-text').textContent = 'Confirm Payment';
            logoEl.classList.add('hidden');
            pinContainer.classList.add('hidden');
        }

        document.getElementById('payment-processing-section').classList.remove('hidden');
        
        // Handle PIN submit
        submitPinBtn.onclick = () => {
            if (paymentMethod === 'upi' && upiInput.value.length < 4) {
                showToast("Please enter a valid 4 or 6 digit PIN");
                return;
            }
            
            submitPinBtn.classList.add('hidden');
            spinner.classList.remove('hidden');
            document.getElementById('processing-text').textContent = 'Processing Securely...';
            
            setTimeout(() => {
                document.getElementById('payment-processing-section').classList.add('hidden');
                navigateTo('catalog-section');
                
                const orderId = Math.floor(100000 + Math.random() * 900000);
                document.getElementById('order-number').textContent = orderId;
                document.getElementById('tracking-modal').classList.remove('hidden');
                
                // Log Order
                let orderItems = checkoutItemsList.map(p => p.Name);
                if (checkoutMode === 'cart') {
                    cart = []; // clear cart
                }
                const newOrder = { id: orderId, items: orderItems, total: checkoutTotalAmt };
                orders.push(newOrder);
                syncUserData({ new_order: newOrder });
            }, 2000);
        };
    });

    document.getElementById('close-tracking').addEventListener('click', () => {
        document.getElementById('tracking-modal').classList.add('hidden');
    });
});
