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
});
