import random
import os

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import UserData, BookData, PurchaseBook, Category
from core.serializers import UserDataSerializer, BookDataSerializer, PurchaseBookSerializer, CategorySerializer


class UserDataViewSet(viewsets.ModelViewSet):
    """
    get, create, edit and delete AdminData
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer

    def list(self, request):
        """
        get all AdminData
        """
        admin_serializer = UserDataSerializer(self.queryset, many=True)
        return Response(admin_serializer.data)

    def createt(self, request):
        print("Incoming data:", request.data)
        """
        create single AdminData
        """
        if not request.user.is_superuser:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserDataSerializer(data=request.data)

        if serializer.is_valid():
            serializer.validated_data['request'] = request
            user = serializer.save()  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
    def retrieve(self, request, pk=None):
        """
        get single AdminData by id
        """
        try:
            admin_instance = self.get_object()
            admin_serializer = self.serializer_class(admin_instance)
            return Response(admin_serializer.data)
        except UserData.DoesNotExist:
            return Response(
                {"error": "AdminData not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, pk=None):
        """
        update single AdminData by id
        """
        try:
            admin_instance = self.get_object()
            serializer = self.serializer_class(
                admin_instance, data=request.data, partial=True
            )
            if serializer.is_valid():
                admin = serializer.save()
                # * hash password
                admin.set_password(admin.password)
                admin.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserData.DoesNotExist:
            return Response(
                {"error": "AdminData not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """
        Handles DELETE requests to delete an AdminData instance.
        """
        try:
            admin_instance = self.get_object()
            admin_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserData.DoesNotExist:
            return Response(
                {"error": "AdminData not found."}, status=status.HTTP_404_NOT_FOUND
            )


class UserLoginView(APIView):
    """handle login with JWT"""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        print(f"Attempting to login with Username: {username}")

        # * check username and password
        admin = authenticate(request, username=username, password=password)

        if admin is not None:
            # * Generate JWT tokens
            refresh = RefreshToken.for_user(admin)
            return Response(
                {
                    "refresh_token": str(refresh),
                    "access_token": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        else:
            print(f"Login failed for Username: {username}")
            return Response(
                {"detail": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            
class BookViewSet(viewsets.ModelViewSet):
    queryset = BookData.objects.all()
    serializer_class = BookDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        """
        user = self.request.user
        if user.is_authenticated:
            if user.normal_user:
                # * User has access, return all books
                return BookData.objects.all()
            else:
                # * User does not have access, return only public books (private = False)
                return BookData.objects.filter(public=True)
        else:
            # * If the user is not authenticated, return only public books
            return BookData.objects.filter(public=True)
        
    def validate_file_format(self, file):
        """
        Validate that the uploaded file is a .pdf.
        """
        if file and not file.name.endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed for book uploads.")
        
    def create(self, request, *args, **kwargs):
        """
        book file upload.
        """
        file = request.FILES.get('file', None)
        self.validate_file_format(file)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)         

    def update(self, request, *args, **kwargs):
        """
        book updates
        """
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        file = request.FILES.get('file', None)

        # Validate file format if a file is provided
        if file:
            self.validate_file_format(file)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PurchaseBookView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        book_id = request.data.get('book')
        quantity = request.data.get('quantity', 1)
        
        book = get_object_or_404(BookData, id=book_id)
        
        if not user.normal_user and not book.public:
            return Response({"error": "You are not allowed to purchase this book."}, status=status.HTTP_403_FORBIDDEN)
        
        if PurchaseBook.objects.filter(user=user, book=book).exists():
            return Response({"error": "You have already purchased this book."}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > book.book_amount:
            return Response(
                {"error": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_price = book.price * quantity

        if user.balance < total_price:
            return Response(
                {"error": "Insufficient balance."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if settings.TEST_ENVIRONMENT:
            otp = random.randint(1000, 9999)
            request.session['otp'] = otp
            request.session['otp_used'] = False  # *track OTP 
            return Response(
                {"message": f"OTP code is {otp}. Use this code to complete your purchase."},
                status=status.HTTP_200_OK
            )
        else:
            # * In production
            pass

        return Response(
            {"message": "OTP sent. Use the OTP to complete the transaction."},
            status=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        """Complete the purchase with OTP verification"""
        user = request.user
        book_id = request.data.get('book')
        otp_code = request.data.get('otp_code')
        quantity = request.data.get('quantity', 1)

        book = get_object_or_404(BookData, id=book_id)
        
        if not user.normal_user and not book.public:
            return Response({"error": "You are not allowed to purchase this book."}, status=status.HTTP_403_FORBIDDEN)


        if settings.TEST_ENVIRONMENT:
            if str(request.session.get('otp')) != otp_code:
                return Response({"error": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST)
            
            if request.session.get('otp_used'):
                return Response({"error": "OTP has already been used."}, status=status.HTTP_400_BAD_REQUEST)

            request.session['otp_used'] = True

            
        total_price = book.price * quantity
        if user.balance - total_price < 0:
            return Response({"error": "Insufficient balance. Balance cannot be negative."}, status=status.HTTP_400_BAD_REQUEST)

        user.balance -= total_price
        user.save()
        
        if book.book_amount - quantity < 0:
            return Response(
            {"error": "Not enough books in stock. Stock cannot be negative."},
            status=status.HTTP_400_BAD_REQUEST
            )
        book.book_amount -= quantity
        book.save()

        purchase = PurchaseBook.objects.create(
            user=user,
            book=book,
            quantity=quantity,
        )

        serializer = PurchaseBookSerializer(purchase)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DownloadBookView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id):
        user = request.user
        purchase = PurchaseBook.objects.filter(user=user, book_id=book_id).first()

        if purchase:
            book = purchase.book

            # * Check if the book is public and the user doesn't have access
            if book.private and not user.allow_access:
                return Response(
                    {"error": "You don't have access to download this private book."},
                    status=status.HTTP_403_FORBIDDEN
                )

            file = book.file
            if file:
                return FileResponse(file.open('rb'), content_type='application/pdf')
            else:
                return Response({"error": "Book file not available."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "You haven't purchased this book."}, status=status.HTTP_403_FORBIDDEN)


class CategoryViewSet(viewsets.ModelViewSet):
    """create category
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class BalanceTopUpView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Step 1: Request OTP for balance top-up.
        """
        amount = request.data.get("amount", 0)

        if amount <= 0:
            return Response({"error": "Invalid top-up amount."}, status=status.HTTP_400_BAD_REQUEST)

        if settings.TEST_ENVIRONMENT:
            otp = random.randint(1000, 9999)
            request.session['otp'] = otp
            request.session['otp_used'] = False
            return Response(
                {"message": f"OTP code is {otp}. Use this code to complete your top-up."},
                status=status.HTTP_200_OK
            )
        else:
            # *In production
            pass

        return Response(
            {"message": "OTP sent. Use the OTP to complete the transaction."},
            status=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        """
        Step 2: Confirm OTP and charge balance.
        """
        otp_code = request.data.get("otp_code")
        amount = request.data.get("amount", 0)

        if amount <= 0:
            return Response({"error": "Invalid top-up amount."}, status=status.HTTP_400_BAD_REQUEST)

        if settings.TEST_ENVIRONMENT:
            if str(request.session.get('otp')) != otp_code:
                return Response({"error": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST)

            if request.session.get('otp_used'):
                return Response({"error": "OTP has already been used."}, status=status.HTTP_400_BAD_REQUEST)
            
            request.session['otp_used'] = True
            
        user = request.user
        user.balance += amount
        user.save()

        return Response({"message": f"Balance successfully charged by {amount} units."}, status=status.HTTP_200_OK)

