"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

from django.contrib.sitemaps.views import sitemap
from products.sitemaps import ProductSitemap, CategorySitemap, StaticViewSitemap

from rest_framework.routers import DefaultRouter
from products.api_views import ProductViewSet, CategoryViewSet

# API Router
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # API Routes
    path('api/', include(router.urls)),

    # Admin API (Must be before admin.site.urls)
    path('admin/dashboard/stats/', core_views.admin_stats_api, name='admin_stats_api'),
    path('admin/analytics/', core_views.analytics_dashboard, name='analytics_dashboard'), # New Dashboard
    path('admin/orders/invoice/<int:order_id>/', core_views.admin_order_invoice, name='order_invoice'),
    # path('accounts/', include('allauth.urls')),
    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=True)), # Redirect legacy/default login URL
    path('admin/', admin.site.urls),
    # Legacy/Template URLs (Keep them for now, or comment out if we valid strictly API only)
    # path('', include('products.urls')),
    # path('', include('users.urls')),
    # path('', include('orders.urls')),
    
    # We will keep the template URLs valid for now to not break the existing admin or any hybrid usage
    path('', include('products.urls')),
    path('', include('users.urls')),
    path('', include('orders.urls')),

    # Static Pages
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', core_views.contact, name='contact'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('faq/', TemplateView.as_view(template_name='pages/faq.html'), name='faq'),
    
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),

    # Admin API
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass  # debug_toolbar not installed

