from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
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



# PDF Generation Imports
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.admin.views.decorators import staff_member_required
from orders.models import Order
from .models import ContactMessage
from django.contrib import messages

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, 'Your message has been sent successfully! We will contact you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'pages/contact.html')

@staff_member_required
def admin_order_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    # Increment download count
    order.invoice_download_count += 1
    order.save(update_fields=['invoice_download_count'])
    
    template_path = 'pdf/invoice.html'
    context = {'order': order}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.invoice_number}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # Create PDF
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@staff_member_required
def analytics_dashboard(request):
    # Time Range (Default 30 days)
    days = int(request.GET.get('days', 30))
    
    # Cache Key based on days (5 min expiry)
    cache_key = f"analytics_dashboard_v2_{days}"
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'admin/analytics_dashboard.html', cached_context)

    start_date = timezone.now() - timedelta(days=days)
    
    # 1. Traffic Metrics
    sessions = VisitorSession.objects.filter(start_time__gte=start_date)
    total_sessions = sessions.count()
    total_users = sessions.filter(user__isnull=False).values('user').distinct().count()
    total_visitors = sessions.values('ip_address').distinct().count()
    
    # Bounce Rate
    bounces = sessions.filter(is_bounce=True).count()
    bounce_rate = (bounces / total_sessions * 100) if total_sessions > 0 else 0
    
    # Avg Session Duration (Database Aggregation)
    from django.db.models import ExpressionWrapper, fields, Q
    avg_duration_data = sessions.annotate(
        duration=ExpressionWrapper(F('last_seen') - F('start_time'), output_field=fields.DurationField())
    ).aggregate(avg_duration=Avg('duration'))
    avg_duration = avg_duration_data['avg_duration'].total_seconds() / 60 if avg_duration_data['avg_duration'] else 0

    # Avg Page Load Time
    page_views = PageView.objects.filter(timestamp__gte=start_date)
    avg_load_time = page_views.aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0

    # 2. Device & Browser Breakdown
    devices = sessions.values('device_type').annotate(count=Count('id')).order_by('-count')
    device_data = {d['device_type']: d['count'] for d in devices}
    
    # Browser Stats (Fixed: Now using 'browser' field instead of 'os')
    browsers = sessions.values('browser').annotate(count=Count('id')).order_by('-count')[:5]
    browser_data = {b['browser'] or 'Unknown': b['count'] for b in browsers}

    # 3. Events Logic (Optimized: Single Aggregation Query)
    events = AnalyticsEvent.objects.filter(timestamp__gte=start_date)
    
    stats = events.aggregate(
        adds=Count('id', filter=Q(event_type='add_to_cart')),
        starts=Count('id', filter=Q(event_type='checkout_start')),
        payments=Count('id', filter=Q(event_type='payment_success')),
        logins=Count('id', filter=Q(event_type='login')),
        signups=Count('id', filter=Q(event_type='signup')),
        logouts=Count('id', filter=Q(event_type='logout')),
        wishlist_adds=Count('id', filter=Q(event_type='wishlist_add')),
        removes_from_cart=Count('id', filter=Q(event_type='remove_from_cart')),
        coupon_usage=Count('id', filter=Q(event_type='coupon_used')),
        payment_failed=Count('id', filter=Q(event_type='payment_failed')),
        out_of_stock_clicks=Count('id', filter=Q(event_type='out_of_stock_click')),
    )

    # Top Searches
    top_searches = events.filter(event_type='search').values('value').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Top Products (Most Viewed) - Clean URLs
    raw_top_products = page_views.filter(url__startswith='/product/').values('url').annotate(count=Count('id')).order_by('-count')[:8]
    top_products = []
    for item in raw_top_products:
        # Clean /product/slug/ -> slug
        clean_name = item['url'].replace('/product/', '').strip('/')
        top_products.append({'url': clean_name.replace('-', ' ').title(), 'count': item['count']})

    # 404 Errors
    errors_404 = events.filter(event_type='error_404').values('url').annotate(count=Count('id')).order_by('-count')[:5]
    
    # 5. Advanced eCommerce logic
    # Abandoned Carts: Sessions with add_to_cart but NO payment_success
    # (This still requires subquery or separate logic as it depends on session flow, keeping distinct check)
    cart_sessions = sessions.filter(events__event_type='add_to_cart')
    purchased_sessions = sessions.filter(events__event_type='payment_success')
    abandoned_carts = cart_sessions.exclude(id__in=purchased_sessions.values('id')).distinct().count()
    
    # Coupons redundancy check
    orders_with_coupon = Order.objects.filter(created_at__gte=start_date, coupon__isnull=False).count()
    total_coupon_usage = max(stats['coupon_usage'], orders_with_coupon)
    
    # 6. Customer Retention
    new_users_count = User.objects.filter(date_joined__gte=start_date).count()
    active_users_count = sessions.filter(user__isnull=False).values('user').distinct().count()
    returning_users_count = max(0, active_users_count - new_users_count)
    
    # Repeat Customers
    repeat_customers = Order.objects.filter(created_at__gte=start_date) \
        .values('user') \
        .annotate(order_count=Count('id')) \
        .filter(order_count__gt=1) \
        .count()
        
    # Checkout Drop-off Rate
    checkout_starts = stats['starts']
    checkout_success = stats['payments']
    drop_off_rate = 0
    if checkout_starts > 0:
        drop_off_rate = ((checkout_starts - checkout_success) / checkout_starts) * 100

    # User Conversion Rate
    user_conversion_rate = (stats['payments'] / total_visitors * 100) if total_visitors > 0 else 0

    context = {
        'days': days,
        'total_sessions': total_sessions,
        'total_visitors': total_visitors, 
        'bounce_rate': round(bounce_rate, 1),
        'avg_duration': round(avg_duration, 1),
        'avg_load_time': int(avg_load_time),
        'device_data': device_data,
        'browser_data': browser_data,
        'funnel': {
            'adds': stats['adds'],
            'starts': stats['starts'],
            'sales': stats['payments'],
            'rate': round(user_conversion_rate, 2) if total_users > 0 else 0,
            'drop_off': round(drop_off_rate, 1)
        },
        'auth_stats': {
            'logins': stats['logins'],
            'signups': stats['signups'],
            'logouts': stats['logouts'],
            'new_users': new_users_count,
            'returning_users': returning_users_count,
            'repeat_customers': repeat_customers
        },
        'ecommerce': {
            'wishlist_adds': stats['wishlist_adds'],
            'abandoned_carts': abandoned_carts,
            'coupons': total_coupon_usage,
            'payment_failed': stats['payment_failed'],
            'out_of_stock': stats['out_of_stock_clicks'],
        },
        'top_searches': top_searches,
        'top_products': top_products,
        'errors_404': errors_404,
    }
    
    # Save to cache (5 minutes)
    cache.set(cache_key, context, 300)
    
    return render(request, 'admin/analytics_dashboard.html', context)

@staff_member_required
def admin_stats_api(request):
    # Time window (Last 30 days)
    last_30_days = timezone.now() - timedelta(days=30)
    
    # 1. Headline KPIs
    total_revenue_30d = Order.objects.filter(created_at__gte=last_30_days).exclude(status__in=['cancelled', 'returned']).aggregate(total=Sum('total'))['total'] or 0
    total_orders_30d = Order.objects.filter(created_at__gte=last_30_days).count()
    total_users = User.objects.count()
    
    # Today's stats
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = Order.objects.filter(created_at__gte=today_start).count()
    today_revenue = Order.objects.filter(created_at__gte=today_start).exclude(status__in=['cancelled', 'returned']).aggregate(total=Sum('total'))['total'] or 0
    
    # 2. Sales Chart (Daily Revenue last 30 days)
    sales_data = Order.objects.filter(created_at__gte=last_30_days).exclude(status__in=['cancelled', 'returned']) \
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
