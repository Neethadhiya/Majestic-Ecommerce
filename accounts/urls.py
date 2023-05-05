from django.urls import path
from accounts import views
urlpatterns=[
    path('',views.adminLogin,name='adminLogin'),
    path('adminHome/',views.adminHome,name="adminHome"), 
    path('adminLogout/',views.adminLogout,name='adminLogout'),
    path('adminHome/userManagement/',views.userManagement,name="userManagement"), 
    path('adminHome/userManagement/blockCustomer/',views.blockCustomer,name='blockCustomer'),
    path('searchUser/',views.searchUser,name='searchUser'),
    path('add_banner/', views.add_banner,name='add_banner'),
    path('banner_management/delete_banner/<int:id>', views.delete_banner,name='delete_banner'),
    path('banner_management/', views.banner_management,name='banner_management'),
    path('admin_add_coupon/', views.admin_add_coupon,name='admin_add_coupon'),
    path('display_couponlist/', views.display_couponlist,name='display_couponlist'),
    path('display_couponlist/block_coupon/',  views.block_coupon,name='block_coupon'),
    path('add_category_offers/',views.add_category_offers,name='add_category_offers'),
    path('add_product_offers/',views.add_product_offers,name='add_product_offers'),
    path('add_product_offers/get_products/', views.get_products, name='get_products'),    path('admin_orders/',views.admin_orders,name='admin_orders'),
    path('display_offers/',views.display_offers,name='display_offers'),
    path('display_offers/block_category_offer/',views.block_category_offer,name='block_category_offer'),
    path('admin_order_status/<int:id>', views.admin_order_status,name='admin_order_status'),
    path('admin_order_details/<int:id>',views.admin_order_details,name='admin_order_details'),
    path('sales_report/',views.sales_report,name='sales_report'),
    path('date_range',views.date_range,name='date_range'),
    path('monthly_report/<int:date>/',views.monthly_report,name='monthly_report'),
    path('yearly_report/<int:date>/',views.yearly_report,name='yearly_report') ,    
    path('monthly_sales_pdf_download/<str:frmdate>/',views.monthly_sales_pdf_download,name='monthly_sales_pdf_download'),
    path('yearly_sales_pdf_download/<int:year>/',views.yearly_sales_pdf_download,name='yearly_sales_pdf_download'),
    path('date_range_sales_pdf_download/<str:from_date>/<str:to_date>/',views.date_range_sales_pdf_download,name='date_range_sales_pdf_download'),
    path('monthly_sales_excel_download/<str:frmdate>/', views.monthly_sales_excel_download, name='monthly_sales_excel_download'),
    path('yearly_sales_excel_download/<int:year>/',views.yearly_sales_excel_download,name='yearly_sales_excel_download'),
    path('date_range_sales_excel_download/<str:from_date>/<str:to_date>/',views.date_range_sales_excel_download,name='date_range_sales_excel_download'),
]  