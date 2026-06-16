# Monkey patch Django's format_html to handle cases where no args or kwargs are passed.
# This fixes a TypeError in Django 5.x/6.x when used with django-jazzmin.
import django.utils.html
from django.utils.safestring import mark_safe

original_format_html = django.utils.html.format_html

def patched_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return mark_safe(format_string)
    return original_format_html(format_string, *args, **kwargs)

django.utils.html.format_html = patched_format_html
