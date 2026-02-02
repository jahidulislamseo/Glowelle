from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Review, Wishlist, StockAlert
from marketing.models import HomeSlider, DealOfTheDay
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from analytics.models import AnalyticsEvent, VisitorSession
from django.utils import timezone
from orders.models import Order

def home(request):
    # Try fetching from cache first
    home_data = cache.get('home_page_data')
    
    if not home_data:
        featured_products = list(Product.objects.select_related('category', 'brand').all()[:8])
        new_arrivals = list(Product.objects.select_related('category', 'brand').order_by('-created_at')[:4])
        on_sale_products = list(Product.objects.select_related('category', 'brand').filter(original_price__isnull=False)[:4])
        best_products = list(Product.objects.select_related('category', 'brand').order_by('-rating', '-reviews_count')[:10])
        sliders = list(HomeSlider.objects.filter(is_active=True).order_by('sort_order'))
        
        # Deal of the Day
        deal_of_the_day = DealOfTheDay.objects.filter(is_active=True, end_date__gt=timezone.now()).first()
        
        # Categorized Products for Homepage
        target_slugs = ['fruits', 'vegetables', 'meat-fish', 'personal-care', 'snacks', 'beverages', 'dairy']
        categorized_products = []
        
        for slug in target_slugs:
            try:
                category = Category.objects.get(slug=slug)
                products = list(Product.objects.select_related('category', 'brand').filter(category=category)[:4])
                if products:
                    categorized_products.append({
                        'category': category,
                        'products': products
                    })
            except Category.DoesNotExist:
                pass
        
        home_data = {
            'categories': list(Category.objects.all()),
            'featured_products': featured_products,
            'new_arrivals': new_arrivals,
            'on_sale_products': on_sale_products,
            'sliders': sliders,
            'categorized_products': categorized_products,
            'deal_of_the_day': deal_of_the_day,
            'best_products': best_products,
        }
        # Cache for 15 minutes (900 seconds)
        cache.set('home_page_data', home_data, 900)

    # Wishlist Context (Dynamic, per user)
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = home_data.copy()
    context['wishlist_product_ids'] = wishlist_product_ids
    
    return render(request, 'products/home.html', context)

def shop(request):
    products = Product.objects.select_related('category', 'brand')\
        .prefetch_related('additional_images', 'reviews')\
        .all().order_by('-created_at')
    categories = Category.objects.all()
    
    # Filter by Category
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
        
    # Filter by Price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    else: # newest
        products = products.order_by('-created_at')

    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )
        
        # [ANALYTICS] Log Search Event
        session_key = request.session.session_key
        if session_key:
            session = VisitorSession.objects.filter(session_key=session_key).first()
            if session:
                AnalyticsEvent.objects.create(
                    session=session,
                    user=request.user if request.user.is_authenticated else None,
                    event_type='search',
                    value=query[:255]
                )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12) # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Wishlist Context
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
        
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'query': query,
        'wishlist_product_ids': wishlist_product_ids,
        'page_obj': page_obj,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        from django.http import JsonResponse
        html = render_to_string('products/partials/product_list.html', context, request=request)
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None
        })

    return render(request, 'products/shop.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # [ANALYTICS] View Content
    session_key = request.session.session_key
    if session_key:
        session = VisitorSession.objects.filter(session_key=session_key).first()
        if session:
             # Check if view already logged recently to avoid dupes? 
             # For simplicity, we log every view or rely on PageView 'url'
             # Let's add a specific event for higher granularity if needed
             pass

    # Smart Related Products Algorithm
    related_products = []
    
    # 1. Try "Bought Together" logic first (for all users, not just authenticated)
    from orders.models import OrderItem
    from django.db.models import Count
    
    # Find products frequently bought together with this product
    bought_together = OrderItem.objects.filter(
        order__items__product=product
    ).exclude(
        product=product
    ).values('product').annotate(
        count=Count('product')
    ).order_by('-count')[:5]
    
    if bought_together.exists():
        product_ids = [item['product'] for item in bought_together]
        related_products = list(Product.objects.filter(id__in=product_ids).select_related('category', 'brand')[:5])
    
    # 2. Fallback to category + brand based if not enough
    if len(related_products) < 5:
        category_products = Product.objects.filter(
            Q(brand=product.brand) | Q(category=product.category)
        ).exclude(id=product.id).select_related('category', 'brand').distinct()[:5]
        
        # Merge and deduplicate
        existing_ids = [p.id for p in related_products]
        for p in category_products:
            if p.id not in existing_ids and len(related_products) < 5:
                related_products.append(p)
    
    reviews = product.reviews.all().order_by('-created_at')
    
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'is_in_wishlist': is_in_wishlist,
    }
    return render(request, 'products/product_detail.html', context)

def product_quick_view(request, product_id):
    """AJAX endpoint for quick view modal"""
    from django.http import JsonResponse
    from django.template.loader import render_to_string
    
    product = get_object_or_404(Product.objects.select_related('category', 'brand'), id=product_id)
    
    # Check if in wishlist
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Get additional images
    additional_images = product.additional_images.all()[:4]
    
    # Render partial template
    html = render_to_string('products/partials/quick_view_content.html', {
        'product': product,
        'is_in_wishlist': is_in_wishlist,
        'additional_images': additional_images
    }, request=request)
    
    return JsonResponse({'html': html})

@login_required
@require_POST
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '')
    
    image = request.FILES.get('image')
    
    # Check for Verified Purchase
    is_verified = Order.objects.filter(
        user=request.user,
        items__product=product,
        status='delivered'
    ).exists()
    
    Review.objects.create(
        user=request.user,
        product=product,
        rating=rating,
        comment=comment,
        image=image,
        is_verified_purchase=is_verified
    )
    
    # Update product stats
    reviews = product.reviews.all()
    product.reviews_count = reviews.count()
    product.rating = sum(r.rating for r in reviews) / reviews.count()
    product.save()
    
    return redirect('product_detail', slug=slug)

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    action = 'added'
    if not created:
        wishlist_item.delete()
        action = 'removed'
    else:
        # [ANALYTICS] Log Wishlist Add
        session_key = request.session.session_key
        if session_key:
            session = VisitorSession.objects.filter(session_key=session_key).first()
            if session:
                AnalyticsEvent.objects.create(
                    session=session,
                    user=request.user,
                    event_type='wishlist_add',
                    value=str(product.id)
                )
    
    # Check for AJAX request (X-Requested-With header or accepts JSON)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
        from django.http import JsonResponse
        return JsonResponse({
            'status': 'success', 
            'action': action,
            'product_id': product_id
        })
        
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category', 'product__brand')
    products = [item.product for item in wishlist_items]
    return render(request, 'products/wishlist.html', {'products': products})

from orders.cart import Cart

@login_required
def wishlist_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.add(product=product, quantity=1)
    
    # Remove from wishlist
    Wishlist.objects.filter(user=request.user, product=product).delete()
    
    return redirect('cart_detail')

def create_stock_alert(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        email = request.POST.get('email')
        
        if request.user.is_authenticated:
            StockAlert.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'email': request.user.email}
            )
        elif email:
            # For guests, we might need a separate way to track but for now we store email
            # We don't have a 'Guest' user so we might just use email only or skip for now
            # But the model requires a user. Let's make user optional or use a placeholder.
            # Actually, per my model, user is NOT null. 
            # I will only allow it for logged in users for now or ask user.
            # Wait, the implementation plan said 'track users waiting'.
            # I'll stick to logged in users for now or fix model.
            from django.contrib import messages
            messages.info(request, "Please login to set stock alerts.")
            return redirect('login')
            
        from django.contrib import messages
        messages.success(request, "We'll notify you when this item is back in stock!")
        return redirect('product_detail', slug=product.slug)
    return redirect('shop')
