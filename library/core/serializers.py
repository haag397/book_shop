"""serializer for users
"""
from rest_framework import serializers

from .models import UserData, BookData, PurchaseBook, Category

class UserDataSerializer(serializers.ModelSerializer):
    """serializer for UserData"""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, max_length=100)
    
    class Meta:
        model = UserData
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password',
                  'date_joined', 'last_edit', 'normal_user', 'purchased_books']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def create(self, validated_data):
            password = validated_data.pop('password')  
            user = UserData(**validated_data) 
            user.set_password(password)  
            user.save()  
            return user

class BookDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookData
        fields = ['id', 'book_name', 'author_name', 'book_amount', 'price','file','category','public']


class PurchaseBookSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()  
    book = serializers.StringRelatedField()  
    class Meta:
        model = PurchaseBook
        fields = ['id', 'user', 'book', 'purchase_date', 'quantity']
        read_only_fields = ['id', 'purchase_date']  

class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ['id', 'name']