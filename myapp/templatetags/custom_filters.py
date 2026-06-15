from csv import reader

from mysite.myapp.models import PDS

# myapp/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """
    Ginagamit para i-split ang string: {{ "a,b,c"|split:"," }}
    """
    if value:
        return value.split(arg)
    return value