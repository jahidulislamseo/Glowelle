document.addEventListener('DOMContentLoaded', function () {
    // Mobile Menu Logic
    const btn = document.getElementById('mobile-menu-btn');
    const closeBtn = document.getElementById('mobile-menu-close');
    const overlay = document.getElementById('mobile-menu-overlay');
    const drawer = document.getElementById('mobile-menu-drawer');

    if (btn && closeBtn && overlay && drawer) {
        function openMenu() {
            overlay.classList.remove('hidden');
            setTimeout(() => overlay.classList.remove('opacity-0'), 10);
            drawer.classList.remove('-translate-x-full');
        }

        function closeMenu() {
            overlay.classList.add('opacity-0');
            drawer.classList.add('-translate-x-full');
            setTimeout(() => overlay.classList.add('hidden'), 300);
        }

        btn.addEventListener('click', openMenu);
        closeBtn.addEventListener('click', closeMenu);
        overlay.addEventListener('click', closeMenu);
    }

    // Dark Mode Logic
    var themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    var themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    var themeToggleBtn = document.getElementById('theme-toggle');

    if (themeToggleDarkIcon && themeToggleLightIcon && themeToggleBtn) {
        // Change the icons inside the button based on previous settings
        if (localStorage.getItem('color-theme') === 'dark') {
            themeToggleLightIcon.classList.remove('hidden');
            document.documentElement.classList.add('dark');
        } else {
            themeToggleDarkIcon.classList.remove('hidden');
            document.documentElement.classList.remove('dark');
        }

        themeToggleBtn.addEventListener('click', function () {
            // toggle icons inside button
            themeToggleDarkIcon.classList.toggle('hidden');
            themeToggleLightIcon.classList.toggle('hidden');

            // if set via local storage previously
            if (localStorage.getItem('color-theme')) {
                if (localStorage.getItem('color-theme') === 'light') {
                    document.documentElement.classList.add('dark');
                    localStorage.setItem('color-theme', 'dark');
                } else {
                    document.documentElement.classList.remove('dark');
                    localStorage.setItem('color-theme', 'light');
                }
            } else {
                // if NOT set via local storage previously
                if (document.documentElement.classList.contains('dark')) {
                    document.documentElement.classList.remove('dark');
                    localStorage.setItem('color-theme', 'light');
                } else {
                    document.documentElement.classList.add('dark');
                    localStorage.setItem('color-theme', 'dark');
                }
            }
        });
    }

    // Global Loading State
    document.addEventListener("submit", function (e) {
        const form = e.target;
        const btn = form.querySelector("button[type='submit']");
        if (btn && !btn.classList.contains('no-loading')) {
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.classList.add('opacity-75', 'cursor-not-allowed');
            // Check if Lucide icons are used or text
            btn.innerHTML = `<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processing...`;
        }
    });

    // Wishlist AJAX Logic
    const wishlistButtons = document.querySelectorAll('.wishlist-btn');
    wishlistButtons.forEach(btn => {
        btn.addEventListener('click', async function (e) {
            e.preventDefault();

            // Optimistic UI Toggle
            const icon = this.querySelector('.lucide-heart') || this.querySelector('svg');
            const isActive = this.classList.contains('text-red-500');

            // Toggle classes
            if (isActive) {
                this.classList.remove('text-red-500');
                this.classList.add('text-gray-500');
                if (icon) icon.classList.remove('fill-current');
            } else {
                this.classList.remove('text-gray-500');
                this.classList.add('text-red-500');
                if (icon) icon.classList.add('fill-current');
            }
            // For buttons that use opacity group-hover (card overlay)
            if (this.classList.contains('opacity-0')) {
                this.classList.remove('opacity-0');
                this.classList.add('opacity-100');
            }

            try {
                const response = await fetch(this.getAttribute('href'), {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) throw new Error('Network response was not ok');

                const data = await response.json();
                if (data.status === 'success') {
                    // Success (could show toast here)
                } else {
                    // Revert on error
                    throw new Error('Server error');
                }
            } catch (error) {
                // Revert UI on error
                if (isActive) {
                    this.classList.add('text-red-500');
                    this.classList.remove('text-gray-500');
                    if (icon) icon.classList.add('fill-current');
                } else {
                    this.classList.add('text-gray-500');
                    this.classList.remove('text-red-500');
                    if (icon) icon.classList.remove('fill-current');
                }
            }
        });
    });

    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Password Toggle
    document.querySelectorAll('[data-toggle-password]').forEach(button => {
        button.addEventListener('click', function () {
            const targetId = this.getAttribute('data-toggle-password');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.setAttribute('data-lucide', 'eye-off');
            } else {
                input.type = 'password';
                icon.setAttribute('data-lucide', 'eye');
            }
            lucide.createIcons();
        });
    });

    // AJAX Add to Cart
    document.addEventListener('submit', function (e) {
        if (e.target.classList.contains('ajax-cart-form')) {
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2" class="h-3 w-3 animate-spin"></i> Adding...';
            lucide.createIcons();

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Update cart badge
                        updateCartBadge(data.cart_count);
                        showToast(data.message, 'success');
                    } else {
                        showToast(data.error, 'error');
                    }
                })
                .catch(err => {
                    showToast('Failed to add item to cart', 'error');
                })
                .finally(() => {
                    // Re-enable button
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                    lucide.createIcons();
                });
        }
    });

    // Update Cart Badge
    function updateCartBadge(count) {
        const badge = document.querySelector('.cart-badge, [class*="cart"] span[class*="badge"]');
        if (badge) {
            badge.textContent = count;
            if (count > 0) {
                badge.classList.remove('hidden');
            }
        }
    }

    // Toast Notification System
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-all duration-300 pointer-events-auto ${type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`;
        toast.style.transform = 'translateX(400px)';
        toast.innerHTML = `
            <div class="flex items-center gap-3">
                <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}" class="h-5 w-5"></i>
                <p class="font-medium">${message}</p>
            </div>
        `;

        document.body.appendChild(toast);
        lucide.createIcons();

        // Animate in
        setTimeout(() => toast.style.transform = 'translateX(0)', 10);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(400px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Quick View Modal
    document.addEventListener('click', function (e) {
        if (e.target.closest('.quick-view-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.quick-view-btn');
            const productId = btn.dataset.productId;

            fetch(`/product/quick-view/${productId}/`)
                .then(res => res.json())
                .then(data => {
                    showQuickViewModal(data.html);
                })
                .catch(err => {
                    showToast('Failed to load product details', 'error');
                });
        }
    });

    function showQuickViewModal(html) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative shadow-2xl transform transition-all">
                <button class="quick-view-close absolute top-4 right-4 z-10 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors">
                    <i data-lucide="x" class="h-5 w-5"></i>
                </button>
                ${html}
            </div>
        `;

        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden'; // Prevent background scroll
        lucide.createIcons();

        // Close on overlay click, X button, or Escape key
        modal.addEventListener('click', function (e) {
            if (e.target === modal || e.target.closest('.quick-view-close')) {
                closeModal();
            }
        });

        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        });

        function closeModal() {
            modal.classList.add('animate-fade-out');
            setTimeout(() => {
                modal.remove();
                document.body.style.overflow = ''; // Restore scroll
            }, 200);
        }
    }
});
