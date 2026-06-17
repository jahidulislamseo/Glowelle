import random
from datetime import timedelta

from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, login, authenticate, logout
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.http import HttpResponse

from django_ratelimit.decorators import ratelimit

from core.utils import generate_pdf_response, generate_otp
from orders.models import Order
from orders.cart import Cart
from products.models import Product
from .models import User, Address, Wallet, SupportTicket
from .forms import RegisterForm, UserUpdateForm, AddressForm, SupportTicketForm

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
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
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
                    cart = Cart(request)
                    
                    for product_id, item_data in guest_cart_data.items():
                        try:
                            product = Product.objects.get(id=int(product_id))
                            # Add to cart (will merge quantities if item already exists)
                            cart.add(product, quantity=item_data['quantity'], update_quantity=False)
                        except (Product.DoesNotExist, ValueError):
                            pass
                
                # Handle Remember Me - Moved inside successful auth
                if request.POST.get('remember-me'):
                    request.session.set_expiry(1209600) # 2 weeks
                else:
                    request.session.set_expiry(0) # Browser close
                    
                from django.utils.http import url_has_allowed_host_and_scheme
                next_url = request.POST.get('next') or request.GET.get('next') or ''
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    next_url = 'home'
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
    addresses = request.user.addresses.all().order_by('-is_default', 'id')
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

@login_required
def invoice_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return generate_pdf_response(
        template_src='users/order_invoice.html',
        context_dict={'order': order},
        filename=f"Invoice_{order.id}.pdf",
        download=request.GET.get("download") == "true"
    )

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

# --- OTP Authentication Views ---

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def request_otp(request):
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        if not phone:
            messages.error(request, "Phone number is required.")
            return render(request, 'users/otp_request.html')
        
        # Clean phone number (simple version)
        phone = phone.strip()
        
        # Find or create user
        user, created = User.objects.get_or_create(phone_number=phone, defaults={
            'username': f'user_{phone[-4:]}_{random.randint(1000, 9999)}',
            'email': f'{phone}@example.com' # Placeholder email
        })
        
        # Generate 6-digit OTP
        otp = generate_otp(6)
        user.otp_code = otp
        user.otp_expires_at = timezone.now() + timedelta(minutes=5)
        user.save()
        
        # SIMULATION: Log OTP to console (since we don't have an SMS gateway yet)
        print(f"DEBUG: OTP for {phone} is {otp}")
        
        request.session['otp_phone'] = phone
        messages.success(request, f"OTP sent to {phone} (Check console for debug)")
        return redirect('verify_otp')
        
    return render(request, 'users/otp_request.html')

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def verify_otp(request):
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('request_otp')
        
    if request.method == 'POST':
        code = request.POST.get('otp_code')
        user = User.objects.filter(phone_number=phone).first()
        
        if user and user.otp_code == code and user.otp_expires_at > timezone.now():
            # SUCCESS
            user.otp_code = None # Clear after use
            user.otp_expires_at = None
            user.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Logged in successfully!")
            
            # Clean session
            del request.session['otp_phone']
            
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid or expired OTP.")
            
    return render(request, 'users/otp_verify.html', {'phone': phone})
