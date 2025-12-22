from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('tracking_url_template', models.CharField(blank=True, help_text="e.g. https://courier.com/track?id={}", max_length=500, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='orders.courier'),
        ),
        migrations.AddField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
    ]
