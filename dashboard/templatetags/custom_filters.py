from django import template

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    """Return the absolute value of a number."""
    return abs(value)