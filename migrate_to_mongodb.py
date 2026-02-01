import os
import django
from pymongo import MongoClient
from decimal import Decimal
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, Category, Brand

# Setup MongoDB
MONGO_URI = "mongodb+srv://Shop:Shop123456@shop.xtmkurh.mongodb.net/?appName=Shop"
client = MongoClient(MONGO_URI)
db = client['shop_db']

def serialize(obj):
    """Serialize Django model fields for MongoDB."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def migrate_data():
    print("Starting data migration from SQLite to MongoDB...")
    print("-" * 40)

    # 1. Migrate Categories
    print("Migrating Categories...")
    categories_col = db['categories']
    categories_col.delete_many({}) # Clear existing to avoid duplicates
    cats = Category.objects.all()
    cat_list = []
    for c in cats:
        cat_data = {
            "sqlite_id": c.id,
            "name": c.name,
            "slug": c.slug,
            "icon": c.icon,
            "image": c.image.url if c.image else None
        }
        cat_list.append(cat_data)
    if cat_list:
        categories_col.insert_many(cat_list)
    print(f"  ==> Successfully migrated {len(cat_list)} categories.")

    # 2. Migrate Brands
    print("Migrating Brands...")
    brands_col = db['brands']
    brands_col.delete_many({})
    brands = Brand.objects.all()
    brand_list = []
    for b in brands:
        brand_data = {
            "sqlite_id": b.id,
            "name": b.name,
            "slug": b.slug,
            "logo": b.logo.url if b.logo else None
        }
        brand_list.append(brand_data)
    if brand_list:
        brands_col.insert_many(brand_list)
    print(f"  ==> Successfully migrated {len(brand_list)} brands.")

    # 3. Migrate Products
    print("Migrating Products...")
    products_col = db['products']
    products_col.delete_many({})
    products = Product.objects.all()
    prod_list = []
    for p in products:
        prod_data = {
            "sqlite_id": p.id,
            "title": p.title,
            "slug": p.slug,
            "short_description": p.short_description,
            "description": p.description,
            "price": serialize(p.price),
            "original_price": serialize(p.original_price),
            "image": p.image.url if p.image else None,
            "rating": p.rating,
            "reviews_count": p.reviews_count,
            "in_stock": p.in_stock,
            "stock_quantity": p.stock_quantity,
            "is_new": p.is_new,
            "is_best_seller": p.is_best_seller,
            "category_slug": p.category.slug,
            "category_name": p.category.name,
            "brand_name": p.brand.name if p.brand else None,
            "created_at": serialize(p.created_at),
            "updated_at": serialize(p.updated_at)
        }
        prod_list.append(prod_data)
    if prod_list:
        products_col.insert_many(prod_list)
    print(f"  ==> Successfully migrated {len(prod_list)} products.")

    print("-" * 40)
    print("Migration completed successfully!")

if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        print(f"Migration failed: {e}")
