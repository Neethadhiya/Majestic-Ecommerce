from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email               =    models.EmailField(unique=True,null=True,blank=True)
    phone_number        =    models.CharField(max_length=12,unique=True,null=True,blank=True)
    otp                 =    models.CharField(max_length=100,null=True,blank=True)
    first_name          =    models.CharField(max_length=30, blank=True)
    last_name           =    models.CharField(max_length=30, blank=True)
    wallet              =    models.FloatField(default=0)
    is_staff            =    models.BooleanField(default=False)
    is_active           =    models.BooleanField(default=True)
    date_of_birth       =    models.DateField(null=True, blank=True)
    is_blocked          =    models.BooleanField(default=False)
    is_staff            =    models.BooleanField(default=False)
    created_at          =    models.DateField(auto_now=False, auto_now_add=True)
    updated_at          =    models.DateTimeField( auto_now=True, auto_now_add=False)
    objects             =    CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def _str_(self):
        return self.email
