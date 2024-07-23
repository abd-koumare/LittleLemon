from rest_framework import serializers
from rest_framework import validators
from .models import User, Category, MenuItem, Cart, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
        read_only_fields = ['id']

class MenuItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']
        read_only_fields = ['id']

class CartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['id', 'user', 'unit_price', 'price']


    def validate(self, data):
        
        user = self.context['request'].user
        menuitem = data.get('menuitem')
        
        if user and menuitem and Cart.objects.filter(user=user, menuitem=menuitem).exists():
            raise serializers.ValidationError("You already have this item in your cart.")
        
        return data

    def create(self, validated_data):

        user = self.context['request'].user 
        validated_data['user'] = user
        validated_data['unit_price'] = validated_data['menuitem'].price
        validated_data['price'] = validated_data['menuitem'].price * validated_data['quantity']
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']
        read_only_fields = ['id', 'user', 'total', 'date']


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price'] 
        read_only_fields = ['id']