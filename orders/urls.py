from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/add-ajax/<int:product_id>/', views.cart_add_ajax, name='cart_add_ajax'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.order_create, name='order_create'),
    path('payment/<int:order_id>/', views.payment_process, name='payment_process'),
    path('payment/<int:order_id>/success/', views.payment_success, name='payment_success'),
    path('cart/apply-coupon/', views.coupon_apply, name='coupon_apply'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cart/update/<int:product_id>/<str:action>/', views.cart_update, name='cart_update'),
]
