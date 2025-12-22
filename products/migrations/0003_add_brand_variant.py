from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_review_wishlist'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brands')),
            ],
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField(blank=True, max_length=50, null=True)),
                ('color', models.CharField(blank=True, max_length=50, null=True)),
                ('sku', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('price_adjustment', models.DecimalField(decimal_places=2, default=0.0, help_text='Add/Subtract from base price', max_digits=10)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.product')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='products.brand'),
        ),
    ]
