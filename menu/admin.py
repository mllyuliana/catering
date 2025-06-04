from django.contrib import admin
from .models import Category, MenuItem, MenuType, AdditionalService

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'preparation_time')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description', 'ingredients')

@admin.register(MenuType)
class MenuTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price_per_guest', 'is_available')
    list_editable = ('price_per_guest', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'description', 'composition')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price_per_guest', 'is_available', 'image')
        }),
        ('Состав меню', {
            'fields': ('composition',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'price_type', 'is_available')
    list_editable = ('price', 'price_type', 'is_available')
    list_filter = ('is_available', 'price_type')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price', 'price_type', 'is_available')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at') 