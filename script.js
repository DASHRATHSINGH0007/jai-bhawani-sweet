document.addEventListener('DOMContentLoaded', () => {
    // --- Navbar Scroll Effect ---
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('shadow-md', 'bg-white/90');
            navbar.classList.remove('bg-white/40', 'border-white/20');
        } else {
            navbar.classList.remove('shadow-md', 'bg-white/90');
            navbar.classList.add('bg-white/40', 'border-white/20');
        }
    });

    // --- Intersection Observer for Scroll Animations ---
    const revealElements = document.querySelectorAll('.reveal-fade-up, .reveal-fade-left, .reveal-fade-right');
    
    const revealOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
    };
    
    const revealObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, revealOptions);
    
    revealElements.forEach(el => {
        revealObserver.observe(el);
    });

    // --- Product Slider Controls ---
    const slider = document.getElementById('product-slider');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (slider && prevBtn && nextBtn) {
        const scrollAmount = 350; // approximate width of one card + gap

        nextBtn.addEventListener('click', () => {
            slider.scrollBy({
                left: scrollAmount,
                behavior: 'smooth'
            });
        });

        prevBtn.addEventListener('click', () => {
            slider.scrollBy({
                left: -scrollAmount,
                behavior: 'smooth'
            });
        });
    }

    // --- Quantity Buttons Logic ---
    const quantityContainers = document.querySelectorAll('.bg-gray-50.rounded-lg.border');
    
    quantityContainers.forEach(container => {
        const minusBtn = container.querySelector('button:first-child');
        const plusBtn = container.querySelector('button:last-child');
        const qtySpan = container.querySelector('span');

        if (minusBtn && plusBtn && qtySpan) {
            minusBtn.addEventListener('click', () => {
                let current = parseInt(qtySpan.textContent);
                if (current > 1) {
                    qtySpan.textContent = current - 1;
                }
            });

            plusBtn.addEventListener('click', () => {
                let current = parseInt(qtySpan.textContent);
                qtySpan.textContent = current + 1;
            });
        }
    });
    // --- Shopping Cart Logic ---
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    const cartIcon = document.getElementById('cart-icon');
    const cartSidebar = document.getElementById('cart-sidebar');
    const closeCartBtn = document.getElementById('close-cart');
    const cartOverlay = document.getElementById('cart-overlay');
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotalElement = document.getElementById('cart-total');
    const cartCountElement = document.getElementById('cart-count');
    const toastContainer = document.getElementById('toast-container');
    
    function saveCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
    }
    
    function updateCartUI() {
        // Update badge
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        if (totalItems > 0) {
            cartCountElement.textContent = totalItems;
            cartCountElement.style.display = 'flex';
        } else {
            cartCountElement.style.display = 'none';
        }
        
        // Render items
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-full text-gray-500 mt-10">
                    <i class="ph ph-shopping-cart text-6xl mb-4 text-gray-300"></i>
                    <p>Your cart is empty</p>
                </div>
            `;
            cartTotalElement.textContent = '₹0';
            return;
        }
        
        let total = 0;
        cartItemsContainer.innerHTML = cart.map((item, index) => {
            total += item.price * item.quantity;
            return `
                <div class="flex items-center gap-4 bg-white p-3 rounded-lg border shadow-sm">
                    <img src="${item.image}" alt="${item.name}" class="w-16 h-16 object-contain rounded bg-[#f7f3ec]">
                    <div class="flex-grow">
                        <h4 class="font-semibold text-sm text-textdark">${item.name}</h4>
                        <div class="text-primary font-bold text-sm">₹${item.price}</div>
                        <div class="flex items-center gap-3 mt-2">
                            <div class="flex items-center bg-gray-50 rounded border">
                                <button class="px-2 py-0.5 text-gray-600 hover:bg-gray-200 decrease-qty" data-index="${index}">-</button>
                                <span class="px-2 text-sm font-medium">${item.quantity}</span>
                                <button class="px-2 py-0.5 text-gray-600 hover:bg-gray-200 increase-qty" data-index="${index}">+</button>
                            </div>
                            <button class="text-red-500 hover:text-red-700 text-sm remove-item" data-index="${index}">
                                <i class="ph ph-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        cartTotalElement.textContent = `₹${total}`;
        
        // Attach event listeners for cart item buttons
        document.querySelectorAll('.decrease-qty').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = e.target.getAttribute('data-index');
                if (cart[idx].quantity > 1) {
                    cart[idx].quantity--;
                } else {
                    cart.splice(idx, 1);
                }
                saveCart();
                updateCartUI();
            });
        });
        
        document.querySelectorAll('.increase-qty').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = e.target.getAttribute('data-index');
                cart[idx].quantity++;
                saveCart();
                updateCartUI();
            });
        });
        
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = e.currentTarget.getAttribute('data-index');
                cart.splice(idx, 1);
                saveCart();
                updateCartUI();
            });
        });
    }
    
    function showToast(message) {
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = "bg-[#4a1515] text-white px-4 py-3 rounded-lg shadow-lg text-sm transition-all duration-300 transform translate-y-0 opacity-100";
        toast.innerHTML = `<div class="flex items-center gap-2"><i class="ph-fill ph-check-circle text-lg text-[#D4AF37]"></i> ${message}</div>`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.replace('opacity-100', 'opacity-0');
            toast.classList.replace('translate-y-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Add to Cart Button listeners
    document.querySelectorAll('.rounded-xl button').forEach(btn => {
        if (btn.innerText.includes('Add to Cart')) {
            btn.addEventListener('click', (e) => {
                const card = e.currentTarget.closest('.rounded-xl');
                const name = card.querySelector('h3').innerText;
                const priceText = card.querySelector('.text-textdark.mt-auto').innerText;
                const price = parseInt(priceText.replace(/[^0-9]/g, ''));
                const image = card.querySelector('img').src;
                
                const existingItem = cart.find(item => item.name === name);
                if (existingItem) {
                    existingItem.quantity++;
                } else {
                    cart.push({ name, price, image, quantity: 1 });
                }
                
                saveCart();
                updateCartUI();
                showToast(`Added ${name} to cart!`);
                
                // Animate badge
                if (cartCountElement) {
                    cartCountElement.classList.add('scale-125');
                    setTimeout(() => cartCountElement.classList.remove('scale-125'), 200);
                }
            });
        }
    });
    
    // Sidebar toggle logic
    function toggleCart(show) {
        if (show) {
            cartSidebar.classList.remove('translate-x-full');
            cartOverlay.classList.remove('hidden');
        } else {
            cartSidebar.classList.add('translate-x-full');
            cartOverlay.classList.add('hidden');
        }
    }
    
    if (cartIcon && cartSidebar && cartOverlay && closeCartBtn) {
        cartIcon.addEventListener('click', () => toggleCart(true));
        closeCartBtn.addEventListener('click', () => toggleCart(false));
        cartOverlay.addEventListener('click', () => toggleCart(false));
    }
    
    // Initialize cart UI on load
    if (cartSidebar) {
        updateCartUI();
    }
});
