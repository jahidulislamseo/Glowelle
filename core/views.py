from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count, F, Avg
from django.db.models.functions import TruncDate, TruncHour
from orders.models import Order, OrderItem
from users.models import User
from datetime import timedelta
from products.models import Product
from analytics.models import VisitorSession, PageView, AnalyticsEvent
from django.contrib.auth import get_user_model


@staff_member_required
def analytics_dashboard(request):
    # Time Range (Default 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # 1. Traffic Metrics
    sessions = VisitorSession.objects.filter(start_time__gte=start_date)
    total_sessions = sessions.count()
    total_users = sessions.filter(user__isnull=False).values('user').distinct().count()
    
    # Bounce Rate
    bounces = sessions.filter(is_bounce=True).count()
    bounce_rate = (bounces / total_sessions * 100) if total_sessions > 0 else 0
    
    # Avg Session Duration
    valid_sessions = sessions.filter(last_seen__gt=F('start_time'))
    avg_duration = 0
    if valid_sessions.exists():
        total_seconds = sum([(s.last_seen - s.start_time).total_seconds() for s in valid_sessions])
        avg_duration = total_seconds / valid_sessions.count() / 60 # Minutes

    # Avg Page Load Time
    page_views = PageView.objects.filter(timestamp__gte=start_date)
    avg_load_time = page_views.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0

    # 2. Device & Browser Breakdown
    devices = sessions.values('device_type').annotate(count=Count('id')).order_by('-count')
    device_data = {d['device_type']: d['count'] for d in devices}
    
    # Simple Browser Stats (Grouping by raw string for now, ideally parsed)
    # We will just take top 5 raw strings or ideally use 'browser' field if populated
    # Since middleware didn't parse browser fully, we rely on what we have or user_agent
    # For now, let's assume 'browser' field is being populated or just show OS
    browsers = sessions.values('os').annotate(count=Count('id')).order_by('-count')[:5]
    browser_data = {b['os'] or 'Unknown': b['count'] for b in browsers}

    # 3. Events Logic
    events = AnalyticsEvent.objects.filter(timestamp__gte=start_date)
    
    # Cart & Checkout Funnel
    adds = events.filter(event_type='add_to_cart').count()
    starts = events.filter(event_type='checkout_start').count()
    payments = events.filter(event_type='payment_success').count()
    
    # Auth Stats
    logins = events.filter(event_type='login').count()
    signups = events.filter(event_type='signup').count()
    
    # Top Searches
    top_searches = events.filter(event_type='search').values('value').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Top Products (Most Viewed)
    # Filter PageViews where url starts with /product/
    top_products = page_views.filter(url__startswith='/product/').values('url').annotate(count=Count('id')).order_by('-count')[:8]

    # 404 Errors
    errors_404 = events.filter(event_type='error_404').values('url').annotate(count=Count('id')).order_by('-count')[:5]

    context = {
        'total_sessions': total_sessions,
        'total_visitors': sessions.values('ip_address').distinct().count(), 
        'bounce_rate': round(bounce_rate, 1),
        'avg_duration': round(avg_duration, 1),
        'avg_load_time': int(avg_load_time),
        'device_data': device_data,
        'browser_data': browser_data,
        'funnel': {
            'adds': adds,
            'starts': starts,
            'sales': payments
        },
        'auth_stats': {
            'logins': logins,
            'signups': signups
        },
        'top_searches': top_searches,
        'top_products': top_products,
        'errors_404': errors_404,
        'days': days
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)

@staff_member_required
def admin_stats_api(request):
    # Time window (Last 30 days)
    last_30_days = timezone.now() - timedelta(days=30)
    
    # 1. Headline KPIs
    total_revenue_30d = Order.objects.filter(created_at__gte=last_30_days, status='delivered').aggregate(total=Sum('total'))['total'] or 0
    total_orders_30d = Order.objects.filter(created_at__gte=last_30_days).count()
    total_users = User.objects.count()
    
    # Today's stats
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = Order.objects.filter(created_at__gte=today_start).count()
    today_revenue = Order.objects.filter(created_at__gte=today_start, status='delivered').aggregate(total=Sum('total'))['total'] or 0
    
    # 2. Sales Chart (Daily Revenue last 30 days)
    sales_data = Order.objects.filter(created_at__gte=last_30_days, status__in=['processing', 'shipped', 'delivered']) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(daily_revenue=Sum('total')) \
        .order_by('date')
    
    labels = [s['date'].strftime('%Y-%m-%d') for s in sales_data]
    revenue_points = [s['daily_revenue'] for s in sales_data]

    # 3. Order Status Breakdown
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    status_map = {s['status']: s['count'] for s in status_counts}

    # 3b. Payment Method Breakdown
    payment_counts = Order.objects.values('payment_method').annotate(count=Count('id'))
    payment_map = {p['payment_method']: p['count'] for p in payment_counts}

    # 3c. Courier Breakdown
    courier_counts = Order.objects.values('courier__name').annotate(count=Count('id'))
    courier_map = {c['courier__name']: c['count'] for c in courier_counts if c['courier__name']}

    # 4. Top Selling Products
    top_products = OrderItem.objects.filter(order__status__in=['processing', 'shipped', 'delivered']) \
        .values('product__title') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')[:5]

    # 5. Live Stats (New)
    from django.core.cache import cache
    online_users_dict = cache.get('online_users', {})
    live_users_count = len(online_users_dict)
    
    # Calculate Unique Buyers
    purchasing_users_count = Order.objects.filter(status__in=['processing', 'shipped', 'delivered']).values('user').distinct().count()

    # 6. Average Order Value (AOV)
    aov = total_revenue_30d / total_orders_30d if total_orders_30d > 0 else 0

    # 7. Low Stock Products (< 10)
    from products.models import Product
    low_stock_products = Product.objects.filter(stock_quantity__lt=10, in_stock=True).values('title', 'stock_quantity')[:5]

    # 8. Sales by Category
    category_sales = OrderItem.objects.filter(order__status__in=['processing', 'shipped', 'delivered']) \
        .values('product__category__name') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')
    category_map = {c['product__category__name']: c['total_qty'] for c in category_sales if c['product__category__name']}

    data = {
        'kpi': {
            'revenue_30d': total_revenue_30d,
            'orders_30d': total_orders_30d,
            'users': total_users,
            'orders_today': today_orders,
            'revenue_today': today_revenue,
            'live_users': live_users_count,
            'purchasing_users': purchasing_users_count,
            'aov': round(aov, 2),
        },
        'sales_chart': {
            'labels': labels,
            'data': revenue_points,
        },
        'status_chart': {
            'pending': status_map.get('pending', 0),
            'processing': status_map.get('processing', 0),
            'shipped': status_map.get('shipped', 0),
            'delivered': status_map.get('delivered', 0),
            'cancelled': status_map.get('cancelled', 0),
        },
        'payment_chart': payment_map,
        'courier_chart': courier_map,
        'category_chart': category_map,
        'top_products': list(top_products),
        'low_stock': list(low_stock_products),
    }

    return JsonResponse(data)
