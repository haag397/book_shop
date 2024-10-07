from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserDataViewSet,
    UserLoginView,
    BookViewSet,
    PurchaseBookView,
    DownloadBookView,
    CategoryViewSet,
    BalanceTopUpView,

)
from rest_framework_simplejwt.views import TokenBlacklistView

router = DefaultRouter()
router.register(r'users', UserDataViewSet, basename='user')
router.register(r'books', BookViewSet, basename='book')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('api/', include(router.urls)), 
    path('api/login/', UserLoginView.as_view(), name='login'),  
    path('api/purchase/', PurchaseBookView.as_view(), name='purchase'),  
    path('api/download/<uuid:book_id>/', DownloadBookView.as_view(), name='download_book'), 
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/topup/', BalanceTopUpView.as_view(), name='balance_topup'),  

]
