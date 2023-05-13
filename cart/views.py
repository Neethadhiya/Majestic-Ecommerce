from django.conf import settings
from django.shortcuts import render,redirect,get_object_or_404
from category.models import *
from customer import views
# from customer.views import customer_signin ,index
from django.contrib import messages,auth
import os
import imghdr
import datetime
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from category.models import Category, Product, ProductImage, Variant, Offer, Banner, Coupon, UsedCoupon
from .models import Cart, NewCartItem, Address, Payment, Orders, OrderProduct
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponseRedirect, JsonResponse
from accounts.models import CustomUser
from django.shortcuts import HttpResponse
from django.db.models import Sum
from django.views.decorators.cache import cache_control
from datetime import date
delivery_address = None
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.db.models import Q
from django.core import serializers


# Create your views here.   
def shop_page(request):
    products        =   Product.objects.filter(is_deleted=False)
    categories      =   Category.objects.filter(is_blocked=True)
    variants        =   Variant.objects.values_list('variant_name', flat=True).distinct()
    if request.user.is_authenticated:
        context={
                  'products'    :   products,
                  'euser'       :   True,
                  'categories'  :   categories, 
                  'variants'    :   variants,
                  'cart'        :   True,
                 }
        return render(request,'store/shop.html',context)
    else:
        context={
                'products'   :  products,
                'categories' :  categories,
                'variants'   :  variants,
                 'cart'      :   True,
            }
        return render(request,'store/shop.html',context)
    
def singleProduct(request,id):
    categories      =   Category.objects.filter(is_blocked=True)
    products        =   Product.objects.get(id=id)
    variants        =   products.variants.all()
    if request.user.is_authenticated :
        context={
                 'products'    :   products,
                 'euser'       :   True,
                 'categories'  :   categories,
                 'variants'    :   variants,
                 'cart'        :   True,
}
        return render(request,'store/storeSingleProduct.html',context)
    else:
        context={
                 'products'    :   products,
                 'categories'  :   categories,
                 'variants'    :   variants,
                 'cart'        :   True,
                 }
        return render(request,'store/storeSingleProduct.html',context)
    
def get_variant_price(request):
    variant_id = request.GET.get('variant_id')
    try:
        variant = Variant.objects.get(id=variant_id)
        price = variant.price
    except Variant.DoesNotExist:
        price = None
    return JsonResponse({ 'price': price })    

def _cart_id(request):
    session_id = request.session.session_key
    if not session_id:
        session_id    =   request.session.create()
    return session_id

def add_to_cart(request):
    if request.method == 'POST':
        data        =   json.loads(request.body)
        variant_id  =   data.get('variant_id')
        variant     =   Variant.objects.get(id=variant_id)
        product     =   variant.product
        offer       =   product.offer
        if offer:
            offer_discount = (variant.price * offer.discount_percentage)/100
        else:
            offer_discount = 0
        if variant.stock<=0:
            response_data = {'error': 'Out of stock','stock':'false'}
            return JsonResponse(response_data, status=200)        
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user = request.user) 
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id = _cart_id(request),user = request.user)
            try:
                cart_item = NewCartItem.objects.get(user = request.user , variant = variant, cart=cart,offer_discount = offer_discount)
                if variant.stock >= cart_item.quantity+1:
                    cart_item.quantity += 1 
                else:
                    response_data = {'error': 'Out of stock','stock':'false'}
                    return JsonResponse(response_data, status=200)
                cart_item.save()
                item_count    =   NewCartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
                request.session["item_count"]   =   item_count 
            except NewCartItem.DoesNotExist:
                cart_item   =    NewCartItem.objects.create(
                                        quantity = 1,
                                        user = request.user, 
                                        variant = variant, 
                                        cart = cart, 
                                        offer_discount = offer_discount
                                    )
                item_count  =    NewCartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0      
                request.session["item_count"]   =   item_count  
        else:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request)) 
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id = _cart_id(request))
            try:
                cart_item = NewCartItem.objects.get(variant = variant, cart = cart,offer_discount = offer_discount)
                cart_item.quantity += 1 
                cart_item.save()
            except NewCartItem.DoesNotExist:
                cart_item = NewCartItem.objects.create(
                    quantity  = 1, 
                    cart      = cart,
                    variant=variant,
                    offer_discount = offer_discount
                )
            item_count =NewCartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum'] or 0      
            request.session["item_count"]   =   item_count  
    
        response_data = {'message': 'Product added to cart successfully','item_count':item_count}
        return JsonResponse(response_data, status=200)
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def cartview(request,total = 0, quantity = 0, cart_items =None ):
    categories  =   Category.objects.filter(is_blocked=True)
    if request.user.is_authenticated:
        cart_items       =   NewCartItem.objects.filter(user = request.user, is_active = True).order_by("-id")
        item_count    =   NewCartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        request.session["item_count"]   =   item_count  
        if item_count==0:
            context = {
                        'categories'    :   categories,
                        'euser'         :   True,
                        'cart'          :   True,
            }
            return render(request,'store/nothing.html',context) 
        else:     
            total            =   sum([item.sub_total for item in cart_items])
            context = {
                        'total'         :   total,
                        'cart_items'    :   cart_items,
                        'categories'    :   categories,
                        'euser'         :   True,
                        'cart'          :   True,
            }
    else:
        try:
            cart             =      Cart.objects.get(cart_id = _cart_id(request))
            cart_items       =      NewCartItem.objects.filter(cart = cart, is_active = True)
            # for cart_item in cart_items:
            #     quantity    +=      cart_item.quantity
            item_count =NewCartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum'] or 0      
            request.session["item_count"]   =   item_count  
            total = sum([item.sub_total for item in cart_items])
        except ObjectDoesNotExist:
            pass #just ignore
        context = {
                    'total'             :   total,
                    'cart_items'        :   cart_items,
                    'categories'        :   categories,
                    'cart'              :   True,
                  }
    return render (request,'store/cart_view.html' ,context)  

def decrement_quantity(request):
    if request.method == 'POST':
        data            =   json.loads(request.body)
        variant         =   data.get('variant_id')
        quantity        =   data.get('quantity')
        if request.user.is_authenticated:
            cart_item       =   NewCartItem.objects.get(variant=variant,user=request.user)
            if cart_item:
                cart_item.quantity = int(quantity)
                cart_item.save()
                item_count    =   NewCartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
                request.session["item_count"]   =   item_count  
                sub_total=(cart_item.variant.price*cart_item.quantity)-(cart_item.offer_discount*cart_item.quantity)
                id = cart_item.variant.id
                total = sum([item.sub_total for item in  NewCartItem.objects.filter(user=request.user,is_active=True)])
                response_data = {
                    'message': 'Quantity updated successfully', 
                    'new_total': total,
                    'sub_total':sub_total,
                    'id':id,
                    'item_count':item_count
                    }
                return JsonResponse(response_data, status=200)
            else:
                response_data = {'error': 'Cart item not found'}
                return JsonResponse(response_data, status=400)
        else:
            cart        =   Cart.objects.get(cart_id = _cart_id(request))
            cart_item   =   NewCartItem.objects.get(cart=cart, variant=variant)
            if cart_item:
                cart_item.quantity  =   quantity
                cart_item.save()
                item_count =NewCartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum'] or 0      
                request.session["item_count"]   =   item_count                  
                total   =   sum([item.sub_total for item in NewCartItem.objects.filter(cart=cart,is_active=True)])
                response_data = {
                    'message': 'Quantity updated successfully', 
                    'new_total': total,
                    'item_count':item_count
                    }
                return JsonResponse(response_data, status=200)
            else:
                response_data = {'error': 'Cart item not found'}
                return JsonResponse(response_data, status=400)
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  
    
def deletecart_item(request):
    if request.method == 'POST':
        data               =    json.loads(request.body)
        cart_item_id       =    data.get('cart_item_id')
        this_cart_item     =    NewCartItem.objects.get(id = cart_item_id)
        this_cart_item.delete()
        if request.user.is_authenticated:
            item_count         =   NewCartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        else:
            cart        =   Cart.objects.get(cart_id = _cart_id(request))
            item_count =NewCartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum'] or 0      
        request.session['item_count'] =  item_count
        response_data      =    {'message': 'item deleted','item_count':item_count}
        return JsonResponse(response_data, status=200)
   
@login_required(login_url='customer_signin')       
def checkout(request,total = 0,cart_items =None):
    categories          =   Category.objects.filter(is_blocked=True)
    cart_items          =   NewCartItem.objects.filter(user=request.user, is_active=True).order_by("-id")
    addresses           =   Address.objects.filter(user=request.user)
    coupons             =   Coupon.objects.filter(is_active=True)
    total               =   sum([item.sub_total for item in cart_items])
    request.session['sub_total']  =  total
    context             =   {
                            'categories'   :   categories, 
                            'addresses'    :   addresses, 
                            'euser'        :   True,
                            'cart_items'   :   cart_items,
                            'coupons'      :   coupons,
                         }
    return render(request, 'store/checkout.html', context=context)  
 
def apply_coupon(request):
    if request.method == 'POST':
        data        =   json.loads(request.body)
        coupon_id   =   data.get('coupon_id')
        coupon      =   Coupon.objects.get(id=coupon_id)
        if coupon:
            try:
                if UsedCoupon.objects.get(user=request.user,coupon = coupon):
                    response_data   =   {
                                            'message': 'used coupon',
                                            "used_coupon":True,
                                            'coupon':coupon.coupon_code
                                        }
                    return JsonResponse(response_data, status=200)
            except:
                cart_items         =   NewCartItem.objects.filter(user = request.user, is_active = True).order_by("-id")
                total              =   sum([item.sub_total for item in cart_items])
                discounted_price   =   total-(total*coupon.discount)/100
                request.session['coupon_code']         =   coupon.coupon_code
                request.session['sub_total']           =   total
                request.session['discount']            =   (total*coupon.discount)/100
                request.session['grand_total']         =   discounted_price
        response_data = {
                            'grand_total'      :    discounted_price,
                            'discount'         :   (total*coupon.discount)/100,
                            'sub_total'        :   total,
                            'coupon_code'      :   coupon.coupon_code
                         }
        return JsonResponse(response_data, status=200)
    
def remove_coupon(request):    
    if request.method    ==  'POST':
        data             =   json.loads(request.body)
        coupon_id        =   data.get('coupon_id')
        coupon           =   Coupon.objects.get(id=coupon_id)
        sub_total        =   request.session['sub_total']
        del request.session['coupon_code']
        response_data    =   {'coupon_code': coupon.coupon_code,'sub_total':sub_total}
        return JsonResponse(response_data, status=200) # Add this line
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)

razorpay_client     =    razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

@cache_control(no_cache=True, must_revalidate=True, no_store=True, max_age=0)
@login_required(login_url='customer_signin')       
def place_order(request):
    delivery_address = None
    categories = Category.objects.filter(is_blocked=True)
    cart_items = None
    price_total = 0
    razor_amount = 0

    if request.method == "POST":
        delivery_address_id = request.POST.get('address')
        try:
            address = Address.objects.get(id=delivery_address_id)
            cart_items = NewCartItem.objects.filter(user=request.user, is_active=True)
            cart_total = Cart.objects.get(user=request.user).cart_total
            request.session['delivery_address_id'] = delivery_address_id
        except ObjectDoesNotExist:
            request.session['delivery_address_id'] = None

    address = None
    if request.session.get('delivery_address_id'):
        try:
            address = Address.objects.get(id=request.session.get('delivery_address_id'))
        except Address.DoesNotExist:
            address = None
    else:
        messages.error(request, "Please add an address.")

    if not address:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    if 'coupon_code' in request.session:
        price_total = request.session.get('grand_total')
    else:
        price_total = request.session.get('sub_total')

    razor_amount = price_total * 100
    request.session['razor_amount'] = razor_amount
    currency = 'INR'

    razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
    razorpay_order = razorpay_client.order.create(dict(amount=razor_amount, currency=currency, payment_capture='0'))
    razorpay_order_id = razorpay_order['id']
    callback_url = 'paymenthandler/'

    context = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZOR_KEY_ID,
        'razorpay_amount': razor_amount,
        'currency': currency,
        'callback_url': callback_url,
        'categories': categories,
        'cart_items': cart_items,
        'address': address,
        'euser': True,
    }
    return render(request, 'store/place_order.html', context)

@csrf_exempt
def paymenthandler(request):
    categories      =   Category.objects.filter(is_blocked=True)
    orders          =   Orders.objects.filter(user=request.user)
    order_product   =   OrderProduct.objects.filter
    # only accept POST request.
    global razorpay_order_id
    if request.method == "POST":
        try:
            # get the required parameters from post request.
            payment_id          =   request.POST.get('razorpay_payment_id', '')
            razorpay_order_id   =   request.POST.get('razorpay_order_id', '')
            request.session['razorpay_order_id'] = razorpay_order_id
            signature           =   request.POST.get('razorpay_signature', '')
            params_dict         =   {
                'razorpay_order_id'     :   razorpay_order_id,
                'razorpay_payment_id'   :   payment_id,
                'razorpay_signature'    :   signature
            }
            # verify the payment signature.

            result      =    razorpay_client.utility.verify_payment_signature(
                params_dict)
            if result is not None:
                amount = request.session.get('razor_amount')  # Rs. 200
                try:
                    razorpay_client.payment.capture(payment_id, amount)
                    return redirect('payment_razorpay')
                except:
                    return render(request, 'store/paymentfail.html')
            else:
                # if signature verification fails.
                return render(request, 'store/paymentfail.html')
        except:
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
       # if other than POST request is made.
        return HttpResponseBadRequest()
    
def payment_razorpay(request):
    categories                  =  Category.objects.filter(is_blocked=True)
    cart_items                  =      None
    grand_total_without_coupon  =      0
    grand_total_with_coupon     =      0
    sub_total                   =      0
    discount                    =      0    
    razorpay_order_id           =   request.session.get('razorpay_order_id')
    try:
        cart_items              =   NewCartItem.objects.filter(user = request.user, is_active = True)
        cart_itemcount          =   cart_items.count()
        if cart_itemcount <= 0 :
            context = {
                        'categories'    :   categories,
                        'euser'         :   True,
                        'cart'          :   True,
            }
            return render(request,'store/nothing.html',context)
        else:
            if 'coupon_code' in request.session:
                cart_total     =   request.session.get('grand_total')
                coupon         =    True
                grand_total_with_coupon  =  cart_total
                sub_total      =    request.session.get('sub_total')
                discount       =    request.session.get('discount')
                coupons        =    Coupon.objects.get(coupon_code=request.session['coupon_code'])
                used_coupon    =    UsedCoupon.objects.create(user = request.user , coupon =coupons)
                del request.session['coupon_code']
                request.session["coupon_check"] =  coupon            
            else:
                coupon         =    False
                request.session["coupon_check"] =  coupon
                cart_total     =   request.session.get('sub_total')
                grand_total_without_coupon =  cart_total
            payments          =   Payment.objects.create(
                                                user            =   request.user,
                                                payment_id      =   razorpay_order_id,
                                                payment_method  =   'Razorpay',
                                                amount_paid     =   cart_total ,
                                                status          =   'Completed',
                                            )
            delivery_address        =   request.session.get('delivery_address_id')
            address                 =   Address.objects.get(id=delivery_address) 
            order_id_generated      =   str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
            payment           =         Payment.objects.get(id = payments.id)
            order                   =   Orders.objects.create(
                                            user        =   request.user,
                                            address     =   address,
                                            total       =   cart_total,
                                            orderid     =   order_id_generated,
                                            payment     =   payment
                                        )
            order                         =   Orders.objects.get(orderid = order.orderid)
            order.is_ordered              =   True    
            order.save()            
                #MOVE THE CART ITEMS TO ORDER PRODUCTS TABLE
            for x in cart_items:
                order_product             =   OrderProduct(order=order)
                variants                  =   Variant.objects.get(id = x.variant.id)
                order_product.variant     =   variants
                order_product.quantity    =   x.quantity
                order_product.offer_discount = x.offer_discount
                    #REDUCE THE QUANTITY OF STOCK
                variants.stock           -=   x.quantity
                variants.save()
                order_product.save()
            for x in cart_items:
                x.delete()
            request.session["item_count"]=0

            order_product       =    OrderProduct.objects.filter(order=order)  
            context             =    {
                                        "orders"            :   order,
                                        "order_products"    :   order_product,
                                        "grand_total"       :   cart_total,
                                        'address'           :   address,
                                        'payment_method'    :  'Razorpay',
                                        'euser'             :   True,
                                        'sub_total'         :   sub_total,
                                        'discount'          :   discount,
                                'grand_total_with_coupon'  :   grand_total_with_coupon,
                                'grand_total_without_coupon':   grand_total_without_coupon,                                    
                                    }
            return render(request,'store/invoice.html',context)
    except (Payment.DoesNotExist,Orders.DoesNotExist):
        return redirect('cartview')


@login_required(login_url='customer_signin')  
@cache_control(no_cache =True, must_revalidate =True, no_store =True)
def cash_on_delivery(request):
    cart_items                  =      None
    grand_total_without_coupon  =      0
    grand_total_with_coupon     =      0
    sub_total                   =      0
    discount                    =      0
    categories                  =      Category.objects.filter(is_blocked=True)
    order_id_generated          =      str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    delivery_address            =      request.session.get('delivery_address_id')
    try:
        address                 =      Address.objects.get(id = delivery_address )
        user                    =      request.user
        cart_items              =      NewCartItem.objects.filter(user = request.user, is_active = True)
        cart_item_count         =      cart_items.count()
        if cart_item_count <= 0 :
            context = {
                        'categories'    :   categories,
                        'euser'         :   True,
                        'cart'          :   True,
            }
            return render(request,'store/nothing.html',context)
        else:
            if 'coupon_code' in request.session:
                cart_total     =    request.session.get('grand_total')
                coupon         =    True
                grand_total_with_coupon  =  cart_total
                sub_total      =    request.session.get('sub_total')
                discount       =    request.session.get('discount')
                coupons        =    Coupon.objects.get(coupon_code=request.session['coupon_code'])
                used_coupon    =    UsedCoupon.objects.create(user = request.user , coupon =coupons)
                del request.session['coupon_code']
                request.session["coupon_check"] =  coupon
            else:
                coupon         =    False
                request.session["coupon_check"] =  coupon
                cart_total     =   request.session.get('sub_total')
                grand_total_without_coupon =  cart_total
            paymethod          =   'COD'
            payment            =   Payment.objects.create(
                                        user            =   request.user,
                                        payment_method  =   paymethod,
                                        amount_paid     =   cart_total ,
                                        status          =   'Pending',
                                        )
            
            payments            =   Payment.objects.get(id = payment.id)
            order               =   Orders.objects.create(
                                            user        =   user,
                                            address     =   address ,
                                            total       =   cart_total,
                                            orderid     =   order_id_generated,
                                            payment     =   payments
                                            )
            order                         =   Orders.objects.get(orderid = order.orderid)
            for x in cart_items:
                order_product             =   OrderProduct(order=order)
                variants                  =   Variant.objects.get(id = x.variant.id)
                order_product.variant     =   variants
                order_product.quantity    =   x.quantity
                order_product.offer_discount = x.offer_discount
                variants.stock           -=  x.quantity
                variants.save()
                order_product.save()
            for x in cart_items:
                x.delete()
            request.session["item_count"]=0
    except ObjectDoesNotExist:
            pass #just ignore
    order               =   Orders.objects.get(orderid = order.orderid)
    order.is_ordered    =   True    
    order.save()
    order_product       =    OrderProduct.objects.filter(order=order)
    context             = {
            'categories'        :   categories,
            'order_products'    :   order_product,
            'address'           :   address,
            'euser'             :   True,
            'orders'            :   order,
            'payment_method'    :  'COD',
            'sub_total'         :   sub_total,
            'discount'          :   discount,
            'grand_total_with_coupon'     :   grand_total_with_coupon,
            'grand_total_without_coupon'  :   grand_total_without_coupon,

        }
    return render(request,'store/invoice.html',context) 

@login_required(login_url='customer_signin')  
@cache_control(no_cache =True, must_revalidate =True, no_store =True)
def wallet(request):
    cart_items                  =      None
    grand_total_without_coupon  =      0
    grand_total_with_coupon     =      0
    sub_total                   =      0
    discount                    =      0
    categories                  =      Category.objects.filter(is_blocked=True)
    order_id_generated          =      str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    delivery_address            =      request.session.get('delivery_address_id')
    try:
        address                 =      Address.objects.get(id = delivery_address ) 
        cart_items              =      NewCartItem.objects.filter(user = request.user, is_active = True)
        cart_item_count         =      cart_items.count()
        user                    =      CustomUser.objects.get(email=request.user)
        context = {
                        'categories'    :   categories,
                        'euser'         :   True,
                        'cart'          :   True,
            }
        if cart_item_count <= 0 :
            return render(request,'store/nothing.html',context)
        else:
            if 'coupon_code' in request.session:
                cart_total     =    request.session.get('grand_total')
                coupon         =    True
                grand_total_with_coupon  =  cart_total
                sub_total      =    request.session.get('sub_total')
                discount       =    request.session.get('discount')
                coupons        =    Coupon.objects.get(coupon_code=request.session['coupon_code'])
                used_coupon    =    UsedCoupon.objects.create(user = request.user , coupon =coupons)
                if grand_total_with_coupon <= user.wallet:
                    user.wallet     =  user.wallet - grand_total_with_coupon
                    user.save()
                    del request.session['coupon_code']
                    request.session["coupon_check"] =  coupon
                else:
                    messages.error(request,"Wallet has insufficient balance...")
                    return redirect(place_order)
            else:
                coupon         =    False
                request.session["coupon_check"] =  coupon
                cart_total     =   request.session.get('sub_total')
                grand_total_without_coupon =  cart_total
                if grand_total_without_coupon <= user.wallet:
                    user.wallet     =  user.wallet - grand_total_without_coupon
                    user.save()
                else:
                    messages.error(request,"Wallet has insufficient balance...")
                    return redirect(place_order)
                
            paymethod          =   'WALLET'
            payment            =   Payment.objects.create(
                                            user            =   request.user,
                                            payment_method  =   paymethod,
                                            amount_paid     =   cart_total ,
                                            status          =   'Completed',
                                            )
        
            payments            =   Payment.objects.get(id = payment.id)
            order               =   Orders.objects.create(
                                                user        =   request.user,
                                                address     =   address ,
                                                total       =   cart_total,
                                                orderid     =   order_id_generated,
                                                payment     =   payments
                                            )
            order                         =   Orders.objects.get(orderid = order.orderid)
            for x in cart_items:
                order_product             =   OrderProduct(order=order)
                variants                  =   Variant.objects.get(id = x.variant.id)
                order_product.variant     =   variants
                order_product.quantity    =   x.quantity
                order_product.offer_discount = x.offer_discount
                variants.stock           -=  x.quantity
                variants.save()
                order_product.save()
            for x in cart_items:
                x.delete()
            request.session["item_count"]=0
    except ObjectDoesNotExist:
            pass #just ignore
    order               =   Orders.objects.get(orderid = order.orderid)
    order.is_ordered    =   True    
    order.save()
    order_product       =    OrderProduct.objects.filter(order=order)
    context             = {
            'categories'        :   categories,
            'order_products'    :   order_product,
            'address'           :   address,
            'euser'             :   True,
            'orders'            :   order,
            'payment_method'    :   'Wallet',
            'sub_total'         :    sub_total,
            'discount'          :    discount,
            'grand_total_with_coupon'     :   grand_total_with_coupon,
            'grand_total_without_coupon'  :   grand_total_without_coupon,

        }

    return render(request,'store/invoice.html',context) 

from django.db.models import Min, Max

def filter_products(request):
    categories = Category.objects.filter(is_blocked=True)
    variants = Variant.objects.values_list('variant_name', flat=True).distinct()
    sizevar = list(Variant.objects.order_by('variant_name').values_list('variant_name', flat=True).distinct())
    category = None  # Initialize category variable to None
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        size = request.POST.get('variant')
        min_price = request.POST.get('min')
        max_price = request.POST.get('max')
        products = Product.objects.filter(is_deleted=False).order_by('product_name')
        
        if category_id:
            category = Category.objects.get(id=category_id)  # Set the category variable to the selected category object
            products = products.filter(category__category_name__iexact=category.category_name)
        
        if size:
            products = products.filter(variants__variant_name__iexact=size)
        
        if min_price and max_price:
            products = products.annotate(
                min_price=Min('variants__price'),
                max_price=Max('variants__price')
            ).filter(variants__price__gte=min_price, variants__price__lte=max_price)
        elif min_price:
            products = products.annotate(min_price=Min('variants__price')).filter(variants__price__gte=min_price)
        elif max_price:
            products = products.annotate(max_price=Max('variants__price')).filter(variants__price__lte=max_price)
    else:
        products = Product.objects.filter(is_deleted=False).order_by('product_name')
    if not products:
        no_product = True
    else:
        no_product = False
       
    context = {
        'categories': categories,
        'sizevar': sizevar,
        'products': products,
        'category': category,
        'category_id': int(category_id),
        'size': request.POST.get('variant'),
        'min_price': request.POST.get('min'),
        'max_price': request.POST.get('max'),
        'filter': True,
        'variants': variants,
        'euser'   :   True,
        'no_product' :  no_product,
    }

    return render(request, 'store/shop.html', context)

def search_products(request):
    query = request.GET.get('q')
    categories = Category.objects.filter(is_blocked=True)
    variants = Variant.objects.values_list('variant_name', flat=True).distinct()
    sizevar = list(Variant.objects.order_by('variant_name').values_list('variant_name', flat=True).distinct())
    
    products = Product.objects.filter(is_deleted=False).order_by('product_name')
    
    if query:
        products = products.filter(Q(product_name__icontains=query) | Q(category__category_name__icontains=query) | Q(variants__variant_name__icontains=query)).distinct()
    if not products:
        no_product = True
    else:
        no_product = False
        
    context = {
        'categories': categories,
        'sizevar': sizevar,
        'products': products,
        'variants':variants,
        'filter': True,
        'query': query,
        'euser'   :   True,
        'no_product' :  no_product,
    }

    return render(request, 'store/shop.html', context)



