from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_services_price(services):
    """Суммирует цены всех услуг"""
    try:
        return sum(service.price for service in services)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Складывает два значения"""
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except (ValueError, TypeError):
        return 0 