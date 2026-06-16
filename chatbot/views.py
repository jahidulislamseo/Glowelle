
import json
import os
import re
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.db import models
import google.generativeai as genai
from openai import OpenAI
from decouple import config

# Internal Imports
from orders.models import Order, OrderItem
from products.models import Product
from core.mongodb_utils import get_mongodb_db
from core.models import SiteSettings
from .models import ChatbotFAQ, ChatbotSettings, ChatbotSuggestion, ChatbotIntent
from .ai_training_helpers import (
    detect_intent_advanced, 
    get_greeting_response, 
    get_training_response,
    save_conversation_memory,
    get_session_memory,
    get_user_info
)
from .analytics_models import ChatbotMetric, ChatbotAnalytics, PopularProduct
from .recommendation_engine import get_recommendation_context
from .language_support import detect_language, get_system_prompt_by_language
from .payment_integration import get_payment_service
from .discount_engine import get_discount_context
from .order_manager import get_order_manager
from .personality_engine import get_contextual_greeting, get_time_based_greeting

User = get_user_model()

# Initialize API Clients
gemini_key = config('GEMINI_API_KEY', default=None)
is_openrouter = gemini_key and gemini_key.startswith('sk-or-v1')
chat_client = None

if is_openrouter:
    try:
        chat_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=gemini_key,
        )
    except Exception as e:
        chat_client = None
elif gemini_key and gemini_key != 'your-gemini-api-key-here':
    genai.configure(api_key=gemini_key)
    chat_client = genai.GenerativeModel(
        'models/gemini-1.5-flash',
        generation_config={
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 300,
        }
    )
else:
    pass

# Wrapper for OpenRouter to mimic Gemini ChatSession
class OpenRouterSession:
    def __init__(self, client, model="google/gemini-2.0-flash-001"):
        self.client = client
        self.model = model
        self.history = [] 

    def send_message(self, message, system_instructions=""):
        if system_instructions and not self.history:
            self.history.append({"role": "system", "content": system_instructions})
        elif system_instructions:
            # Update system prompt if it changed or ensure it's at the top
            if self.history and self.history[0]["role"] == "system":
                self.history[0]["content"] = system_instructions
            else:
                self.history.insert(0, {"role": "system", "content": system_instructions})
                
        self.history.append({"role": "user", "content": message})
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "GlowElle",
                },
                model=self.model,
                messages=self.history,
                temperature=0.9,
                max_tokens=400
            )
            response_text = completion.choices[0].message.content
            self.history.append({"role": "assistant", "content": response_text})
            class Response:
                text = response_text
            return Response()
        except Exception as e:
            raise e

def extract_order_details(text):
    phone_pattern = r'(?:\+88|88)?01[3-9]\d{8}'
    phone_match = re.search(phone_pattern, text)
    details = {'phone': None, 'address': None}
    
    # Extract phone
    if phone_match:
        details['phone'] = phone_match.group(0)
    
    # Extract address (logic: if there's no phone, or if address is separate)
    # Looking for keywords that usually precede an address in this context
    address_indicators = ['address', 'ঠিকানা', 'dhaka', 'road', 'house', 'block', 'sector']
    if any(ind in text.lower() for ind in address_indicators):
        # Clean up the text to extract just the address
        clean_address = text
        if details['phone']:
            clean_address = clean_address.replace(details['phone'], '')
        
        # Remove common instruction words with word boundaries
        clean_address = re.sub(r'\b(address|phone|mobile|delivery|to|ঠিকানা|মোবাইল|নাম্বার)\b', '', clean_address, flags=re.IGNORECASE).strip()
        
        # Also handle colons
        clean_address = clean_address.replace(':', '').strip()
        
        if len(clean_address) > 5:
            details['address'] = clean_address
            
    return details

def create_order_from_chat(session_id, phone, address, chat_history):
    db = get_mongodb_db()
    target_product = None
    target_qty = 1
    all_products = list(Product.objects.all().values('id', 'title', 'price'))
    for msg in reversed(chat_history):
        content = msg.get('content', '') if isinstance(msg, dict) else ''
        if not content and hasattr(msg, 'parts'):
             content = msg.parts[0].text
        msg_content = content.lower()
        for p in all_products:
            if p['title'].lower() in msg_content:
                target_product = p
                break
        if target_product:
            break
    if not target_product:
        return None, "❌ I couldn't figure out which product you want. Please mention the product name again."
    last_msg = chat_history[-1].get('content', '') if isinstance(chat_history[-1], dict) else ''
    qty_match = re.search(r'(\d+)\s?(kg|pc|pcs|ta|ti)', address + " " + last_msg, re.IGNORECASE)
    if qty_match:
        try:
            target_qty = int(qty_match.group(1))
        except:
            pass
    try:
        # Try to find user by phone
        user = User.objects.filter(phone=phone).first()
        
        # If no user found, try to find by phone in different format
        if not user:
            clean_phone = phone.replace('+88', '').replace('88', '').replace('-', '').replace(' ', '')
            user = User.objects.filter(phone__contains=clean_phone).first()
        
        # Get user email or use a valid default
        user_email = user.email if user and user.email else f"chatbot_{phone.replace('+', '').replace(' ', '')}@glowellebd.com"
        user_name = user.get_full_name() if user and hasattr(user, 'get_full_name') else "Chat Customer"
        
        # Create order with all required fields
        order = Order.objects.create(
            user=user,
            full_name=user_name,
            email=user_email,
            phone=phone,
            address=address,
            city="Dhaka",
            payment_method='cod',
            payment_status='unpaid',
            subtotal=target_product['price'] * target_qty,
            delivery_charge=0,
            total=target_product['price'] * target_qty,
            status='pending',
            source='website'
        )
        
        # Create order item
        product_obj = Product.objects.get(id=target_product['id'])
        OrderItem.objects.create(
            order=order,
            product=product_obj,
            quantity=target_qty,
            price=target_product['price']
        )
        
        # Track order in analytics
        try:
            from .analytics_models import ChatbotMetric
            metric = ChatbotMetric.objects.filter(session_id=session_id).order_by('-started_at').first()
            if metric:
                metric.mark_order_placed(order)
        except Exception as analytics_error:
            print(f"Analytics tracking error: {analytics_error}")
        
        # Send notification (if configured)
        try:
            from .notification_service import send_order_notification
            send_order_notification(order)
        except Exception as notif_error:
            print(f"Notification error: {notif_error}")
        
        return order, f"✅ Order #{order.order_reference} Placed! Total: {order.total} BDT. We will call you soon."
    except Exception as e:
        print(f"Order creation error: {e}")
        return None, f"❌ Sorry, I couldn't place the order. Error: {str(e)}"

def detect_intent(message):
    message_lower = message.lower()
    if re.search(r'(?:\+88|88)?01[3-9]\d{8}', message):
        return 'buying_confirmed'
    intents = ChatbotIntent.objects.all()
    for intent in intents:
        keywords = [k.strip().lower() for k in intent.keywords.split(',')]
        if any(keyword in message_lower for keyword in keywords):
            return intent.intent_key
    buying_keywords = ['order', 'buy', 'purchase', 'কিনতে', 'অর্ডার', 'নিতে চাই', 'কিনব']
    if any(keyword in message_lower for keyword in buying_keywords):
        return 'buying'
    if any(keyword in message_lower for keyword in ['track', 'ট্র্যাক', 'status']):
        return 'track_order'
    return 'browsing'

def check_faq(message):
    try:
        faqs = ChatbotFAQ.objects.filter(is_active=True)
        message_lower = message.lower()
        for faq in faqs:
            keywords = [k.strip().lower() for k in faq.keywords.split(',')]
            if any(keyword in message_lower for keyword in keywords):
                return faq.answer
        faq_path = os.path.join(settings.BASE_DIR, 'core', 'faq_data.json')
        if os.path.exists(faq_path):
            with open(faq_path, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
            for faq in faq_data.get('faqs', []):
                if any(keyword in message_lower for keyword in faq['keywords']):
                    return faq['answer']
        return None
    except Exception as e:
        return None

def handle_order_tracking(message, session_id):
    order_ref_match = re.search(r'(ORD-\d+|#\d+)', message, re.IGNORECASE)
    phone_match = re.search(r'(?:\+88|88)?01[3-9]\d{8}', message)
    try:
        if order_ref_match:
            order_ref = order_ref_match.group(1).upper().replace('#', 'ORD-')
            order = Order.objects.filter(order_reference=order_ref).first()
        elif phone_match:
            phone = phone_match.group(0)
            orders = Order.objects.filter(phone=phone).order_by('-created_at')
            order = orders.first() if orders.exists() else None
        else:
            return "📦 **Order Tracking**\n\nPlease provide your:\n- Order Reference (e.g., ORD-12345)\n- OR Phone Number\n\nI'll help you track your order! 😊"
        if not order:
            return "❌ **Order Not Found**\n\nI couldn't find any order with that information. Please check and try again, or contact support for help. 📞"
        status_emoji = {'pending': '⏳', 'processing': '🔄', 'shipped': '🚚', 'delivered': '✅', 'cancelled': '❌'}
        emoji = status_emoji.get(order.status, '📦')
        response = f"""📦 **Order Tracking**\n\n🔖 Order: **{order.order_reference}**\n{emoji} Status: **{order.get_status_display().upper()}**\n💰 Total: **{order.total} BDT**\n📅 Placed: {order.created_at.strftime('%d %b, %Y')}\n\n📍 **Delivery Address:**\n{order.address}, {order.city}\n\n"""
        if order.status == 'shipped':
            response += "🚚 Your order is on the way! Expected delivery: 1-2 days.\n"
        elif order.status == 'delivered':
            response += "✅ Order delivered! Thank you for shopping with us! 🎉\n"
        elif order.status == 'pending':
            response += "⏳ We're processing your order. You'll receive an update soon!\n"
        return response
    except Exception as e:
        return "❌ Sorry, I encountered an error while tracking your order. Please try again or contact support."

def get_product_context(query, intent='browsing'):
    """
    Advanced search with keyword cleaning, tokenization, and multi-DB retrieval.
    """
    # 1. Clean the query
    noise_words = [
        'ase', 'hobe', 'ache', 'chi', 'koto', 'dam', 'price', 'bhai', 'apnader', 
        'have', 'is', 'available', 'want', 'need', 'অাছে', 'হবে', 'দাম', 'কত', 'চান', 'ভাই'
    ]
    # Remove punctuation and split into tokens
    clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
    tokens = [t for t in clean_query.split() if t and t not in noise_words]
    
    if not tokens:
        # Fallback to original query if everything was noise
        tokens = [query.lower()]

    # 2. Retrieval from Django DB (Primary)
    # Search for products where title or description contains ANY of the tokens
    q_objects = models.Q()
    for token in tokens:
        q_objects |= models.Q(title__icontains=token) | models.Q(short_description__icontains=token)
    
    django_products = list(Product.objects.filter(q_objects).values(
        'id', 'title', 'price', 'slug', 'short_description', 'original_price', 'stock_quantity', 'category__name'
    )[:5])

    # 3. Retrieval from MongoDB (Secondary/Archive)
    db = get_mongodb_db()
    mongo_products = []
    if db is not None:
        try:
            mongo_query = {"$or": []}
            for token in tokens:
                mongo_query["$or"].extend([
                    {"title": {"$regex": token, "$options": "i"}},
                    {"description": {"$regex": token, "$options": "i"}},
                    {"category_name": {"$regex": token, "$options": "i"}}
                ])
            if mongo_query["$or"]:
                mongo_products = list(db['products'].find(mongo_query).limit(5))
        except Exception:
            pass

    # 4. Merge and Deduplicate (Prioritize Django DB)
    seen_slugs = set()
    unified_products = []
    
    for p in django_products:
        if p['slug'] not in seen_slugs:
            # Rename original_price to compare_at_price for consistent logic below
            p['compare_at_price'] = p.pop('original_price')
            p['category_name'] = p.pop('category__name')
            unified_products.append(p)
            seen_slugs.add(p['slug'])
            
    for p in mongo_products:
        p_slug = p.get('slug')
        if p_slug and p_slug not in seen_slugs:
            # MongoDB objects usually have compare_at_price if synced correctly
            unified_products.append(p)
            seen_slugs.add(p_slug)

    # 5. Handle Priority Products
    if not query == "":
        priority_products = list(Product.objects.filter(chatbot_priority=True).values(
            'id', 'title', 'price', 'slug', 'short_description', 'original_price', 'stock_quantity', 'category__name'
        ))
        matched_priority = [p for p in priority_products if any(t in p['title'].lower() for t in tokens)]
        for mp in matched_priority:
            if mp['slug'] not in seen_slugs:
                mp['compare_at_price'] = mp.pop('original_price')
                mp['category_name'] = mp.pop('category__name')
                unified_products.insert(0, mp)
                seen_slugs.add(mp['slug'])

    # 6. Generate Context String
    if not unified_products:
        return "❌ I couldn't find specific products matching your query. However, GlowElle sources the freshest organic items daily. Try asking for Rice, Fish, Meat, or Honey!", []
    
    branding_ctx = "🌟 BRAND KNOWLEDGE: GlowElle sources directly from organic farms. 100% Chemical-free. Return-on-delivery if quality fails.\n"
    context = branding_ctx + "📦 Available Products:\n"
    for p in unified_products[:5]:
        context += f"\n🛒 **{p['title']}**\n   💰 Price: **{p['price']} BDT**"
        
        compare_price = p.get('compare_at_price')
        if compare_price and float(compare_price) > float(p['price']):
            discount = ((float(compare_price) - float(p['price'])) / float(compare_price)) * 100
            context += f" (🔥 **{discount:.0f}% OFF!**)"
            
        context += f"\n   📂 Status: {'✅ In Stock' if int(p.get('stock_quantity', 0)) > 0 else '❌ Out of Stock'}"
        if p.get('short_description'):
            context += f"\n   📝 {p['short_description']}"
        
        context += f"\n   🔗 Product URL: /products/{p['slug']}/\n"
        
    return context, unified_products[:5]

def get_chat_history_from_db(session_id):
    db = get_mongodb_db()
    if db is None:
        return []
    chat_doc = db['chat_history'].find_one({"session_id": session_id})
    if chat_doc:
        return chat_doc.get('history', [])
    return []

def save_chat_interaction(session_id, user_msg, bot_msg):
    db = get_mongodb_db()
    if db is None:
        return
    new_messages = [{"role": "user", "content": user_msg}, {"role": "assistant", "content": bot_msg}]
    db['chat_history'].update_one(
        {"session_id": session_id},
        {"$push": {"history": {"$each": new_messages}}, "$set": {"updated_at": datetime.datetime.now()}},
        upsert=True
    )

@csrf_exempt
@require_POST
def chatbot_response(request):
    if not chat_client:
        return JsonResponse({"response": "Hello! My AI brain isn't configured yet.", "status": "error"})
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Track session metrics
        metric, created = ChatbotMetric.objects.get_or_create(
            session_id=session_id,
            defaults={'user': request.user if request.user.is_authenticated else None}
        )
        metric.messages_count += 1
        metric.save()
        
        if not user_message:
            return JsonResponse({"response": "I didn't catch that. Could you repeat?", "status": "error"})
        history = get_chat_history_from_db(session_id)
        chat = None
        if is_openrouter:
            chat = OpenRouterSession(chat_client)
            chat.history = history 
        else:
            gemini_history = []
            for msg in history:
                role = "user" if msg['role'] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg['content']]})
            chat = chat_client.start_chat(history=gemini_history)
        bot_settings = ChatbotSettings.objects.first()
        site_settings = SiteSettings.objects.first()
        support_phone = site_settings.support_phone if site_settings and site_settings.support_phone else "+880 1609132361"
        welcome_msg = bot_settings.welcome_message if bot_settings else "👋 Hi! Welcome to GlowElle!"
        fast_replies = {
            "hi": welcome_msg, "hello": welcome_msg, "saalam": "Walaikum Assalam!", "salam": "Walaikum Assalam!",
            "thanks": "You're welcome! 😊", "thank you": "My pleasure! ✨", "ok": "Got it! 👍", "bye": "Goodbye! 👋",
            "menu": "How can I help you today?",
            "human": f"I'm connecting you to our support team. Call us at {support_phone}.",
            "delivery": "🚚 Inside Dhaka: Same Day (80 BDT) | Outside: 2-3 Days (150 BDT)"
        }
        clean_msg = user_message.lower().strip()
        # Only use fast replies for very short/exact keyword matches to prevent AI bypass
        if clean_msg in fast_replies or clean_msg == 'back to menu':
            response_text = fast_replies.get(clean_msg, fast_replies['menu'])
            save_chat_interaction(session_id, user_message, response_text)
            return JsonResponse({"response": response_text, "status": "success", "suggestions": get_random_suggestions()})
        faq_answer = check_faq(user_message)
        if faq_answer:
            save_chat_interaction(session_id, user_message, faq_answer)
            return JsonResponse({"response": faq_answer, "status": "success", "suggestions": ["🛒 Browse Products", "📦 Track Order"]})
        # Get session memory for context
        user_prefs, greeting_count = get_session_memory(session_id)
        if not user_prefs: user_prefs = {}
        
        # Extract details from current message
        current_details = extract_order_details(user_message)
        if current_details['phone']:
            user_prefs['phone'] = current_details['phone']
        if current_details['address']:
            user_prefs['address'] = current_details['address']
        
        # Detect user's language
        user_language = detect_language(user_message)
        
        # Advanced intent detection
        intent = detect_intent_advanced(user_message)
        
        # Handle greeting with flow control
        if intent == 'greeting':
            greeting_resp = get_greeting_response(session_id, greeting_count)
            save_conversation_memory(session_id, user_message, greeting_resp, intent, preferences=user_prefs)
            save_chat_interaction(session_id, user_message, greeting_resp)
            return JsonResponse({"response": greeting_resp, "status": "success", "suggestions": get_random_suggestions()})
        
        # Check training data for quick responses
        training_resp = get_training_response(intent, user_message)
        if training_resp:
            save_conversation_memory(session_id, user_message, training_resp, intent, preferences=user_prefs)
            save_chat_interaction(session_id, user_message, training_resp)
            return JsonResponse({"response": training_resp, "status": "success", "suggestions": get_random_suggestions()})
        
        # Handle order tracking
        if intent == 'order_tracking':
            tracking_response = handle_order_tracking(user_message, session_id)
            save_conversation_memory(session_id, user_message, tracking_response, intent, preferences=user_prefs)
            save_chat_interaction(session_id, user_message, tracking_response)
            return JsonResponse({"response": tracking_response, "status": "success", "suggestions": [{"text": "⬅ Back to Menu", "action": "message"}]})
        product_context, products_list = get_product_context(user_message, intent)
        
        # Get logged-in user info for auto-fill
        user_info = get_user_info(request.user)
        
        # Get AI recommendations
        recommendation_context = ""
        if request.user and request.user.is_authenticated:
            recommendation_context = get_recommendation_context(request.user)
        
        # Get discount offers
        discount_context = ""
        if request.user and request.user.is_authenticated:
            discount_context = get_discount_context(request.user)
        
        user_context = ""
        if user_info and user_info['has_complete_info']:
            user_context = f"""\n\n🔐 LOGGED-IN USER INFO (Auto-detected):
- Name: {user_info['name']}
- Phone: {user_info['phone']}
- Address: {user_info['address']}

ORDERING RULES FOR LOGGED-IN USER:
- Use the above information automatically for orders
- Only confirm with user before placing order
- If user wants to change info, allow them to provide new details
- Format: ORDER_READY|{user_info['name']}|{user_info['phone']}|{user_info['address']}
"""
        elif user_info and not user_info['has_complete_info']:
            missing = []
            if not user_info.get('phone'): missing.append('Phone')
            if not user_info.get('address'): missing.append('Address')
            user_context = f"\n\n🔐 USER LOGGED IN: {user_info['name']}\nMISSING INFO: {', '.join(missing)}\nAsk user for missing information only.\n"
        
        # Add guest info context from memory
        if not request.user.is_authenticated or not user_info or not user_info['has_complete_info']:
            guest_phone = user_prefs.get('phone')
            guest_address = user_prefs.get('address')
            if guest_phone or guest_address:
                user_context += f"\n\n📍 GUEST USER INFO (Collected from chat):"
                if guest_phone: user_context += f"\n- Phone: {guest_phone}"
                if guest_address: user_context += f"\n- Address: {guest_address}"
                user_context += "\nRULES: If info is present, DON'T ask again. Just confirm or ask for MISSING info."
        
        sys_prompt = bot_settings.system_prompt if bot_settings else "You are 'GlowElle Assistant'."
        promo_ctx = f"\n🔥 PROMO: {bot_settings.promo_message}" if bot_settings and bot_settings.is_promo_active else ""
        system_instructions = f"{sys_prompt}{promo_ctx}{user_context}{recommendation_context}{discount_context}\nRULES: 1. NO HALLUCINATIONS. 2. ORDERING: Need Name, Phone, Address. 3. TOKEN: ORDER_READY|Name|Phone|Address. DATA:\n{product_context}"
        try:
            if is_openrouter: response = chat.send_message(user_message, system_instructions=system_instructions)
            else: response = chat.send_message(f"{system_instructions}\n\nCustomer: {user_message}")
            ai_text = response.text
            
            # Process ORDER_READY token
            if "ORDER_READY|" in ai_text:
                print(f"DEBUG: ORDER_READY detected in response: {ai_text}")
                
                # Extract ORDER_READY line
                lines = ai_text.split('\n')
                order_line = None
                for line in lines:
                    if "ORDER_READY|" in line:
                        order_line = line.strip()
                        break
                
                if order_line:
                    parts = order_line.split("|")
                    print(f"DEBUG: ORDER_READY parts: {parts}")
                    
                    if len(parts) >= 4:
                        name = parts[1].strip()
                        phone = parts[2].strip()
                        address = parts[3].strip()
                        
                        # Create order
                        order_obj, confirm_msg = create_order_from_chat(session_id, phone, address, history)
                        
                        if order_obj:
                            # Update order with name
                            order_obj.full_name = name
                            order_obj.save()
                            
                            print(f"DEBUG: Order created successfully: {order_obj.order_reference}")
                            
                            # Remove ORDER_READY line from response
                            ai_text = ai_text.replace(order_line, '').strip()
                            
                            # Add confirmation message
                            ai_text = f"{confirm_msg}\n\n{ai_text}" if ai_text else confirm_msg
                        else:
                            print(f"DEBUG: Order creation failed: {confirm_msg}")
                            # Remove ORDER_READY line and show error
                            ai_text = ai_text.replace(order_line, '').strip()
                            ai_text = f"{confirm_msg}\n\n{ai_text}" if ai_text else confirm_msg
                    else:
                        print(f"DEBUG: Invalid ORDER_READY format, expected 4+ parts, got {len(parts)}")
            
            # Save to conversation memory for learning
            save_conversation_memory(session_id, user_message, ai_text, intent, preferences=user_prefs)
            save_chat_interaction(session_id, user_message, ai_text)
            return JsonResponse({"response": ai_text, "status": "success", "suggestions": get_random_suggestions()})
        except Exception as e:
            print(f"ERROR in chatbot response: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"response": "Sorry, try again!", "status": "error"})
    except Exception as e:
        return JsonResponse({"response": "Encountered an error.", "status": "error"})

@csrf_exempt
def get_chat_history(request):
    session_id = request.GET.get('session_id', 'default')
    history = get_chat_history_from_db(session_id)
    return JsonResponse({"history": history, "status": "success"})

@csrf_exempt
def cart_status(request):
    from orders.cart import Cart
    cart = Cart(request)
    return JsonResponse({"item_count": len(cart), "total": float(cart.get_total_price())})

def get_random_suggestions():
    suggestions = ChatbotSuggestion.objects.filter(is_active=True).order_by('order')
    if suggestions.exists():
        return [{"text": s.text, "action": s.action, "value": s.value} for s in suggestions]
    return [{"text": "🔥 Popular", "action": "message"}, {"text": "📦 Track Order", "action": "message"}]

@staff_member_required
def admin_chat_history(request):
    db = get_mongodb_db()
    sessions = []
    if db is not None:
        cursor = db['chat_history'].find().sort("updated_at", -1)
        for doc in cursor:
            sessions.append({'session_id': doc.get('session_id'), 'updated_at': doc.get('updated_at'), 'message_count': len(doc.get('history', [])), 'last_message': doc['history'][-1].get('content', '')[:50] + "...", 'history': doc.get('history', [])})
    return render(request, 'chatbot/admin/chat_history.html', {'sessions': sessions})
