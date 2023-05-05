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
from category.models import *
from .models import CartItem,Cart , Address,Payment,Orders,OrderProduct,Coupon,UsedCoupon
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
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

# Create your views here.

def store_category(request,id):
    categories      =   Category.objects.filter(is_blocked=True)
    products        =   Product.objects.filter(category=id)
    variants        =   Variant.objects.values_list('variant_name', flat=True).distinct()

    if request.user.is_authenticated :
        context={'products':products,'euser':True,'categories':categories, 'variants'   :  variants,}
        return render(request,'store/storeCategory.html',context)
    else:
        context={
                'products'   :  products,
                'categories' :  categories,
                'variants'   :  variants,
            }
        return render(request,'store/storeCategory.html',context)
    
def singleProduct(request,id):
    categories      =   Category.objects.all()
    products        =   Product.objects.get(id=id)
    variants        =   products.variants.all()
    if request.user.is_authenticated :
        context={'products':products,'euser':True,'categories':categories,'variants':variants}
        return render(request,'store/storeSingleProduct.html',context)
    else:
        context={'products':products,'categories':categories,'variants':variants}
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
 
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user = request.user) 
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id = _cart_id(request),user = request.user)
            try:
                cart_item = CartItem.objects.get(user = request.user , variant = variant, cart=cart)
                if variant.stock >= cart_item.quantity+1:
                    cart_item.quantity += 1 
                cart_item.save()
                item_count    =   CartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
                request.session["item_count"]   =   item_count 
            except CartItem.DoesNotExist:
                cart_item   =    CartItem.objects.create(quantity = 1,user = request.user, variant = variant, cart = cart)
                item_count  =    CartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0      
                request.session["item_count"]   =   item_count  
        else:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request)) #get the cart using the cartid present in the session
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id = _cart_id(request))
            try:
                cart_item = CartItem.objects.get(variant = variant, cart = cart)
                cart_item.quantity += 1 
                cart_item.save()
            except CartItem.DoesNotExist:
                cart_item = CartItem.objects.create(quantity = 1, cart = cart,variant=variant)
            item_count =CartItem.objects.filter(cart=cart).aggregate(Sum('quantity'))['quantity__sum'] or 0      
            request.session["item_count"]   =   item_count  
    
        response_data = {'message': 'Product added to cart successfully','item_count':item_count}
        return JsonResponse(response_data, status=200)
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)
    
def cartview(request,total = 0, quantity = 0, cart_items =None ):
    categories  =   Category.objects.all()
    if request.user.is_authenticated:
        cart_items       =   CartItem.objects.filter(user = request.user, is_active = True).order_by("-id")
        total            =   sum([item.sub_total for item in cart_items])
        context = {
                    'total'         :   total,
                    'cart_items'    :   cart_items,
                    'categories'    :   categories,
                    'euser'         :   True,
        }
    else:
        try:
            cart             =      Cart.objects.get(cart_id = _cart_id(request))
            cart_items       =      CartItem.objects.filter(cart = cart, is_active = True)
            for cart_item in cart_items:
                quantity    +=      cart_item.quantity
            total = sum(item.sub_total for item in cart_items)
        except ObjectDoesNotExist:
            pass #just ignore
        context = {
                    'total'             :   total,
                    'cart_items'        :   cart_items,
                    'categories'        :   categories,
                  }
    return render (request,'store/cart.html' ,context)  

def decrement_quantity(request):
    if request.method == 'POST':
        data            =   json.loads(request.body)
        variant         =   data.get('variant_id')
        quantity        =   data.get('quantity')
        if request.user.is_authenticated:
            cart_item       =   CartItem.objects.get(variant=variant,user=request.user)
            if cart_item:
                cart_item.quantity = quantity
                cart_item.save()
                total = sum([item.sub_total for item in  CartItem.objects.filter(user=request.user,is_active=True)])
                response_data = {'message': 'Quantity updated successfully', 'new_total': total}
                return JsonResponse(response_data, status=200)
            else:
                response_data = {'error': 'Cart item not found'}
                return JsonResponse(response_data, status=400)
        else:
            cart        =   Cart.objects.get(cart_id = _cart_id(request))
            cart_item   =   CartItem.objects.get(cart=cart, variant=variant)
            if cart_item:
                cart_item.quantity  =   quantity
                cart_item.save()
                total   =   sum([item.sub_total for item in CartItem.objects.filter(cart=cart,is_active=True)])
                response_data = {'message': 'Quantity updated successfully', 'new_total': total}
                return JsonResponse(response_data, status=200)
            else:
                response_data = {'error': 'Cart item not found'}
                return JsonResponse(response_data, status=400)
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  
    
def deletecart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        thiscartitem = CartItem.objects.get(id = cart_item_id)
        thiscartitem.delete()
        response_data = {'message': 'item deleted'}
        return JsonResponse(response_data, status=200)
    
@login_required(login_url='customer_signin')       
def checkout(request,total = 0,cart_items =None):
    global price_total
    categories      =   Category.objects.all()
    cart_items      =   CartItem.objects.filter(user=request.user, is_active=True).order_by("-id")
    categories      =   Category.objects.all()
    addresses       =   Address.objects.filter(user=request.user)
    coupons         =   Coupon.objects.filter(is_active=True)
    context         =   {
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
                    response_data   =   {'message': 'used coupon'}
                    return JsonResponse(response_data, status=200)
            except:
                cart_items         =   CartItem.objects.filter(user = request.user, is_active = True).order_by("-id")
                total              =   sum([item.sub_total for item in cart_items])
                discounted_price   =   total-(total*coupon.discount)/100
                request.session['coupon_code']         =   coupon.coupon_code
                request.session['sub_total']           =   total
                request.session['discount']            =   (total*coupon.discount)/100
                request.session['grand_total']         =   discounted_price
                price_total                            =   discounted_price
        response_data = {'grand_total'      :    discounted_price,
                         'discount'         :   (total*coupon.discount)/100,
                         'sub_total'        :   total,
                         'coupon_code'      :   coupon.coupon_code}
        return JsonResponse(response_data, status=200)
    
def remove_coupon(request):    
    if request.method == 'POST':
        data = json.loads(request.body)
        coupon_id = data.get('coupon_id')
        coupon = Coupon.objects.get(id=coupon_id)
        del request.session['coupon_code']
        response_data = {'coupon_code': coupon.coupon_code}
        return JsonResponse(response_data, status=200) # Add this line
    else:
        response_data = {'error': 'Invalid request method'}
        return JsonResponse(response_data, status=400)

razorpay_client     =    razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

@cache_control(no_cache =True, must_revalidate =True, no_store =True)
@login_required(login_url='customer_signin')       
def confirm_payment(request):
    categories=Category.objects.all()
    if request.method == "POST":
        global delivery_address
        delivery_address    =   request.POST.get('address')
    if not delivery_address:
            messages.error(request,'Please add a delivery address.')
            return redirect('checkout')
   
    request.session['delivery_address'] =   delivery_address
    cart_items     =   None
    try:
        order_id_generated      =   str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
        address                 =   Address.objects.get(id = delivery_address)
        cart_items              =   CartItem.objects.filter(user = request.user, is_active = True)
        cart_total              =   Cart.objects.get(user=request.user).cart_total
    
    except ObjectDoesNotExist:
        pass #just ignore
    request.session['order_id_generated']   =   order_id_generated
    if 'coupon_code' in request.session:
        price_total  =   request.session.get('grand_total')
    else:
        price_total     =   sum([item.sub_total for item in cart_items])    
    global razor_amount 
    razor_amount        =   price_total * 100
    currency            =   'INR'
    razorpay_client     =    razorpay.Client(
                                        auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
    razorpay_order      =   razorpay_client.order.create(dict(amount=razor_amount,
                                                                currency=currency,
                                                                payment_capture='0'))
    razorpay_order_id = razorpay_order['id']
    callback_url = 'paymenthandler/'

    context = {
            'razorpay_order_id'     :   razorpay_order_id,
            'razorpay_merchant_key' :   settings.RAZOR_KEY_ID,
            'razorpay_amount'       :   razor_amount,
            'currency'              :   currency,
            'callback_url'          :   callback_url,
            'categories'            :   categories,
            'cart_items'            :   cart_items,
            'address'               :   address,
            'price_total'           :   price_total,
            'euser'                 :   True
    }
    return render(request,'store/cod_invoice.html',context)

@csrf_exempt
def paymenthandler(request):
    categories      =   Category.objects.all()
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
                amount = razor_amount  # Rs. 200
                try:
                    razorpay_client.payment.capture(payment_id, amount)
                    # sub_total           =   Cart.objects.get(user=request.user).cart_total
                    # shipping_amount     =   sub_total+50
                    # context = {
                    #             'categories'        :   categories,
                    #             'cart_total'        :   sub_total,
                    #             'address'           :   delivery_address,
                    #             'euser'             :   True,
                    #             'orders'            :   orders,
                    #             'payment_method'    :   'Razorpay',
                    #             'razorpay_amount'   :   shipping_amount,

                    # }
                    # render success page on successful caputre of payment
                    return redirect('razorpay_home')
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
    
def razorpay_home(request):
    razorpay_order_id       =   request.session.get('razorpay_order_id')
    try:
        cart_items          =   CartItem.objects.filter(user = request.user, is_active = True)
        cart_itemcount      =   cart_items.count()
        if cart_itemcount <= 0 :
            return render(request,'nothing.html')
        if 'coupon_code' in request.session:
            cart_total    =   request.session.get('grand_total')
        else:
            cart_total    =   Cart.objects.get(user=request.user).cart_total
        payments      =   Payment.objects.create(
                                            user            =   request.user,
                                            payment_id      =   razorpay_order_id,
                                            payment_method  =   'Razorpay',
                                            amount_paid     =   cart_total ,
                                            status          =   'Completed',
                                        )
        delivery_address        =   request.session.get('delivery_address')
        address                 =   Address.objects.get(id=delivery_address) 
        order_id_generated      =   str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
        order                   =   Orders.objects.create(
                                        user        =   request.user,
                                        address     =   address,
                                        total       =   cart_total,
                                        orderid     =   order_id_generated,
                                        payment     =   payments
                                    )
            #MOVE THE CART ITEMS TO ORDER PRODUCTS TABLE
        for x in cart_items:
            order_product             =   OrderProduct(order=order)
            variants                  =   Variant.objects.get(id = x.variant.id)
            order_product.variant     =   variants
            order_product.quantity    =   x.quantity
                #REDUCE THE QUANTITY OF STOCK
            variants.stock           -=   x.quantity
            variants.save()
            order_product.save()
    # for x in cart_items:
    #     x.delete()
    # request.session["item_count"]=0
    # for context
        order_product       =    OrderProduct.objects.filter(order=order)  
        context             =    {
                                    "orders"            :   order,
                                    "order_products"    :   order_product,
                                    "grand_total"       :   cart_total,
                                    'address'           :   address,
                                    'payment_method'    :  'Razorpay',
                                    'euser'             :   True,


                                }
        return render(request,'store/bill.html',context)
    except (Payment.DoesNotExist,Orders.DoesNotExist):
        return redirect('cartview')
    
@login_required(login_url='customer_signin')  
@cache_control(no_cache =True, must_revalidate =True, no_store =True)
def payment_cod(request):
    quantity                    =      0
    cart_items                  =      None
    categories                  =      Category.objects.all()
    order_id_generated          =      str(int(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))  
    try:
        address                 =      Address.objects.get(id = delivery_address ) #passed that global address
        user                    =      request.user
        cart_items              =      CartItem.objects.filter(user = request.user, is_active = True)
        cart_item_count         =      cart_items.count()
        if cart_item_count <= 0 :
            return render(request,'store/nothing.html')
        else:
            if 'coupon_code' in request.session:
                cart_total     =    request.session.get('grand_total')
                coupons        =    Coupon.objects.get(coupon_code=request.session['coupon_code'])
                used_coupon    =    UsedCoupon.objects.create(user = request.user , coupon =coupons)
                coupon         =    True
                sub_total      =    request.session['sub_total']
                reduction      =    request.session['reduction']
                cart_total     =    request.session['grand_total']

                del request.session['coupon_code']
                del request.session['coupon']           
            else:            
                cart_total     =   Cart.objects.get(user = request.user).cart_total
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
            order                         =   Orders.objects.get(orderid = order_id_generated)
            for x in cart_items:
                order_product             =   OrderProduct(order=order)
                variants                  =   Variant.objects.get(id = x.variant.id)
                order_product.variant     =   variants
                order_product.quantity    =   x.quantity
                variants.stock           -=  x.quantity
                variants.save()
                order_product.save()
            # for x in cart_items:
            #     x.delete()
            # request.session["item_count"]=0
    except ObjectDoesNotExist:
            pass #just ignore
    order               =   Orders.objects.get(orderid = order_id_generated)
    order.is_ordered    =   True
    order.save()
    order_product       =    OrderProduct.objects.filter(order=order)
    context             = {
            'categories'        :   categories,
            'order_products'    :   order_product,
            'grand_total'       :   cart_total,
            'address'           :   address,
            'euser'             :   True,
            'orders'            :   order,
            'payment_method'    :  'COD',
            'coupon'            :   True,
            'sub_total'         :   sub_total,
            'reduction'         :   reduction,

            
        }
    return render(request,'store/bill.html',context)

def filter_product(request):
    if request.method == 'POST':
        category   =    request.POST.get('category')
        variant    =    request.POST.get('variant')
        min        =    request.POST.get('min')
        max        =    request.POST.get('max')
        print(category)
        print(variant)
    return redirect('store_category')




       
        

