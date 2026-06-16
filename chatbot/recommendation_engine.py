"""
Product Recommendation Engine for GlowElle Chatbot
Provides intelligent product suggestions based on user behavior and purchase history.
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from orders.models import Order, OrderItem


class RecommendationEngine:
    """
    AI-powered product recommendation system.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def get_recommendations(self, limit=5):
        """
        Get personalized product recommendations.
        Returns list of recommended products with reasons.
        """
        recommendations = []
        
        if self.user and self.user.is_authenticated:
            # Personalized recommendations for logged-in users
            recommendations.extend(self._get_repeat_purchase_suggestions())
            recommendations.extend(self._get_complementary_products())
            recommendations.extend(self._get_frequently_bought_together())
        
        # Add seasonal/trending products
        recommendations.extend(self._get_seasonal_products())
        recommendations.extend(self._get_trending_products())
        
        # Remove duplicates and limit
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec['product'].id not in seen:
                seen.add(rec['product'].id)
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    def _get_repeat_purchase_suggestions(self):
        """Suggest products user bought before."""
        if not self.user:
            return []
        
        # Get products ordered in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = Order.objects.filter(
            user=self.user,
            created_at__gte=thirty_days_ago
        )
        
        # Get most frequently ordered products
        product_counts = {}
        for order in recent_orders:
            for item in order.items.all():
                product_counts[item.product.id] = product_counts.get(item.product.id, 0) + 1
        
        # Sort by frequency
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for product_id, count in sorted_products[:3]:
            product = Product.objects.filter(id=product_id).first()
            if product and product.in_stock:
                recommendations.append({
                    'product': product,
                    'reason': f'আপনি গত মাসে {count} বার এটি কিনেছেন',
                    'score': 10 + count
                })
        
        return recommendations
    
    def _get_complementary_products(self):
        """Suggest products that complement user's purchases."""
        if not self.user:
            return []
        
        # Get user's recent purchases
        recent_orders = Order.objects.filter(user=self.user).order_by('-created_at')[:5]
        purchased_products = []
        for order in recent_orders:
            purchased_products.extend([item.product for item in order.items.all()])
        
        recommendations = []
        complementary_map = {
            'fish': ['spices', 'oil', 'lemon'],
            'meat': ['spices', 'onion', 'garlic'],
            'rice': ['lentils', 'oil'],
            'মাছ': ['মসলা', 'তেল', 'লেবু'],
            'মাংস': ['মসলা', 'পেঁয়াজ', 'রসুন'],
        }
        
        for product in purchased_products:
            title_lower = product.title.lower()
            for key, complements in complementary_map.items():
                if key in title_lower:
                    # Find complementary products
                    for complement in complements:
                        comp_products = Product.objects.filter(
                            Q(title__icontains=complement) | Q(category__name__icontains=complement),
                            in_stock=True
                        )[:2]
                        
                        for comp_prod in comp_products:
                            recommendations.append({
                                'product': comp_prod,
                                'reason': f'{product.title} এর সাথে যায়',
                                'score': 8
                            })
        
        return recommendations
    
    def _get_frequently_bought_together(self):
        """Find products frequently bought together."""
        if not self.user:
            return []
        
        # Get user's last order
        last_order = Order.objects.filter(user=self.user).order_by('-created_at').first()
        if not last_order:
            return []
        
        # Get products from last order
        last_products = [item.product for item in last_order.items.all()]
        
        # Find orders containing these products
        similar_orders = Order.objects.filter(
            items__product__in=last_products
        ).exclude(user=self.user).distinct()[:20]
        
        # Count products in similar orders
        product_counts = {}
        for order in similar_orders:
            for item in order.items.all():
                if item.product not in last_products:
                    product_counts[item.product.id] = product_counts.get(item.product.id, 0) + 1
        
        # Sort by frequency
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for product_id, count in sorted_products[:3]:
            product = Product.objects.filter(id=product_id, in_stock=True).first()
            if product:
                recommendations.append({
                    'product': product,
                    'reason': 'অন্যরা এটিও কিনেছেন',
                    'score': 7 + count
                })
        
        return recommendations
    
    def _get_seasonal_products(self):
        """Get seasonal product recommendations."""
        import datetime
        month = datetime.datetime.now().month
        
        seasonal_keywords = {
            # Summer (April-June)
            4: ['mango', 'watermelon', 'আম', 'তরমুজ'],
            5: ['mango', 'lychee', 'আম', 'লিচু'],
            6: ['jackfruit', 'mango', 'কাঁঠাল', 'আম'],
            # Monsoon (July-September)
            7: ['hilsa', 'ইলিশ'],
            8: ['hilsa', 'ইলিশ'],
            9: ['hilsa', 'ইলিশ'],
            # Winter (November-February)
            11: ['vegetables', 'শাকসবজি'],
            12: ['vegetables', 'date', 'শাকসবজি', 'খেজুর'],
            1: ['vegetables', 'শাকসবজি'],
            2: ['strawberry', 'স্ট্রবেরি'],
        }
        
        keywords = seasonal_keywords.get(month, [])
        if not keywords:
            return []
        
        recommendations = []
        for keyword in keywords[:2]:
            products = Product.objects.filter(
                Q(title__icontains=keyword) | Q(category__name__icontains=keyword),
                in_stock=True
            )[:2]
            
            for product in products:
                recommendations.append({
                    'product': product,
                    'reason': 'এখন মৌসুমী পণ্য',
                    'score': 6
                })
        
        return recommendations
    
    def _get_trending_products(self):
        """Get currently trending products."""
        # Get best sellers from last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        trending = OrderItem.objects.filter(
            order__created_at__gte=seven_days_ago,
            product__in_stock=True
        ).values('product').annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:3]
        
        recommendations = []
        for item in trending:
            product = Product.objects.filter(id=item['product']).first()
            if product:
                recommendations.append({
                    'product': product,
                    'reason': 'এখন সবচেয়ে জনপ্রিয়',
                    'score': 5
                })
        
        return recommendations
    
    def get_recommendation_text(self, limit=3):
        """
        Get formatted recommendation text for chatbot.
        """
        recommendations = self.get_recommendations(limit=limit)
        
        if not recommendations:
            return ""
        
        text = "\n\n🎯 **আপনার জন্য সুপারিশ:**\n"
        for i, rec in enumerate(recommendations[:limit], 1):
            product = rec['product']
            reason = rec['reason']
            text += f"{i}. **{product.title}** - {product.price} BDT\n   ({reason})\n"
        
        return text


def get_user_recommendations(user, limit=5):
    """
    Helper function to get recommendations for a user.
    """
    engine = RecommendationEngine(user)
    return engine.get_recommendations(limit=limit)


def get_recommendation_context(user):
    """
    Get recommendation context for chatbot system prompt.
    """
    engine = RecommendationEngine(user)
    return engine.get_recommendation_text(limit=3)
