    // Handle action button clicks
    function handleButtonAction(item) {
        const action = item.action;
        
        if (action === 'add_to_cart') {
            // Add to cart via AJAX
            fetch('/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    product_id: item.product_id,
                    quantity: 1
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage('✅ Added to cart! You can continue shopping or checkout.', false);
                } else {
                    addMessage('❌ Could not add to cart. Please try again.', false);
                }
            })
            .catch(error => {
                addMessage('❌ Error adding to cart.', false);
            });
            
        } else if (action === 'view_product') {
            // Open product page in new tab
            window.open(`/products/${item.slug}/`, '_blank');
            addMessage('🔗 Product page opened in new tab!', false);
            
        } else if (action === 'buy_now') {
            // Add to cart and redirect to checkout
            fetch('/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    product_id: item.product_id,
                    quantity: 1
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/checkout/';
                } else {
                    addMessage('❌ Could not proceed to checkout.', false);
                }
            });
        }
    }
    
    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
