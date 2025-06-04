from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.MenuListView.as_view(), name='menu_list'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<str:category>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menu_item_detail'),
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('types/', views.MenuTypeListView.as_view(), name='menu_type_list'),
    path('types/<int:pk>/', views.MenuTypeDetailView.as_view(), name='menu_type_detail'),
] 