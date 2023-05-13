from django.contrib import messages,auth
from django.shortcuts import render,redirect,get_object_or_404
from category.models import Category, Product, ProductImage, Variant, Offer, Banner, Coupon, UsedCoupon
import os
import imghdr
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.utils import timezone

@csrf_exempt
def blockCategoryAjax(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = Category.objects.get(id=category_id)

        if category.is_blocked:
            category.is_blocked = False
        else:
            category.is_blocked = True
        category.save()
        return JsonResponse({'is_blocked': category.is_blocked})
    else:
        return JsonResponse({'error': 'Invalid request method'})


def addCategory(request):
    if request.method == 'POST':
        category_name   =   request.POST['name']
        if category_name.strip() == '':
            messages.error(request, "Category name cannot be null")
            return redirect('addCategory') 
        try:
            category    =   Category(category_name=category_name)
            category.save()
            messages.success(request, 'Category added successfully')
            return redirect('addCategory')
        except IntegrityError:
            error_message =  'Category with name "{}" already exists'.format(category_name)
            messages.error(request, error_message)
            return render(request, 'category/addCategory.html', {'error': error_message})
    else:
        return render(request, 'category/addCategory.html')
    
@login_required(login_url='adminLogin')
@permission_required('is_superuser')
def categoryManagement(request):
    categories=Category.objects.all().order_by('-updated_at')
    context={'categories':categories}
    return render(request,'category/categoryManagement.html',context)

def handle_uploaded_file(file):
    directory = 'uploads/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(directory + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

def addProduct(request):
    stock = ''
    price = ''
    categories                  =   Category.objects.filter(is_blocked=True)
    context                     =   {'categories':categories}
    if request.method == 'POST':
        try:
            category_id         =   request.POST.get('subCategory')
            category            =   Category.objects.get(id=category_id)
            name                =   request.POST.get('name')
            description         =   request.POST.get('description')
            variants            =   request.POST.getlist('variant')
            stocks              =   request.POST.getlist('stock')
            prices              =   request.POST.getlist('price')
            images              =   request.FILES.getlist('images')
            unique_variants     =   []
            for variant in variants:
                if variant in unique_variants:
                    messages.error(request,"Warning: Add different size variants..")
                    return redirect('addProduct')
                else:
                    unique_variants.append(variant)
            if name.strip() == '':
                messages.error(request, "Product name cannot be null")
                return redirect('addProduct') 
            if Product.objects.filter(product_name=name).exists():
                messages.error(request,"Product with the name '{}' already exists".format(name))
                return redirect('addProduct')
            product             =   Product.objects.create(
                product_name    =   name,
                description     =   description,
                category        =   category
            )           
            product.save()

            for variant,stock,price in zip(unique_variants,stocks,prices):
                variant         =   Variant.objects.create(
                    variant_name    =   variant,
                    stock           =   int(stock),
                    price           =   float(price),
                    product         =   product
                    )
            variant.save()
            for image in images:
                file_format     =   imghdr.what(image)
                if file_format is None:
                    messages.error(request, 'Invalid image format')
                    product.delete()
                    return redirect('addProduct')
                product_image   =   ProductImage.objects.create(image=image,product=product)  
                product_image.save()            
            messages.success(request, f"Product '{name}' added successfully")
            return redirect('addProduct')
        except ObjectDoesNotExist:
            messages.error(request, 'Invalid category selected') 
            return redirect('addProduct')
        except IntegrityError as e:
            messages.error(request, 'Product with the same slug already exists')
            product.delete()
            return redirect('addProduct')
    else:
        return render(request, 'product/addProduct.html', context)      
           
def productManagement(request):
    products=Product.objects.filter(is_deleted=False).order_by('-updated_at')
    context={'products':products}
    return render(request,'product/productManagement.html',context)

def archived_products(request):
    products=Product.objects.filter(is_deleted=True).order_by('-updated_at')
    context={'products':products}
    return render(request,'product/archived_products.html',context)

def restore_product(request,id):
    product                 =   Product.objects.get(id=id)
    product.is_deleted      =   False
    product.save()
    context={'product':product}
    messages.success(request,"Product '{}' has been resored...".format(product.product_name))
    return redirect('productManagement')

def delete_single_image(request, id):
    image = ProductImage.objects.get(id=id)
    image.delete()
    messages.success(request,'Image deleted successfully')
    return redirect('productManagement')

def delete_single_image_edit(request, id):
    image = ProductImage.objects.get(id=id)
    image.delete()
    messages.success(request,'Image deleted successfully')
    id=image.product.id
    return redirect('editProduct',id)

def soft_delete_product(request,id):
    product             =   Product.objects.get(id=id)
    product.is_deleted  =   True
    product.deleted_at  =   timezone.now()
    product.save()
    messages.success(request,"Product '{}' has been archived and is no longer available on the site...".format(product.product_name))
    return redirect('productManagement')

def deleteCategory(request,id):
    category=Category.objects.get(id=id)
    category.delete()
    return redirect('categoryManagement')

def editProduct(request,id):
    products=Product.objects.get(id=id)
    context={'products':products}
    return render(request,'product/editProduct.html',context)

def updateProduct(request, id):
    product = Product.objects.get(id=id)

    if request.method == 'POST':
        product.product_name    =   request.POST.get('name')
        product.description     =   request.POST.get('description')
        sizes                   =   request.POST.getlist('size')
        stocks                  =   request.POST.getlist('stock')
        price                   =   request.POST.getlist('price')
        variant_items           =   Variant.objects.filter(product=product)
        variant_items.delete()
        unique_variants     =   []
        for variant in sizes:
            if variant in unique_variants:
                messages.error(request,"Warning: Multiple variants have the same value..")
                return redirect('addProduct')
            else:
                unique_variants.append(variant)
        for size, stock, price in zip(unique_variants, stocks, price):
            new_variant=Variant.objects.create(
                product=product,
                variant_name=size,
                stock=stock,
                price=price,
                )
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)
        product.save()
        messages.success(request, f"Product '{product.product_name}' updated successfully")
        return redirect('productManagement')
    else:
        context = {'products': product}
        return render(request, 'product/editProduct.html', context)

    
