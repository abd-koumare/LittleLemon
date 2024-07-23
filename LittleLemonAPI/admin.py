from django.contrib import admin
from .models import Category, MenuItem, Order, Cart, OrderItem


admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
