from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from products.models import Product, Category, Brand
from orders.models import Order, Courier
from marketing.models import Coupon
from users.models import User, SupportTicket


ROLE_PERMISSIONS = {
    'Manager': {
        'products': ['add', 'change', 'delete', 'view'],
        'orders':   ['add', 'change', 'delete', 'view'],
        'marketing':['add', 'change', 'delete', 'view'],
        'users':    ['view'],
        'core':     ['view'],
    },
    'Staff': {
        'orders':   ['view', 'change'],
        'products': ['view'],
        'users':    ['view'],
    },
    'Delivery': {
        'orders':   ['view', 'change'],
    },
    'Marketing': {
        'marketing':['add', 'change', 'delete', 'view'],
        'products': ['view'],
    },
}


class Command(BaseCommand):
    help = 'Setup role-based Groups with permissions'

    def handle(self, *args, **options):
        for group_name, app_perms in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            for app_label, actions in app_perms.items():
                cts = ContentType.objects.filter(app_label=app_label)
                for ct in cts:
                    for action in actions:
                        codename = f'{action}_{ct.model}'
                        try:
                            perm = Permission.objects.get(content_type=ct, codename=codename)
                            group.permissions.add(perm)
                        except Permission.DoesNotExist:
                            pass

            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'[OK] {group_name} group {status}'))

        self.stdout.write(self.style.SUCCESS('All role groups setup complete!'))
