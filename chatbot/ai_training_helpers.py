import re
import json

# Greeting detection keywords
GREETING_KEYWORDS = ['hi', 'hello', 'salam', 'assalamualaikum', 'oi', 'hey', 'hola']
SMALL_TALK_KEYWORDS = ['kemon', 'ki koro', 'bhalo', 'how are you', 'tumi ke']
HUMAN_TRANSFER_KEYWORDS = ['manush', 'agent', 'operator', 'human', 'মানুষ']

def detect_intent_advanced(message):
    """
    Advanced intent detection with support for Bangla Q&A training data.
    """
    message_lower = message.lower()
    
    # Check for human transfer request
    if any(keyword in message_lower for keyword in HUMAN_TRANSFER_KEYWORDS):
        return 'human_support'
    
    # Check for greeting
    if any(keyword in message_lower for keyword in GREETING_KEYWORDS):
        return 'greeting'
    
    # Check for small talk
    if any(keyword in message_lower for keyword in SMALL_TALK_KEYWORDS):
        return 'small_talk'
    
    # Check for product query
    product_keywords = ['fish', 'meat', 'chal', 'oil', 'vegetables', 'মাছ', 'মাংস', 'তেল']
    if any(keyword in message_lower for keyword in product_keywords):
        return 'product_query'
    
    # Check for price query
    if any(keyword in message_lower for keyword in ['dam', 'price', 'koto', 'দাম', 'কত']):
        return 'price_query'
    
    # Check for delivery
    if any(keyword in message_lower for keyword in ['delivery', 'kokhon', 'asbe', 'কখন', 'ডেলিভারি']):
        return 'delivery_time'
    
    # Check for order tracking
    if any(keyword in message_lower for keyword in ['track', 'order', 'kothay', 'ট্র্যাক', 'অর্ডার']):
        return 'order_tracking'
    
    # Check for complaint
    if any(keyword in message_lower for keyword in ['kharap', 'problem', 'late', 'wrong', 'খারাপ']):
        return 'complaint'
    
    return 'browsing'

def get_greeting_response(session_id, greeting_count):
    """
    Returns appropriate greeting based on how many times user has greeted.
    """
    if greeting_count == 0:
        return "Assalamualaikum! Al Barakah Mart এ স্বাগতম 😊 কি নিতে চান?"
    elif greeting_count == 1:
        return "Alhamdulillah bhalo 😊 Apni ki nite chan?"
    else:
        return "Ki lagbe?"

def get_training_response(intent, user_message):
    """
    Get response from training data based on intent.
    """
    try:
        import os
        from django.conf import settings
        
        training_path = os.path.join(settings.BASE_DIR, 'chatbot', 'fixtures', 'training_data.json')
        if not os.path.exists(training_path):
            return None
        
        with open(training_path, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        # Find matching intent
        for intent_data in training_data:
            if intent_data['intent'] == intent:
                # Find best matching variation
                user_lower = user_message.lower()
                for variation in intent_data['variations']:
                    if variation['user'].lower() in user_lower or user_lower in variation['user'].lower():
                        return variation['bot']
                # Return first variation if no exact match
                if intent_data['variations']:
                    return intent_data['variations'][0]['bot']
        
        return None
    except Exception as e:
        return None

def save_conversation_memory(session_id, user_message, bot_response, detected_intent, preferences=None):
    """
    Save conversation to memory for learning.
    """
    try:
        from .models import ChatbotConversationMemory
        
        # Get or create memory for this session
        memory = ChatbotConversationMemory.objects.filter(session_id=session_id).order_by('-created_at').first()
        
        # Update greeting count if greeting intent
        greeting_count = 0
        if memory:
            greeting_count = memory.greeting_count
            if detected_intent == 'greeting':
                greeting_count += 1
        else:
            if detected_intent == 'greeting':
                greeting_count = 1
        
        # Merge preferences
        user_prefs = preferences or {}
        if memory and memory.user_preferences:
            user_prefs = {**memory.user_preferences, **user_prefs}
        
        # Create new memory entry
        ChatbotConversationMemory.objects.create(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response,
            detected_intent=detected_intent,
            user_preferences=user_prefs,
            greeting_count=greeting_count
        )
        
        return greeting_count
    except Exception as e:
        return 0

def get_session_memory(session_id):
    """
    Get recent conversation memory for context.
    """
    try:
        from .models import ChatbotConversationMemory
        
        memories = ChatbotConversationMemory.objects.filter(
            session_id=session_id
        ).order_by('-created_at')[:3]
        
        if not memories:
            return None, 0
        
        latest = memories[0]
        return latest.user_preferences, latest.greeting_count
    except Exception as e:
        return None, 0

def get_user_info(user):
    """
    Extract user information for auto-filling in chatbot orders.
    Returns dict with name, phone, and address.
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        from users.models import Address
        
        # Get user's full name
        full_name = f"{user.first_name} {user.last_name}".strip()
        if not full_name:
            full_name = user.username
        
        # Get phone number
        phone = user.phone_number if hasattr(user, 'phone_number') and user.phone_number else None
        
        # Get default address
        default_address = Address.objects.filter(user=user, is_default=True).first()
        address_text = None
        
        if default_address:
            address_text = f"{default_address.street}, {default_address.city}"
            # Use address phone if user doesn't have phone
            if not phone and default_address.phone:
                phone = default_address.phone
        
        return {
            'name': full_name,
            'phone': phone,
            'address': address_text,
            'has_complete_info': bool(full_name and phone and address_text)
        }
    except Exception as e:
        return None
