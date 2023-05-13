from django.urls import path
from cart import views
urlpatterns=[
    path('cartview/',views.cartview, name='cartview'),
    path('cartview/checkout/',views.checkout, name='checkout'),
    path('singleProduct/<int:id>',views.singleProduct,name='singleProduct'),
    path('singleProduct/add_to_cart/',views.add_to_cart,name='add_to_cart'),
    path('cartview/deletecart_item/', views.deletecart_item, name='deletecart_item'),
    path('get_variant_price/', views.get_variant_price, name='get_variant_price'),
    path('cartview/decrement_quantity/',views.decrement_quantity,name='decrement_quantity'),
    path('place_order/',views.place_order,name='place_order') , 
    path('cash_on_delivery/', views.cash_on_delivery, name='cash_on_delivery'),
    path('place_order/paymenthandler/', views.paymenthandler , name='paymenthandler'), 
    path('place_order/payment_razorpay/',views.payment_razorpay , name='payment_razorpay'),  
    path('cartview/apply_coupon/',views.apply_coupon, name='apply_coupon'),
    path('cartview/remove_coupon/', views.remove_coupon, name='remove_coupon'),
    path('shop_page/filter_products/', views.filter_products, name='filter_products'),
    path('shop_page/search_products/', views.search_products, name='search_products'),
    path('shop_page/', views.shop_page, name='shop_page'),
    path('wallet/', views.wallet, name='wallet'),
      ] 