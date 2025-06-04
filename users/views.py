from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserProfileForm, ProfileEditForm, CustomPasswordChangeForm
from .models import CustomUser, UserActivity
from orders.models import Order

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
    
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Ошибка регистрации: ' + ' '.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
            })
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

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

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            UserActivity.objects.create(
                user=request.user,
                description=_('Профиль обновлен')
            )
            messages.success(request, _('Профиль успешно обновлен'))
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)

    # Получаем статистику заказов
    total_orders = Order.objects.filter(user=request.user).count()
    active_orders = Order.objects.filter(user=request.user, status__in=['new', 'processing']).count()
    completed_orders = Order.objects.filter(user=request.user, status='completed').count()

    # Получаем историю активности
    user_activities = request.user.activities.all()[:10]  # Последние 10 активностей

    context = {
        'form': form,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'user_activities': user_activities,
    }
    return render(request, 'users/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            UserActivity.objects.create(
                user=request.user,
                description=_('Пароль изменен')
            )
            messages.success(request, _('Пароль успешно изменен'))
            return redirect('users:profile')
        else:
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме'))
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})
