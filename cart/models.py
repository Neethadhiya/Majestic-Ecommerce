from django.db import models
from accounts.models import *
from category.models import *
from category.models import Product,Variant,ProductImage
from django.utils import timezone
class Cart(models.Model):
    cart_id         =   models.CharField(max_length=250,blank=True)
    date_added      =   models.DateField(auto_now_add=True)
    user            =   models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='cart_user', null=True)
    @property
    def cart_total(self):
        cart_items  =   NewCartItem.objects.filter(user = self.user,cart = self)
        cart_total  =   0
        for item in cart_items:
            cart_total += item.sub_total
        return cart_total

    def __str__(self):
        return self.cart_id
    
class NewCartItem(models.Model):
    user        =   models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='cartItems', null=True)
    variant     =   models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="variants",null=True)
    cart        =   models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cartItems' ,null=True)
    offer_discount   =   models.FloatField(null = True)
    quantity    =   models.IntegerField(default=1)
    is_active   =   models.BooleanField(default=True)
    created_at  =   models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at  =   models.DateTimeField(auto_now=True, auto_now_add=False)
    is_deleted  =   models.BooleanField(default=False)
    @property
    def sub_total(self):
        sub_total = (self.variant.price * self.quantity) - (self.offer_discount *self.quantity)
        return sub_total

class Address(models.Model):
    firstname       =   models.CharField(max_length=50, null=True)
    lastname        =   models.CharField(max_length=50, null=True)
    phonenumber     =   models.CharField(max_length=50, null=True)
    housename       =   models.CharField(max_length=50, null=True)
    locality        =   models.CharField(max_length=50, null=True)
    city            =   models.CharField(max_length=50, null=True)
    state           =   models.CharField(max_length=50, null=True)
    pincode         =   models.CharField(max_length=50, null=True)
    user            =   models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.user.last_name

class Payment(models.Model):
    user            =   models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True)
    payment_id      =   models.CharField(max_length=100,null=True)
    payment_method  =   models.CharField(max_length=100)
    amount_paid     =   models.CharField(max_length=100)
    status          =   models.CharField(max_length=100)
    created_at      =   models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at      =   models.DateTimeField(auto_now=True, auto_now_add=False)    
    def __str__(self):
        return self.payment_method

class Orders(models.Model):
    STATUS = ( 
        ('Confirmed','Confirmed'),
        ('Shipped','Shipped'),
        # ('Out_for_delivery','Out_for_delivery'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
        ('Returned','Returned')
    )

    user        =   models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True)
    address     =   models.ForeignKey(Address,on_delete=models.CASCADE, null=True)
    payment     =   models.ForeignKey(Payment,on_delete=models.SET_NULL, blank=True, null=True)
    orderid     =   models.CharField(max_length=100,null=True)
    date_added  =   models.DateField(null=True,auto_now_add=True)
    status      =   models.CharField(max_length=30, choices=STATUS, default='Confirmed')
    total       =   models.FloatField(null=True)
    is_ordered  =   models.BooleanField(default=False)
    is_deleted  =   models.BooleanField(default=False)
    created_at  =   models.DateTimeField(auto_now=False, auto_now_add=True,null=True)
    updated_at  =   models.DateTimeField(auto_now=True, auto_now_add=False)    
    def __str__(self):
        return self.user.first_name

class OrderProduct(models.Model):
    STATUS = (
        ('Confirmed','Confirmed'),
        ('Shipped','Shipped'),
        ('Out_for_delivery','Out_for_delivery'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
        ('Returned','Returned')
    )
    order          =   models.ForeignKey(Orders,on_delete=models.CASCADE, null=True,related_name='order_products')
    offer_discount   =   models.FloatField(null = True)
    quantity       =   models.IntegerField(default=1)
    status         =   models.CharField(max_length=30, choices=STATUS, default='Confirmed')
    created_at     =   models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at     =   models.DateTimeField(auto_now=True, auto_now_add=False)
    variant        =   models.ForeignKey(Variant,on_delete=models.CASCADE,null=True)
    is_deleted     =   models.BooleanField(default=False)

    @property
    def sub_total(self):
        sub_total_amount    =   (self.variant.price * int(self.quantity)) - (self.offer_discount * int(self.quantity))
        return sub_total_amount
    def __str__(self):
        return self.variant.product.product_name
    

