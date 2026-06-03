import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chatbot.models import ChatbotIntent, ChatbotFAQ

def import_training_data():
    fixture_path = os.path.join('chatbot', 'fixtures', 'training_data.json')
    if not os.path.exists(fixture_path):
        print(f"Fixture not found at {fixture_path}")
        return

    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Importing {len(data)} intents/categories...")

    for item in data:
        intent_key = item.get('intent')
        variations = item.get('variations', [])
        
        # 1. Create/Update Intent
        keywords = ", ".join(set([v['user'] for v in variations]))
        intent, created = ChatbotIntent.objects.update_or_create(
            intent_key=intent_key,
            defaults={
                'display_name': intent_key.capitalize().replace('_', ' '),
                'keywords': keywords,
                'is_active': True
            }
        )
        print(f"{'Created' if created else 'Updated'} Intent: {intent_key}")

        # 2. Create FAQs for each variation (or at least one representative one)
        # For simplicity, we'll create one FAQ per intent for now if it doesn't exist
        if variations:
            faq, created = ChatbotFAQ.objects.update_or_create(
                question=f"Tell me about {intent_key}",
                defaults={
                    'keywords': intent_key,
                    'answer': variations[0]['bot'],
                    'is_active': True
                }
            )
            print(f"{'Created' if created else 'Updated'} FAQ for: {intent_key}")

    print("\nTraining Data Import Complete!")

if __name__ == "__main__":
    import_training_data()
