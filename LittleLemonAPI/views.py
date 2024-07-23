from decimal import Decimal 

from django.utils import timezone
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group

from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED
)
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


from .serializers import (
    UserSerializer, MenuItemSerializer, CartSerializer,
    OrderSerializer, OrderItemSerializer
)
from .models import (
    MenuItem, Cart, Order, 
    OrderItem
)
from LittleLemon.settings import (
    CUSTOMER_GROUP, DELIVERY_CREW_GROUP, MANAGER_GROUP
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def menu_items_view(request):
        
    if request.method == 'GET':
        serializer = MenuItemSerializer(MenuItem.objects.select_related('category').all(), many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    

    elif request.method == 'POST':
        if request.user.groups.filter(Q(name=CUSTOMER_GROUP) | Q(name=DELIVERY_CREW_GROUP)):
            return Response(status=HTTP_401_UNAUTHORIZED)
        
        serializer = MenuItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_menu_item_view(request, pk):

    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and request.user.groups.filter(Q(name=DELIVERY_CREW_GROUP) | Q(name=CUSTOMER_GROUP)).exists():
        return Response(status=HTTP_401_UNAUTHORIZED)


    menu_item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'GET':
        return Response(MenuItemSerializer(menu_item).data, status=HTTP_200_OK)
    
    elif request.method == 'DELETE':
        menu_item.delete()
        return Response(status=HTTP_200_OK)
    
    if request.method == 'PUT':
        serializer = MenuItemSerializer(menu_item, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)
    
    else:
        return Response(status=HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def groups_manager_users_view(request):

    if not request.user.groups.filter(name=MANAGER_GROUP).exists():
        return Response(status=HTTP_401_UNAUTHORIZED)
    

    if request.method == 'GET':
        users = User.objects.filter(Q(groups__name=MANAGER_GROUP))
        return Response(UserSerializer(users, many=True).data, status=HTTP_200_OK)

    elif request.method == 'POST':

        username = request.data.get('username')
        if username is not None:
            user = get_object_or_404(User, username=username)
            user.groups.add(Group.objects.get(name=MANAGER_GROUP))
            return Response(status=HTTP_201_CREATED)
        return Response(status=HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_manager_group_view(request, username):

    if not request.user.groups.filter(name=MANAGER_GROUP):
        return Response(status=HTTP_403_FORBIDDEN)
    
    user  = get_object_or_404(User, username=username)
    user.groups.remove(Group.objects.get(name=MANAGER_GROUP))
    return Response(status=HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def groups_manager_delivery_crew_users_view(request):
    
    if not request.user.groups.filter(name=MANAGER_GROUP).exists():
        return Response(status=HTTP_401_UNAUTHORIZED)


    if request.method == 'GET':

        users = User.objects.filter(Q(groups__name=DELIVERY_CREW_GROUP))
        return Response(UserSerializer(users, many=True).data, status=HTTP_200_OK)

    elif request.method == 'POST':
        username = request.data.get('username')

        if username is not None:
            user = get_object_or_404(User, username=username)
            user.groups.add(Group.objects.get(name=DELIVERY_CREW_GROUP))
            return Response(status=HTTP_201_CREATED)
        return Response(status=HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_delivery_crew_group_view(request, username):

    if not request.user.groups.filter(name=MANAGER_GROUP):
        return Response(status=HTTP_401_UNAUTHORIZED)
    
    user  = get_object_or_404(User, username=username)
    user.groups.remove(Group.objects.get(name=DELIVERY_CREW_GROUP))
    return Response(status=HTTP_200_OK)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_menu_items_view(request):

    if not request.user.groups.filter(name=CUSTOMER_GROUP).exists():
        return Response(status=HTTP_401_UNAUTHORIZED)

    items = Cart.objects.filter(user=request.user)

    if request.method == 'GET':
        return Response(CartSerializer(items, many=True).data, status=HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)
             
    elif request.method == 'DELETE':
        items.delete()
        return Response(status=HTTP_200_OK)
    

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders_view(request):

    if request.method == 'GET':

        orders = Order.objects.none()

        if request.user.groups.filter(name=MANAGER_GROUP).exists():
            orders = Order.objects.all()
        else:    
            orders = Order.objects.filter(delivery_crew=request.user) if request.user.groups.filter(name=DELIVERY_CREW_GROUP).exists() else Order.objects.filter(user=request.user)
        
        order_serializer = OrderSerializer(orders, many=True)

        for order in order_serializer.data:
            items_serializer = OrderItemSerializer(OrderItem.objects.filter(order__id=order['id']), many=True)
            order['items'] = items_serializer.data
        return Response(order_serializer.data, status=HTTP_200_OK)
    
    elif request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        
        if len(cart_items) > 0:
            
            total = cart_items.aggregate(Sum('price', default=Decimal(0)))['price__sum']
            order = Order.objects.create(
                user=request.user,
                total=total,
                date=timezone.now().date(),
            )
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    price=cart_item.price,
                )
            cart_items.delete()
            return Response(status=HTTP_201_CREATED)
        
        return Response(status=HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_order_view(request, order_id):

    order = get_object_or_404(Order, pk=order_id)

    if request.method == 'GET':
        
        if request.user != order.user:
            return Response(status=HTTP_403_FORBIDDEN)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=HTTP_200_OK)
    
    elif request.method == 'PUT':
        if request.user.groups.filter(name=MANAGER_GROUP).exists():

            serializer = OrderSerializer(order, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=HTTP_200_OK)
       
        return Response(status=HTTP_403_FORBIDDEN)
        
    elif request.method == 'PATCH':

        if request.user.groups.filter(Q(name=MANAGER_GROUP) | Q(name=DELIVERY_CREW_GROUP)).exists():
            serializer = OrderSerializer(order, data=request.data, partial=True)

            if serializer.is_valid() and ('status' in request.data) and len(request.data.keys()) == 1:
                serializer.save()
                return Response(serializer.data, status=HTTP_200_OK)
            
            return Response(status=HTTP_400_BAD_REQUEST)
        
        return Response(status=HTTP_403_FORBIDDEN)

    elif request.method == 'DELETE' and request.user.groups.filter(name=MANAGER_GROUP).exists():
        order.delete()
        return Response(status=HTTP_200_OK)
