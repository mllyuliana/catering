from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from .models import Category, MenuItem, AdditionalService, Order, OrderItem, OrderService, User, Cart, CartItem, CartService, Worker, OrderAssignment, WorkerSchedule, MenuType
from .forms import OrderForm, UserRegistrationForm, UserProfileForm, CartItemForm, CartServiceForm, CartUpdateForm, WorkerProfileForm, OrderAssignmentForm, WorkerScheduleForm, CalculatorForm, EventDateTimeForm, EventFormatForm, MenuForm, AdditionalServicesForm
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth import authenticate, login, logout
from formtools.wizard.views import SessionWizardView
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

def home(request):
    return render(request, 'catering_app/home.html')

def menu(request):
    return render(request, 'catering_app/menu.html')

def services(request):
    return render(request, 'catering_app/services.html')

def contacts(request):
    return render(request, 'catering_app/contacts.html')

def gallery(request):
    return render(request, 'catering_app/gallery.html')

def about(request):
    return render(request, 'catering_app/about.html')

def calculator(request):
    return render(request, 'catering_app/calculator.html')

def order(request):
    # Получаем сохраненные данные из сессии
    context = {
        'event_date': request.session.get('event_date', ''),
        'start_time': request.session.get('start_time', ''),
        'end_time': request.session.get('end_time', ''),
        'event_types': request.session.get('event_types', []),
        'guests_count': request.session.get('guests_count', ''),
        'selected_services': request.session.get('selected_services', []),
        'selected_menu': request.session.get('selected_menu', '')
    }
    return render(request, 'catering_app/order.html', context)

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'catering_app/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Профиль успешно обновлен')
            return response
        except Exception as e:
            messages.error(self.request, f'Ошибка при обновлении профиля: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        return context

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Неверное имя пользователя или пароль'})
    
    return render(request, 'catering_app/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            return JsonResponse({'success': False, 'error': 'Пароли не совпадают'})
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Пользователь с таким именем уже существует'})
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Пользователь с таким email уже существует'})
        
        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return JsonResponse({'success': True})
    
    return render(request, 'catering_app/register.html')

def about_view(request):
    return render(request, 'catering_app/about.html')

class MenuView(ListView):
    model = MenuItem
    template_name = 'catering_app/menu.html'
    context_object_name = 'menu_items'
    paginate_by = 6

    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        sort = self.request.GET.get('sort')

        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MenuItem.CATEGORY_CHOICES
        context['selected_category'] = self.request.GET.get('category')
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_order'] = self.request.GET.get('sort')
        return context

class ServicesView(ListView):
    model = AdditionalService
    template_name = 'catering_app/services.html'
    context_object_name = 'services'

    def get_queryset(self):
        return AdditionalService.objects.filter(is_available=True)

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'catering_app/order.html'
    success_url = reverse_lazy('order_success')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        order = form.save(commit=False)
        order.user = self.request.user
        order.save()
        
        # Сохраняем блюда заказа
        for item in self.request.session.get('cart', []):
            menu_item = MenuItem.objects.get(id=item['id'])
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item['quantity'],
                price=menu_item.price
            )
        
        # Сохраняем дополнительные услуги
        for service in self.request.session.get('services', []):
            additional_service = AdditionalService.objects.get(id=service['id'])
            OrderService.objects.create(
                order=order,
                service=additional_service,
                quantity=service['quantity'],
                price=additional_service.price
            )
        
        # Очищаем корзину
        self.request.session['cart'] = []
        self.request.session['services'] = []
        
        messages.success(self.request, 'Ваш заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.request.session.get('cart', [])
        context['services'] = self.request.session.get('services', [])
        return context

def order_success(request):
    return render(request, 'catering_app/order_success.html')

class UserLoginView(LoginView):
    template_name = 'catering_app/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        try:
            # Проверяем, является ли пользователь работником
            worker_profile = self.request.user.worker_profile
            return reverse_lazy('worker_detail', kwargs={'pk': worker_profile.pk})
        except Worker.DoesNotExist:
            # Если пользователь является администратором, перенаправляем в админ-панель
            if self.request.user.is_staff:
                return reverse_lazy('admin:index')
            # Для обычных пользователей - на профиль
            return reverse_lazy('profile')

class UserLogoutView(LogoutView):
    next_page = 'home'

class UserRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'catering_app/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        
        # Если пользователь отметил "Я работник", создаем профиль работника
        if form.cleaned_data.get('is_worker'):
            Worker.objects.create(
                user=user,
                position='Новый работник',  # Значения по умолчанию
                experience=0,
                specialization='Не указано',
                working_hours='Не указано',
                description='Новый работник'
            )
            messages.success(self.request, 'Регистрация успешно завершена! Профиль работника создан. Теперь вы можете войти в систему.')
        else:
            messages.success(self.request, 'Регистрация успешно завершена! Теперь вы можете войти в систему.')
        
        return response

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'catering_app/orders.html', {'orders': user_orders})

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    cart_items = cart.items.all()
    cart_services = cart.services.all()
    
    if request.method == 'POST':
        form = CartUpdateForm(request.POST, cart=cart)
        if form.is_valid():
            # Удаляем отмеченные элементы
            items_to_delete = form.cleaned_data['items']
            services_to_delete = form.cleaned_data['services']
            items_to_delete.delete()
            services_to_delete.delete()
            messages.success(request, 'Корзина обновлена')
            return redirect('cart')
    else:
        form = CartUpdateForm(cart=cart)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_services': cart_services,
        'form': form,
    }
    return render(request, 'catering_app/cart.html', context)

@login_required
def add_to_cart(request, item_type, item_id):
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    if item_type == 'menu':
        item = get_object_or_404(MenuItem, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=item,
            defaults={'price': item.price}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        service = get_object_or_404(AdditionalService, id=item_id)
        cart_service, created = CartService.objects.get_or_create(
            cart=cart,
            service=service,
            defaults={'price': service.price}
        )
        if not created:
            cart_service.quantity += 1
            cart_service.save()

    messages.success(request, 'Товар добавлен в корзину')
    return redirect('menu')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        form = CartItemForm(request.POST, instance=cart_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Количество обновлено')
    return redirect('cart')

@login_required
def update_cart_service(request, service_id):
    cart_service = get_object_or_404(CartService, id=service_id, cart__user=request.user)
    if request.method == 'POST':
        form = CartServiceForm(request.POST, instance=cart_service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Количество обновлено')
    return redirect('cart')

@login_required
def remove_from_cart(request, item_type, item_id):
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    if item_type == 'menu':
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
    else:
        item = get_object_or_404(CartService, id=item_id, cart=cart)
    item.delete()
    messages.success(request, 'Товар удален из корзины')
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                order.items.create(
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    special_requests=cart_item.special_requests
                )
            
            for cart_service in cart.services.all():
                order.services.create(
                    service=cart_service.service,
                    quantity=cart_service.quantity,
                    price=cart_service.price,
                    special_requests=cart_service.special_requests
                )
            
            # Деактивируем корзину
            cart.is_active = False
            cart.save()
            
            messages.success(request, 'Заказ успешно оформлен')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(initial={
            'contact_phone': request.user.phone,
            'contact_email': request.user.email,
            'address': request.user.address
        })
    
    context = {
        'cart': cart,
        'form': form
    }
    return render(request, 'catering_app/checkout.html', context)

class WorkerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Worker
    template_name = 'catering_app/worker_list.html'
    context_object_name = 'workers'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = Worker.objects.all()
        specialization = self.request.GET.get('specialization')
        available = self.request.GET.get('available')

        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        if available == 'true':
            queryset = queryset.filter(is_available=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specializations'] = Worker.objects.values_list('specialization', flat=True).distinct()
        return context

class WorkerDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Worker
    template_name = 'catering_app/worker_detail.html'
    context_object_name = 'worker'

    def test_func(self):
        return self.request.user.is_staff or self.request.user == self.get_object().user

class WorkerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Worker
    form_class = WorkerProfileForm
    template_name = 'catering_app/worker_form.html'
    success_url = reverse_lazy('worker_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class WorkerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Worker
    form_class = WorkerProfileForm
    template_name = 'catering_app/worker_form.html'
    success_url = reverse_lazy('worker_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user == self.get_object().user

class WorkerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Worker
    template_name = 'catering_app/worker_confirm_delete.html'
    success_url = reverse_lazy('worker_list')

    def test_func(self):
        return self.request.user.is_staff

@login_required
@user_passes_test(lambda u: u.is_staff)
def assign_workers_to_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = OrderAssignmentForm(request.POST, order=order)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.order = order
            assignment.save()
            
            # Добавляем работника в заказ
            order.workers.add(assignment.worker)
            
            messages.success(request, f'Работник {assignment.worker.user.get_full_name()} назначен на заказ')
            return redirect('order_detail', pk=order_id)
    else:
        form = OrderAssignmentForm(order=order)
    
    context = {
        'order': order,
        'form': form,
        'current_assignments': order.assignments.all()
    }
    return render(request, 'catering_app/assign_workers.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def remove_worker_from_order(request, assignment_id):
    assignment = get_object_or_404(OrderAssignment, id=assignment_id)
    order_id = assignment.order.id
    
    # Удаляем работника из заказа
    assignment.order.workers.remove(assignment.worker)
    assignment.delete()
    
    messages.success(request, 'Работник удален из заказа')
    return redirect('order_detail', pk=order_id)

class WorkerOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'catering_app/worker_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        worker = get_object_or_404(Worker, user=self.request.user)
        return Order.objects.filter(workers=worker).order_by('-event_date')

@require_http_methods(["POST"])
def submit_order(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Необходимо авторизоваться'}, status=401)
    
    try:
        data = json.loads(request.body)
        print("Received data:", data)  # Для отладки
        
        # Проверяем обязательные поля
        required_fields = ['event_date', 'start_time', 'end_time', 'format', 'guests_count', 
                         'contact_name', 'contact_phone', 'contact_email', 'menu_type_id']
        
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False, 
                    'error': f'Отсутствует обязательное поле: {field}'
                }, status=400)
        
        # Получаем формат меню
        try:
            menu_type = MenuType.objects.get(id=data['menu_type_id'])
        except MenuType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Выбранный формат меню не найден'
            }, status=400)
        
        # Создаем новый заказ
        order = Order.objects.create(
            user=request.user,
            event_date=data['event_date'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            event_type=data['format'],
            menu_type=menu_type,
            guests_count=data['guests_count'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            contact_email=data['contact_email'],
            special_requests=data.get('special_requests', ''),
            status='pending'
        )
        
        # Добавляем выбранные блюда
        total_price = 0
        for item in data.get('menu_items', []):
            try:
                menu_item = MenuItem.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price=menu_item.price
                )
                total_price += menu_item.price * item['quantity']
            except MenuItem.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Блюдо с ID {item["id"]} не найдено'
                }, status=400)
        
        # Обновляем общую стоимость заказа
        order.total_price = total_price
        order.save()
        
        # Очищаем данные заказа из сессии
        if 'order_data' in request.session:
            del request.session['order_data']
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'redirect_url': reverse('orders')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        print("Error creating order:", str(e))  # Для отладки
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def update_order_status(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'})
    
    try:
        order = Order.objects.get(id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Если заказ подтвержден, можно добавить уведомление пользователю
            if new_status == 'confirmed':
                # Здесь можно добавить отправку email или другое уведомление
                pass
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Неверный статус'})
            
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Заказ не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

class WorkerScheduleView(LoginRequiredMixin, ListView):
    model = WorkerSchedule
    template_name = 'catering_app/worker_schedule.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        worker = get_object_or_404(Worker, user=self.request.user)
        return WorkerSchedule.objects.filter(worker=worker).order_by('date', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = get_object_or_404(Worker, user=self.request.user)
        context['worker'] = worker
        return context

class WorkerScheduleCreateView(LoginRequiredMixin, CreateView):
    model = WorkerSchedule
    form_class = WorkerScheduleForm
    template_name = 'catering_app/worker_schedule_form.html'
    success_url = reverse_lazy('worker_schedule')

    def form_valid(self, form):
        worker = get_object_or_404(Worker, user=self.request.user)
        form.instance.worker = worker
        return super().form_valid(form)

class WorkerScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkerSchedule
    form_class = WorkerScheduleForm
    template_name = 'catering_app/worker_schedule_form.html'
    success_url = reverse_lazy('worker_schedule')

    def get_queryset(self):
        worker = get_object_or_404(Worker, user=self.request.user)
        return WorkerSchedule.objects.filter(worker=worker)

class WorkerScheduleDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkerSchedule
    template_name = 'catering_app/worker_schedule_confirm_delete.html'
    success_url = reverse_lazy('worker_schedule')

    def get_queryset(self):
        worker = get_object_or_404(Worker, user=self.request.user)
        return WorkerSchedule.objects.filter(worker=worker)

class WorkerScheduleCalendarView(LoginRequiredMixin, ListView):
    model = WorkerSchedule
    template_name = 'catering_app/worker_schedule_calendar.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        worker = get_object_or_404(Worker, user=self.request.user)
        return WorkerSchedule.objects.filter(worker=worker).order_by('date', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = get_object_or_404(Worker, user=self.request.user)
        context['worker'] = worker
        return context

class CalculatorView(View):
    template_name = 'catering_app/calculator.html'
    form_class = CalculatorForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Базовая стоимость за гостя
            base_price_per_guest = 1000
            
            # Множители для разных типов мероприятий
            event_type_multipliers = {
                'wedding': 1.5,
                'corporate': 1.2,
                'birthday': 1.0,
                'other': 1.0
            }
            
            # Множители для уровней обслуживания
            service_level_multipliers = {
                'basic': 1.0,
                'premium': 1.5,
                'luxury': 2.0
            }
            
            # Стоимость дополнительных услуг
            additional_services_prices = {
                'decoration': 5000,
                'furniture': 3000,
                'staff': 2000,
                'entertainment': 10000
            }
            
            # Расчет стоимости
            guests_count = form.cleaned_data['guests_count']
            event_type = form.cleaned_data['event_type']
            service_level = form.cleaned_data['service_level']
            additional_services = form.cleaned_data['additional_services']
            
            # Базовая стоимость
            total_price = base_price_per_guest * guests_count
            
            # Умножаем на коэффициент типа мероприятия
            total_price *= event_type_multipliers[event_type]
            
            # Умножаем на коэффициент уровня обслуживания
            total_price *= service_level_multipliers[service_level]
            
            # Добавляем стоимость дополнительных услуг
            for service in additional_services:
                total_price += additional_services_prices[service]
            
            context = {
                'form': form,
                'total_price': round(total_price),
                'guests_count': guests_count,
                'event_type': dict(form.fields['event_type'].choices)[event_type],
                'service_level': dict(form.fields['service_level'].choices)[service_level],
                'additional_services': [dict(form.fields['additional_services'].choices)[s] for s in additional_services]
            }
            
            return render(request, self.template_name, context)
        
        return render(request, self.template_name, {'form': form})

class OrderWizardView(TemplateView):
    template_name = 'catering_app/order_wizard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.kwargs.get('step', '1')
        context['current_step'] = step
        context['min_date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        if step == '3':
            context['menu_types'] = MenuType.objects.all()
        
        return context

@require_http_methods(["POST"])
def save_order_data(request):
    try:
        data = json.loads(request.body)
        step = data.get('step')
        form_data = data.get('data', {})
        
        # Сохраняем данные в сессии
        request.session[f'order_step_{step}'] = form_data
        
        # Базовая валидация
        if step == '1':
            if not all([form_data.get('event_date'), form_data.get('start_time'), form_data.get('end_time')]):
                return JsonResponse({'success': False, 'error': 'Заполните все поля даты и времени'})
            
            if form_data.get('start_time') >= form_data.get('end_time'):
                return JsonResponse({'success': False, 'error': 'Время окончания должно быть позже времени начала'})
        
        elif step == '2':
            if not form_data.get('format'):
                return JsonResponse({'success': False, 'error': 'Выберите формат мероприятия'})
            
            if not form_data.get('guests_count') or int(form_data.get('guests_count', 0)) < 1:
                return JsonResponse({'success': False, 'error': 'Укажите корректное количество гостей'})
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'catering_app/order_confirmation.html', {'order': order})

def contact_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Здесь можно добавить логику отправки email или сохранения в базу данных
        # Например:
        # send_mail(
        #     subject=f'Новое сообщение от {name}',
        #     message=f'Имя: {name}\nEmail: {email}\nТелефон: {phone}\nСообщение: {message}',
        #     from_email=email,
        #     recipient_list=['your@email.com'],
        # )
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})
