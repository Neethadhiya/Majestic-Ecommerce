from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
# class AccountAdmin(UserAdmin):
#     list_display=('email','first_name','last_name','username','last_login','date_joined','is_active')
#     list_display_links=('email','first_name','last_name')
#     readonly_fields=('last_login','date_joined')
#     odering=('-date_joined',)
#     filter_horizondal=()
#     list_filter=()
#     fieldsets=()
# # admin.site.register(Account,AccountAdmin)
admin.site.register(CustomUser)
# Register your models here.
