from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
import os
import markdown
from django.utils import timezone
from django.db.models import Sum, Count, F, Avg, Q, ExpressionWrapper, fields
from django.db.models.functions import TruncDate
from django.contrib import messages

from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Product
from analytics.models import VisitorSession, PageView, AnalyticsEvent
from .models import ContactMessage
from .utils import generate_pdf_response
from .email_utils import send_admin_contact_email

User = get_user_model()

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            contact_msg = ContactMessage.objects.create(name=name, email=email, message=message)
            send_admin_contact_email(contact_msg)
            messages.success(request, 'Your message has been sent successfully! We will contact you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'pages/contact.html')

@staff_member_required
def admin_order_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    # Increment download count (Atomic update)
    Order.objects.filter(pk=order_id).update(invoice_download_count=F('invoice_download_count') + 1)
    
    return generate_pdf_response(
        template_src='pdf/invoice.html',
        context_dict={'order': order},
        filename=f"invoice_{order.invoice_number}.pdf",
        download=request.GET.get('download') == 'true'
    )

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

    # 7. Sales Metrics (For Charts)
    order_data = Order.objects.filter(created_at__gte=start_date)
    
    # Daily Revenue & Order Count
    sales_trend = order_data.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(revenue=Sum('total'), orders=Count('id')) \
        .order_by('date')
    
    sales_labels = [s['date'].strftime('%b %d') for s in sales_trend]
    revenue_data = [float(s['revenue']) for s in sales_trend]
    orders_data = [s['orders'] for s in sales_trend]

    # Order Status Breakdown
    status_counts = order_data.values('status').annotate(count=Count('id'))
    status_data = {s['status']: s['count'] for s in status_counts}

    # Category-wise Sales
    category_sales_data = OrderItem.objects.filter(order__created_at__gte=start_date) \
        .values('product__category__name') \
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('price') * F('quantity'))) \
        .order_by('-total_revenue')
    
    category_labels = [c['product__category__name'] or 'Unknown' for c in category_sales_data]
    category_revenue = [float(c['total_revenue']) for c in category_sales_data]

    context = {
        'days': days,
        'total_sessions': total_sessions,
        'total_visitors': total_visitors, 
        'bounce_rate': round(bounce_rate, 1),
        'avg_duration': round(avg_duration, 1),
        'avg_load_time': int(avg_load_time),
        'device_data': device_data,
        'browser_data': browser_data,
        'sales_chart': {
            'labels': sales_labels,
            'revenue': revenue_data,
            'orders': orders_data,
        },
        'status_chart': status_data,
        'category_chart': {
            'labels': category_labels,
            'revenue': category_revenue,
        },
        'funnel': {
            'sessions': total_sessions,
            'adds': stats['adds'],
            'starts': stats['starts'],
            'sales': stats['payments'],
            'rate': round(user_conversion_rate, 2) if total_visitors > 0 else 0,
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
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    prev_30_days_start = now - timedelta(days=60)
    prev_30_days_end = last_30_days
    
    # 1. Headline KPIs
    total_revenue_30d = Order.objects.filter(created_at__gte=last_30_days).exclude(status__in=['cancelled', 'returned']).aggregate(total=Sum('total'))['total'] or 0
    total_orders_30d = Order.objects.filter(created_at__gte=last_30_days).count()
    total_users = User.objects.count()
    
    # 1b. Trend Calculation (Comparison with prev 30 days)
    rev_prev = Order.objects.filter(created_at__gte=prev_30_days_start, created_at__lt=prev_30_days_end).exclude(status__in=['cancelled', 'returned']).aggregate(total=Sum('total'))['total'] or 0
    ord_prev = Order.objects.filter(created_at__gte=prev_30_days_start, created_at__lt=prev_30_days_end).count()
    
    def calc_trend(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((float(current) - float(previous)) / float(previous)) * 100, 1)

    rev_trend = calc_trend(total_revenue_30d, rev_prev)
    ord_trend = calc_trend(total_orders_30d, ord_prev)
    
    # Today's stats
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = Order.objects.filter(created_at__gte=today_start).count()
    today_revenue = Order.objects.filter(created_at__gte=today_start).exclude(status__in=['cancelled', 'returned']).aggregate(total=Sum('total'))['total'] or 0
    
    # 2. Sales Chart (Daily Revenue last 30 days) - PROPER TIMELINE
    raw_sales_data = Order.objects.filter(created_at__gte=last_30_days).exclude(status__in=['cancelled', 'returned']) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(daily_revenue=Sum('total')) \
        .order_by('date')
    
    sales_map = {s['date'].strftime('%Y-%m-%d'): float(s['daily_revenue']) for s in raw_sales_data}
    
    labels = []
    revenue_points = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append(day)
        revenue_points.append(sales_map.get(day, 0.0))

    # 3. Order Status Breakdown
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    status_map = {s['status']: s['count'] for s in status_counts}

    # 3b. Payment Method Breakdown
    payment_counts = Order.objects.values('payment_method').annotate(count=Count('id'))
    payment_map = {p['payment_method']: p['count'] for p in payment_counts if p['payment_method']}

    # 3c. City Breakdown (New)
    city_counts = Order.objects.values('city').annotate(count=Count('id')).order_by('-count')
    city_map = {c['city'].title() if c['city'] else "Unknown": c['count'] for c in city_counts[:5]}

    # 4. Top Selling Products
    top_products = OrderItem.objects.filter(order__status__in=['processing', 'shipped', 'delivered']) \
        .values('product__title') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')[:5]

    # 4b. Top Customers (New)
    top_customers = Order.objects.exclude(user__isnull=True) \
        .values('user__username', 'full_name') \
        .annotate(total_spent=Sum('total')) \
        .order_by('-total_spent')[:5]
    top_customers_data = [{
        'name': c['full_name'] or c['user__username'],
        'total': float(c['total_spent'])
    } for c in top_customers]

    # 5. Recent Activity
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    recent_orders_data = [{
        'id': o.id,
        'customer': o.full_name or (o.user.username if o.user else "Guest"),
        'amount': float(o.total),
        'status': o.status,
        'time': o.created_at.strftime('%H:%M') if o.created_at.date() == now.date() else o.created_at.strftime('%b %d')
    } for o in recent_orders]

    # Live Stats
    online_users_dict = cache.get('online_users', {})
    live_users_count = len(online_users_dict)
    
    # Calculate Unique Buyers
    purchasing_users_count = Order.objects.filter(status__in=['processing', 'shipped', 'delivered']).values('user').distinct().count()

    # 6. Average Order Value (AOV)
    aov = float(total_revenue_30d) / total_orders_30d if total_orders_30d > 0 else 0.0

    # 7. Low Stock Products
    low_stock_products = Product.objects.filter(stock_quantity__lt=10, in_stock=True).values('title', 'stock_quantity')[:5]

    data = {
        'kpi': {
            'revenue_30d': float(total_revenue_30d),
            'orders_30d': total_orders_30d,
            'rev_trend': rev_trend,
            'ord_trend': ord_trend,
            'users': total_users,
            'orders_today': today_orders,
            'revenue_today': float(today_revenue),
            'live_users': live_users_count,
            'purchasing_users': purchasing_users_count,
            'aov': round(aov, 2),
        },
        'sales_chart': {
            'labels': labels,
            'data': revenue_points,
        },
        'status_chart': {
            'labels': list(status_map.keys()),
            'data': list(status_map.values()),
            'map': status_map, # For backwards compatibility if any
        },
        'payment_chart': payment_map,
        'city_chart': city_map,
        'top_products': list(top_products),
        'top_customers': top_customers_data,
        'low_stock': list(low_stock_products),
        'recent_orders': recent_orders_data,
    }

    return JsonResponse(data)


@staff_member_required
def error_log(request):
    from .models import ErrorLog
    from django.db.models import Count

    level_filter = request.GET.get('level', '')
    resolved_filter = request.GET.get('resolved', '')

    qs = ErrorLog.objects.all()
    if level_filter:
        qs = qs.filter(level=level_filter)
    if resolved_filter == '0':
        qs = qs.filter(is_resolved=False)
    elif resolved_filter == '1':
        qs = qs.filter(is_resolved=True)

    # Mark single error resolved via POST
    if request.method == 'POST':
        error_id = request.POST.get('resolve_id')
        clear_all = request.POST.get('clear_all')
        if clear_all:
            ErrorLog.objects.all().delete()
        elif error_id:
            ErrorLog.objects.filter(pk=error_id).update(is_resolved=True)
        from django.shortcuts import redirect
        return redirect(request.path + ('?' + request.META.get('QUERY_STRING', '') if request.META.get('QUERY_STRING') else ''))

    total = ErrorLog.objects.count()
    unresolved = ErrorLog.objects.filter(is_resolved=False).count()
    by_level = ErrorLog.objects.values('level').annotate(count=Count('id'))

    return render(request, 'admin/error_log.html', {
        'errors': qs[:200],
        'total': total,
        'unresolved': unresolved,
        'by_level': {x['level']: x['count'] for x in by_level},
        'level_filter': level_filter,
        'resolved_filter': resolved_filter,
    })


@staff_member_required
def website_log(request):
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WEBSITE_LOG.md')
    content_html = ''
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        content_html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    return render(request, 'admin/website_log.html', {'content_html': content_html})


@staff_member_required
def admin_logs(request):
    from .models import ErrorLog
    from django.db.models import Count

    active_tab = request.GET.get('tab', 'errors')
    level_filter = request.GET.get('level', '')
    resolved_filter = request.GET.get('resolved', '')

    if request.method == 'POST':
        error_id = request.POST.get('resolve_id')
        clear_all = request.POST.get('clear_all')
        if clear_all:
            ErrorLog.objects.all().delete()
        elif error_id:
            ErrorLog.objects.filter(pk=error_id).update(is_resolved=True)
        from django.shortcuts import redirect
        qs_str = request.META.get('QUERY_STRING', '')
        return redirect(request.path + ('?' + qs_str if qs_str else ''))

    # Error log data
    qs = ErrorLog.objects.all()
    if level_filter:
        qs = qs.filter(level=level_filter)
    if resolved_filter == '0':
        qs = qs.filter(is_resolved=False)
    elif resolved_filter == '1':
        qs = qs.filter(is_resolved=True)

    total = ErrorLog.objects.count()
    unresolved = ErrorLog.objects.filter(is_resolved=False).count()
    by_level = ErrorLog.objects.values('level').annotate(count=Count('id'))

    # Website log data
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WEBSITE_LOG.md')
    website_log_html = ''
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            website_log_html = markdown.markdown(f.read(), extensions=['tables', 'fenced_code'])

    return render(request, 'admin/logs.html', {
        'active_tab': active_tab,
        'errors': qs[:200],
        'total': total,
        'unresolved': unresolved,
        'by_level': {x['level']: x['count'] for x in by_level},
        'level_filter': level_filter,
        'resolved_filter': resolved_filter,
        'website_log_html': website_log_html,
    })
