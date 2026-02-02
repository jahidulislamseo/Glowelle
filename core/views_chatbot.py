
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from orders.models import Order, OrderItem
from products.models import Product
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
import re
import datetime
import google.generativeai as genai
from openai import OpenAI
from decouple import config
from .mongodb_utils import get_mongodb_db
from .models import ChatbotFAQ, ChatbotSettings, SiteSettings, ChatbotSuggestion, ChatbotIntent

# Initialize API Clients
gemini_key = config('GEMINI_API_KEY', default=None)
is_openrouter = gemini_key and gemini_key.startswith('sk-or-v1')
chat_client = None

if is_openrouter:
    # print("🚀 Configuring OpenRouter API...")
    try:
        chat_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=gemini_key,
        )
        print("OpenRouter Client Configured!")
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        chat_client = None
elif gemini_key and gemini_key != 'your-gemini-api-key-here':
    genai.configure(api_key=gemini_key)
    # Use Gemini 1.5 Flash as stable fallback
    chat_client = genai.GenerativeModel(
        'models/gemini-1.5-flash',
        generation_config={
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 300,
        }
    )
    print("Gemini 1.5 Flash (Stable) loaded successfully!")
else:
    print("API Key missing or invalid")

# Wrapper for OpenRouter to mimic Gemini ChatSession
class OpenRouterSession:
    def __init__(self, client, model="google/gemini-2.0-flash-001"):
        self.client = client
        self.model = model
        self.history = [] 

    def send_message(self, message):
        # Add user message to history
        self.history.append({"role": "user", "content": message})
        
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Al Barakah Mart",
                },
                model=self.model,
                messages=self.history,
                temperature=0.9,
                max_tokens=300
            )
            
            response_text = completion.choices[0].message.content
            # Add assistant response to history
            self.history.append({"role": "assistant", "content": response_text})
            
            # Return object with text attribute (mimicking Gemini response)
            class Response:
                text = response_text
            return Response()
            
        except Exception as e:
            # If error, remove the last user message to keep history clean?
            # self.history.pop() 
            raise e

# Store conversation sessions
conversation_sessions = {}


def extract_order_details(text):
    """Extract phone and address from text."""
    phone_pattern = r'(?:\+88|88)?01[3-9]\d{8}'
    phone_match = re.search(phone_pattern, text)
    
    details = {
        'phone': None,
        'address': None
    }
    
    if phone_match:
        details['phone'] = phone_match.group(0)
        # Assume everything else is address for now
        address_text = text.replace(details['phone'], '').strip()
        # Remove common words
        clean_address = re.sub(r'address|phone|mobile|delivery|to|:', '', address_text, flags=re.IGNORECASE).strip()
        if len(clean_address) > 5:
            details['address'] = clean_address
            
    return details

def create_order_from_chat(session_id, phone, address, chat_history):
    """Create a pending order based on chat context."""
    db = get_mongodb_db()
    
    target_product = None
    target_qty = 1
    
    # 1. Identify Product
    all_products = list(Product.objects.all().values('id', 'title', 'price'))
    
    # Check history backwards for product mention
    for msg in reversed(chat_history):
        # Handle OpenRouter (dict) vs Gemini (object) format normalization needed?
        # history from DB is list of dicts: {'role':..., 'content':...}
        content = msg.get('content', '') if isinstance(msg, dict) else ''
        if not content and hasattr(msg, 'parts'): # Gemini Object
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

    # 2. Extract Quantity
    # Check simple patterns
    last_msg = chat_history[-1].get('content', '') if isinstance(chat_history[-1], dict) else ''
    qty_match = re.search(r'(\d+)\s?(kg|pc|pcs|ta|ti)', address + " " + last_msg, re.IGNORECASE)
    if qty_match:
        try:
            target_qty = int(qty_match.group(1))
        except:
            pass

    # 3. Create Order
    try:
        user = User.objects.filter(phone=phone).first()
        
        order = Order.objects.create(
            user=user,
            full_name="Chat Customer",
            phone=phone,
            address=address,
            city="Dhaka",
            payment_method='cod',
            subtotal=target_product['price'] * target_qty,
            total=target_product['price'] * target_qty,
            status='pending',
            source='website'
        )
        
        product_obj = Product.objects.get(id=target_product['id'])
        OrderItem.objects.create(
            order=order,
            product=product_obj,
            quantity=target_qty,
            price=target_product['price']
        )
        
        return order, f"✅ Order #{order.order_reference} Placed! Total: {order.total} BDT. We will call you soon."
        
    except Exception as e:
        print(f"Order Creation Error: {e}")
        return None, "❌ Sorry, I couldn't place the order due to a technical error."

def detect_intent(message):
    """Detect user intent from their message using database keywords."""
    message_lower = message.lower()
    
    # Check for Phone Number (Strong indicator of order confirmation)
    if re.search(r'(?:\+88|88)?01[3-9]\d{8}', message):
        return 'buying_confirmed'

    # Fetch intents from database
    intents = ChatbotIntent.objects.all()
    for intent in intents:
        keywords = [k.strip().lower() for k in intent.keywords.split(',')]
        if any(keyword in message_lower for keyword in keywords):
            return intent.intent_key
    
    # Fallback to defaults if DB is empty
    buying_keywords = ['order', 'buy', 'purchase', 'কিনতে', 'অর্ডার', 'নিতে চাই', 'কিনব']
    if any(keyword in message_lower for keyword in buying_keywords):
        return 'buying'
    
    # ... (rest of old logic as backup)
    if any(keyword in message_lower for keyword in ['track', 'ট্র্যাক', 'status']):
        return 'track_order'

    return 'browsing'
def check_faq(message):
    """Check if message matches any FAQ and return instant answer."""
    try:
        # Check database FAQs first
        faqs = ChatbotFAQ.objects.filter(is_active=True)
        message_lower = message.lower()
        
        for faq in faqs:
            keywords = [k.strip().lower() for k in faq.keywords.split(',')]
            if any(keyword in message_lower for keyword in keywords):
                return faq.answer

        # Fallback to local JSON if it exists (legacy support)
        faq_path = os.path.join(os.path.dirname(__file__), 'faq_data.json')
        if os.path.exists(faq_path):
            with open(faq_path, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
            for faq in faq_data.get('faqs', []):
                if any(keyword in message_lower for keyword in faq['keywords']):
                    return faq['answer']
        
        return None  # No match found
        
    except Exception as e:
        print(f"FAQ Error: {e}")
        return None

def handle_order_tracking(message, session_id):
    """Extract order reference/phone and return tracking info."""
    # Try to extract order reference (e.g., ORD-12345)
    order_ref_match = re.search(r'(ORD-\d+|#\d+)', message, re.IGNORECASE)
    
    # Try to extract phone number
    phone_match = re.search(r'(?:\+88|88)?01[3-9]\d{8}', message)
    
    try:
        if order_ref_match:
            # Search by order reference
            order_ref = order_ref_match.group(1).upper().replace('#', 'ORD-')
            order = Order.objects.filter(order_reference=order_ref).first()
        elif phone_match:
            # Search by phone number
            phone = phone_match.group(0)
            orders = Order.objects.filter(phone=phone).order_by('-created_at')
            order = orders.first() if orders.exists() else None
        else:
            # No order identifier found
            return "📦 **Order Tracking**\n\nPlease provide your:\n- Order Reference (e.g., ORD-12345)\n- OR Phone Number\n\nI'll help you track your order! 😊"
        
        if not order:
            return "❌ **Order Not Found**\n\nI couldn't find any order with that information. Please check and try again, or contact support for help. 📞"
        
        # Format order status
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '🚚',
            'delivered': '✅',
            'cancelled': '❌'
        }
        
        emoji = status_emoji.get(order.status, '📦')
        
        response = f"""📦 **Order Tracking**

🔖 Order: **{order.order_reference}**
{emoji} Status: **{order.get_status_display().upper()}**
💰 Total: **{order.total} BDT**
📅 Placed: {order.created_at.strftime('%d %b, %Y')}

📍 **Delivery Address:**
{order.address}, {order.city}

"""
        
        if order.status == 'shipped':
            response += "🚚 Your order is on the way! Expected delivery: 1-2 days.\n"
        elif order.status == 'delivered':
            response += "✅ Order delivered! Thank you for shopping with us! 🎉\n"
        elif order.status == 'pending':
            response += "⏳ We're processing your order. You'll receive an update soon!\n"
        
        return response
        
    except Exception as e:
        print(f"Order Tracking Error: {e}")
        return "❌ Sorry, I encountered an error while tracking your order. Please try again or contact support."

def get_product_context(query, intent='browsing'):
    """Enhanced product search with intent-based results."""
    db = get_mongodb_db()
    if db is None:
        return "", []

    # Boost priority products
    priority_products = list(Product.objects.filter(chatbot_priority=True).values('id', 'title', 'price', 'slug', 'short_description'))
    
    # Text search in MongoDB
    products = db['products'].find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"category_name": {"$regex": query, "$options": "i"}},
            {"short_description": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5)
    
    products_list = list(products)
    
    # Merge priority products at the top if they match query or simply as suggestions
    if priority_products and not query == "":
        # Simple string match for priority products too
        matched_priority = [p for p in priority_products if query.lower() in p['title'].lower()]
        products_list = matched_priority + products_list
    
    if not products_list:
        return "❌ No specific products found.", []
    
    context = "📦 Available Products:\n"
    
    for p in products_list:
        context += f"\n🛒 **{p['title']}**\n"
        context += f"   💰 Price: **{p['price']} BDT**"
        
        if p.get('compare_at_price') and float(p['compare_at_price']) > float(p['price']):
            discount = ((float(p['compare_at_price']) - float(p['price'])) / float(p['compare_at_price'])) * 100
            context += f" (🔥 **{discount:.0f}% OFF!**)"
        
        context += f"\n   📂 Category: {p.get('category_name', 'N/A')}"
        
        if p.get('short_description'):
            context += f"\n   📝 {p['short_description']}"
        
        stock_qty = int(p.get('stock_quantity', 0))
        if stock_qty > 10:
            context += "\n   ✅ **In Stock**"
        elif stock_qty > 0:
            context += f"\n   ⚠️ **Only {stock_qty} left!**"
        else:
            context += "\n   ❌ **Out of Stock**"
        
        if intent == 'buying' and stock_qty > 0:
            context += "\n   🚀 **Order now!**"
        
        context += f"\n   🔗 /products/{p['slug']}/\n"
    
    return context, products_list

def get_upsell_suggestions(products_list):
    """Get related products for upselling/cross-selling."""
    if not products_list:
        return ""
    
    category = products_list[0].get('category_name', '')
    
    suggestions = {
        'Electronics': "📱 **Combo:** Phone case + screen protector 20% off!",
        'Fashion': "👗 **Style Tip:** Matching accessories available!",
        'Groceries': "🛒 **Bundle:** Add 3 items, get free delivery!",
        'Beauty': "💄 **Set:** Complete skincare 15% discount!"
    }
    
    for key, value in suggestions.items():
        if key.lower() in category.lower():
            return f"\n\n{value}"
    
    return "\n\n💡 **Tip:** Order 2+ items, save on delivery!"

# Database Helper Functions
def get_chat_history_from_db(session_id):
    """Load chat history from MongoDB."""
    db = get_mongodb_db()
    if db is None:
        return []
    
    chat_doc = db['chat_history'].find_one({"session_id": session_id})
    if chat_doc:
        return chat_doc.get('history', [])
    return []

def save_chat_interaction(session_id, user_msg, bot_msg):
    """Save chat interaction to MongoDB."""
    db = get_mongodb_db()
    if db is None:
        return

    # Create message objects
    new_messages = [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": bot_msg}
    ]

    db['chat_history'].update_one(
        {"session_id": session_id},
        {
            "$push": {"history": {"$each": new_messages}},
            "$set": {"updated_at": datetime.datetime.now()}
        },
        upsert=True
    )

@csrf_exempt
@require_POST
def chatbot_response(request):
    """
    Advanced chatbot with persistent memory (MongoDB) and smart logic.
    """
    if not chat_client:
        return JsonResponse({
            "response": "Hello! My AI brain isn't configured yet.",
            "status": "error"
        })

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return JsonResponse({
                "response": "I didn't catch that. Could you repeat? / আমি বুঝতে পারিনি।",
                "status": "error"
            })

        # Load history from MongoDB
        history = get_chat_history_from_db(session_id)
        
        # Initialize Chat Session based on Provider
        chat = None
        if is_openrouter:
            chat = OpenRouterSession(chat_client)
            # Reconstruct history for OpenRouter
            chat.history = history 
        else:
            # Reconstruct history for Gemini
            gemini_history = []
            for msg in history:
                role = "user" if msg['role'] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg['content']]})
            
            chat = chat_client.start_chat(history=gemini_history)

        # Smart Greeting Control
        is_first_message = len(history) == 0

        # 0.⚡ INSTANT FAST REPLY (Bypass AI for speed)
        # Simple/Common phrases should be instant
        # Get dynamic settings and contact info
        bot_settings = ChatbotSettings.objects.first()
        site_settings = SiteSettings.objects.first()
        
        support_phone = site_settings.support_phone if site_settings and site_settings.support_phone else "+880 1609132361"
        welcome_msg = bot_settings.welcome_message if bot_settings else "👋 Hi! Welcome to Al Barakah Mart! How can I help you today?"

        fast_replies = {
            "hi": welcome_msg,
            "hello": welcome_msg,
            "saalam": "Walaikum Assalam! 🌙 Welcome to Al Barakah Mart. How can I assist you today?",
            "salam": "Walaikum Assalam! 🌙 Welcome to Al Barakah Mart. How can I assist you today?",
            "thanks": "You're very welcome! 😊 Always here to help. Happy Shopping! 🛍️",
            "thank you": "My pleasure! Let me know if there's anything else you need. ✨",
            "ok": "Got it! 👍 Is there anything else I can help with?",
            "bye": "Goodbye! Have a wonderful day. See you soon! 👋",
            "menu": "Here is our main menu! How can I help you today? 😊",
            "human": f"I'm connecting you to our support team. Please leave your message or call us at {support_phone}. 📞",
            "delivery": "🚚 **Delivery Information**\n\n• **Inside Dhaka:** Same Day / Next Day delivery (80 BDT)\n• **Outside Dhaka:** 2-3 Days delivery (150 BDT)\n\nWe guarantee 100% freshness on all organic items! 🥦"
        }
        
        clean_msg = user_message.lower().strip()
        # Keyword mapping for fast replies
        if 'delivery' in clean_msg or 'ডেলিভারি' in clean_msg:
            clean_msg = 'delivery'
        elif 'support' in clean_msg or 'human' in clean_msg or 'মানুষ' in clean_msg:
            clean_msg = 'human'
            
        if clean_msg in fast_replies or clean_msg == 'back to menu':
            # Special check for human handover working hours
            if clean_msg == 'human':
                from django.utils import timezone
                now = timezone.localtime().time()
                
                if bot_settings:
                    is_outside_hours = now < bot_settings.working_hours_start or now > bot_settings.working_hours_end
                    if is_outside_hours:
                        response_text = bot_settings.offline_message
                    else:
                        response_text = fast_replies.get(clean_msg, fast_replies['menu'])
                else:
                    response_text = fast_replies.get(clean_msg, fast_replies['menu'])
            else:
                response_text = fast_replies.get(clean_msg, fast_replies['menu'])

            save_chat_interaction(session_id, user_message, response_text)
            return JsonResponse({
                "response": response_text, 
                "status": "success",
                "suggestions": get_random_suggestions()
            })

        # 1.❓ FAQ AUTO-RESPONSE (Check before AI)
        faq_answer = check_faq(user_message)
        if faq_answer:
            save_chat_interaction(session_id, user_message, faq_answer)
            return JsonResponse({
                "response": faq_answer,
                "status": "success",
                "suggestions": ["🛒 Browse Products", "📦 Track Order", "💬 Chat More"]
            })

        # Detect Intent
        intent = detect_intent(user_message)
        
        # 2.📦 ORDER TRACKING (Check before general AI)
        if intent == 'track_order':
            tracking_response = handle_order_tracking(user_message, session_id)
            if tracking_response:
                save_chat_interaction(session_id, user_message, tracking_response)
                return JsonResponse({
                    "response": tracking_response,
                    "status": "success",
                    "suggestions": [{"text": "⬅ Back to Menu", "action": "message"}]
                })

        # 3.🚚 DELIVERY INFO
        if intent == 'delivery_info':
            delivery_response = "🚚 **Delivery Information**\n\n• **Inside Dhaka:** Same Day / Next Day delivery (80 BDT)\n• **Outside Dhaka:** 2-3 Days delivery (150 BDT)\n\nWe guarantee 100% freshness on all organic items! 🥦"
            save_chat_interaction(session_id, user_message, delivery_response)
            return JsonResponse({
                "response": delivery_response,
                "status": "success",
                "suggestions": get_random_suggestions()
            })
        
        # Handle Order Confirmation Logic (Moved to AI Token Parser below)
        # We removed the regex-based 'buying_confirmed' so logic flows to LLM

        # Get Product Context (RAG)
        product_context, products_list = get_product_context(user_message, intent)
        
        # Get Quick Suggestions (Buttons)
        suggestions = get_intent_suggestions(intent, products_list)

        # Build system context - SMART SALES V4 (HUMANIZED)
        sys_prompt = bot_settings.system_prompt if bot_settings else "You are 'Al Barakah Assistant'. Be helpful, confident, and professional."
        
        promo_ctx = ""
        if bot_settings and bot_settings.is_promo_active and bot_settings.promo_message:
            promo_ctx = f"\n🔥 CURRENT PROMOTION: {bot_settings.promo_message}\n(Mention this to the customer if relevant!)"

        system_instructions = f"""{sys_prompt}{promo_ctx}

🧠 CORE RULES:
1. **NO HALLUCINATIONS:** Use ONLY product data below.
2. **STRICT ORDERING:**
   - To place an order, User MUST provide: **Name, Phone, AND Address**.
   - If ANY is missing, ask for it politely.
   - If ALL are present (Name, Phone, Address), start your reply EXACTLY like this:
     `ORDER_READY|Customer Name|Phone Number|Address`
     (Do not say anything else in that confirmed message).

3. **STRUCTURED PRODUCTS WITH IMAGES:**
   When suggesting products, ALWAYS use this format:
   
   🍗 **[Product Name]**
   💰 Price: [Price] BDT
   📦 Stock: available
   
   **IMPORTANT:** If a product has an image URL in the data, include it using markdown:
   ![Product Image](image_url_here)

4. **LANGUAGE:** Reply in User's Language.

📦 PRODUCT DATA:
{product_context}

🎯 USER INTENT: {intent}

💡 STYLE GUIDE:
- Be confident, expert, and helpful.
- **Trust Signals:** Mention that we are trusted by 5,000+ customers and guarantee 100% freshness.
- Never mention being an AI or having limitations.
- Keep responses short and mobile-friendly.
- Use emojis subtly to feel friendly.
- Suggest today's best items if the user is unsure.
"""

        # For first message in session, send system context
        full_message = user_message
        if is_first_message:
            full_message = f"{system_instructions}\n\nCustomer: {user_message}"
        else:
            full_message = f"{system_instructions}\n\nCustomer: {user_message}"
        
        # Get AI Response
        try:
            if is_openrouter: # Correct variable name
                response = chat.send_message(user_message) 
                ai_text = response.text
            else:
                response = chat.send_message(full_message)
                ai_text = response.text
            
            # 🔍 CHECK FOR ORDER TOKEN (STRICT VALIDATION)
            if "ORDER_READY|" in ai_text:
                try:
                    # Expected format: ORDER_READY|Name|Phone|Address
                    parts = ai_text.split("|")
                    if len(parts) >= 4:
                        c_name = parts[1].strip()
                        c_phone = parts[2].strip()
                        c_addr = parts[3].strip()
                        
                        # Create Order
                        # Refactor create_order_from_chat to accept name? 
                        # For now, create_order_from_chat takes (session, phone, addr, history)
                        # We will update it or just update the object after
                        order_obj, confirm_msg = create_order_from_chat(session_id, c_phone, c_addr, history)
                        
                        if order_obj:
                            order_obj.full_name = c_name
                            order_obj.save()
                            ai_text = confirm_msg
                        else:
                            ai_text = confirm_msg # Error state
                    else:
                         ai_text = "I am ready to order, but I had a glitch reading the details. Please confirm your Name, Phone, and Address again."

                except Exception as e:
                    print(f"Parsing Order Token Error: {e}")
                    ai_text = "⚠️ Sorry, I had trouble processing that order. Please try again."

            # Save Logic
            save_chat_interaction(session_id, user_message, ai_text)
            
            return JsonResponse({
                "response": ai_text, 
                "status": "success",
                "suggestions": get_random_suggestions()
            })

        except Exception as e:
            print(f"❌ AI Error: {str(e)}")
            return JsonResponse({
                "response": "Sorry, I'm having a brief moment. Please try again!",
                "status": "error"
            })

    except Exception as e:
        print(f"❌ Global System Error: {str(e)}")
        return JsonResponse({
            "response": "Sorry, I encountered a system error. Please try again.",
            "status": "error"
        })


@csrf_exempt
def cart_status(request):
    """API to check if the cart has items (used for chatbot reminders)."""
    from orders.cart import Cart
    cart = Cart(request)
    return JsonResponse({
        "item_count": len(cart),
        "total": float(cart.get_total_price())
    })

def get_random_suggestions():
    """Return standardized main menu suggestions from database."""
    suggestions = ChatbotSuggestion.objects.filter(is_active=True).order_by('order')
    if suggestions.exists():
        return [{"text": s.text, "action": s.action, "value": s.value} for s in suggestions]
        
    return [
        {"text": "🔥 Popular Items", "action": "message"},
        {"text": "🐟 Fresh Fish", "action": "message"},
        {"text": "🥩 Meat", "action": "message"},
        {"text": "🚚 Delivery Time", "action": "message"},
        {"text": "📦 Track Order", "action": "message"},
        {"text": "🙋 Talk to a Human", "action": "message"}
    ]


def get_intent_suggestions(intent, products):
    """Generate smart quick reply buttons with actionable data."""
    suggestions = []
    
    # If products are available, add product-specific actions
    if products and len(products) > 0:
        # Take first product for quick actions
        first_product = products[0]
        product_id = first_product.get('_id') or first_product.get('id')
        product_slug = first_product.get('slug', '')
        
        # Return action buttons with metadata
        return [
            {"text": "🛒 Add to Cart", "action": "add_to_cart", "product_id": str(product_id)},
            {"text": "👁️ View Product", "action": "view_product", "slug": product_slug},
            {"text": "⚡ Buy Now", "action": "buy_now", "product_id": str(product_id)}
        ]
    
    # Intent-based suggestions
    if intent == 'buying':
        suggestions = [
            {"text": "🛒 Order Now", "action": "message"},
            {"text": "💰 Check Price", "action": "message"},
            {"text": "🚚 Delivery Info", "action": "message"}
        ]
    
    elif intent == 'price_negotiation':
        suggestions = [
            {"text": "🔥 Best Deals", "action": "message"},
            {"text": "📦 Combo Offer", "action": "message"}
        ]
    
    elif intent == 'confused' or intent == 'browsing':
        suggestions = [
            {"text": "🐟 Fresh Fish", "action": "message"},
            {"text": "🥩 Meat", "action": "message"},
            {"text": "🍉 Fruits", "action": "message"}
        ]
        
    else:
        suggestions = [
            {"text": "📦 Track Order", "action": "message"},
            {"text": "📞 Human Support", "action": "message"}
        ]

    # Add standard navigation to any intent-based suggestions
    suggestions.append({"text": "⬅ Back to Menu", "action": "message"})
    return suggestions


@staff_member_required
def admin_chat_history(request):
    """Admin view to see all chat history."""
    db = get_mongodb_db()
    
    sessions = []
    if db is not None:
        # Fetch all chat sessions, sorted by latest update
        cursor = db['chat_history'].find().sort("updated_at", -1)
        
        for doc in cursor:
            # Format time
            updated_at = doc.get('updated_at', datetime.datetime.now())
            if isinstance(updated_at, str): # Handle legacy string dates if any
                try: 
                    updated_at = datetime.datetime.fromisoformat(updated_at)
                except:
                    pass
            
            # Get last message preview
            last_msg = ""
            if doc.get('history'):
                last_msg = doc['history'][-1].get('content', '')[:50] + "..."

            sessions.append({
                'session_id': doc.get('session_id'),
                'updated_at': updated_at,
                'message_count': len(doc.get('history', [])),
                'last_message': last_msg,
                'history': doc.get('history', [])
            })

    return render(request, 'admin/chat_history.html', {'sessions': sessions})
