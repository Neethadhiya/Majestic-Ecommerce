from django.contrib import admin
from .models import Cart, Address, OrderProduct, Payment, Orders
# Register your models here.
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(Payment)
admin.site.register(Orders)
admin.site.register(OrderProduct)
# admin.site.register(NewCartItems)
