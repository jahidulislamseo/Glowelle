from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from .forms import RegisterForm, UserUpdateForm, AddressForm, SupportTicketForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login, authenticate, logout
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from orders.models import Order, OrderItem
from orders.cart import Cart
from .models import User, Address, Wallet, SupportTicket

# ... (existing imports)

# ... (existing views)

@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'users/address_form.html', {'form': form})

@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'users/address_form.html', {'form': form})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    return redirect('address_list')

@login_required
def address_make_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.is_default = True
        address.save()
        messages.success(request, 'Default address updated!')
    return redirect('address_list')

@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Support ticket created!')
            return redirect('support_tickets')
    else:
        form = SupportTicketForm()
    return render(request, 'users/ticket_form.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Preserve guest cart before creating account
            guest_cart_data = request.session.get('cart', {}).copy()
            
            user = form.save()
            login(request, user)
            
            # Restore cart after login
            if guest_cart_data:
                request.session['cart'] = guest_cart_data
                request.session.modified = True
            
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    user = None # Initialize user to avoid UnboundLocalError
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Preserve guest cart before login
                guest_cart_data = request.session.get('cart', {}).copy()
                
                login(request, user)
                
                # Merge guest cart with authenticated session
                if guest_cart_data:
                    from orders.cart import Cart
                    cart = Cart(request)
                    from products.models import Product
                    
                    for product_id, item_data in guest_cart_data.items():
                        try:
                            product = Product.objects.get(id=int(product_id))
                            # Add to cart (will merge quantities if item already exists)
                            cart.add(product, quantity=item_data['quantity'], update_quantity=False)
                        except Product.DoesNotExist:
                            pass
                
                # Handle Remember Me - Moved inside successful auth
                if request.POST.get('remember-me'):
                    request.session.set_expiry(1209600) # 2 weeks
                else:
                    request.session.set_expiry(0) # Browser close
                    
                next_url = request.POST.get('next') or request.GET.get('next') or 'home'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

from .models import User, Address, Wallet, SupportTicket
from django.contrib.auth.decorators import login_required

# ... (register and login views remain unchanged)

@login_required
def dashboard(request):
    orders = request.user.orders.all().order_by('-created_at')
    
    # Ensure wallet exists
    if not hasattr(request.user, 'wallet'):
        Wallet.objects.create(user=request.user)
        
    context = {
        'orders': orders,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'wallet_balance': request.user.wallet.balance,
        'active_tickets': request.user.tickets.exclude(status='closed').count(),
        'addresses': request.user.addresses.all(),
    }
    return render(request, 'users/dashboard_overview.html', context)

@login_required
def order_history(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'users/dashboard_orders.html', {'orders': orders})

@login_required
def address_list(request):
    addresses = request.user.addresses.all().order_by('-is_default', '-created_at')
    return render(request, 'users/dashboard_addresses.html', {'addresses': addresses})

@login_required
def wallet_view(request):
    if not hasattr(request.user, 'wallet'):
        Wallet.objects.create(user=request.user)
    transactions = request.user.wallet.transactions.all().order_by('-created_at')
    return render(request, 'users/dashboard_wallet.html', {'wallet': request.user.wallet, 'transactions': transactions})

@login_required
def support_tickets(request):
    tickets = request.user.tickets.all().order_by('-updated_at')
    return render(request, 'users/dashboard_support.html', {'tickets': tickets})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'users/dashboard_profile.html', {'form': form})

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/password_change.html', {'form': form})

# PDF Invoice & Order Features
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from orders.models import Order, OrderItem
from orders.cart import Cart

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@login_required
def invoice_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    pdf = render_to_pdf('users/order_invoice.html', {'order': order})
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Invoice_%s.pdf" % (order.id)
        content = "inline; filename='%s'" % (filename)
        if request.GET.get("download"):
            content = "attachment; filename='%s'" % (filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Error generating PDF", status=500)

@login_required
def reorder_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    cart = Cart(request)
    for item in order.items.all():
        cart.add(product=item.product, quantity=item.quantity)
    messages.success(request, "Items added to cart!")
    return redirect('cart_detail')

@login_required
def tracking_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'users/order_tracking.html', {'order': order})
