from django.urls import path
from category import views
urlpatterns=[
    path('addCategory',views.addCategory,name='addCategory'),
    path('categoryManagement/',views.categoryManagement,name='categoryManagement'),
    path('addProduct/',views.addProduct,name='addProduct'),
    path('productManagement',views.productManagement,name='productManagement'),
    path('deleteCategory/<int:id>/',views.deleteCategory,name='deleteCategory'),
    # path('blockCategory/<int:id>/',views.blockCategory,name='blockCategory'),
    path('ajax/blockCategory/', views.blockCategoryAjax, name='blockCategoryAjax'),
    path('delete_single_image_edit/<int:id>', views.delete_single_image_edit, name='delete_single_image_edit'),
    path('soft_delete_product/<int:id>',views.soft_delete_product,name='soft_delete_product'),
    path('category/editProduct/<int:id>/',views.editProduct,name="editProduct"),
    path('updateProduct/<int:id>',views.updateProduct,name='updateProduct'),
    path('delete_single_image/<int:id>', views.delete_single_image, name='delete_single_image'),
    path('archived_products',views.archived_products,name='archived_products'),
    path('restore_product/<int:id>',views.restore_product,name='restore_product'),
]