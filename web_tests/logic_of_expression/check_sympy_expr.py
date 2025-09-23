import numpy as np
import sympy as sp
from .tex_to_sympy import Tex2Sympy as ts

class CheckAnswer:
    """
    Класс для проверки правильности ответа студента.
    Поддерживает: выбор (choice), целочисленные, строковые и символьные/числовые ответы.
    """
    # Теги, запрещённые в строковых и символьных ответах, пока не добавлены соответственные типы ответов
    _FORBIDDEN_TAGS = ['int', 'matrix', 'sum', 'prod', 'lim', 'intop', 'operator']

    def __init__(self, right_ans, stud_ans, is_choice, eps=0., type_ans=float):

        self.teach_raw = right_ans.strip().lower()
        self.stud_raw = stud_ans.strip().lower()
        self.eps = eps
        self.type_ans = type_ans
        self.is_choice = is_choice

    def compare_answer(self):
        """
        Выбор метода проверки в зависимости от типа вопроса и ожидаемого формата ответа.
        """
        # Вопрос с выбором: точное сравнение строк
        if self.is_choice:
            return int(self.teach_raw == self.stud_raw)

        # Целочисленный ответ: сравнение без конвертации TeX
        if self.type_ans is int:
            try:
                return int(int(self.teach_raw) == int(self.stud_raw))
            except ValueError:
                return 0

        # Строковый ответ: запрещаем математические теги
        if self.type_ans is str:
            for tag in self._FORBIDDEN_TAGS:
                if tag in self.stud_raw:
                    return 0
            return int(self.teach_raw == self.stud_raw)

        # Числовой или символьный ответ: конвертация и сравнение
        try:
            first_expr = ts(self.teach_raw).get_result()
            second_expr = ts(self.stud_raw).get_result()
        except Exception:
            return 0
        return self._compare_expr(first_expr, second_expr)

    def _compare_expr(self, f_expr, s_expr):
        """
        Сравнение двух символьных выражений через SymPy с учётом eps.
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


exp1 = "\frac{1}{2\ln{3}\sqrt{x}\sqrt{x+1}}"
exp2 = "\dfrac{2\,\sqrt{x}\,\sqrt{x+1}+2\,x+1}{2\,\ln\left(3\right)\,\left(2\,{x}^{2}+\sqrt{x}\,\sqrt{x+1}\,\left(2\,x+1\right)+2\,x\right)}"
obj = CheckAnswer(exp1, exp2, 0)
print(obj._compare_expr(exp1, exp2))