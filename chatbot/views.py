
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
import google.generativeai as genai
from openai import OpenAI
from decouple import config

# Internal Imports
from orders.models import Order, OrderItem
from products.models import Product
from core.mongodb_utils import get_mongodb_db
from core.models import SiteSettings
from .models import ChatbotFAQ, ChatbotSettings, ChatbotSuggestion, ChatbotIntent

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

    def send_message(self, message):
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
    if phone_match:
        details['phone'] = phone_match.group(0)
        address_text = text.replace(details['phone'], '').strip()
        clean_address = re.sub(r'address|phone|mobile|delivery|to|:', '', address_text, flags=re.IGNORECASE).strip()
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
        return None, "❌ Sorry, I couldn't place the order due to a technical error."

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
    db = get_mongodb_db()
    if db is None:
        return "", []
    priority_products = list(Product.objects.filter(chatbot_priority=True).values('id', 'title', 'price', 'slug', 'short_description'))
    products = db['products'].find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"category_name": {"$regex": query, "$options": "i"}},
            {"short_description": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5)
    products_list = list(products)
    if priority_products and not query == "":
        matched_priority = [p for p in priority_products if query.lower() in p['title'].lower()]
        products_list = matched_priority + products_list
    if not products_list:
        return "❌ No specific products found.", []
    context = "📦 Available Products:\n"
    for p in products_list:
        context += f"\n🛒 **{p['title']}**\n   💰 Price: **{p['price']} BDT**"
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
        welcome_msg = bot_settings.welcome_message if bot_settings else "👋 Hi! Welcome to Al Barakah Mart!"
        fast_replies = {
            "hi": welcome_msg, "hello": welcome_msg, "saalam": "Walaikum Assalam!", "salam": "Walaikum Assalam!",
            "thanks": "You're welcome! 😊", "thank you": "My pleasure! ✨", "ok": "Got it! 👍", "bye": "Goodbye! 👋",
            "menu": "How can I help you today?",
            "human": f"I'm connecting you to our support team. Call us at {support_phone}.",
            "delivery": "🚚 Inside Dhaka: Same Day (80 BDT) | Outside: 2-3 Days (150 BDT)"
        }
        clean_msg = user_message.lower().strip()
        if 'delivery' in clean_msg: clean_msg = 'delivery'
        elif 'support' in clean_msg or 'human' in clean_msg: clean_msg = 'human'
        if clean_msg in fast_replies or clean_msg == 'back to menu':
            response_text = fast_replies.get(clean_msg, fast_replies['menu'])
            save_chat_interaction(session_id, user_message, response_text)
            return JsonResponse({"response": response_text, "status": "success", "suggestions": get_random_suggestions()})
        faq_answer = check_faq(user_message)
        if faq_answer:
            save_chat_interaction(session_id, user_message, faq_answer)
            return JsonResponse({"response": faq_answer, "status": "success", "suggestions": ["🛒 Browse Products", "📦 Track Order"]})
        intent = detect_intent(user_message)
        if intent == 'track_order':
            tracking_response = handle_order_tracking(user_message, session_id)
            save_chat_interaction(session_id, user_message, tracking_response)
            return JsonResponse({"response": tracking_response, "status": "success", "suggestions": [{"text": "⬅ Back to Menu", "action": "message"}]})
        product_context, products_list = get_product_context(user_message, intent)
        sys_prompt = bot_settings.system_prompt if bot_settings else "You are 'Al Barakah Assistant'."
        promo_ctx = f"\n🔥 PROMO: {bot_settings.promo_message}" if bot_settings and bot_settings.is_promo_active else ""
        system_instructions = f"{sys_prompt}{promo_ctx}\nRULES: 1. NO HALLUCINATIONS. 2. ORDERING: Need Name, Phone, Address. 3. TOKEN: ORDER_READY|Name|Phone|Address. DATA:\n{product_context}"
        try:
            if is_openrouter: response = chat.send_message(user_message)
            else: response = chat.send_message(f"{system_instructions}\n\nCustomer: {user_message}")
            ai_text = response.text
            if "ORDER_READY|" in ai_text:
                parts = ai_text.split("|")
                if len(parts) >= 4:
                    order_obj, confirm_msg = create_order_from_chat(session_id, parts[2].strip(), parts[3].strip(), history)
                    if order_obj:
                        order_obj.full_name = parts[1].strip()
                        order_obj.save()
                        ai_text = confirm_msg
            save_chat_interaction(session_id, user_message, ai_text)
            return JsonResponse({"response": ai_text, "status": "success", "suggestions": get_random_suggestions()})
        except Exception as e:
            return JsonResponse({"response": "Sorry, try again!", "status": "error"})
    except Exception as e:
        return JsonResponse({"response": "Encountered an error.", "status": "error"})

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
