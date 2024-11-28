# Generated by Django 5.0.1 on 2024-11-28 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuariosApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='crypto',
            name='crypto_id',
            field=models.CharField(default='undefined', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='crypto',
            name='market_cap',
            field=models.DecimalField(decimal_places=2, max_digits=30),
        ),
    ]
