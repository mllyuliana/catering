from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Order, OrderItem, OrderService, Cart, CartItem, CartService
from menu.models import MenuItem, AdditionalService, MenuType
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
from django import forms
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from users.models import UserActivity
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = context['orders']
        
        # Подсчет заказов по статусам
        context['total_orders'] = orders.count()
        context['active_orders'] = orders.filter(status='confirmed').count()
        context['completed_orders'] = orders.filter(status='completed').count()
        
        return context

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = 'orders/order_create.html'
    fields = ['event_date', 'start_time', 'end_time', 'guests_count',
              'contact_name', 'contact_phone', 'contact_email', 'special_requests']
    
    def get_success_url(self):
        return reverse_lazy('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Добавляем скрытое поле для формата мероприятия
        form.fields['format'] = forms.CharField(widget=forms.HiddenInput(), required=False)
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем или создаем корзину
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            is_active=True,
            defaults={'is_active': True}
        )
        context['cart'] = cart
        
        # Получаем типы меню и дополнительные услуги
        menu_types = MenuType.objects.all()
        additional_services = AdditionalService.objects.filter(is_available=True)
        
        # Преобразуем в JSON для передачи в шаблон
        menu_types_data = []
        for menu_type in menu_types:
            menu_types_data.append({
                'id': menu_type.id,
                'name': menu_type.name,
                'description': menu_type.description,
                'price_per_guest': float(menu_type.price_per_guest),
                'composition': menu_type.composition.replace('\n', ' ').replace('\r', '') if menu_type.composition else ''
            })
        
        additional_services_data = []
        for service in additional_services:
            additional_services_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description.replace('\n', ' ').replace('\r', '') if service.description else '',
                'price': float(service.price),
                'price_type': service.price_type
            })
        
        context['menu_types'] = json.dumps(menu_types_data, ensure_ascii=False)
        context['additional_services'] = json.dumps(additional_services_data, ensure_ascii=False)
        
        return context
    
    def form_valid(self, form):
        try:
            cart = Cart.objects.filter(user=self.request.user, is_active=True).first()
            if not cart:
                return JsonResponse({
                    'success': False,
                    'error': 'Ваша корзина пуста!'
                }, status=400)
            
            order = form.save(commit=False)
            order.user = self.request.user
            order.event_address = self.request.POST.get('event_address', '')
            # Получаем формат мероприятия из POST данных
            order.event_type = self.request.POST.get('format', 'buffet')
            
            # Получаем тип меню
            menu_type_id = self.request.POST.get('menu_type_id')
            if menu_type_id:
                try:
                    order.menu_type = MenuType.objects.get(id=menu_type_id)
                except MenuType.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Выбранный тип меню не найден'
                    }, status=400)
            
            order.save()
            
            # Перенос товаров из корзины в заказ
            for item in cart.items.all():
                # Пересчитываем цену с учетом количества гостей
                price = item.price
                if order.menu_type and item.menu_item.menu_type == order.menu_type:
                    price = order.menu_type.price_per_guest
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=item.menu_item,
                    quantity=item.quantity,
                    price=price,
                    special_requests=item.special_requests
                )
            
            # Получаем дополнительные услуги из POST данных
            additional_services = self.request.POST.get('additional_services')
            if additional_services:
                try:
                    services_data = json.loads(additional_services)
                    for service_data in services_data:
                        try:
                            service = AdditionalService.objects.get(id=service_data['id'])
                            # Рассчитываем цену в зависимости от типа услуги
                            if service.price_type == 'per_guest':
                                price = service.price * Decimal(str(order.guests_count))
                            elif service.price_type == 'per_hour':
                                # Вычисляем количество часов
                                start = datetime.strptime(str(order.start_time), '%H:%M:%S')
                                end = datetime.strptime(str(order.end_time), '%H:%M:%S')
                                hours = Decimal(str((end - start).total_seconds() / 3600))
                                price = service.price * hours
                            else:  # per_event
                                price = service.price
                            
                            OrderService.objects.create(
                                order=order,
                                service=service,
                                quantity=service_data.get('quantity', 1),
                                price=price
                            )
                        except AdditionalService.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': f'Услуга с ID {service_data["id"]} не найдена'
                            }, status=400)
                        except Exception as e:
                            return JsonResponse({
                                'success': False,
                                'error': f'Ошибка при создании услуги: {str(e)}'
                            }, status=400)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Неверный формат данных дополнительных услуг'
                    }, status=400)
            
            # Очистка корзины
            cart.is_active = False
            cart.save()
            
            messages.success(self.request, 'Заказ успешно создан!')
            
            # Возвращаем JSON с ID заказа
            return JsonResponse({
                'success': True,
                'order_id': order.id
            })
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return JsonResponse({
                'success': False,
                'error': f'Произошла ошибка: {str(e)}\n{error_details}'
            }, status=500)

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_confirmation.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'orders/order_edit.html'
    fields = ['event_date', 'start_time', 'end_time', 'event_type', 'menu_type', 'guests_count',
              'contact_name', 'contact_phone', 'contact_email', 'special_requests', 'event_address']
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, status__in=['new', 'pending'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_types'] = MenuType.objects.all()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Заказ успешно обновлен!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orders:order_list')

class OrderCancelView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'orders/order_cancel.html'
    fields = []
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, status__in=['new', 'pending'])
    
    def form_valid(self, form):
        order = form.save(commit=False)
        order.status = 'cancelled'
        order.save()
        messages.success(self.request, 'Заказ успешно отменен!')
        return redirect('orders:order_list')

# Cart views
class CartDetailView(LoginRequiredMixin, DetailView):
    model = Cart
    template_name = 'orders/cart_detail.html'
    context_object_name = 'cart'
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user, is_active=True)
        # Обновляем цены услуг при каждом просмотре корзины
        cart.update_services_prices()
        return cart

class CartAddItemView(LoginRequiredMixin, CreateView):
    model = CartItem
    fields = []
    
    def form_valid(self, form):
        cart, created = Cart.objects.get_or_create(user=self.request.user, is_active=True)
        menu_item = get_object_or_404(MenuItem, id=self.kwargs['item_id'], is_available=True)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={'price': menu_item.price}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(self.request, f'{menu_item.name} добавлен в корзину!')
        return redirect('orders:cart_detail')

class CartRemoveItemView(LoginRequiredMixin, DeleteView):
    model = CartItem
    success_url = reverse_lazy('orders:cart_detail')
    
    def get_object(self):
        cart = get_object_or_404(Cart, user=self.request.user, is_active=True)
        return get_object_or_404(CartItem, cart=cart, menu_item_id=self.kwargs['item_id'])
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Товар удален из корзины!')
        return super().delete(request, *args, **kwargs)

class CartAddServiceView(LoginRequiredMixin, CreateView):
    model = CartService
    fields = []
    
    def form_valid(self, form):
        cart, created = Cart.objects.get_or_create(user=self.request.user, is_active=True)
        service = get_object_or_404(AdditionalService, id=self.kwargs['service_id'], is_available=True)
        
        # Получаем данные о мероприятии из сессии
        event_data = self.request.session.get('order_step_1', {})
        if isinstance(event_data, str):
            event_data = json.loads(event_data)
        
        guests_count = event_data.get('guests_count', 1)
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        
        # Рассчитываем цену в зависимости от типа услуги
        if service.price_type == 'per_guest':
            price = service.price * guests_count
        elif service.price_type == 'per_hour' and start_time and end_time:
            # Вычисляем количество часов
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            hours = (end - start).total_seconds() / 3600
            price = service.price * hours
        else:  # per_event
            price = service.price
        
        cart_service, created = CartService.objects.get_or_create(
            cart=cart,
            service=service,
            defaults={
                'price': price,
                'quantity': 1
            }
        )
        
        if not created:
            cart_service.quantity += 1
            cart_service.price = price  # Обновляем цену при каждом добавлении
            cart_service.save()
        
        messages.success(self.request, f'{service.name} добавлена в корзину!')
        return redirect('orders:cart_detail')

class CartRemoveServiceView(LoginRequiredMixin, DeleteView):
    model = CartService
    success_url = reverse_lazy('orders:cart_detail')
    
    def get_object(self):
        cart = get_object_or_404(Cart, user=self.request.user, is_active=True)
        return get_object_or_404(CartService, cart=cart, service_id=self.kwargs['service_id'])
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Услуга удалена из корзины!')
        return super().delete(request, *args, **kwargs)

class CartClearView(LoginRequiredMixin, DeleteView):
    model = Cart
    success_url = reverse_lazy('orders:cart_detail')
    
    def get_object(self):
        return get_object_or_404(Cart, user=self.request.user, is_active=True)
    
    def delete(self, request, *args, **kwargs):
        cart = self.get_object()
        cart.items.all().delete()
        cart.services.all().delete()
        messages.success(request, 'Корзина очищена!')
        return redirect(self.success_url)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    items = order.items.all()
    services = order.order_services.all()
    
    # Записываем активность пользователя
    UserActivity.objects.create(
        user=request.user,
        description=f'Просмотр заказа #{order.id}'
    )
    
    return render(request, 'orders/order_confirmation.html', {
        'order': order,
        'items': items,
        'services': services
    })

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    items = cart.items.all()
    services = cart.services.all()
    
    total_items_price = sum(item.total_price for item in items)
    total_services_price = sum(service.total_price for service in services)
    total_price = total_items_price + total_services_price
    
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'items': items,
        'services': services,
        'total_items_price': total_items_price,
        'total_services_price': total_services_price,
        'total_price': total_price
    })

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_type = data.get('type')
        item_id = data.get('id')
        quantity = int(data.get('quantity', 1))
        
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        
        if item_type == 'menu_item':
            menu_item = get_object_or_404(MenuItem, id=item_id)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                menu_item=menu_item,
                defaults={'quantity': quantity, 'price': menu_item.price}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
        elif item_type == 'service':
            service = get_object_or_404(AdditionalService, id=item_id)
            cart_service, created = CartService.objects.get_or_create(
                cart=cart,
                service=service,
                defaults={'quantity': quantity, 'price': service.price}
            )
            if not created:
                cart_service.quantity += quantity
                cart_service.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_type = data.get('type')
        item_id = data.get('id')
        
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        if item_type == 'menu_item':
            CartItem.objects.filter(cart=cart, menu_item_id=item_id).delete()
        elif item_type == 'service':
            CartService.objects.filter(cart=cart, service_id=item_id).delete()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_type = data.get('type')
        item_id = data.get('id')
        quantity = int(data.get('quantity', 1))
        
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        
        if item_type == 'menu_item':
            cart_item = get_object_or_404(CartItem, cart=cart, menu_item_id=item_id)
            cart_item.quantity = quantity
            cart_item.save()
        elif item_type == 'service':
            cart_service = get_object_or_404(CartService, cart=cart, service_id=item_id)
            cart_service.quantity = quantity
            cart_service.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    
    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            event_date=request.POST.get('event_date'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            event_type=request.POST.get('event_type'),
            guests_count=request.POST.get('guests_count'),
            contact_name=request.POST.get('contact_name'),
            contact_phone=request.POST.get('contact_phone'),
            contact_email=request.POST.get('contact_email'),
            special_requests=request.POST.get('special_requests', ''),
            status='pending'
        )
        
        # Получаем тип меню
        menu_type_id = request.POST.get('menu_type_id')
        if menu_type_id:
            try:
                order.menu_type = MenuType.objects.get(id=menu_type_id)
                order.save()
            except MenuType.DoesNotExist:
                pass
        
        # Переносим товары из корзины в заказ
        for cart_item in cart.items.all():
            # Пересчитываем цену с учетом количества гостей
            price = cart_item.price
            if order.menu_type and cart_item.menu_item.menu_type == order.menu_type:
                price = order.menu_type.price_per_guest
            
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                price=price,
                special_requests=cart_item.special_requests
            )
        
        # Переносим услуги из корзины в заказ
        for cart_service in cart.services.all():
            # Рассчитываем цену в зависимости от типа услуги
            if cart_service.service.price_type == 'per_guest':
                price = cart_service.service.price * Decimal(str(order.guests_count))
            elif cart_service.service.price_type == 'per_hour':
                # Вычисляем количество часов
                start = datetime.strptime(str(order.start_time), '%H:%M:%S')
                end = datetime.strptime(str(order.end_time), '%H:%M:%S')
                hours = Decimal(str((end - start).total_seconds() / 3600))
                price = cart_service.service.price * hours
            else:  # per_event
                price = cart_service.service.price
            
            OrderService.objects.create(
                order=order,
                service=cart_service.service,
                quantity=cart_service.quantity,
                price=price,
                special_requests=cart_service.special_requests
            )
        
        # Деактивируем корзину
        cart.is_active = False
        cart.save()
        
        # Создаем новую активную корзину
        Cart.objects.create(user=request.user, is_active=True)
        
        # Записываем активность пользователя
        UserActivity.objects.create(
            user=request.user,
            description=f'Создан новый заказ #{order.id}'
        )
        
        messages.success(request, 'Заказ успешно создан!')
        return redirect('order_detail', pk=order.id)
    
    return render(request, 'orders/checkout.html', {'cart': cart})

class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = 'orders/order_confirm_delete.html'
    success_url = reverse_lazy('orders:order_list')
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.object
        return context
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Заказ успешно удален!')
        return response

def send_order_confirmation_email(order):
    """Отправка email при подтверждении заказа"""
    subject = f'Заказ #{order.id} подтвержден'
    html_message = render_to_string('orders/email/order_confirmed.html', {'order': order})
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    to_email = order.user.email
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=[to_email],
        html_message=html_message,
        fail_silently=False,
    )

@require_POST
@login_required
def update_order_status(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        order = Order.objects.get(id=order_id)
        new_status = request.POST.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        order.status = new_status
        order.save()
        
        # Отправляем email только при подтверждении заказа
        if new_status == 'confirmed':
            send_order_confirmation_email(order)
        
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
