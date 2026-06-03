from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductVariant, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'image']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo']

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']

    def get_image(self, obj):
        return obj.display_image_url

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'sku', 'stock', 'price_adjustment']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    image = serializers.SerializerMethodField()
    additional_images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'price', 
            'original_price', 'image', 'rating', 'reviews_count', 
            'in_stock', 'stock_quantity', 'is_new', 'is_best_seller', 
            'category', 'brand', 'additional_images', 'variants', 'reviews',
            'created_at', 'updated_at'
        ]

    def get_image(self, obj):
        return obj.display_image_url
