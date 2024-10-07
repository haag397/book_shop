from django.contrib import admin
from .models import UserData, PurchaseBook, BookData, Category

admin.site.register(UserData)
admin.site.register(PurchaseBook)
admin.site.register(BookData)
admin.site.register(Category)
