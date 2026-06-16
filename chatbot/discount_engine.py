"""
Smart Discount System for GlowElle
Provides intelligent discount recommendations and automatic coupon application.
"""

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class DiscountEngine:
    """
    AI-powered discount recommendation system.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def get_available_discounts(self, order_total=None):
        """
        Get all available discounts for the user.
        Returns list of discount offers with reasons.
        """
        discounts = []
        
        if self.user and self.user.is_authenticated:
            # Loyalty points discount
            loyalty_discount = self._check_loyalty_points()
            if loyalty_discount:
                discounts.append(loyalty_discount)
            
            # First-time buyer discount
            first_time_discount = self._check_first_time_buyer()
            if first_time_discount:
                discounts.append(first_time_discount)
            
            # Repeat customer discount
            repeat_discount = self._check_repeat_customer()
            if repeat_discount:
                discounts.append(repeat_discount)
        
        # Order value-based discounts
        if order_total:
            value_discount = self._check_order_value_discount(order_total)
            if value_discount:
                discounts.append(value_discount)
        
        # Active coupons
        coupon_discounts = self._check_active_coupons()
        discounts.extend(coupon_discounts)
        
        # Seasonal/Festival discounts
        seasonal_discount = self._check_seasonal_discount()
        if seasonal_discount:
            discounts.append(seasonal_discount)
        
        return discounts
    
    def _check_loyalty_points(self):
        """Check if user has enough loyalty points for discount."""
        if not self.user:
            return None
        
        try:
            from users.models import Wallet
            wallet = Wallet.objects.filter(user=self.user).first()
            
            if wallet and wallet.loyalty_points >= 100:
                discount_percent = min(wallet.loyalty_points // 100, 20)  # Max 20%
                return {
                    'type': 'loyalty_points',
                    'discount_percent': discount_percent,
                    'description': f'আপনার {wallet.loyalty_points} পয়েন্ট আছে! {discount_percent}% ছাড় পান!',
                    'code': f'LOYALTY{discount_percent}',
                    'priority': 8
                }
        except:
            pass
        
        return None
    
    def _check_first_time_buyer(self):
        """Check if user is a first-time buyer."""
        if not self.user:
            return None
        
        try:
            from orders.models import Order
            order_count = Order.objects.filter(user=self.user).count()
            
            if order_count == 0:
                return {
                    'type': 'first_time',
                    'discount_percent': 15,
                    'description': '🎉 প্রথম অর্ডারে ১৫% ছাড়!',
                    'code': 'FIRST15',
                    'priority': 10
                }
        except:
            pass
        
        return None
    
    def _check_repeat_customer(self):
        """Check if user is a repeat customer."""
        if not self.user:
            return None
        
        try:
            from orders.models import Order
            
            # Check orders in last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_orders = Order.objects.filter(
                user=self.user,
                created_at__gte=thirty_days_ago,
                status='delivered'
            ).count()
            
            if recent_orders >= 3:
                return {
                    'type': 'repeat_customer',
                    'discount_percent': 10,
                    'description': f'🌟 আপনি একজন নিয়মিত ক্রেতা! ১০% ছাড় পান!',
                    'code': 'REPEAT10',
                    'priority': 7
                }
        except:
            pass
        
        return None
    
    def _check_order_value_discount(self, order_total):
        """Check for order value-based discounts."""
        order_total = Decimal(str(order_total))
        
        if order_total >= 5000:
            return {
                'type': 'order_value',
                'discount_percent': 15,
                'description': '💰 ৫০০০+ টাকার অর্ডারে ১৫% ছাড়!',
                'code': 'BIG15',
                'priority': 6
            }
        elif order_total >= 3000:
            return {
                'type': 'order_value',
                'discount_percent': 10,
                'description': '💰 ৩০০০+ টাকার অর্ডারে ১০% ছাড়!',
                'code': 'MEDIUM10',
                'priority': 5
            }
        elif order_total >= 1000:
            return {
                'type': 'order_value',
                'discount_percent': 5,
                'description': '💰 ১০০০+ টাকার অর্ডারে ৫% ছাড়!',
                'code': 'SMALL5',
                'priority': 4
            }
        
        return None
    
    def _check_active_coupons(self):
        """Check for active coupons."""
        coupons = []
        
        try:
            from marketing.models import Coupon
            
            active_coupons = Coupon.objects.filter(
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            
            if self.user:
                # User-specific coupons
                user_coupons = active_coupons.filter(user=self.user)
                for coupon in user_coupons:
                    coupons.append({
                        'type': 'coupon',
                        'discount_percent': coupon.discount_percentage,
                        'description': f'🎫 {coupon.code}: {coupon.discount_percentage}% ছাড়',
                        'code': coupon.code,
                        'priority': 9
                    })
            
            # Public coupons
            public_coupons = active_coupons.filter(user__isnull=True)[:3]
            for coupon in public_coupons:
                coupons.append({
                    'type': 'coupon',
                    'discount_percent': coupon.discount_percentage,
                    'description': f'🎫 {coupon.code}: {coupon.discount_percentage}% ছাড়',
                    'code': coupon.code,
                    'priority': 6
                })
        except:
            pass
        
        return coupons
    
    def _check_seasonal_discount(self):
        """Check for seasonal/festival discounts."""
        import datetime
        today = datetime.date.today()
        month = today.month
        day = today.day
        
        # Eid discounts (approximate dates)
        if month in [4, 5, 6, 7]:  # Eid season
            return {
                'type': 'seasonal',
                'discount_percent': 20,
                'description': '🌙 ঈদ মুবারক! ২০% ছাড়!',
                'code': 'EID20',
                'priority': 9
            }
        
        # Pohela Boishakh (April 14)
        if month == 4 and day == 14:
            return {
                'type': 'seasonal',
                'discount_percent': 15,
                'description': '🎊 শুভ নববর্ষ! ১৫% ছাড়!',
                'code': 'BOISHAKH15',
                'priority': 9
            }
        
        # Victory Day (December 16)
        if month == 12 and day == 16:
            return {
                'type': 'seasonal',
                'discount_percent': 16,
                'description': '🇧🇩 বিজয় দিবস! ১৬% ছাড়!',
                'code': 'VICTORY16',
                'priority': 9
            }
        
        return None
    
    def get_best_discount(self, order_total=None):
        """
        Get the best available discount.
        """
        discounts = self.get_available_discounts(order_total)
        
        if not discounts:
            return None
        
        # Sort by priority (highest first)
        discounts.sort(key=lambda x: x['priority'], reverse=True)
        
        return discounts[0]
    
    def apply_discount(self, order_total, discount_code=None):
        """
        Apply discount to order total.
        """
        order_total = Decimal(str(order_total))
        
        if discount_code:
            # Find discount by code
            discounts = self.get_available_discounts(order_total)
            discount = next((d for d in discounts if d['code'] == discount_code), None)
        else:
            # Get best discount
            discount = self.get_best_discount(order_total)
        
        if not discount:
            return {
                'original_total': order_total,
                'discount_amount': Decimal('0'),
                'final_total': order_total,
                'discount_applied': None
            }
        
        discount_amount = (order_total * Decimal(str(discount['discount_percent']))) / Decimal('100')
        final_total = order_total - discount_amount
        
        return {
            'original_total': order_total,
            'discount_amount': discount_amount,
            'final_total': final_total,
            'discount_applied': discount
        }
    
    def get_discount_text_for_chat(self, order_total=None):
        """
        Get formatted discount text for chatbot.
        """
        discounts = self.get_available_discounts(order_total)
        
        if not discounts:
            return ""
        
        # Get top 3 discounts
        discounts.sort(key=lambda x: x['priority'], reverse=True)
        top_discounts = discounts[:3]
        
        text = "\n\n💰 **আপনার জন্য বিশেষ ছাড়:**\n"
        for i, discount in enumerate(top_discounts, 1):
            text += f"{i}. {discount['description']}\n   Code: `{discount['code']}`\n"
        
        return text


def get_user_discounts(user, order_total=None):
    """
    Helper function to get discounts for a user.
    """
    engine = DiscountEngine(user)
    return engine.get_available_discounts(order_total)


def get_discount_context(user, order_total=None):
    """
    Get discount context for chatbot system prompt.
    """
    engine = DiscountEngine(user)
    return engine.get_discount_text_for_chat(order_total)
