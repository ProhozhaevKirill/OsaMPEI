import numpy as np
import sympy as sp
from .tex_to_sympy import Tex2Sympy as ts
 

class CheckAnswer:
    def __init__(self, right_ans, mb_right_ans, eps=0, type_ans=float):

        self.teach_ans = right_ans.lower() + ' '
        self.user_ans = mb_right_ans.lower() + ' '
        self.eps = 10 ** (-int(eps))
        self.type_ans = type_ans

    def compare_answer(self):
        first_expr = ts(self.teach_ans).get_result()
        second_expr = ts(self.user_ans).get_result()

        res = sp.simplify(first_expr + '- (' + second_expr + ')')

        if self.eps == 1.0:
            if res == 0:
                return 1
            elif res != 0:
                return 0
        else:
            if abs(res) < self.eps:
                return 1
            else:
                return 0
