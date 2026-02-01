// Chatbot JavaScript
(function() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeChatbot = document.getElementById('close-chatbot');
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const toggleIcon = document.getElementById('toggle-icon');

    let isOpen = false;
    
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

    chatbotToggle.addEventListener('click', toggleChatbot);
    closeChatbot.addEventListener('click', toggleChatbot);

    // Add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
        
        const bubble = document.createElement('div');
        bubble.className = `max-w-[80%] p-3 rounded-2xl shadow-sm text-sm ${
            isUser 
                ? 'bg-green-600 text-white rounded-tr-none' 
                : 'bg-white text-gray-800 rounded-tl-none border border-gray-100'
        }`;
        bubble.textContent = message;
        
        messageDiv.appendChild(bubble);
        chatbotMessages.appendChild(messageDiv);
        
        // Scroll to bottom
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
    chatbotForm.addEventListener('submit', async function(e) {
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
            
            // Remove typing indicator
            removeTypingIndicator();

            // Add bot response
            if (data.status === 'success') {
                addMessage(data.response);
                
                // Render Suggested Actions (Buttons)
                if (data.suggestions && data.suggestions.length > 0) {
                    const suggestionsDiv = document.createElement('div');
                    suggestionsDiv.className = 'flex flex-wrap gap-2 mt-2 ml-2';
                    
                    data.suggestions.forEach(text => {
                        const btn = document.createElement('button');
                        btn.className = 'bg-gray-100 hover:bg-green-100 text-green-700 text-xs px-3 py-1.5 rounded-full transition-colors border border-gray-200';
                        btn.textContent = text;
                        btn.onclick = () => {
                            chatbotInput.value = text;
                            chatbotForm.dispatchEvent(new Event('submit'));
                        };
                        suggestionsDiv.appendChild(btn);
                    });
                    
                    chatbotMessages.appendChild(suggestionsDiv);
                    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
                }
            } else {
                addMessage(data.response || 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, I could not connect to the server. Please check your internet connection.');
        } finally {
            chatbotInput.disabled = false;
            chatbotInput.focus();
        }
    });
})();
