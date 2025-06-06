"""
URL configuration for catering project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from users.views import register_view
from .views import contact_form_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='catering_app/home.html'), name='home'),
    path('services/', TemplateView.as_view(template_name='catering_app/services.html'), name='services'),
    path('menu/', include('menu.urls')),
    path('gallery/', TemplateView.as_view(template_name='catering_app/gallery.html'), name='gallery'),
    path('about/', TemplateView.as_view(template_name='catering_app/about.html'), name='about'),
    path('contacts/', TemplateView.as_view(template_name='catering_app/contacts.html'), name='contacts'),
    path('contact-form/', contact_form_view, name='contact_form'),
    path('users/', include('users.urls')),
    path('orders/', include('orders.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', register_view, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
