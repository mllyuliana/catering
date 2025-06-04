from django.contrib import admin
from .models import Order, OrderItem, OrderService, Cart, CartItem, CartService
from django.utils.html import format_html
from .views import send_order_confirmation_email

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderServiceInline(admin.TabularInline):
    model = OrderService
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event_date', 'guests_count', 'status', 'created_at')
    list_filter = ('status', 'event_date')
    search_fields = ('id', 'user__username', 'contact_name', 'contact_phone', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
    inlines = [OrderItemInline, OrderServiceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'event_date', 'start_time', 'end_time', 'menu_type', 'guests_count')
        }),
        ('Контактная информация', {
            'fields': ('contact_name', 'contact_phone', 'contact_email')
        }),
        ('Дополнительно', {
            'fields': ('special_requests', 'status', 'admin_comment')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_price(self, obj):
        """Отображает итоговую стоимость заказа"""
        return f"{obj.calculate_total_price()} BYN"
    total_price.short_description = 'Итоговая стоимость'
    
    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            return [field for field in list_display if field != 'status']
        return list_display

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status and obj.status == 'confirmed':
                send_order_confirmation_email(obj)
        elif obj.status == 'confirmed':
            send_order_confirmation_email(obj)
        super().save_model(request, obj, form, change)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'menu_item', 'quantity', 'price')
    list_filter = ('menu_item',)
    search_fields = ('cart__user__username', 'menu_item__name')

@admin.register(CartService)
class CartServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'service', 'quantity', 'price')
    list_filter = ('service',)
    search_fields = ('cart__user__username', 'service__name')
