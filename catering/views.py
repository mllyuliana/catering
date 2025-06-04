from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def order(request):
    return render(request, 'order.html')

@require_POST
@csrf_exempt
def contact_form_view(request):
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Здесь можно добавить логику отправки email или сохранения сообщения в базе данных
        # Например:
        # send_mail(
        #     subject=f'Новое сообщение от {name}',
        #     message=f'Имя: {name}\nEmail: {email}\nТелефон: {phone}\nСообщение: {message}',
        #     from_email=email,
        #     recipient_list=['your-email@example.com'],
        # )

        return JsonResponse({
            'status': 'success',
            'message': 'Сообщение успешно отправлено'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 