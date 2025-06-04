from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_services_price(services):
    """Суммирует стоимость всех услуг"""
    try:
        return sum(service.price * service.quantity for service in services)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    try:
        return Decimal(value or 0) + Decimal(arg or 0)
    except (InvalidOperation, TypeError, ValueError):
        return 0 