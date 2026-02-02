from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/orders/', views.order_history, name='order_history'),
    path('dashboard/orders/<int:pk>/invoice/', views.invoice_view, name='order_invoice'),
    path('dashboard/orders/<int:pk>/reorder/', views.reorder_view, name='order_reorder'),
    path('dashboard/orders/<int:pk>/track/', views.tracking_view, name='order_tracking'),
    path('dashboard/addresses/', views.address_list, name='address_list'),
    path('dashboard/addresses/add/', views.address_add, name='address_add'),
    path('dashboard/addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('dashboard/addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('dashboard/addresses/<int:pk>/default/', views.address_make_default, name='address_make_default'),
    path('dashboard/wallet/', views.wallet_view, name='wallet'),
    path('dashboard/support/', views.support_tickets, name='support_tickets'),
    path('dashboard/support/new/', views.ticket_create, name='ticket_create'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.change_password_view, name='change_password'),
    # OTP Login
    path('otp/request/', views.request_otp, name='request_otp'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),
]
