import numpy as np
import sympy as sp
from .tex_to_sympy import Tex2Sympy as ts
from .matrix import MasterMatrix as mm


class CheckAnswer:
    """
    Класс для проверки правильности ответа студента.
    Поддерживает: выбор (choice), целочисленные, строковые и символьные/числовые ответы.
    """
    # Теги, запрещённые в строковых и символьных ответах, пока не добавлены соответственные типы ответов
    _FORBIDDEN_TAGS = ['sum', 'prod', 'lim', 'intop', 'operator']
    # _EXISTS_TYPE = {"1": int,
    #                 "2": float,
    #                 "3": str,
    #                 "4": "matrix"}

    def __init__(self, right_ans, stud_ans, is_choice, expression='', eps=0., type_ans=float, type_norm=''):

        self.all_expr = expression.strip().lower()
        self.teach_raw = right_ans.strip().lower()
        self.stud_raw = stud_ans.strip().lower()
        self.eps = eps
        self.type_ans = type_ans
        self.type_norm = type_norm
        self.is_choice = is_choice

    def compare_answer(self):
        """
        Выбор метода проверки в зависимости от типа вопроса и ожидаемого формата ответа.
        """

        # Вопрос с выбором: точное сравнение строк
        if self.is_choice:
            return int(self.teach_raw == self.stud_raw)

        match self.type_ans:
            case 1: # int
                try:
                    return self.teach_raw == self.stud_raw
                except ValueError:
                    return 0

            case 2: # float
                try:
                    return self._compare_expr(self.teach_raw, self.stud_raw)
                except ValueError:
                    return 0

            case 3: # symbolic
                f_expr = ts(self.teach_raw).get_result()
                s_expr = ts(self.stud_raw).get_result()

                try:
                    return self._compare_expr(f_expr, s_expr)
                except ValueError:
                    return 0

            case 4: # matrix
                return mm(self.all_expr, self.teach_raw, self.stud_raw, self.type_norm, self.eps).get_result()

            case _:
                return 0


    def _compare_expr(self, f_expr, s_expr):
        """
        Сравнение двух выражений через SymPy с учётом eps.
        """
        if not s_expr:
            return 0
        try:
            diff = sp.simplify(f_expr + ' - (' + s_expr + ')')
        except Exception:
            return 0
        # Точное сравнение
        if self.eps == 0.:
            return int(diff == 0)
        # Сравнение с погрешностью
        try:
            return int(abs(diff) < self.eps)
        except Exception:
            return 0
