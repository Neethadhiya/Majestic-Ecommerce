from customer import views
from django.urls import path, include
from .views import ResetPasswordView
from django.contrib.auth import views as auth_views
urlpatterns=[
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='customer/password_reset_confirm.html'),
         name='password_reset_confirm'),    
         path('',views.index,name='index'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='customer/password_reset_complete.html'),
         name='password_reset_complete'),    
    path('customer_signUp/',views.customer_signUp,name='customer_signUp'),
    path('customer_signin',views.customer_signin,name='customer_signin'),
    path('verify_otp',views.verify_otp,name='verify_otp'),
    path('customer_logout',views.customer_logout,name='customer_logout'),
    path('user_profile',views.user_profile,name='user_profile'),
    path('user_edit_profile/<int:id>',views.user_edit_profile,name='user_edit_profile'),
    path('update_user/<int:id>/',views.update_user,name='update_user'),
    path('change_password/',views.change_password,name='change_password'),
    path('editAddress/<int:id>',views.editAddress,name='editAddress'),
    path('update_address/<int:id>',views.update_address,name='update_address'),
    path('removeAddress/<int:id>',views.removeAddress,name='removeAddress'),
    path('add_address/',views.add_address,name='add_address'),
    path('editAddress/<int:id>',views.editAddress,name='editAddress'),
    path('update_address/<int:id>',views.update_address,name='update_address'),
    path('user_orders/<int:id>/',views.user_orders,name='user_orders'),
    path('user_order_details/<int:id>/', views.user_order_details,name='user_order_details'),
    path('user_order_details/cancel_product/', views.cancel_product,name='cancel_product'),
    path('user_order_details/return_product/', views.return_product,name='return_product'),
    path('user_orders/download_invoice/',views.download_invoice,name='download_invoice'),
    path('user_wallet/',views.user_wallet,name='user_wallet'),
    path('download_invoice_excel/', views.download_invoice_excel,name='download_invoice_excel'),

]
