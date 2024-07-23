from django.urls import path
from . import views

urlpatterns = [

    path('menu-items', views.menu_items_view),
    path('menu-items/<int:pk>', views.single_menu_item_view),

    path('cart/menu-items', views.cart_menu_items_view),

    path('orders', views.orders_view),

    path('orders/<int:order_id>', views.single_order_view),
]
