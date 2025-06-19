from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='is_owner')
def is_owner(user):
    return user.is_superuser or user.groups.filter(name='Владельцы').exists()

@register.simple_tag
def test_tag():
    return 'STORE_TAGS_WORK' 
