from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from menu.models import MenuItem, AdditionalService, MenuType
import json
from datetime import datetime

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
        ('pending', 'Ожидает подтверждения')
    ]

    FORMAT_CHOICES = [
        ('buffet', 'Фуршет'),
        ('banquet', 'Банкет'),
        ('coffee', 'Кофе-брейк'),
        ('bar', 'Бар')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    event_date = models.DateField(default=timezone.now)
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    event_type = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='buffet')
    menu_type = models.ForeignKey(MenuType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Формат меню')
    guests_count = models.IntegerField(default=1)
    contact_name = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_comment = models.TextField(blank=True)
    event_address = models.CharField(max_length=255, verbose_name='Адрес мероприятия')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.id} - {self.event_date}'

    def get_format_display(self):
        return dict(self.FORMAT_CHOICES).get(self.event_type, self.event_type)

    def calculate_total_price(self):
        total = 0
        # Стоимость меню
        if self.menu_type:
            total += self.menu_type.price_per_guest * self.guests_count
        
        # Суммируем стоимость всех блюд
        for item in self.items.all():
            total += item.price * item.quantity
        
        # Суммируем стоимость всех услуг
        for service in self.order_services.all():
            total += service.price * service.quantity
        
        return total

    def get_total_cost(self):
        """Рассчитывает общую стоимость заказа"""
        total = 0
        
        # Стоимость меню
        if self.menu_type:
            total += self.menu_type.price_per_guest * self.guests_count
        
        # Стоимость дополнительных услуг
        for service in self.order_services.all():
            total += service.price
        
        return total

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ', null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name='Блюдо', null=True, blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    special_requests = models.TextField(blank=True, verbose_name='Особые пожелания')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        if self.menu_item:
            return f'{self.menu_item.name} x {self.quantity}'
        return f'Позиция заказа #{self.id}'

class OrderService(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_services', null=True, blank=True)
    service = models.ForeignKey(AdditionalService, on_delete=models.CASCADE, verbose_name='Услуга', null=True, blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    special_requests = models.TextField(blank=True, verbose_name='Особые пожелания')

    class Meta:
        verbose_name = 'Услуга заказа'
        verbose_name_plural = 'Услуги заказа'

    def __str__(self):
        if self.service:
            return f'{self.service.name} x {self.quantity}'
        return f'Услуга заказа #{self.id}'

class AdditionalService(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название услуги')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Дополнительная услуга'
        verbose_name_plural = 'Дополнительные услуги'

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_('Пользователь'), related_name='carts', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активна'))

    class Meta:
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')
        ordering = ['-created_at']

    def __str__(self):
        return f'Корзина пользователя {self.user.username if self.user else "Неизвестный"}'

    @property
    def total_items_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_services_price(self):
        return sum(service.total_price for service in self.services.all())

    @property
    def total_price(self):
        return self.total_items_price + self.total_services_price

    def update_services_prices(self):
        """Обновляет цены всех услуг в корзине"""
        for service in self.services.all():
            if service.service.price_type == 'per_guest':
                # Получаем количество гостей из сессии
                event_data = self.user.session.get('order_step_1', {})
                if isinstance(event_data, str):
                    event_data = json.loads(event_data)
                guests_count = event_data.get('guests_count', 1)
                service.price = service.service.price * guests_count
            elif service.service.price_type == 'per_hour':
                # Получаем время начала и окончания из сессии
                event_data = self.user.session.get('order_step_1', {})
                if isinstance(event_data, str):
                    event_data = json.loads(event_data)
                start_time = event_data.get('start_time')
                end_time = event_data.get('end_time')
                if start_time and end_time:
                    start = datetime.strptime(start_time, '%H:%M')
                    end = datetime.strptime(end_time, '%H:%M')
                    hours = (end - start).total_seconds() / 3600
                    service.price = service.service.price * hours
            else:  # per_event
                service.price = service.service.price
            service.save()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name=_('Корзина'), related_name='items', null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name=_('Блюдо'), null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name=_('Количество'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Цена'))
    special_requests = models.TextField(blank=True, verbose_name=_('Особые пожелания'))

    class Meta:
        verbose_name = _('Позиция корзины')
        verbose_name_plural = _('Позиции корзины')
        unique_together = ['cart', 'menu_item']

    def __str__(self):
        if self.menu_item:
            return f'{self.menu_item.name} x {self.quantity}'
        return f'Позиция корзины #{self.id}'

    @property
    def total_price(self):
        return self.price * self.quantity

class CartService(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name=_('Корзина'), related_name='services', null=True, blank=True)
    service = models.ForeignKey(AdditionalService, on_delete=models.CASCADE, verbose_name=_('Услуга'), null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name=_('Количество'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Цена'))
    special_requests = models.TextField(blank=True, verbose_name=_('Особые пожелания'))

    class Meta:
        verbose_name = _('Услуга корзины')
        verbose_name_plural = _('Услуги корзины')
        unique_together = ['cart', 'service']

    def __str__(self):
        if self.service:
            return f'{self.service.name} x {self.quantity}'
        return f'Услуга корзины #{self.id}'

    @property
    def total_price(self):
        return self.price * self.quantity
