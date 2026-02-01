
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
from decouple import config
from .mongodb_utils import get_mongodb_db
import google.generativeai as genai
import re
from openai import OpenAI
import datetime # Added for datetime.datetime.now()

# Initialize API Clients
gemini_key = config('GEMINI_API_KEY', default=None)
is_openrouter = gemini_key and gemini_key.startswith('sk-or-v1')
chat_client = None

if is_openrouter:
    print("🚀 Configuring OpenRouter API...")
    try:
        chat_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=gemini_key,
        )
        print("✅ OpenRouter Client Configured!")
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")
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
    print("✅ Gemini 1.5 Flash (Stable) loaded successfully!")
else:
    print("❌ API Key missing or invalid")

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
    """Detect user intent from their message."""
    message_lower = message.lower()
    
    # Check for Phone Number (Strong indicator of order confirmation)
    if re.search(r'(?:\+88|88)?01[3-9]\d{8}', message):
        return 'buying_confirmed'

    buying_keywords = ['order', 'buy', 'purchase', 'কিনতে', 'অর্ডার', 'নিতে চাই', 'কিনব']
    if any(keyword in message_lower for keyword in buying_keywords):
        return 'buying'
    
    compare_keywords = ['compare', 'difference', 'better', 'তুলনা', 'কোনটা ভালো']
    if any(keyword in message_lower for keyword in compare_keywords):
        return 'comparing'
    
    price_keywords = ['discount', 'ছাড়', 'কম দাম', 'cheap', 'সস্তা']
    if any(keyword in message_lower for keyword in price_keywords):
        return 'price_negotiation'
    
    support_keywords = ['help', 'problem', 'সমস্যা', 'delivery', 'return']
    if any(keyword in message_lower for keyword in support_keywords):
        return 'support'
    
    confused_keywords = ['confused', 'বুঝতে পারছি না', 'কোনটা']
    if any(keyword in message_lower for keyword in confused_keywords):
        return 'confused'
    
    return 'browsing'

def get_product_context(query, intent='browsing'):
    """Enhanced product search with intent-based results."""
    db = get_mongodb_db()
    if db is None:
        return "", []
    
    products = db['products'].find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"category_name": {"$regex": query, "$options": "i"}},
            {"short_description": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5)
    
    products_list = list(products)
    
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
        fast_replies = {
            "hi": "Hello! 👋 Welcome to Al Barakah Mart. How can I help you today?",
            "hello": "Hi there! 👋 Welcome to Al Barakah Mart.",
            "saalam": "Walaikum Assalam! 🌙 How can I assist you?",
            "salam": "Walaikum Assalam! 🌙 Welcome to Al Barakah Mart.",
            "thanks": "You're welcome! 😊 Happy Shopping!",
            "thank you": "Anytime! Let me know if you need anything else. 🛍️",
            "ok": "Great! 👍",
            "bye": "Goodbye! See you soon. 👋",
            "call me": "Sure! Please provide your phone number. 📞"
        }
        
        clean_msg = user_message.lower().strip()
        if clean_msg in fast_replies:
            response_text = fast_replies[clean_msg]
            save_chat_interaction(session_id, user_message, response_text)
            return JsonResponse({
                "response": response_text, 
                "status": "success",
                "suggestions": get_random_suggestions()
            })

        # Detect Intent
        intent = detect_intent(user_message)
        
        # Handle Order Confirmation Logic (Moved to AI Token Parser below)
        # We removed the regex-based 'buying_confirmed' so logic flows to LLM

        # Get Product Context (RAG)
        product_context, products_list = get_product_context(user_message, intent)
        
        # Get Quick Suggestions (Buttons)
        suggestions = get_intent_suggestions(intent, products_list)

        # Build system context - SMART SALES V3 (STRICT ORDER MODE)
        system_instructions = f"""You are 'Al Barakah Assistant'.

🧠 CORE RULES:
1. **NO HALLUCINATIONS:** Use ONLY product data below.
2. **STRICT ORDERING:**
   - To place an order, User MUST provide: **Name, Phone, AND Address**.
   - If ANY is missing, ask for it politely.
   - If ALL are present (Name, Phone, Address), start your reply EXACTLY like this:
     `ORDER_READY|Customer Name|Phone Number|Address`
     (Do not say anything else in that confirmed message).

3. **STRUCTURED PRODUCTS:**
   🍗 [Product Name]
   💰 Price: [Price]
   stock: available

4. **LANGUAGE:** Reply in User's Language.

📦 PRODUCT DATA:
{product_context}

🎯 USER INTENT: {intent}
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


def get_intent_suggestions(intent, products):
    """Generate smart quick reply buttons based on intent."""
    if intent == 'buying' or (products and len(products) > 0):
        return ["🛒 Order Now", "💰 Check Price", "🚚 Delivery Info"]
    
    if intent == 'price_negotiation':
        return ["🔥 Best Deals", "📦 Combo Offer"]
    
    if intent == 'confused' or intent == 'browsing':
        return ["🐟 Fresh Fish", "🥩 Meat", "🍉 Fruits", "🍗 Chicken"]
        
    return ["📦 Track Order", "📞 Human Support"]

import datetime

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
