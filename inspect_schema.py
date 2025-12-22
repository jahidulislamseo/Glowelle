import os
import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'products_product';
    """)
    rows = cursor.fetchall()
    print("Column | Type | Max Length")
    print("---|---|---")
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]}")
