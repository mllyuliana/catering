from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

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

class MenuType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price_per_guest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за гостя')
    composition = models.TextField(verbose_name='Состав меню')
    image = models.ImageField(upload_to='menu_types/', null=True, blank=True, verbose_name='Изображение')
    
    class Meta:
        verbose_name = 'Тип меню'
        verbose_name_plural = 'Типы меню'
    
    def __str__(self):
        return self.name

class ContactMessage(models.Model):
    name = models.CharField(_('Имя'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Телефон'), max_length=20)
    message = models.TextField(_('Сообщение'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_read = models.BooleanField(_('Прочитано'), default=False)

    class Meta:
        verbose_name = _('Контактное сообщение')
        verbose_name_plural = _('Контактные сообщения')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.created_at}'
