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
TONE: Warm, expert, and proactive.
LANGUAGES: Strictly use Bengali, English, and Banglish (English words in Bengali script or vice versa). 🚫 DO NOT use Hindi, Gujarati, or any other languages.

RULES: 
1. NO HALLUCINATIONS. Only recommend products provided in the DATA.
2. CONTEXT: Always pay attention to previous messages. If a user says "1 ta", refer back to the exact product mentioned previously (e.g., Herbal Shampoo).
3. ORDERING: DO NOT ask for Name/Phone/Address until availability and quantity are confirmed.
4. TOKEN: Output 'ORDER_READY|Name|Phone|Address' ONLY when all info is collected.
5. UPSELLING: Suggest complementary items ONLY from the database. DO NOT invent products.
6. QUALITY: Guarantee 100% freshness; refund at delivery if quality fails."""
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
