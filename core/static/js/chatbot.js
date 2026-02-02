// Chatbot JavaScript
(function () {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeChatbot = document.getElementById('close-chatbot');
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const toggleIcon = document.getElementById('toggle-icon');

    let isOpen = false;
    let idleTimer = null;
    const IDLE_TIME = 45000; // 45 seconds
    const TYPING_SPEED = 1500; // 1.5 seconds delay for human feel

    // Generate unique session ID for conversation history
    let sessionId = localStorage.getItem('chatbot_session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatbot_session_id', sessionId);
    }

    // Toggle chatbot window
    function toggleChatbot() {
        isOpen = !isOpen;
        if (isOpen) {
            chatbotWindow.classList.remove('hidden');
            chatbotWindow.classList.add('flex');
            setTimeout(() => {
                chatbotWindow.classList.remove('scale-95', 'opacity-0');
                chatbotWindow.classList.add('scale-100', 'opacity-100');
            }, 10);
            chatbotInput.focus();
            toggleIcon.className = 'fas fa-times text-xl';
        } else {
            chatbotWindow.classList.remove('scale-100', 'opacity-100');
            chatbotWindow.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                chatbotWindow.classList.add('hidden');
                chatbotWindow.classList.remove('flex');
            }, 300);
            toggleIcon.className = 'fas fa-comment-dots text-xl';
        }
    }

    chatbotToggle.addEventListener('click', () => {
        toggleChatbot();
        if (isOpen && chatbotMessages.children.length === 0) {
            showWelcomeMessage();
        }
        resetIdleTimer();
    });
    closeChatbot.addEventListener('click', toggleChatbot);

    function showWelcomeMessage() {
        showTypingIndicator();
        setTimeout(() => {
            removeTypingIndicator();
            const locationMsg = "🚚 Same-day delivery available in Dhaka!";
            addMessage(`👋 Hi! Welcome to Al Barakah Mart\nFresh daily essentials delivered to your door 🛒\n\n${locationMsg}\n\nHow can I help you today?`);
            addMessage("⭐ Trusted by 5,000+ happy customers\n✔ Freshness guaranteed");
            renderSuggestions([
                { "text": "🔥 Popular Items", "action": "message" },
                { "text": "🐟 Fresh Fish", "action": "message" },
                { "text": "🚚 Delivery Time", "action": "message" },
                { "text": "📦 Track Order", "action": "message" },
                { "text": "🙋 Talk to a Human", "action": "message" }
            ]);
        }, 1000);
    }

    async function checkCart() {
        try {
            const resp = await fetch('/api/cart-status/');
            const data = await resp.json();
            return data.item_count > 0;
        } catch (e) { return false; }
    }

    function resetIdleTimer() {
        if (idleTimer) clearTimeout(idleTimer);
        if (!isOpen) return;

        idleTimer = setTimeout(async () => {
            if (isOpen && chatbotMessages.children.length > 0) {
                const hasItems = await checkCart();
                if (hasItems) {
                    addMessage("👀 Still thinking? Your selected items are waiting in the cart. 🛒");
                    renderSuggestions([
                        { "text": "🛒 Go to Cart", "action": "message" },
                        { "text": "🔥 Today's Deals", "action": "message" },
                        { "text": "⬅ Back to Menu", "action": "message" }
                    ]);
                } else {
                    addMessage("😊 Need help choosing? I can suggest today’s best items.");
                    renderSuggestions([
                        { "text": "🔥 Popular Items", "action": "message" },
                        { "text": "🐟 Fresh Fish", "action": "message" },
                        { "text": "⬅ Back to Menu", "action": "message" }
                    ]);
                }
            }
        }, IDLE_TIME);
    }

    // Monitor interactions to reset idle timer
    document.addEventListener('mousedown', resetIdleTimer);
    document.addEventListener('keypress', resetIdleTimer);

    // Add message to chat
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`;

        const bubble = document.createElement('div');
        bubble.className = `max-w-[75%] px-4 py-2 rounded-2xl ${isUser
            ? 'bg-green-600 text-white rounded-br-none'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
            }`;

        // Enhanced markdown parsing with image support
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\n/g, '<br>');  // Line breaks

        // Parse markdown images: ![alt](url)
        formattedText = formattedText.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, url) => {
            return `<img src="${url}" alt="${alt}" class="max-w-full h-auto rounded-lg mt-2 mb-2" style="max-height: 200px; object-fit: cover;" loading="lazy" onerror="this.style.display='none'">`;
        });

        bubble.innerHTML = formattedText;
        messageDiv.appendChild(bubble);
        chatbotMessages.appendChild(messageDiv);

        // Mobile-first spacing adjustment
        if (window.innerWidth < 640) {
            bubble.classList.add('text-sm');
            messageDiv.classList.add('mb-2');
        }

        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex justify-start';
        typingDiv.id = 'typing-indicator';

        const bubble = document.createElement('div');
        bubble.className = 'bg-white p-3 rounded-2xl rounded-tl-none shadow-sm border border-gray-100';
        bubble.innerHTML = '<div class="flex space-x-1"><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div></div>';

        typingDiv.appendChild(bubble);
        chatbotMessages.appendChild(typingDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Handle form submission
    chatbotForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const message = chatbotInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, true);
        chatbotInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Disable input
        chatbotInput.disabled = true;

        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId  // Send session ID for conversation history
                })
            });

            const data = await response.json();

            // Fake typing delay for human feel
            setTimeout(() => {
                removeTypingIndicator();

                // Add bot response
                if (data.status === 'success') {
                    addMessage(data.response);

                    // Render Suggested Actions (Enhanced Buttons)
                    if (data.suggestions && data.suggestions.length > 0) {
                        const suggestionsDiv = document.createElement('div');
                        suggestionsDiv.className = 'flex flex-wrap gap-2 mt-2 ml-2';

                        data.suggestions.forEach(item => {
                            const btn = document.createElement('button');
                            btn.className = 'bg-white hover:bg-green-50 text-green-700 text-xs px-3 py-1.5 rounded-full transition-all border border-green-100 shadow-sm active:scale-95';

                            // Handle both string and object suggestions
                            const buttonText = typeof item === 'string' ? item : item.text;
                            btn.textContent = buttonText;

                            btn.onclick = () => {
                                resetIdleTimer();
                                if (typeof item === 'object' && item.action && item.action !== 'message') {
                                    handleButtonAction(item);
                                } else {
                                    // Simple text message
                                    chatbotInput.value = buttonText;
                                    chatbotForm.dispatchEvent(new Event('submit'));
                                }
                            };
                            suggestionsDiv.appendChild(btn);
                        });

                        chatbotMessages.appendChild(suggestionsDiv);
                        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
                    }
                } else {
                    addMessage(data.response || 'Sorry, I encountered an error. Please try again.');
                }
                resetIdleTimer();
            }, TYPING_SPEED);

        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, I could not connect to the server. Please check your internet connection.');
        } finally {
            chatbotInput.disabled = false;
            chatbotInput.focus();
        }
    });

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
        } else if (action === 'message') {
            // Simple text message
            chatbotInput.value = item.text || item;
            chatbotForm.dispatchEvent(new Event('submit'));
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
})();
