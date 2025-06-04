from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import MenuItem, AdditionalService, MenuType

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

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ('name', 'category', 'description', 'price', 'image', 'is_available', 
                 'preparation_time', 'calories', 'ingredients')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preparation_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AdditionalServiceForm(forms.ModelForm):
    class Meta:
        model = AdditionalService
        fields = ('name', 'description', 'price', 'is_available')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MenuTypeForm(forms.ModelForm):
    class Meta:
        model = MenuType
        fields = ('name', 'description', 'price_per_guest', 'composition', 'image')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_per_guest': forms.NumberInput(attrs={'class': 'form-control'}),
            'composition': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        } 