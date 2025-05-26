from django import template
from django.utils.timesince import timesince
from django.utils.timezone import now

register = template.Library()

@register.filter
def time_ago(value):
    if value:
        return timesince(value, now()) + " ago"
    return ""
