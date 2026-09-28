import re

import numpy as np


class MasterMatrix:
    base_norm = {
        'frobenius': lambda matrix: np.linalg.norm(matrix, 'fro'),
        'one': lambda matrix: np.linalg.norm(matrix, 1),
        'inf': lambda matrix: np.linalg.norm(matrix, np.inf),
    }

    def __init__(self, all_expr, ans_r, ans_s, type_norm='', eps=0):
        self.all_expr = all_expr
        self.ans_r = ans_r
        self.ans_s = ans_s
        code = getattr(type_norm, 'type_code', type_norm)
        self.norm = {1: 'frobenius', 2: 'one', 3: 'inf', '': 'frobenius'}.get(code, code)
        self.eps = float(eps or 0)

    @staticmethod
    def _number(cell):
        cell = re.sub(r'\\[,;!]|\\(?:quad|qquad)\b|\s+', '', cell)
        fraction = re.fullmatch(r'([+-]?)\\(?:d?frac)\{([^{}]+)\}\{([^{}]+)\}', cell)
        if fraction:
            sign, numerator, denominator = fraction.groups()
            return (-1 if sign == '-' else 1) * float(numerator) / float(denominator)
        return float(cell)

    def tex_to_np(self, expr):
        match = re.search(
            r'\\begin\{(matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|smallmatrix|array)\}'
            r'(.*?)\\end\{\1\}', expr, re.DOTALL,
        )
        if not match:
            raise ValueError('Matrix environment is missing')
        body = match.group(2).strip()
        if match.group(1) == 'array':
            body = re.sub(r'^\{[clr| ]+\}', '', body).strip()
        rows = re.split(r'\\\\(?:\[[^\]]*\])?', body)
        if rows and not rows[-1].strip():
            rows.pop()
        values = [[self._number(cell) for cell in row.split('&')] for row in rows]
        if not values or not values[0] or any(len(row) != len(values[0]) for row in values):
            raise ValueError('Matrix rows must have equal length')
        result = np.array(values, dtype=float)
        if not np.isfinite(result).all():
            raise ValueError('Matrix entries must be finite')
        return result

    def get_result(self):
        try:
            right = self.tex_to_np(self.ans_r)
            student = self.tex_to_np(self.ans_s)
            if right.shape != student.shape:
                return False
            if self.eps == 0:
                return bool(np.array_equal(right, student))
            return bool(self.base_norm[self.norm](right - student) <= self.eps)
        except (ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError):
            return False
