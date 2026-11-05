/**
 * RELATE (LUXSTORE) - FRONTEND APPLICATION CORE
 * Advanced ML Recommendations • GSAP Animations • Responsive SPA • Auth & Profile
 */

const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';

function getProductImage(prod) {
    if (!prod) return FALLBACK_IMAGE;
    let raw = '';
    if (typeof prod === 'string') raw = prod.trim();
    else if (prod.Image) raw = String(prod.Image).trim();
    if (!raw) return FALLBACK_IMAGE;
    const first = raw.split(',')[0].trim();
    if (!first.startsWith('http://') && !first.startsWith('https://')) {
        return FALLBACK_IMAGE;
    }
    return first;
}

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // STATE MANAGEMENT
    // -------------------------------------------------------------
    let allProducts = [];
    let allCategories = [];
    let currentCategory = 'All';
    let currentSearchQuery = '';
    let currentSort = 'featured';
    let currentUser = null;
    let currentProductObj = null;
    let cart = [];
    let wishlist = [];
    let orders = [];
    let currentFbtBundle = [];
    let currentUpsellList = [];

    // OTP Timer state
    let otpTimerInterval = null;
    let otpResendInterval = null;
    let otpTargetEmail = '';

    // Initialize User from LocalStorage if available
    try {
        const savedUser = localStorage.getItem('relate_user');
        if (savedUser) {
            currentUser = JSON.parse(savedUser);
        }
    } catch (e) {
        currentUser = null;
    }

    // -------------------------------------------------------------
    // SPA NAVIGATION (HISTORY & SECTIONS)
    // -------------------------------------------------------------
    function navigateTo(sectionId, push = true) {
        document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
        const target = document.getElementById(sectionId);
        if (target) {
            target.classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // GSAP Section Entrance Animation
            if (typeof gsap !== 'undefined') {
                gsap.fromTo(target, { opacity: 0, y: 15 }, { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' });
            }
        }

        // Update Nav Link Active States
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('data-target') === sectionId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

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

    // Handle hash on initial load
    const initialHash = window.location.hash.replace('#', '');
    if (initialHash && document.getElementById(initialHash)) {
        navigateTo(initialHash, false);
    } else {
        history.replaceState({ section: 'catalog-section' }, '', '#catalog-section');
    }

    // -------------------------------------------------------------
    // TOAST NOTIFICATION UTILITY
    // -------------------------------------------------------------
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-item ${type}`;

        let icon = 'fa-solid fa-circle-info';
        if (type === 'success') icon = 'fa-solid fa-circle-check';
        if (type === 'error') icon = 'fa-solid fa-triangle-exclamation';

        toast.innerHTML = `<i class="${icon}"></i> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            if (typeof gsap !== 'undefined') {
                gsap.to(toast, {
                    opacity: 0,
                    y: -10,
                    duration: 0.3,
                    onComplete: () => toast.remove()
                });
            } else {
                toast.remove();
            }
        }, 3600);
    }

    // -------------------------------------------------------------
    // THEME MANAGEMENT (LIGHT / DARK)
    // -------------------------------------------------------------
    const themeToggleBtn = document.getElementById('nav-theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');

    function applyTheme(theme) {
        const body = document.body;
        if (theme === 'light') {
            body.classList.remove('luxury-dark-theme');
            body.classList.add('luxury-light-theme');
            if (themeIcon) {
                themeIcon.className = 'fa-solid fa-moon';
            }
            if (themeToggleBtn) {
                themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
            }
        } else {
            body.classList.remove('luxury-light-theme');
            body.classList.add('luxury-dark-theme');
            if (themeIcon) {
                themeIcon.className = 'fa-solid fa-sun';
            }
            if (themeToggleBtn) {
                themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            }
        }
        localStorage.setItem('relate_theme', theme);
    }

    const currentSavedTheme = localStorage.getItem('relate_theme') || 'light';
    applyTheme(currentSavedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isLight = document.body.classList.contains('luxury-light-theme');
            const nextTheme = isLight ? 'dark' : 'light';
            applyTheme(nextTheme);
            showToast(`Switched to ${nextTheme === 'light' ? 'Light' : 'Dark'} theme`, 'info');
        });
    }

    // -------------------------------------------------------------
    // FORMATTING HELPERS
    // -------------------------------------------------------------
    function formatPrice(price) {
        if (typeof price !== 'number') price = Number(price) || 0;
        return '₹' + price.toLocaleString('en-IN');
    }

    function generateStars(rating) {
        let starsHtml = '';
        rating = Number(rating) || 4.5;
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

    // -------------------------------------------------------------
    // PRODUCT CARDS & GRID RENDERING
    // -------------------------------------------------------------
    function createProductCard(product, reason = null) {
        const card = document.createElement('div');
        card.className = 'product-card';
        const mainImage = getProductImage(product);
        const mrp = Math.round(product.Price * 1.25);
        const isWishlisted = wishlist.includes(product.ID);

        let reasonHtml = '';
        if (reason || product.recommendation_reason) {
            const rText = reason || product.recommendation_reason;
            let iconClass = 'fa-solid fa-sparkles';
            let badgeVariant = '';
            if (rText.startsWith('You usually buy this product with') || rText.startsWith('You usually buy this with')) {
                iconClass = 'fa-solid fa-user-check';
                badgeVariant = 'reason-personal';
            } else if (rText.startsWith('Most people buy this with') || rText.startsWith('Most people usually buy this with')) {
                iconClass = 'fa-solid fa-users';
                badgeVariant = 'reason-crowd';
            } else if (rText.includes('Useful product') || rText.includes('Accessory') || rText.includes('Useful accessory') || rText.includes('Essential accessory') || rText.includes('Compatible')) {
                iconClass = 'fa-solid fa-plug';
                badgeVariant = 'reason-accessory';
            }
            reasonHtml = `<span class="card-reason-badge ${badgeVariant}"><i class="${iconClass}"></i> ${rText}</span>`;
        }

        card.innerHTML = `
            <div class="card-image-box">
                <button class="card-wishlist-btn ${isWishlisted ? 'liked' : ''}" data-id="${product.ID}" title="Save to wishlist">
                    <i class="${isWishlisted ? 'fa-solid' : 'fa-regular'} fa-heart"></i>
                </button>
                <img src="${mainImage}" alt="${product.Name}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
            </div>
            <div class="card-body">
                ${reasonHtml}
                <h4 class="card-title" title="${product.Name}">${product.Name}</h4>
                <div class="card-category-desc">${product.Category || 'Botanicals'}</div>
                <div class="card-price">${formatPrice(product.Price)}</div>
                <button class="botanical-card-btn" data-id="${product.ID}">VIEW PRODUCT</button>
            </div>
        `;

        // Card Click opens Product Detail
        card.addEventListener('click', (e) => {
            if (e.target.closest('.card-wishlist-btn')) {
                return; // Handled separately
            }
            showProductDetail(product);
        });

        // Wishlist button click
        const wishBtn = card.querySelector('.card-wishlist-btn');
        wishBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleWishlist(product.ID);
            const liked = wishlist.includes(product.ID);
            wishBtn.classList.toggle('liked', liked);
            wishBtn.querySelector('i').className = liked ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        });

        // Card Action button click (VIEW PRODUCT)
        const viewBtn = card.querySelector('.botanical-card-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showProductDetail(product);
            });
        }

        // Quick Add to Cart button click (if present)
        const addBtn = card.querySelector('.card-add-btn');
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                addToCart(product.ID);
                showToast(`Added ${product.Name} to cart`, 'success');
                if (typeof gsap !== 'undefined') {
                    gsap.fromTo(addBtn, { scale: 0.8 }, { scale: 1, duration: 0.25, ease: 'back.out(2)' });
                }
            });
        }

        return card;
    }

    function renderGrid(products, container, animate = true) {
        if (!container) return;
        container.innerHTML = '';

        if (!products || products.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align:center; padding: 2.5rem; color: var(--text-muted);">No products match your criteria.</p>';
            return;
        }

        const fragment = document.createDocumentFragment();
        products.forEach(p => {
            fragment.appendChild(createProductCard(p));
        });
        container.appendChild(fragment);

        // GSAP Stagger animation on cards
        if (animate && typeof gsap !== 'undefined') {
            gsap.from(container.children, {
                opacity: 0,
                y: 18,
                duration: 0.35,
                stagger: 0.03,
                ease: 'power2.out'
            });
        }
    }

    // -------------------------------------------------------------
    // METADATA & INITIAL CATALOG LOADING
    // -------------------------------------------------------------
    function loadMetadata() {
        fetch('/api/metadata')
            .then(res => res.json())
            .then(data => {
                allProducts = data.products || [];
                allCategories = data.categories || [];

                populateCategoryControls(allCategories);
                fetchUserFeed();
                updateBadgeCounters();

                // Initial GSAP Hero Entrance Animation
                if (typeof gsap !== 'undefined') {
                    gsap.from('.hero-pill, .hero-title, .hero-subtitle, .hero-cta-group, .hero-metrics-strip', {
                        opacity: 0,
                        y: 25,
                        duration: 0.7,
                        stagger: 0.08,
                        ease: 'power3.out'
                    });
                }
            })
            .catch(err => {
                console.error("Error loading metadata:", err);
                showToast("Could not connect to backend service.", "error");
            });
    }

    function populateCategoryControls(categories) {
        // 1. Scroller Pills
        const pillsContainer = document.getElementById('category-pills-list');
        if (pillsContainer) {
            pillsContainer.innerHTML = '';
            const allPill = document.createElement('button');
            allPill.className = 'category-pill active';
            allPill.textContent = 'All Products';
            allPill.addEventListener('click', () => setCategory('All'));
            pillsContainer.appendChild(allPill);

            categories.forEach(cat => {
                const pill = document.createElement('button');
                pill.className = 'category-pill';
                pill.textContent = cat;
                pill.addEventListener('click', () => setCategory(cat));
                pillsContainer.appendChild(pill);
            });
        }

        // 2. Navbar Dropdown
        const dropdownMenu = document.getElementById('nav-categories-dropdown');
        if (dropdownMenu) {
            dropdownMenu.innerHTML = '';
            const allItem = document.createElement('a');
            allItem.className = 'nav-dropdown-item';
            allItem.textContent = 'All Categories';
            allItem.href = '#shop';
            allItem.addEventListener('click', (e) => {
                e.preventDefault();
                setCategory('All');
                navigateTo('catalog-section');
            });
            dropdownMenu.appendChild(allItem);

            categories.forEach(cat => {
                const item = document.createElement('a');
                item.className = 'nav-dropdown-item';
                item.textContent = cat;
                item.href = '#shop';
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    setCategory(cat);
                    navigateTo('catalog-section');
                });
                dropdownMenu.appendChild(item);
            });
        }
    }

    function setCategory(cat) {
        currentCategory = cat;

        // Update pill active classes
        document.querySelectorAll('.category-pill').forEach(pill => {
            if (pill.textContent === cat || (cat === 'All' && pill.textContent === 'All Products')) {
                pill.classList.add('active');
            } else {
                pill.classList.remove('active');
            }
        });

        // Update Section Header Tag
        const tag = document.getElementById('active-category-tag');
        if (tag) tag.textContent = cat === 'All' ? 'Featured Catalog' : `${cat} Collection`;

        executeFilterAndSort();
    }

    function executeFilterAndSort() {
        let filtered = [...allProducts];

        // 1. Category Filter
        if (currentCategory !== 'All') {
            filtered = filtered.filter(p => p.Category === currentCategory);
        }

        // 2. Search Query Filter
        if (currentSearchQuery.trim()) {
            const q = currentSearchQuery.toLowerCase().trim();
            filtered = filtered.filter(p =>
                (p.Name && p.Name.toLowerCase().includes(q)) ||
                (p.Description && p.Description.toLowerCase().includes(q)) ||
                (p.Category && p.Category.toLowerCase().includes(q))
            );
        }

        // 3. Sorting
        if (currentSort === 'rating-desc') {
            filtered.sort((a, b) => (b.Rating || 0) - (a.Rating || 0));
        } else if (currentSort === 'price-asc') {
            filtered.sort((a, b) => a.Price - b.Price);
        } else if (currentSort === 'price-desc') {
            filtered.sort((a, b) => b.Price - a.Price);
        } else if (currentSort === 'name-asc') {
            filtered.sort((a, b) => a.Name.localeCompare(b.Name));
        }

        const grid = document.getElementById('product-grid');
        const emptyState = document.getElementById('catalog-empty-state');

        if (filtered.length === 0) {
            grid.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            renderGrid(filtered, grid, true);
        }
    }

    // -------------------------------------------------------------
    // FEED: PERSONALIZED VS RECENTLY PURCHASED
    // -------------------------------------------------------------
    function fetchUserFeed() {
        let url = '/api/feed';
        if (currentUser && currentUser.customer_id) {
            url += `?customer_id=${currentUser.customer_id}`;
        }

        fetch(url)
            .then(res => res.json())
            .then(data => {
                const personalizedSection = document.getElementById('personalized-feed-section');
                const recentSection = document.getElementById('recently-purchased-section');

                if (data.recommendations && data.recommendations.length > 0) {
                    personalizedSection.classList.remove('hidden');
                    const titleEl = personalizedSection.querySelector('.section-title');
                    const descEl = personalizedSection.querySelector('.section-desc');
                    const tagEl = personalizedSection.querySelector('.section-tag');
                    
                    if (data.personalized) {
                        if (tagEl) tagEl.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tailored For You';
                        if (titleEl) titleEl.textContent = 'Personalized Recommendations';
                        if (descEl) descEl.textContent = 'Grounded in your transaction history and products bought together across accounts.';
                    } else {
                        if (tagEl) tagEl.innerHTML = '<i class="fa-solid fa-users"></i> Shopper Trends';
                        if (titleEl) titleEl.textContent = 'Frequently Co-Purchased Bundles';
                        if (descEl) descEl.textContent = 'Products most commonly purchased together by customers across accounts.';
                    }

                    const pGrid = document.getElementById('personalized-grid');
                    pGrid.innerHTML = '';
                    data.recommendations.slice(0, 8).forEach(item => {
                        pGrid.appendChild(createProductCard(item, item.recommendation_reason));
                    });
                } else {
                    personalizedSection.classList.add('hidden');
                }

                if (data.recently_purchased && data.recently_purchased.length > 0) {
                    // Show Recently Purchased Block (Strictly Separate from Recommendations)
                    recentSection.classList.remove('hidden');
                    const rGrid = document.getElementById('recently-purchased-grid');
                    rGrid.innerHTML = '';
                    data.recently_purchased.slice(0, 8).forEach(item => {
                        rGrid.appendChild(createProductCard(item, "Purchased in your past order"));
                    });
                } else {
                    recentSection.classList.add('hidden');
                }

                // Render Main Catalog Grid
                executeFilterAndSort();
            })
            .catch(err => {
                console.error("Error fetching feed:", err);
                executeFilterAndSort();
            });
    }

    // -------------------------------------------------------------
    // PRODUCT DETAIL VIEW & THE 4 RECOMMENDATION RAILS
    // -------------------------------------------------------------
    function showProductDetail(product) {
        currentProductObj = product;
        navigateTo('product-detail-section');

        const mainImg = getProductImage(product);
        const images = (product.Image || '').split(',').map(s => s.trim()).filter(Boolean);

        // Breadcrumbs
        document.getElementById('crumb-category').textContent = product.Category || 'General';
        document.getElementById('crumb-title').textContent = product.Name;

        // Viewport Image
        const detailImg = document.getElementById('detail-main-img');
        detailImg.src = mainImg;
        detailImg.onerror = () => { detailImg.src = FALLBACK_IMAGE; };

        // Thumbnails
        const thumbTrack = document.getElementById('detail-thumbnails-track');
        thumbTrack.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            const thumbSrc = images[i] ? getProductImage(images[i]) : mainImg;
            const thumbItem = document.createElement('div');
            thumbItem.className = `thumb-item ${i === 0 ? 'active' : ''}`;
            thumbItem.innerHTML = `<img src="${thumbSrc}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">`;
            thumbItem.addEventListener('click', () => {
                detailImg.src = thumbSrc;
                thumbTrack.querySelectorAll('.thumb-item').forEach(t => t.classList.remove('active'));
                thumbItem.classList.add('active');
            });
            thumbTrack.appendChild(thumbItem);
        }

        // Info details
        document.getElementById('detail-category-badge').textContent = product.Category || 'General';
        document.getElementById('detail-product-title').textContent = product.Name;
        document.getElementById('detail-stars').innerHTML = generateStars(product.Rating);
        document.getElementById('detail-rating-val').textContent = product.Rating || '4.5';
        document.getElementById('detail-price').textContent = formatPrice(product.Price);

        const mrp = Math.round(product.Price * 1.25);
        document.getElementById('detail-mrp').textContent = formatPrice(mrp);
        document.getElementById('detail-desc').textContent = product.Description || 'Elevate your lifestyle with this premium selection.';

        // Highlights
        const highlightsList = document.getElementById('detail-highlights-list');
        highlightsList.innerHTML = `
            <li>Category: <strong>${product.Category}</strong></li>
            <li>Rating: <strong>${product.Rating} / 5.0</strong> (Verified Buyer Satisfaction)</li>
            <li>Condition: <strong>Brand New • Factory Sealed • Authentic</strong></li>
            <li>Warranty: <strong>1 Year Manufacturer Comprehensive Coverage</strong></li>
        `;

        // Wishlist button state
        const detailWishBtn = document.getElementById('detail-wishlist-btn');
        const isWishlisted = wishlist.includes(product.ID);
        detailWishBtn.classList.toggle('liked', isWishlisted);
        detailWishBtn.querySelector('i').className = isWishlisted ? 'fa-solid fa-heart' : 'fa-regular fa-heart';

        // Reset Stepper
        document.getElementById('detail-qty-input').value = 1;

        // Fetch All 4 Dedicated Recommendation Rails
        fetchProductRecommendations(product);
    }

    function fetchProductRecommendations(product) {
        let url = `/api/product_recs?product=${encodeURIComponent(product.Name)}`;
        if (currentUser && currentUser.customer_id) {
            url += `&customer_id=${currentUser.customer_id}`;
        }

        fetch(url)
            .then(res => res.json())
            .then(data => {
                // Helper to render products into rail or hide wrapper if empty
                const setupRail = (wrapperId, gridId, items) => {
                    const wrapper = document.getElementById(wrapperId);
                    const grid = document.getElementById(gridId);
                    if (!wrapper || !grid) return;
                    if (items && items.length > 0) {
                        wrapper.classList.remove('hidden');
                        renderGrid(items, grid, true);
                    } else {
                        wrapper.classList.add('hidden');
                        grid.innerHTML = '';
                    }
                };

                // RAIL 0: Personal Co-purchases (Strictly if and only if buyer bought with another product before)
                setupRail('rail-personal-wrapper', 'personal-copurchase-grid', data.personal_copurchases);

                // RAIL 1: Frequently Bought Together (Other accounts' co-purchases / Market basket rules)
                currentFbtBundle = data.frequently_bought_together || [];
                setupRail('rail-fbt-wrapper', 'fbt-grid', currentFbtBundle);

                // RAIL 2: Recommended Accessories (Hardware/lifestyle accessories compatible with item)
                setupRail('rail-acc-wrapper', 'acc-grid', data.recommended_accessories);

                // RAIL 3: Similar Products (Same category / TF-IDF attribute alternatives)
                setupRail('rail-sim-wrapper', 'sim-grid', data.similar_products);

                // RAIL 4: You May Also Like (Cross-category co-occurrences)
                setupRail('rail-yml-wrapper', 'yml-grid', data.you_may_also_like);
            })
            .catch(err => console.error("Error loading product rails:", err));
    }

    // "Add All to Cart" for Frequently Bought Together
    document.getElementById('bundle-add-all-btn').addEventListener('click', () => {
        if (!currentFbtBundle || currentFbtBundle.length === 0) {
            showToast("No companion bundle available.", "info");
            return;
        }

        // Add main product + bundle items
        if (currentProductObj) addToCart(currentProductObj.ID);
        currentFbtBundle.forEach(item => addToCart(item.ID));
        showToast("Complete bundle added to your shopping bag!", "success");
        openCartDrawer();
    });

    // Quantity stepper
    document.getElementById('qty-plus').addEventListener('click', () => {
        const input = document.getElementById('detail-qty-input');
        input.value = Math.min(10, parseInt(input.value || 1) + 1);
    });

    document.getElementById('qty-minus').addEventListener('click', () => {
        const input = document.getElementById('detail-qty-input');
        input.value = Math.max(1, parseInt(input.value || 1) - 1);
    });

    // Detail Add to Cart
    document.getElementById('detail-add-cart-btn').addEventListener('click', () => {
        if (!currentProductObj) return;
        const qty = parseInt(document.getElementById('detail-qty-input').value || 1);
        for (let i = 0; i < qty; i++) {
            addToCart(currentProductObj.ID);
        }
        showToast(`Added ${qty} × ${currentProductObj.Name} to cart`, 'success');
        openCartDrawer();
    });

    // Detail Buy Now
    document.getElementById('detail-buy-now-btn').addEventListener('click', () => {
        if (!currentProductObj) return;
        addToCart(currentProductObj.ID);
        openCartDrawer();
    });

    // Detail Wishlist Toggle
    document.getElementById('detail-wishlist-btn').addEventListener('click', () => {
        if (!currentProductObj) return;
        toggleWishlist(currentProductObj.ID);
        const liked = wishlist.includes(currentProductObj.ID);
        const btn = document.getElementById('detail-wishlist-btn');
        btn.classList.toggle('liked', liked);
        btn.querySelector('i').className = liked ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
    });

    // -------------------------------------------------------------
    // CART & WISHLIST MANAGEMENT
    // -------------------------------------------------------------
    function addToCart(productId) {
        cart.push(productId);
        updateBadgeCounters();
        syncUserData();
    }

    function toggleWishlist(productId) {
        const idx = wishlist.indexOf(productId);
        if (idx > -1) {
            wishlist.splice(idx, 1);
            showToast("Removed from saved wishlist", "info");
        } else {
            wishlist.push(productId);
            showToast("Saved to your wishlist", "success");
        }
        updateBadgeCounters();
        syncUserData();
    }

    function updateBadgeCounters() {
        const cartBadge = document.getElementById('cart-badge');
        const wishBadge = document.getElementById('wishlist-badge');

        if (cartBadge) {
            cartBadge.textContent = cart.length;
            cartBadge.classList.toggle('hidden', cart.length === 0);
        }

        if (wishBadge) {
            wishBadge.textContent = wishlist.length;
            wishBadge.classList.toggle('hidden', wishlist.length === 0);
        }
    }

    function openCartDrawer() {
        renderCartDrawer();
        const drawer = document.getElementById('cart-drawer-overlay');
        drawer.classList.remove('hidden');

        if (typeof gsap !== 'undefined') {
            gsap.fromTo('#cart-drawer', { x: 440 }, { x: 0, duration: 0.35, ease: 'power3.out' });
        }
    }

    function closeCartDrawer() {
        const overlay = document.getElementById('cart-drawer-overlay');
        if (typeof gsap !== 'undefined') {
            gsap.to('#cart-drawer', {
                x: 440,
                duration: 0.25,
                ease: 'power3.in',
                onComplete: () => overlay.classList.add('hidden')
            });
        } else {
            overlay.classList.add('hidden');
        }
    }

    function renderCartDrawer() {
        const container = document.getElementById('cart-items-container');
        container.innerHTML = '';

        if (cart.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 40px 10px;">
                    <div class="empty-icon"><i class="fa-solid fa-bag-shopping"></i></div>
                    <h4>Your bag is empty</h4>
                    <p>Explore our catalog to add items.</p>
                </div>
            `;
            document.getElementById('cart-subtotal-val').textContent = '₹0';
            document.getElementById('cart-total-val').textContent = '₹0';
            return;
        }

        let subtotal = 0;
        cart.forEach((id, index) => {
            const prod = allProducts.find(p => p.ID === id);
            if (!prod) return;
            subtotal += prod.Price;

            const row = document.createElement('div');
            row.className = 'cart-item-row';
            row.innerHTML = `
                <img src="${getProductImage(prod)}" class="cart-item-img" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
                <div class="cart-item-details">
                    <h5 class="cart-item-title">${prod.Name}</h5>
                    <span class="cart-item-price">${formatPrice(prod.Price)}</span>
                </div>
                <button class="cart-item-remove-btn" title="Remove item"><i class="fa-solid fa-trash-can"></i></button>
            `;

            row.querySelector('.cart-item-remove-btn').addEventListener('click', () => {
                cart.splice(index, 1);
                updateBadgeCounters();
                syncUserData();
                renderCartDrawer();
            });

            container.appendChild(row);
        });

        document.getElementById('cart-subtotal-val').textContent = formatPrice(subtotal);
        document.getElementById('cart-total-val').textContent = formatPrice(subtotal);
    }

    document.getElementById('nav-cart-btn').addEventListener('click', openCartDrawer);
    document.getElementById('close-cart-drawer').addEventListener('click', closeCartDrawer);
    document.getElementById('cart-drawer-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'cart-drawer-overlay') closeCartDrawer();
    });

    // Wishlist Button in Nav -> Navigate to Profile Wishlist Tab
    document.getElementById('nav-wishlist-btn').addEventListener('click', () => {
        if (!currentUser) {
            openAuthModal('login');
            showToast("Please sign in to view your wishlist", "info");
            return;
        }
        navigateTo('profile-section');
        switchProfileTab('tab-profile-wishlist');
    });

    // -------------------------------------------------------------
    // CHECKOUT & SMART UPSELL MODAL
    // -------------------------------------------------------------
    document.getElementById('proceed-checkout-btn').addEventListener('click', () => {
        if (cart.length === 0) {
            showToast("Your cart is empty.", "info");
            return;
        }

        if (!currentUser) {
            closeCartDrawer();
            openAuthModal('login');
            showToast("Please sign in or create an account to complete checkout.", "info");
            return;
        }

        closeCartDrawer();
        showSmartUpsellModal();
    });

    function showSmartUpsellModal() {
        if (!cart || cart.length === 0) {
            executeFinalCheckout();
            return;
        }

        const lastProductId = cart[cart.length - 1];
        const lastProd = allProducts.find(p => p.ID === lastProductId);

        if (!lastProd) {
            executeFinalCheckout();
            return;
        }

        const custId = currentUser ? (currentUser.customer_id || '') : '';
        const url = `/api/product_recs?product=${encodeURIComponent(lastProd.Name)}${custId ? `&customer_id=${custId}` : ''}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                const candidates = [];
                const seenIds = new Set(cart);

                // Priority 1: Personal co-purchases (if buyer bought with this product before)
                (data.personal_copurchases || []).forEach(item => {
                    if (!seenIds.has(item.ID)) {
                        candidates.push({
                            ...item,
                            reason_tag: item.recommendation_reason || `You usually buy this with ${lastProd.Name}`
                        });
                        seenIds.add(item.ID);
                    }
                });

                // Priority 2: Frequently bought together (other customer transactions & Apriori)
                (data.frequently_bought_together || []).forEach(item => {
                    if (!seenIds.has(item.ID)) {
                        candidates.push({
                            ...item,
                            reason_tag: item.recommendation_reason || `Most people usually buy this with ${lastProd.Name}`
                        });
                        seenIds.add(item.ID);
                    }
                });

                // Priority 3: Useful companion accessories (e.g. phone case for mobile)
                if (candidates.length < 3) {
                    (data.recommended_accessories || []).forEach(item => {
                        if (!seenIds.has(item.ID)) {
                            candidates.push({
                                ...item,
                                reason_tag: item.recommendation_reason || `Useful product for ${lastProd.Name}`
                            });
                            seenIds.add(item.ID);
                        }
                    });
                }

                const finalUpsell = candidates.slice(0, 3);
                if (finalUpsell.length === 0) {
                    executeFinalCheckout();
                    return;
                }

                currentUpsellList = finalUpsell;
                const container = document.getElementById('upsell-items-list');
                container.innerHTML = '';

                finalUpsell.forEach(item => {
                    const row = document.createElement('div');
                    row.className = 'upsell-row';
                    row.innerHTML = `
                        <img src="${getProductImage(item)}" class="upsell-img" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
                        <div class="upsell-details">
                            <span class="upsell-reason-tag"><i class="fa-solid fa-sparkles"></i> ${item.reason_tag}</span>
                            <h5 class="upsell-name">${item.Name}</h5>
                            <span class="upsell-price">${formatPrice(item.Price)}</span>
                        </div>
                        <label class="upsell-check-label">
                            <input type="checkbox" class="upsell-checkbox" data-id="${item.ID}" checked>
                            Add to Order
                        </label>
                    `;
                    container.appendChild(row);
                });

                document.getElementById('upsell-modal-backdrop').classList.remove('hidden');
            })
            .catch(() => executeFinalCheckout());
    }

    document.getElementById('skip-upsell-btn').addEventListener('click', () => {
        document.getElementById('upsell-modal-backdrop').classList.add('hidden');
        executeFinalCheckout();
    });

    document.getElementById('close-upsell-modal').addEventListener('click', () => {
        document.getElementById('upsell-modal-backdrop').classList.add('hidden');
    });

    document.getElementById('confirm-checkout-btn').addEventListener('click', () => {
        // Add checked upsell items
        document.querySelectorAll('.upsell-checkbox:checked').forEach(cb => {
            const id = parseInt(cb.getAttribute('data-id'));
            if (!cart.includes(id)) {
                cart.push(id);
            }
        });
        document.getElementById('upsell-modal-backdrop').classList.add('hidden');
        executeFinalCheckout();
    });

    function executeFinalCheckout() {
        if (!currentUser) return;

        let total = 0;
        const itemNames = [];
        cart.forEach(id => {
            const p = allProducts.find(x => x.ID === id);
            if (p) {
                total += p.Price;
                itemNames.push(p.Name);
            }
        });

        const newOrder = {
            id: Math.floor(100000 + Math.random() * 900000),
            items: itemNames,
            total: total,
            status: "Delivered",
            created_at: new Date().toISOString()
        };

        // Submit Order to backend (which automatically appends to transactions.csv and retrains the model!)
        fetch('/api/user/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentUser.email,
                new_order: newOrder,
                cart: [] // Clear cart after order
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                cart = [];
                updateBadgeCounters();
                showToast(`Order #${newOrder.id} placed! Recommender model updated in real-time.`, "success");
                fetchUserFeed(); // Refresh feeds with dynamic recommendations!
                navigateTo('profile-section');
                switchProfileTab('tab-order-history');
                loadUserProfileData();
            } else {
                showToast("Failed to place order. Please try again.", "error");
            }
        })
        .catch(err => {
            console.error("Checkout error:", err);
            showToast("Network error during checkout.", "error");
        });
    }

    // -------------------------------------------------------------
    // USER SYNC & PROFILE MANAGEMENT
    // -------------------------------------------------------------
    function syncUserData() {
        if (!currentUser) return;
        fetch('/api/user/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentUser.email,
                cart: cart,
                wishlist: wishlist
            })
        }).catch(err => console.error("Sync user data error:", err));
    }

    function loadUserProfileData() {
        if (!currentUser) return;

        fetch(`/api/user/profile?email=${encodeURIComponent(currentUser.email)}`)
            .then(res => res.json())
            .then(profile => {
                document.getElementById('profile-summary-name').textContent = profile.name || currentUser.name;
                document.getElementById('profile-summary-email').textContent = profile.email || currentUser.email;
                document.getElementById('profile-summary-id').textContent = `Customer ID: #${profile.customer_id || currentUser.customer_id}`;
                document.getElementById('profile-avatar-circle').textContent = (profile.name || 'U').charAt(0).toUpperCase();

                document.getElementById('profile-name-input').value = profile.name || currentUser.name;
                document.getElementById('profile-email-input').value = profile.email || currentUser.email;
                document.getElementById('profile-id-input').value = `#${profile.customer_id || currentUser.customer_id}`;
                document.getElementById('profile-since-input').value = profile.created_at ? profile.created_at.substring(0, 10) : '2026';
            })
            .catch(err => console.error("Error loading profile:", err));

        // Load Orders & Wishlist
        fetch(`/api/user/data?email=${encodeURIComponent(currentUser.email)}`)
            .then(res => res.json())
            .then(data => {
                cart = data.cart || [];
                wishlist = data.wishlist || [];
                orders = data.orders || [];
                updateBadgeCounters();
                renderProfileOrders(orders);
                renderProfileWishlist(wishlist);
            })
            .catch(err => console.error("Error loading user data:", err));
    }

    function renderProfileOrders(orderList) {
        const container = document.getElementById('profile-orders-list');
        container.innerHTML = '';

        if (!orderList || orderList.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon"><i class="fa-solid fa-box-open"></i></div>
                    <h4>No orders yet</h4>
                    <p>When you complete a purchase, your orders and tracking details will appear here.</p>
                </div>
            `;
            return;
        }

        orderList.slice().reverse().forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-history-card';

            let itemsHtml = '';
            (order.items || []).forEach(itemName => {
                const prod = allProducts.find(p => p.Name === itemName);
                const imgSrc = prod ? getProductImage(prod) : FALLBACK_IMAGE;
                const priceStr = prod ? formatPrice(prod.Price) : '';

                itemsHtml += `
                    <div class="order-subitem">
                        <img src="${imgSrc}" class="order-subitem-img" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${FALLBACK_IMAGE}';">
                        <div class="order-subitem-info">
                            <div class="order-subitem-name">${itemName}</div>
                            <div class="order-subitem-price">${priceStr}</div>
                        </div>
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="order-header-row">
                    <div>
                        <span class="order-id">Order #${order.id}</span>
                        <div class="order-date">${order.created_at ? order.created_at.substring(0, 16).replace('T', ' ') : 'Recently placed'}</div>
                    </div>
                    <span class="order-status-badge"><i class="fa-solid fa-check"></i> ${order.status || 'Delivered'}</span>
                </div>
                <div class="order-items-sublist">
                    ${itemsHtml}
                </div>
                <div class="order-footer-row">
                    <span class="order-total-lbl">Total Paid:</span>
                    <span class="order-total-amt">${formatPrice(order.total || 0)}</span>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function renderProfileWishlist(wishlistIds) {
        const grid = document.getElementById('profile-wishlist-grid');
        grid.innerHTML = '';

        const prods = wishlistIds.map(id => allProducts.find(p => p.ID === id)).filter(Boolean);
        if (prods.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <div class="empty-icon"><i class="fa-regular fa-heart"></i></div>
                    <h4>No saved items</h4>
                    <p>Explore the store and click the heart icon on products to save them for later.</p>
                </div>
            `;
            return;
        }

        renderGrid(prods, grid, true);
    }

    // Profile tab switching
    function switchProfileTab(tabId) {
        document.querySelectorAll('.profile-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
        });
        document.querySelectorAll('.profile-tab-content').forEach(tab => {
            tab.classList.toggle('active', tab.id === tabId);
        });
    }

    document.querySelectorAll('.profile-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchProfileTab(tabId);
        });
    });

    // Profile Name Update Form
    document.getElementById('profile-update-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const newName = document.getElementById('profile-name-input').value.trim();
        if (!newName || !currentUser) return;

        fetch('/api/user/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: currentUser.email, name: newName })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentUser.name = newName;
                localStorage.setItem('relate_user', JSON.stringify(currentUser));
                updateAuthUI();
                showToast("Profile name updated successfully!", "success");
            } else {
                showToast(data.error || "Update failed.", "error");
            }
        });
    });

    // Profile Password Change Form
    document.getElementById('profile-password-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const currentPwd = document.getElementById('security-current-pwd').value;
        const newPwd = document.getElementById('security-new-pwd').value;
        const confirmPwd = document.getElementById('security-confirm-pwd').value;

        if (newPwd !== confirmPwd) {
            showToast("New passwords do not match.", "error");
            return;
        }

        fetch('/api/user/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentUser.email,
                current_password: currentPwd,
                new_password: newPwd
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('profile-password-form').reset();
                showToast("Password updated successfully!", "success");
            } else {
                showToast(data.error || "Password change failed.", "error");
            }
        });
    });

    // -------------------------------------------------------------
    // AUTHENTICATION & FORGOT PASSWORD WIZARD
    // -------------------------------------------------------------
    function updateAuthUI() {
        const guestBtn = document.getElementById('login-trigger-btn');
        const userDropdown = document.getElementById('user-profile-dropdown');

        if (currentUser) {
            guestBtn.classList.add('hidden');
            userDropdown.classList.remove('hidden');

            const initial = (currentUser.name || 'U').charAt(0).toUpperCase();
            document.getElementById('user-avatar-initials').textContent = initial;
            document.getElementById('user-display-name').textContent = currentUser.name.split(' ')[0];
            document.getElementById('menu-user-name').textContent = currentUser.name;
            document.getElementById('menu-user-email').textContent = currentUser.email;
        } else {
            guestBtn.classList.remove('hidden');
            userDropdown.classList.add('hidden');
        }
    }

    function openAuthModal(view = 'login') {
        const backdrop = document.getElementById('auth-modal-backdrop');
        backdrop.classList.remove('hidden');

        document.getElementById('auth-login-view').classList.add('hidden');
        document.getElementById('auth-register-view').classList.add('hidden');
        document.getElementById('auth-forgot-view').classList.add('hidden');

        if (view === 'login') {
            document.getElementById('auth-login-view').classList.remove('hidden');
            document.getElementById('auth-subtitle-text').textContent = "Sign in to access personalized recommendations.";
        } else if (view === 'register') {
            document.getElementById('auth-register-view').classList.remove('hidden');
            document.getElementById('auth-subtitle-text').textContent = "Create an account to start your tailored shopping journey.";
        } else if (view === 'forgot') {
            document.getElementById('auth-forgot-view').classList.remove('hidden');
            document.getElementById('auth-subtitle-text').textContent = "Reset your password securely via email verification code.";
            resetForgotWizard();
        }

        if (typeof gsap !== 'undefined') {
            gsap.fromTo('#auth-modal-card', { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: 'power2.out' });
        }
    }

    function closeAuthModal() {
        document.getElementById('auth-modal-backdrop').classList.add('hidden');
        clearInterval(otpTimerInterval);
        clearInterval(otpResendInterval);
    }

    document.getElementById('login-trigger-btn').addEventListener('click', () => openAuthModal('login'));
    document.getElementById('close-auth-modal').addEventListener('click', closeAuthModal);
    document.getElementById('auth-modal-backdrop').addEventListener('click', (e) => {
        if (e.target.id === 'auth-modal-backdrop') closeAuthModal();
    });

    document.getElementById('trigger-switch-register').addEventListener('click', () => openAuthModal('register'));
    document.getElementById('trigger-switch-login').addEventListener('click', () => openAuthModal('login'));
    document.getElementById('trigger-forgot-password').addEventListener('click', () => openAuthModal('forgot'));
    document.getElementById('trigger-back-login').addEventListener('click', () => openAuthModal('login'));

    // User Dropdown toggle in navbar
    const avatarBtn = document.getElementById('user-avatar-btn');
    const menuDropdown = document.getElementById('user-menu-dropdown-content');

    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        menuDropdown.classList.toggle('hidden');
    });

    document.addEventListener('click', () => {
        if (menuDropdown) menuDropdown.classList.add('hidden');
    });

    // Nav Menu Dropdown Links
    document.getElementById('menu-go-profile').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('profile-section');
        switchProfileTab('tab-personal-info');
        loadUserProfileData();
    });

    document.getElementById('menu-go-orders').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('profile-section');
        switchProfileTab('tab-order-history');
        loadUserProfileData();
    });

    document.getElementById('menu-go-wishlist').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('profile-section');
        switchProfileTab('tab-profile-wishlist');
        loadUserProfileData();
    });

    // Logout Action
    function handleLogout() {
        currentUser = null;
        localStorage.removeItem('relate_user');
        cart = [];
        wishlist = [];
        orders = [];
        updateAuthUI();
        updateBadgeCounters();
        showToast("Signed out successfully.", "info");
        navigateTo('catalog-section');
        fetchUserFeed();
    }

    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('profile-logout-btn').addEventListener('click', handleLogout);

    // Login Form Submit
    document.getElementById('login-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('relate_user', JSON.stringify(currentUser));
                updateAuthUI();
                closeAuthModal();
                showToast(`Welcome back, ${currentUser.name}!`, "success");
                fetchUserFeed();
                loadUserProfileData();
            } else {
                showToast(data.error || "Invalid credentials", "error");
            }
        })
        .catch(err => {
            console.error("Login error:", err);
            showToast("Server error during login.", "error");
        });
    });

    // Register Form Submit
    document.getElementById('register-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;

        if (password !== confirm) {
            showToast("Passwords do not match.", "error");
            return;
        }

        fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('relate_user', JSON.stringify(currentUser));
                updateAuthUI();
                closeAuthModal();
                showToast(`Account created! Welcome, ${currentUser.name}!`, "success");
                fetchUserFeed();
                loadUserProfileData();
            } else {
                showToast(data.error || "Registration failed.", "error");
            }
        })
        .catch(err => {
            console.error("Registration error:", err);
            showToast("Server error during registration.", "error");
        });
    });

    // -------------------------------------------------------------
    // FORGOT PASSWORD 3-STEP WIZARD (NODEMAILER OTP)
    // -------------------------------------------------------------
    function resetForgotWizard() {
        document.getElementById('fp-step-1').classList.remove('hidden');
        document.getElementById('fp-step-2').classList.add('hidden');
        document.getElementById('fp-step-3').classList.add('hidden');
        document.getElementById('fp-email-form').reset();
        document.getElementById('fp-otp-form').reset();
        document.getElementById('fp-new-pwd-form').reset();
        clearInterval(otpTimerInterval);
        clearInterval(otpResendInterval);
    }

    // Step 1: Send OTP
    document.getElementById('fp-email-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('fp-email-input').value.trim();
        if (!email) return;

        otpTargetEmail = email;
        const btn = document.getElementById('fp-send-otp-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending Code...';

        fetch('/api/auth/forgot-password/request-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = 'Send Verification Code <i class="fa-regular fa-paper-plane"></i>';

            if (data.success) {
                showToast("Verification code dispatched to your email.", "success");
                document.getElementById('fp-target-email-display').textContent = email;

                // Move to Step 2
                document.getElementById('fp-step-1').classList.add('hidden');
                document.getElementById('fp-step-2').classList.remove('hidden');
                startOtpCountdown();
                startResendCooldown();
            } else {
                showToast(data.error || "Could not dispatch code.", "error");
            }
        })
        .catch(() => {
            btn.disabled = false;
            btn.innerHTML = 'Send Verification Code <i class="fa-regular fa-paper-plane"></i>';
            showToast("Network error requesting code.", "error");
        });
    });

    function startOtpCountdown() {
        clearInterval(otpTimerInterval);
        let secondsLeft = 300; // 5 minutes
        const timerDisplay = document.getElementById('otp-timer-display');

        function updateDisplay() {
            const m = Math.floor(secondsLeft / 60);
            const s = secondsLeft % 60;
            timerDisplay.innerHTML = `Code expires in: <strong>${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}</strong>`;
        }

        updateDisplay();
        otpTimerInterval = setInterval(() => {
            secondsLeft--;
            if (secondsLeft <= 0) {
                clearInterval(otpTimerInterval);
                timerDisplay.innerHTML = '<span style="color:var(--accent-rose);">Code has expired. Please request a new one.</span>';
            } else {
                updateDisplay();
            }
        }, 1000);
    }

    function startResendCooldown() {
        clearInterval(otpResendInterval);
        let cooldown = 60;
        const resendBtn = document.getElementById('otp-resend-btn');
        resendBtn.disabled = true;

        otpResendInterval = setInterval(() => {
            cooldown--;
            if (cooldown <= 0) {
                clearInterval(otpResendInterval);
                resendBtn.disabled = false;
                resendBtn.textContent = 'Resend Code';
            } else {
                resendBtn.textContent = `Resend in ${cooldown}s`;
            }
        }, 1000);
    }

    // Resend OTP
    document.getElementById('otp-resend-btn').addEventListener('click', () => {
        if (!otpTargetEmail) return;
        fetch('/api/auth/forgot-password/request-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: otpTargetEmail })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("New code sent to your email.", "success");
                startOtpCountdown();
                startResendCooldown();
            } else {
                showToast(data.error || "Resend failed.", "error");
            }
        });
    });

    // Step 2: Verify OTP
    document.getElementById('fp-otp-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const otp = document.getElementById('fp-otp-input').value.trim();
        if (!otp || !otpTargetEmail) return;

        const btn = document.getElementById('fp-verify-otp-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';

        fetch('/api/auth/forgot-password/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: otpTargetEmail, otp })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = 'Verify Code <i class="fa-solid fa-shield-check"></i>';

            if (data.success) {
                clearInterval(otpTimerInterval);
                showToast("Code verified successfully!", "success");
                // Move to Step 3
                document.getElementById('fp-step-2').classList.add('hidden');
                document.getElementById('fp-step-3').classList.remove('hidden');
            } else {
                showToast(data.error || "Invalid code.", "error");
            }
        })
        .catch(() => {
            btn.disabled = false;
            btn.innerHTML = 'Verify Code <i class="fa-solid fa-shield-check"></i>';
            showToast("Network error verifying code.", "error");
        });
    });

    // Step 3: Set New Password
    document.getElementById('fp-new-pwd-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const newPassword = document.getElementById('fp-new-pwd-input').value;
        const confirmPassword = document.getElementById('fp-confirm-pwd-input').value;

        if (newPassword !== confirmPassword) {
            showToast("Passwords do not match.", "error");
            return;
        }

        const btn = document.getElementById('fp-reset-submit-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating...';

        fetch('/api/auth/forgot-password/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: otpTargetEmail, new_password: newPassword })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = 'Reset Password & Sign In <i class="fa-solid fa-lock"></i>';

            if (data.success) {
                showToast("Password reset successfully! Please sign in.", "success");
                openAuthModal('login');
            } else {
                showToast(data.error || "Reset failed.", "error");
            }
        })
        .catch(() => {
            btn.disabled = false;
            btn.innerHTML = 'Reset Password & Sign In <i class="fa-solid fa-lock"></i>';
            showToast("Network error resetting password.", "error");
        });
    });

    // -------------------------------------------------------------
    // SEARCH & FILTER CONTROLS
    // -------------------------------------------------------------
    const searchInput = document.getElementById('global-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    let searchDebounce = null;

    searchInput.addEventListener('input', () => {
        const val = searchInput.value;
        clearBtn.classList.toggle('hidden', val.length === 0);

        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            currentSearchQuery = val;
            navigateTo('catalog-section');
            executeFilterAndSort();
        }, 250);
    });

    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        currentSearchQuery = '';
        clearBtn.classList.add('hidden');
        executeFilterAndSort();
    });

    document.getElementById('sort-select').addEventListener('change', (e) => {
        currentSort = e.target.value;
        executeFilterAndSort();
    });

    document.getElementById('reset-filter-btn').addEventListener('click', () => {
        currentCategory = 'All';
        currentSearchQuery = '';
        searchInput.value = '';
        clearBtn.classList.add('hidden');
        setCategory('All');
    });

    // -------------------------------------------------------------
    // NAVIGATION LINK CLICK HANDLERS
    // -------------------------------------------------------------
    document.getElementById('nav-brand-logo').addEventListener('click', () => {
        navigateTo('catalog-section');
        setCategory('All');
    });

    document.getElementById('nav-link-home').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('catalog-section');
    });

    document.getElementById('nav-link-shop').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('catalog-section');
        document.getElementById('catalog-main-area').scrollIntoView({ behavior: 'smooth' });
    });

    document.getElementById('nav-link-about').addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('about-section');
    });

    document.getElementById('hero-explore-btn').addEventListener('click', () => {
        document.getElementById('catalog-main-area').scrollIntoView({ behavior: 'smooth' });
    });

    document.getElementById('hero-about-btn').addEventListener('click', () => {
        navigateTo('about-section');
    });

    document.getElementById('crumb-home').addEventListener('click', () => {
        navigateTo('catalog-section');
    });

    document.getElementById('crumb-category').addEventListener('click', () => {
        if (currentProductObj && currentProductObj.Category) {
            setCategory(currentProductObj.Category);
        }
        navigateTo('catalog-section');
    });

    // Footer Links
    document.querySelectorAll('.footer-nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = link.getAttribute('data-target');
            if (target) navigateTo(target);
        });
    });

    // -------------------------------------------------------------
    // INITIALIZATION
    // -------------------------------------------------------------
    updateAuthUI();
    loadMetadata();
    if (currentUser) {
        loadUserProfileData();
    }
});
