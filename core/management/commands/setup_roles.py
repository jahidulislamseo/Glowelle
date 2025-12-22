from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from products.models import Product, Category, Brand
from orders.models import Order, Courier
from marketing.models import Coupon
from users.models import User, SupportTicket

class Command(BaseCommand):
    help = 'Setup default Roles (Groups) and Permissions'

    def handle(self, *args, **options):
        # 1. Store Manager Group
        manager_group, created = Group.objects.get_or_create(name='Store Manager')
        self.stdout.write(f'Store Manager Group: {"Created" if created else "Exists"}')
        
        # Permissions for Manager
        # Can manage Products, Orders, Marketing
        models_to_manage = [Product, Category, Brand, Order, Courier, Coupon]
        
        permissions = []
        for model in models_to_manage:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            permissions.extend(perms)
            
        manager_group.permissions.set(permissions)
        
        # 2. Support Agent Group
        support_group, created = Group.objects.get_or_create(name='Support Agent')
        self.stdout.write(f'Support Agent Group: {"Created" if created else "Exists"}')
        
        # Permissions for Support
        # Can View Orders, Can Manage Tickets, Can View Users
        
        # View Orders
        ct_order = ContentType.objects.get_for_model(Order)
        view_order = Permission.objects.filter(content_type=ct_order, codename__startswith='view_')
        
        # Manage Tickets
        ct_ticket = ContentType.objects.get_for_model(SupportTicket)
        manage_ticket = Permission.objects.filter(content_type=ct_ticket)
        
        # View Users
        ct_user = ContentType.objects.get_for_model(User)
        view_user = Permission.objects.filter(content_type=ct_user, codename__startswith='view_')
        
        support_perms = list(view_order) + list(manage_ticket) + list(view_user)
        support_group.permissions.set(support_perms)
        
        self.stdout.write(self.style.SUCCESS('Successfully setup roles and permissions'))
