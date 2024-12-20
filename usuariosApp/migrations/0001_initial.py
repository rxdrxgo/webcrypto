# Generated by Django 5.0.1 on 2024-12-09 19:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Crypto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crypto_id', models.CharField(max_length=100, unique=True)),
                ('symbol', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=100)),
                ('current_price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('market_cap', models.BigIntegerField()),
                ('image_url', models.URLField(blank=True, null=True)),
                ('initial_price', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crypto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuariosApp.crypto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Portafolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('crypto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuariosApp.crypto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=8, max_digits=20)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('transaction_type', models.CharField(choices=[('buy', 'Comprar'), ('sell', 'Vender')], max_length=10)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('crypto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuariosApp.crypto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
