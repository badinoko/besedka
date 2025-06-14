from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def user_navigation(context):
    """
    DEPRECATED: временная заглушка тега, который ранее выводил навигацию пользователя.
    Все актуальные данные навигации уже доступны через partials и context processors.
    Тег возвращает пустую строку, чтобы не ломать старые шаблоны.
    """
    return ""
