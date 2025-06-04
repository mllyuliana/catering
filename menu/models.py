from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Название'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name=_('Изображение'))

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('hot', 'Горячие блюда'),
        ('cold', 'Холодные закуски'),
        ('salad', 'Салаты'),
        ('dessert', 'Десерты'),
        ('drink', 'Напитки'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название блюда')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Категория')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='menu_items/', verbose_name='Изображение', blank=True)
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    preparation_time = models.PositiveIntegerField(verbose_name='Время приготовления (мин)', help_text='Примерное время приготовления в минутах')
    calories = models.PositiveIntegerField(null=True, blank=True, verbose_name='Калории')
    ingredients = models.TextField(help_text="Список ингредиентов", verbose_name='Ингредиенты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

    def __str__(self):
        return self.name

class AdditionalService(models.Model):
    PRICE_TYPE_CHOICES = [
        ('per_hour', 'Почасовая оплата'),
        ('per_guest', 'За каждого гостя'),
        ('per_event', 'За все мероприятие'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    price_type = models.CharField(
        max_length=10,
        choices=PRICE_TYPE_CHOICES,
        default='per_hour',
        verbose_name='Тип расчета стоимости'
    )
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Дополнительная услуга'
        verbose_name_plural = 'Дополнительные услуги'

    def __str__(self):
        return self.name

    def calculate_price(self, guests_count=None, hours=None):
        if self.price_type == 'per_guest' and guests_count:
            return self.price * guests_count
        elif self.price_type == 'per_hour' and hours:
            return self.price * hours
        elif self.price_type == 'per_event':
            return self.price
        return self.price

class MenuType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price_per_guest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за гостя')
    composition = models.TextField(verbose_name='Состав меню')
    image = models.ImageField(upload_to='menu_types/', blank=True, null=True, verbose_name='Изображение')
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тип меню'
        verbose_name_plural = 'Типы меню'

    def __str__(self):
        return self.name 