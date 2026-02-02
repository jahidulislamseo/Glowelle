from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, models
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse

from products.models import Product, StockLog
from analytics.models import AnalyticsEvent, VisitorSession
from marketing.models import Coupon
from .cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem, PaymentGateway

def log_analytics_event(request, event_type, value=None, metadata=None):
    session_key = request.session.session_key
    if session_key:
        session = VisitorSession.objects.filter(session_key=session_key).first()
        if session:
            AnalyticsEvent.objects.create(
                session=session,
                user=request.user if request.user.is_authenticated else None,
                event_type=event_type,
                value=str(value) if value else None,
                metadata=metadata
            )

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    
    # [ANALYTICS]
    log_analytics_event(request, 'add_to_cart', product_id)
    
    if request.POST.get('checkout') == 'true':
        return redirect('order_create')
    
    return redirect('cart_detail')

@require_POST
def cart_add_ajax(request, product_id):
    """AJAX endpoint for adding products to cart"""
    from django.http import JsonResponse
    
    cart = Cart(request)
    try:
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        # Stock validation
        if product.stock_quantity < quantity:
            return JsonResponse({
                'success': False,
                'error': f'Only {product.stock_quantity} items available for {product.title}'
            }, status=400)
        
        cart.add(product=product, quantity=quantity)
        
        # [ANALYTICS]
        log_analytics_event(request, 'add_to_cart', product_id)
        
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'message': f'{product.title} added to cart',
            'product_title': product.title
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def cart_update(request, product_id, action):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    current_quantity = cart.cart.get(str(product_id), {}).get('quantity', 0)
    
    if action == 'increment':
        if product.stock_quantity > current_quantity:
            cart.add(product=product, quantity=1)
            messages.success(request, f'Increased quantity for {product.title}')
        else:
            messages.error(request, f'Only {product.stock_quantity} items available in stock.')
    elif action == 'decrement':
        if current_quantity > 1:
            cart.add(product=product, quantity=-1)
            messages.success(request, f'Decreased quantity for {product.title}')
        else:
            cart.remove(product)
            messages.success(request, f'Removed {product.title} from cart.')
            
    return redirect('cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    # [ANALYTICS]
    log_analytics_event(request, 'remove_from_cart', product_id)

    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})

from marketing.models import Coupon
from django.utils import timezone

@require_POST
def coupon_apply(request):
    code = request.POST.get('code')
    if code:
        try:
            coupon = Coupon.objects.get(code__iexact=code, active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"Coupon '{code}' applied successfully!")
            
            # [ANALYTICS]
            log_analytics_event(request, 'coupon_used', code)

        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, "Invalid or expired coupon code.")
    return redirect('cart_detail')

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        # [ANALYTICS]
        log_analytics_event(request, 'checkout_step', 'submit_form')

        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    # Assign user if authenticated, else allow guest checkout
                    order.user = request.user if request.user.is_authenticated else None
                    
                    # Apply Pricing & Discount
                    order.total = cart.get_total_price_after_discount()
                    order.discount_amount = cart.get_discount()
                    
                    coupon_id = request.session.get('coupon_id')
                    if coupon_id:
                        try:
                            order.coupon = Coupon.objects.get(id=coupon_id)
                        except Exception:
                            pass

                    # Check stock availability
                    for item in cart:
                        product = item['product']
                        if product.stock_quantity < item['quantity']:
                            messages.error(
                                request, 
                                f"Stock updated: Only {product.stock_quantity} of '{product.title}' available. "
                                f"Please update your cart before proceeding."
                            )
                            # Raise exception to rollback
                            raise ValueError("Insufficient stock")

                    order.status = 'pending'
                    order.save()
                    
                    for item in cart:
                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            price=item['price'],
                            quantity=item['quantity']
                        )
                        
                        # Deduct Stock (Atomic update using F expression)
                        Product.objects.filter(id=product.id).update(stock_quantity=models.F('stock_quantity') - item['quantity'])
                        
                        # Refresh product instance for logging or other needs if necessary, 
                        # but StockLog just needs the reference.
                        
                        # Create Stock Log
                        StockLog.objects.create(
                            product=product,
                            quantity=-item['quantity'],
                            reason=f"Order #{order.id}"
                        )
                    
                    if order.payment_method == 'online':
                        return redirect('payment_process', order_id=order.id)
                    
                    cart.clear()
                    return render(request, 'orders/created.html', {'order': order})
            except ValueError:
                return redirect('cart_detail')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('cart_detail')
    else:
        # [ANALYTICS]
        log_analytics_event(request, 'checkout_start')

        # Pre-fill form with user data if authenticated
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial_data)
    
    addresses = []
    if request.user.is_authenticated:
        addresses = request.user.addresses.all()
        
    return render(request, 'orders/create.html', {'cart': cart, 'form': form, 'addresses': addresses})

def payment_process(request, order_id):
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
        
    gateways = PaymentGateway.objects.filter(is_active=True)
    return render(request, 'orders/payment.html', {'order': order, 'gateways': gateways})

@require_POST
def payment_success(request, order_id):
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)

    cart = Cart(request)
    
    # Get Gateway and Trx ID
    gateway_id = request.POST.get('gateway')
    trx_id = request.POST.get('transaction_id')
    
    if gateway_id and trx_id:
        try:
            with transaction.atomic():
                gateway = PaymentGateway.objects.get(id=gateway_id)
                order.payment_gateway = gateway
                order.transaction_id = trx_id
                
                # [ANALYTICS]
                log_analytics_event(request, 'payment_success', order_id, metadata={'gateway': gateway.name})
        
                # Mark as paid and processing
                order.status = 'processing'
                order.save()
            
        except PaymentGateway.DoesNotExist:
            messages.error(request, "Selected payment gateway not found.")
            return redirect('payment_process', order_id=order_id)
        except Exception as e:
            messages.error(request, f"Failed to process payment: {str(e)}")
            return redirect('payment_process', order_id=order_id)
    
    cart.clear()
    return render(request, 'orders/created.html', {'order': order})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'), 
        id=order_id, 
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {'order': order})

from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/admin/invoice_pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
