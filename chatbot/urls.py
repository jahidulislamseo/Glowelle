from django.urls import path
from . import views

urlpatterns = [
    path('api/chatbot/', views.chatbot_response, name='chatbot_api'),
    path('api/get-history/', views.get_chat_history, name='get_chat_history'),
    path('api/cart-status/', views.cart_status, name='cart_status'),
    path('admin/chatbot/history/', views.admin_chat_history, name='chat_history'),
]
