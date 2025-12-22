from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category

class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return Product.objects.filter(in_stock=True)

    def lastmod(self, obj):
        return obj.updated_at

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return Category.objects.all()

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return ['home', 'shop', 'about', 'contact', 'privacy', 'terms']

    def location(self, item):
        return reverse(item)
