from django import template
from django.templatetags.i18n import do_translate as _do_translate

register = template.Library()

# Register 'translate' tag as an alias for Django built-in 'trans' tag (do_translate)
register.tag('translate', _do_translate)
