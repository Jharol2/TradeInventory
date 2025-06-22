from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Filtro para acceder a elementos de diccionario en templates"""
    return dictionary.get(key)

@register.filter
def class_name(value):
    return value.__class__.__name__ 