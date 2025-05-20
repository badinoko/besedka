from django import template

register = template.Library()

@register.simple_tag
def test_tag2():
    return 'TEST_TAGS_WORK' 