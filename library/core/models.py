"""define all models here
"""
from django.db import models
from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class Category(models.Model):
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=100, default="all")

    def __str__(self):
        return self.name

class BookData(models.Model):
    """
    Book model
    """
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    book_name = models.CharField(max_length=150)
    author_name = models.CharField(max_length=100)
    book_amount = models.IntegerField()
    price = models.FloatField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_books', null=True)
    file = models.FileField(upload_to='books/', null=True)
    public = models.BooleanField(default=True)

    def __str__(self):
        return self.book_name
    
    
class UserDataManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault('normal_user', False)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)    
    
# class UserData(models.Model):
class UserData(AbstractBaseUser, PermissionsMixin):

    """
    User model
    """

    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    password = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=40, unique=True, null=True)
    username = models.CharField(max_length=255,unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_edit = models.DateTimeField(auto_now=True)
    normal_user = models.BooleanField(default=True)
    purchased_books = models.ManyToManyField('BookData', through='PurchaseBook', related_name='purchased_by')
    # is_superuser = models.BooleanField(default=True)  
    is_superuser = models.BooleanField(default=False)

    balance = models.FloatField(default=0.0) 
    
    objects = UserDataManager()

    
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["password", "email", "last_name"]

    def __str__(self):
        return self.username
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    
class PurchaseBook(models.Model):
    """
    purchase book by user
    """
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(UserData, related_name='purchases', on_delete=models.CASCADE)
    book = models.ForeignKey(BookData, related_name='purchases', on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.user.username} bought {self.book.book_name} (Quantity: {self.quantity})"
