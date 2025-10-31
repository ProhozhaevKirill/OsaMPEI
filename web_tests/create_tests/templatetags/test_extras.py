from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Разделяет строку по указанному разделителю
    Использование: {{ "a;b;c"|split:";" }}
    """
    if value:
        return value.split(delimiter)
    return []

@register.filter
def get_item(list_obj, index):
    """
    Получает элемент списка по индексу
    Использование: {{ my_list|get_item:0 }}
    """
    try:
        return list_obj[int(index)]
    except (ValueError, TypeError, IndexError):
        return ''