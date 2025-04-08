import numpy as np
import sympy as sp
from .tex_to_sympy import Tex2Sympy as ts
 

class CheckAnswer:
    def __init__(self, right_ans, stud_ans, is_choice, eps=0., type_ans=float):

        self.teach_ans = right_ans.lower() + ' '
        self.stud_ans = stud_ans.lower() + ' '
        self.eps = eps
        self.type_ans = type_ans
        self.is_choice = is_choice

    def compare_answer(self):

        if self.is_choice:
            if int(self.teach_ans, base=10) == int(self.stud_ans, base=10):
                return 1
            return 0
        else:
            first_expr = ts(self.teach_ans).get_result()
            second_expr = ts(self.stud_ans).get_result()
            return self.get_result(first_expr, second_expr)

    def get_result(self, f_expr, s_expr):
        if s_expr == '':
            return 0

        res = sp.simplify(f_expr + '- (' + s_expr + ')')

        if self.eps == 0.:
            if res == 0:
                return 1
            elif res != 0:
                return 0
        else:
            if abs(res) < self.eps:
                return 1
            else:
                return 0
