import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orders.models import PaymentGateway

def seed_gateways():
    gateways = [
        {
            'name': 'bKash',
            'account_number': '01700000000',
            'instructions': 'Send money to this Personal bKash number.',
            'is_active': True
        },
        {
            'name': 'Nagad',
            'account_number': '01700000000',
            'instructions': 'Send money to this Personal Nagad number.',
            'is_active': True
        },
        {
            'name': 'Rocket',
            'account_number': '01700000000',
            'instructions': 'Send money to this Personal Rocket number.',
            'is_active': False
        }
    ]

    for data in gateways:
        pg, created = PaymentGateway.objects.get_or_create(name=data['name'], defaults=data)
        if created:
            print(f"Created Gateway: {pg.name}")
        else:
            print(f"Gateway already exists: {pg.name}")

if __name__ == '__main__':
    seed_gateways()
