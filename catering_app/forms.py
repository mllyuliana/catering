from django import forms
from .models import Order, OrderItem, OrderService, MenuItem, AdditionalService, CartItem, CartService, User, Worker, OrderAssignment, WorkerSchedule
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'event_date', 'start_time', 'end_time',
            'event_type', 'guests_count',
            'contact_name', 'contact_phone', 'contact_email',
            'special_requests'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'special_requests': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class OrderServiceForm(forms.ModelForm):
    class Meta:
        model = OrderService
        fields = ['service', 'quantity']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    is_worker = forms.BooleanField(required=False, label='Я работник')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'address', 'is_worker')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        if commit:
            user.save()
        return user

class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'address', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']
        
        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Этот email уже используется другим пользователем')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Это имя пользователя уже занято')
        return username

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity', 'special_requests']
        widgets = {
            'special_requests': forms.Textarea(attrs={'rows': 2})
        }

class CartServiceForm(forms.ModelForm):
    class Meta:
        model = CartService
        fields = ['quantity', 'special_requests']
        widgets = {
            'special_requests': forms.Textarea(attrs={'rows': 2})
        }

class CartUpdateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        cart = kwargs.pop('cart', None)
        super(CartUpdateForm, self).__init__(*args, **kwargs)
        
        if cart:
            self.fields['items'] = forms.ModelMultipleChoiceField(
                queryset=cart.items.all(),
                required=False,
                widget=forms.CheckboxSelectMultiple
            )
            self.fields['services'] = forms.ModelMultipleChoiceField(
                queryset=cart.services.all(),
                required=False,
                widget=forms.CheckboxSelectMultiple
            )

class OrderAssignmentForm(forms.ModelForm):
    class Meta:
        model = OrderAssignment
        fields = ['worker', 'role', 'is_lead']
        widgets = {
            'role': forms.TextInput(attrs={'placeholder': 'Например: Повар, Официант'})
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order', None)
        super(OrderAssignmentForm, self).__init__(*args, **kwargs)
        
        if order:
            # Фильтруем только доступных работников
            self.fields['worker'].queryset = Worker.objects.filter(
                is_available=True
            ).exclude(
                orders=order  # Исключаем уже назначенных работников
            ) 

class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['position', 'experience', 'specialization', 'photo', 'description', 'working_hours']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'working_hours': forms.TextInput(attrs={'placeholder': 'Например: Пн-Пт 9:00-18:00'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class WorkerScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkerSchedule
        fields = ['date', 'start_time', 'end_time', 'is_available', 'order', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        worker = kwargs.pop('worker', None)
        super().__init__(*args, **kwargs)
        
        if worker:
            self.fields['order'].queryset = Order.objects.filter(
                status__in=['new', 'confirmed']
            )
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class CalculatorForm(forms.Form):
    guests_count = forms.IntegerField(
        min_value=1,
        max_value=1000,
        label='Количество гостей',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    event_type = forms.ChoiceField(
        choices=[
            ('wedding', 'Свадьба'),
            ('corporate', 'Корпоратив'),
            ('birthday', 'День рождения'),
            ('other', 'Другое')
        ],
        label='Тип мероприятия',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    service_level = forms.ChoiceField(
        choices=[
            ('basic', 'Базовый'),
            ('premium', 'Премиум'),
            ('luxury', 'Люкс')
        ],
        label='Уровень обслуживания',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    additional_services = forms.MultipleChoiceField(
        choices=[
            ('decoration', 'Оформление'),
            ('furniture', 'Аренда мебели'),
            ('staff', 'Дополнительный персонал'),
            ('entertainment', 'Развлекательная программа')
        ],
        label='Дополнительные услуги',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    ) 

class EventDateTimeForm(forms.Form):
    event_date = forms.DateField(
        label='Дата мероприятия',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'x-data': '{}',
            'x-init': 'flatpickr($el, {locale: "ru", minDate: "today"})'
        })
    )
    start_time = forms.TimeField(
        label='Время начала',
        widget=forms.TimeInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'x-data': '{}',
            'x-init': 'flatpickr($el, {enableTime: true, noCalendar: true, dateFormat: "H:i", time_24hr: true, minTime: "09:00", maxTime: "23:00"})'
        })
    )
    end_time = forms.TimeField(
        label='Время окончания',
        widget=forms.TimeInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'x-data': '{}',
            'x-init': 'flatpickr($el, {enableTime: true, noCalendar: true, dateFormat: "H:i", time_24hr: true, minTime: "09:00", maxTime: "23:00"})'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if event_date and start_time and end_time:
            start_datetime = datetime.combine(event_date, start_time)
            end_datetime = datetime.combine(event_date, end_time)

            if start_datetime >= end_datetime:
                raise forms.ValidationError('Время окончания должно быть позже времени начала')

            if start_datetime < timezone.now():
                raise forms.ValidationError('Нельзя выбрать прошедшую дату и время')

        return cleaned_data

class EventFormatForm(forms.Form):
    FORMAT_CHOICES = [
        ('buffet', 'Фуршет'),
        ('banquet', 'Банкет'),
        ('coffee', 'Кофе-брейк'),
        ('bar', 'Бар')
    ]

    format = forms.ChoiceField(
        label='Формат мероприятия',
        choices=FORMAT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'format-options',
            'x-data': '{}',
            'x-on:change': '$dispatch("format-changed", $event.target.value)'
        })
    )
    guests_count = forms.IntegerField(
        label='Количество гостей',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите количество гостей'
        })
    )

class MenuForm(forms.Form):
    MENU_CHOICES = [
        ('standard', 'Стандартное меню'),
        ('premium', 'Премиум меню'),
        ('vegetarian', 'Вегетарианское меню'),
        ('business', 'Бизнес-ланч')
    ]

    menu = forms.ChoiceField(
        label='Меню',
        choices=MENU_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'menu-options',
            'x-data': '{}',
            'x-on:change': '$dispatch("menu-changed", $event.target.value)'
        })
    )

class AdditionalServicesForm(forms.Form):
    SERVICES_CHOICES = [
        ('decoration', 'Оформление'),
        ('music', 'Музыка'),
        ('photo', 'Фото и видео'),
        ('transport', 'Транспорт')
    ]

    services = forms.MultipleChoiceField(
        label='Дополнительные услуги',
        choices=SERVICES_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'service-options',
            'x-data': '{}',
            'x-on:change': '$dispatch("services-changed", $event.target.value)'
        })
    )