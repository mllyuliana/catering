from django import forms
from .models import Order, OrderItem, OrderService, Cart, CartItem, CartService, OrderAssignment
from menu.models import MenuItem, AdditionalService

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('event_date', 'event_time', 'guests_count', 'location', 'notes')
        widgets = {
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'guests_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ('menu_item', 'quantity')
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class OrderServiceForm(forms.ModelForm):
    class Meta:
        model = OrderService
        fields = ('service', 'quantity')
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ('menu_item', 'quantity')
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CartServiceForm(forms.ModelForm):
    class Meta:
        model = CartService
        fields = ('service', 'quantity')
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
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