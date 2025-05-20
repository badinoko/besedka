from django import template

register = template.Library()

@register.simple_tag
def test_user_tag():
    return 'USERS_TAGS_WORK' 