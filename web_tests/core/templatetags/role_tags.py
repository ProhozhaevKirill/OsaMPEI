from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_role(context):
    """
    Возвращает строковую роль: 'teacher' или 'student'.
    """
    user = context.get('request').user
    if not user.is_authenticated:
        return 'guest'
    return 'teacher' if user.is_staff else 'student'
