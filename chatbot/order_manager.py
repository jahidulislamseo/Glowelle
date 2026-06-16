"""
Advanced Order Management for GlowElle Chatbot
Handles order modification, cancellation, and repeat orders.
"""

from django.utils import timezone
from decimal import Decimal


class OrderManager:
    """
    Advanced order management system.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def get_last_order(self):
        """Get user's last order."""
        if not self.user:
            return None
        
        try:
            from orders.models import Order
            return Order.objects.filter(user=self.user).order_by('-created_at').first()
        except:
            return None
    
    def repeat_last_order(self):
        """
        Repeat user's last order.
        Creates a new order with same items.
        """
        last_order = self.get_last_order()
        
        if not last_order:
            return None, "❌ আপনার কোনো পূর্ববর্তী অর্ডার নেই।"
        
        try:
            from orders.models import Order, OrderItem
            
            # Create new order
            new_order = Order.objects.create(
                user=self.user,
                full_name=last_order.full_name,
                email=last_order.email,
                phone=last_order.phone,
                address=last_order.address,
                city=last_order.city,
                zip_code=last_order.zip_code,
                payment_method=last_order.payment_method,
                subtotal=last_order.subtotal,
                delivery_charge=last_order.delivery_charge,
                total=last_order.total,
                status='pending',
                source='website'
            )
            
            # Copy order items
            for item in last_order.items.all():
                OrderItem.objects.create(
                    order=new_order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.price
                )
            
            return new_order, f"✅ আপনার অর্ডার পুনরায় তৈরি করা হয়েছে!\n\nOrder: {new_order.order_reference}\nTotal: {new_order.total} BDT\n\nআমরা শীঘ্রই আপনার সাথে যোগাযোগ করব। 😊"
        
        except Exception as e:
            return None, f"❌ অর্ডার পুনরায় তৈরি করতে সমস্যা হয়েছে: {str(e)}"
    
    def modify_order(self, order_reference, modifications):
        """
        Modify an existing order.
        modifications: dict with 'quantity', 'address', etc.
        """
        try:
            from orders.models import Order
            
            order = Order.objects.filter(
                order_reference=order_reference,
                user=self.user,
                status='pending'
            ).first()
            
            if not order:
                return False, "❌ অর্ডার খুঁজে পাওয়া যায়নি অথবা এটি ইতিমধ্যে প্রক্রিয়াধীন।"
            
            # Modify address
            if 'address' in modifications:
                order.address = modifications['address']
            
            # Modify phone
            if 'phone' in modifications:
                order.phone = modifications['phone']
            
            # Modify quantity (for single-item orders)
            if 'quantity' in modifications and order.items.count() == 1:
                item = order.items.first()
                new_quantity = int(modifications['quantity'])
                item.quantity = new_quantity
                item.save()
                
                # Recalculate total
                order.subtotal = item.price * new_quantity
                order.total = order.subtotal + order.delivery_charge
            
            order.save()
            
            return True, f"✅ অর্ডার আপডেট করা হয়েছে!\n\nOrder: {order.order_reference}\nNew Total: {order.total} BDT"
        
        except Exception as e:
            return False, f"❌ অর্ডার আপডেট করতে সমস্যা হয়েছে: {str(e)}"
    
    def cancel_order(self, order_reference, reason=None):
        """
        Cancel an order.
        """
        try:
            from orders.models import Order
            
            order = Order.objects.filter(
                order_reference=order_reference,
                user=self.user
            ).first()
            
            if not order:
                return False, "❌ অর্ডার খুঁজে পাওয়া যায়নি।"
            
            if order.status in ['shipped', 'delivered']:
                return False, "❌ এই অর্ডার ইতিমধ্যে পাঠানো/ডেলিভার হয়ে গেছে। বাতিল করা যাবে না।"
            
            if order.status == 'cancelled':
                return False, "❌ এই অর্ডার ইতিমধ্যে বাতিল করা হয়েছে।"
            
            # Cancel order
            order.status = 'cancelled'
            order.cancellation_reason = reason or "Customer requested cancellation via chatbot"
            order.save()
            
            return True, f"✅ অর্ডার বাতিল করা হয়েছে।\n\nOrder: {order.order_reference}\n\nআপনার টাকা ফেরত দেওয়া হবে (যদি পেমেন্ট করা থাকে)। 😊"
        
        except Exception as e:
            return False, f"❌ অর্ডার বাতিল করতে সমস্যা হয়েছে: {str(e)}"
    
    def get_order_history(self, limit=5):
        """
        Get user's order history.
        """
        if not self.user:
            return []
        
        try:
            from orders.models import Order
            
            orders = Order.objects.filter(user=self.user).order_by('-created_at')[:limit]
            
            history = []
            for order in orders:
                history.append({
                    'order_reference': order.order_reference,
                    'total': order.total,
                    'status': order.get_status_display(),
                    'created_at': order.created_at,
                    'items_count': order.items.count()
                })
            
            return history
        
        except:
            return []
    
    def get_order_history_text(self, limit=5):
        """
        Get formatted order history for chatbot.
        """
        history = self.get_order_history(limit)
        
        if not history:
            return "আপনার কোনো অর্ডার নেই।"
        
        text = "📦 **আপনার সাম্প্রতিক অর্ডার:**\n\n"
        
        status_emoji = {
            'Pending': '⏳',
            'Processing': '🔄',
            'Shipped': '🚚',
            'Delivered': '✅',
            'Cancelled': '❌'
        }
        
        for i, order in enumerate(history, 1):
            emoji = status_emoji.get(order['status'], '📦')
            text += f"{i}. {emoji} **{order['order_reference']}**\n"
            text += f"   Total: {order['total']} BDT\n"
            text += f"   Status: {order['status']}\n"
            text += f"   Date: {order['created_at'].strftime('%d %b, %Y')}\n\n"
        
        return text


def get_order_manager(user):
    """
    Helper function to get order manager for a user.
    """
    return OrderManager(user)
