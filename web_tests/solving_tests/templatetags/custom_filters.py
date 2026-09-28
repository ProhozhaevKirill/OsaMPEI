from create_tests.answer_storage import split_answers
from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Разделяет строку по заданному разделителю."""
    return split_answers(value) if arg == ";" else value.split(arg)

@register.filter(name='zip_lists')
def zip_lists(list1, list2):
    """Соединяет два списка в пары с использованием zip."""
    return zip(list1, list2)
