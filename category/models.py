from django.db import models
from django.utils.text import slugify
from accounts.models import *

class Category(models.Model):
    category_name   =   models.CharField(max_length=20, unique=True,null=False,blank=False)
    slug            =   models.SlugField(max_length=20, unique=True, null=True, blank=True)
    is_blocked      =   models.BooleanField(default=True)
    created_at      =   models.DateField(auto_now=False, auto_now_add=True)
    updated_at      =   models.DateTimeField( auto_now=True, auto_now_add=False)
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name
    
    @property
    def offer(self):
        offer =  Offer.objects.filter(category=self,is_deleted=True)
        return offer.first()
    
class Product(models.Model):
    slug            =   models.CharField(max_length=150, unique=True, null=True, blank=True)
    product_name    =   models.CharField(max_length=150, null=False, blank=False)
    description     =   models.TextField(max_length=250, null=False, blank=False)
    available       =   models.BooleanField(default=False)
    category        =   models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    created_at      =   models.DateField(auto_now=False, auto_now_add=True)
    updated_at      =   models.DateTimeField( auto_now=True, auto_now_add=False)
    is_deleted      =   models.BooleanField(default=False)
    deleted_at      =   models.DateTimeField(null=True, blank=True)
    price           =   models.FloatField(null = True)

    def save(self, *args, **kwargs):
        self.slug    = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.product_name
    
    @property
    def offer(self):
        offer =  Offer.objects.filter(product = self,is_deleted = True)
        if not offer:
            offer = Offer.objects.filter(category = self.category,is_deleted = True)
        print(f"Found offer {offer} for product {self.product_name}") 
        return offer.first()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='productImages', null=True)
    image = models.ImageField(upload_to="product", null=True, blank=True, default='/img/not-avaible.png')


class Variant(models.Model):
    product         =   models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variants', null=True,blank=True)
    variant_name    =   models.CharField(max_length=20,null=True)
    stock           =   models.IntegerField(default=0)
    price           =   models.FloatField()

    # @property
    # def offer_price(self):
    #     offer = self.product.offer
    #     discount = (self.price *offer.discount_percentage )/100
    #     offer_price = self.price - discount
    #     return offer_price

    def __str__(self):
        return self.variant_name
 
class Offer(models.Model):
    discount_percentage  =   models.IntegerField()
    category             =   models.ForeignKey(Category,on_delete=models.CASCADE,related_name='offer_category', null=True)
    product              =   models.ForeignKey(Product,on_delete=models.CASCADE,related_name='offer_product', null=True)
    created_at           =   models.DateField(auto_now=False, auto_now_add=True)
    is_deleted           =   models.BooleanField(default=True)
    deleted_at           =   models.DateTimeField(null=True, blank=True)
   
class Banner(models.Model):
    image                =   models.ImageField(upload_to="banner_image",null=True,blank=True) 
    title                =   models.CharField(max_length=150, null=False, blank=False)
    offer                =   models.ForeignKey(Offer,on_delete=models.CASCADE, null=True,related_name='banner_offer')

class Coupon(models.Model):
    coupon_code     =   models.CharField(max_length=10,blank=True)
    discount        =   models.FloatField()
    is_active       =   models.BooleanField(default=True)
    created_at      =   models.DateTimeField(auto_now=False, auto_now_add=True)
   
class UsedCoupon(models.Model):
    user            =   models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True)
    coupon          =   models.ForeignKey(Coupon,on_delete=models.CASCADE, null=True)


