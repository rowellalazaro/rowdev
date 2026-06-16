from django import template

register = template.Library()

@register.filter
def split(value, arg):
    if value:
        return value.split(arg)
    return []

@register.filter
def get(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)