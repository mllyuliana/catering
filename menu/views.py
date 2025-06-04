from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import MenuItem, AdditionalService, MenuType

class MenuListView(ListView):
    model = MenuType
    template_name = 'menu/menu.html'
    context_object_name = 'menu_types'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_available=True)

class CategoryListView(ListView):
    template_name = 'menu/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return dict(MenuItem.CATEGORY_CHOICES)

class CategoryDetailView(ListView):
    template_name = 'menu/category_detail.html'
    context_object_name = 'menu_items'
    
    def get_queryset(self):
        return MenuItem.objects.filter(
            category=self.kwargs['category'],
            is_available=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.kwargs['category']
        context['category_name'] = dict(MenuItem.CATEGORY_CHOICES).get(
            self.kwargs['category'],
            self.kwargs['category']
        )
        return context

class MenuItemDetailView(DetailView):
    model = MenuItem
    template_name = 'menu/menu_item_detail.html'
    context_object_name = 'menu_item'
    
    def get_queryset(self):
        return MenuItem.objects.filter(is_available=True)

class ServiceListView(ListView):
    model = AdditionalService
    template_name = 'menu/service_list.html'
    context_object_name = 'services'
    
    def get_queryset(self):
        return AdditionalService.objects.filter(is_available=True)

class ServiceDetailView(DetailView):
    model = AdditionalService
    template_name = 'menu/service_detail.html'
    context_object_name = 'service'
    
    def get_queryset(self):
        return AdditionalService.objects.filter(is_available=True)

class MenuTypeListView(ListView):
    model = MenuType
    template_name = 'menu/menu_type_list.html'
    context_object_name = 'menu_types'

class MenuTypeDetailView(DetailView):
    model = MenuType
    template_name = 'menu/menu_type_detail.html'
    context_object_name = 'menu_type' 