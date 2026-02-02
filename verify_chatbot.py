import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chatbot.models import ChatbotSettings
from chatbot.views import get_product_context

# 1. Update System Prompt
s = ChatbotSettings.objects.first()
if not s:
    s = ChatbotSettings.objects.create(id=1)

s.system_prompt = """PERSONA: You are 'AL BARAKAH SUPER AGENT'—the absolute expert in premium organic groceries. 
GOAL: Provide expert assistance and close sales autonomously. 
TONE: Warm, expert, and proactive. 
LANGUAGES: Fluent in Bengali, English, and Banglish. 
KNOWLEDGE: Use provided product DATA strictly. sourcing directly from farms. 100% chemical-free. 

RULES: 
1. NO HALLUCINATIONS. 
2. ORDERING: DO NOT ask for Name/Phone/Address until you have confirmed the product availability and quantity with the user. 
   Step 1: Check stock and tell user about availability.
   Step 2: Confirm quantity. 
   Step 3: Ask for Name, 11-digit Phone, and Landmark-based Address. 
3. Output 'ORDER_READY|Name|Phone|Address' ONLY when name, phone, and address are all collected.
4. UPSELLING: Suggest complementary items (e.g., Rice -> Lentils, Fish -> Spices). 
5. QUALITY: Guarantee 100% freshness; if quality fails, we refund at delivery."""
s.save()
print("System Prompt Updated Successfully")

# 2. Test Search Logic
queries = ["Padma hilsa hobe?", "beef ase?", "foll ase?", "chal hobe?"]
print("\n--- Search Logic Verification ---")
for q in queries:
    ctx, p = get_product_context(q)
    print(f"\nQuery: {q}")
    print(f"Items Found: {len(p)}")
    if p:
        print(f"Top Result: {p[0]['title']}")
    else:
        print("No matches found.")
