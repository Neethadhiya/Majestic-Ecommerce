# Generated by Django 4.1.7 on 2023-05-02 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_remove_usedcoupon_coupon_remove_usedcoupon_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderproduct',
            name='offer_discount',
            field=models.FloatField(null=True),
        ),
    ]