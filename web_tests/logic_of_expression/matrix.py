import numpy as np
import sympy as sp


class MasterMatrix:
    mark = "matrix"
    lenght = len(mark)

    base_norm = {
        'frobenius': lambda matr: np.sqrt(np.sum(matr ** 2)),
        'one': lambda matr: np.max(np.sum(np.abs(matr), axis=0)),
        'inf': lambda matr: np.max(np.sum(np.abs(matr), axis=1))
    }

    def __init__(self, all_expr, ans_r, ans_s, type_norm='', eps=0):
        self.all_expr = all_expr
        self.ans_r = ans_r
        self.ans_s = ans_s
        self.norm = type_norm
        self.eps = eps

    def get_tex_matr(self, expr):
        size = len(expr)
        bound = np.array([], dtype=int)
        flag = True

        for i in range(size):
            if expr[i:i + self.lenght] == self.mark and flag:
                bound = np.append(bound, i + self.lenght + 1)
                flag = False
            elif expr[i:i + self.lenght] == self.mark and not flag:
                bound = np.append(bound, i - self.lenght)

        print(expr[bound[0]:bound[1]])

        return bound

    def tex_to_np(self, expr):
        res = np.array([])

        bound = self.get_tex_matr(expr)
        matr = expr[bound[0]:bound[1]]
        matr = matr.replace(' ', '').split('\\\\')
        print(matr)
        count_row = len(matr)

        for row in matr:
            numbers = [float(x) for x in row.split('&')]  # строки → float
            res = np.append(res, numbers)
        res = res.reshape(count_row, -1)

        print(res)

        return res

    def meas_laz(self):
        return 0

    def is_equivalent_by_rows_cols(self, A, B):
        MA = sp.Matrix(A); rA = MA.rank()
        MB = sp.Matrix(B); rB = MB.rank()

        if rA != rB:
            return False
        else:
            return self.base_norm[self.norm](np.array(MA - MB)) <= self.eps

    def get_result(self):
        # print(self.all_expr, '\n')
        # print(self.ans_r, '\n')
        # print(self.ans_s)


        all_expr = self.tex_to_np(self.all_expr)
        ans_r = self.tex_to_np(self.ans_r)
        ans_s = self.tex_to_np(self.ans_s)

        if self.eps == 0:
            return np.array_equal(ans_r, ans_s)
        else:
            # if np.shape(all_expr) == np.shape(ans_s):
            #     diff_matr = np.eye(np.shape(ans_s)[0]) -
            #     mean_same = self.base_norm[self.norm](diff_matr)
            return self.is_equivalent_by_rows_cols(ans_r, ans_s)


# all_ex = " $$ упростите\\;\\begin{pmatrix}1 & 2\\\\ 2 & 5\\end{pmatrix} $$ "
# ans1 = " $$ \\begin{pmatrix}1 & 2\\\\ 1 & 3\\end{pmatrix} $$ "
# ans2 = " $$ \\begin{pmatrix}1 & 2\\\\ 1 & 3\\end{pmatrix} $$ "
# eps = 1
# norm = 'frobenius'
# obj = MasterMatrix(all_ex, ans1, ans2, type_norm=norm, eps=eps)
# result = obj.get_result()
# print(result)
# print(result, ans1[result[0]], ans1[result[0]:result[1]])

