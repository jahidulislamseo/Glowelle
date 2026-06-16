from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/review/', views.add_review, name='add_review'),
    path('product/quick-view/<int:product_id>/', views.product_quick_view, name='product_quick_view'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/add-to-cart/<int:product_id>/', views.wishlist_to_cart, name='wishlist_to_cart'),
    path('product/<int:product_id>/stock-alert/', views.create_stock_alert, name='create_stock_alert'),
]
