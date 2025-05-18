import re
import numpy as np

# from web_tests.logic_of_expression.test_t_to_s_ver2 import primerExpr


class GetLexeme:
    PER = 'abcdefghijklmnopqrstuvwxyz'
    DIGIT = '.1234567890'
    MATHFUNC = np.array(['log', 'ln',
                         'sin', 'cos', 'tan', 'cot',
                         'arcsin', 'arccos', 'arctan', 'arccot',
                         'sinh', 'cosh', 'tanh', 'coth'
                         ])
    TEXTEG = np.array(['frac', 'sqrt', 'rect'])

    def __init__(self, texExpr):
        self.texExpr = texExpr

    # Удаление всех обратных слешей
    def remove_backslashes(self, latex_expr):
        return re.sub(r'\\([a-zA-Z]+)', r'\1', latex_expr)

    def get_task_and_tex(self):

        replace_of_screen = {
            0: ['\n', '\\n'],
            1: ['\a', '\\a'],
            2: ['\b', '\\b'],
            3: ['\f', '\\f'],
            4: ['\r', '\\r'],
            5: ['\t', '\\t'],
            6: ['\v', '\\v'],
        }

        all_expr = self.texExpr
        for i in range(len(replace_of_screen)):
            all_expr = all_expr.replace(replace_of_screen[i][0], replace_of_screen[i][1])

        all_expr = self.remove_backslashes(all_expr)

        all_expr = all_expr.replace('dfrac', 'frac')
        all_expr = all_expr.replace('^', '**')

        all_expr = all_expr.replace('$', '')
        all_expr = all_expr.replace('right)', ')').replace('left(', '(')
        all_expr = all_expr.replace('displaylines', '')

        # Добавление фигурных скобок для случаев когда они не нужны в теховской нотации (sqrt4)
        i = 0
        while i < len(all_expr):
            atom = ''
            while all_expr[i] in self.PER and i < len(all_expr)-1:
                atom += all_expr[i]
                i += 1
                if atom in self.TEXTEG:
                    if all_expr[i] in self.DIGIT:
                        if atom == 'sqrt' or atom == 'rect':
                            all_expr = all_expr[:i] + '{' + all_expr[i] + '}' + all_expr[i+1:]
                        if atom == 'frac':
                            all_expr = all_expr[:i] + '{' + all_expr[i] + '}{' + all_expr[i+1] + '}' + all_expr[i+2:]
            i += 1

        return all_expr

    def stack_for_math_funk(self, expr, start):

        sdvig = len(expr[:start])
        expr = expr[start:]
        stack = np.array([])
        i = 0
        while True:
            if expr[i] == '(':
                stack = np.append(stack, '(')
            if expr[i] == ')':
                stack = np.delete(stack, -1)

            if len(stack) == 0:
                return i + sdvig

            i += 1

    def get_st_fin(self, expr_obr, flag):

        if expr_obr[0] == '[':
            sq = 2
        else:
            sq = 0

        stack = np.array([])
        i = 0
        while True:
            token = expr_obr[i]
            if token == '{':
                stack = np.append(stack, token)
            if token == '}':
                stack = np.delete(stack, -1)

            if len(stack) == 0 and i > sq:
                flag -= 1
                if flag == 0:
                    break
            i += 1

        return expr_obr, i

    def get_all_teg(self, expr):
        # expr = self.get_task_and_tex()[0]
        size = len(expr) - 1
        all_teg_with_1_ck = np.array(['sqrt', 'rect'])
        all_teg_with_2_ck = np.array(['frac'])

        teg_with_indices = np.array([])

        atom = ''
        i = 0
        while i < size:
            if expr[i] in self.PER:
                start = i
                while expr[i] in self.PER:
                    atom += expr[i]
                    i += 1
                    if expr[i] not in self.PER:
                        len_teg_for_st = len(atom)
                        start += len_teg_for_st
                        if atom in all_teg_with_1_ck or atom in all_teg_with_2_ck:
                            teg_with_indices = np.append(teg_with_indices, atom)
                        if atom in all_teg_with_1_ck:
                            teg_with_indices = np.append(teg_with_indices,
                                                         [start, start + self.get_st_fin(expr[i:], 1)[1]])
                        if atom in all_teg_with_2_ck:
                            teg_with_indices = np.append(teg_with_indices,
                                                         [start, start + self.get_st_fin(expr[i:], 2)[1]])
                        atom = ''
            i += 1

        teg_with_indices = np.array(teg_with_indices, dtype=object)
        for i in range(len(teg_with_indices)):
            if teg_with_indices[i][0] not in self.PER:
                teg_with_indices[i] = int(teg_with_indices[i])

        return teg_with_indices


# -----------------------------------------------------------------------------------------------------------------
# Здесь будет обработка каждого тега конкретно, каждый метод возвращает измененную подстроку, которая потом будет
# заменяться на соответствующую подстроку в первоначальном выражении, и так для каждого тега в выражении
class Tex2Sympy(GetLexeme):

    # Обработка для дробей
    def frac_construct(self, unexpr):
        # print(unexpr)
        unexpr = unexpr.replace('frac', '')
        unexpr = unexpr.replace('}{', ')/(')
        unexpr = unexpr.replace('{', '(')
        unexpr = unexpr.replace('}', ')')
        return f"({unexpr})"

    # Обработка для корней
    def sqrt_construct(self, unexpr):
        # Проверяем на наличие степени
        if '[' in unexpr and ']' in unexpr:
            degree_start = unexpr.find('[') + 1
            degree_end = unexpr.find(']', degree_start)
            degree = unexpr[degree_start:degree_end]
            unexpr = unexpr.replace(f"[{degree}]", "")
        else:
            degree = '2'

        unexpr = unexpr.replace('sqrt', '').strip()
        unexpr = unexpr.replace('{', '(').replace('}', ')')

        processed_expr = f"{unexpr}**1/{degree}"
        return processed_expr

    # Обработка для модулей
    def rect_construct(self, unexpr):
        unexpr = unexpr.replace('|', 'Abs(')
        return unexpr + ')'

    def navigate_for_main_tags(self):
        expr = self.get_task_and_tex()
        all_tex_teg = self.get_all_teg(expr)
        all_tex_teg = np.reshape(all_tex_teg, ((int(len(all_tex_teg) // 3)), 3))

        for i in range(len(all_tex_teg) - 1, -1, -1):
            tag = all_tex_teg[i][0]
            start = all_tex_teg[i][1] - len(tag)
            end = all_tex_teg[i][2] + 1

            before_tag = expr[:start]
            tag_content = expr[start:end]
            after_tag = expr[end:]

            # Та самая маршрутизация для каждого из тега в выражении
            if tag == 'frac':
                processed_tag = self.frac_construct(tag_content)
            elif tag == 'sqrt':
                processed_tag = self.sqrt_construct(tag_content)
            elif tag == 'rect':
                processed_tag = self.rect_construct(tag_content)
            else:
                processed_tag = tag_content

            # Проворачиваем сдвиг индексов
            for j in range(i - 1, -1, -1):
                end_next_tag = all_tex_teg[j][2] + 1
                if end < end_next_tag:
                    all_tex_teg[j][2] += len(processed_tag) - len(tag_content)

            # Формируем результат на каждом шаге
            expr = before_tag + processed_tag + after_tag

        return expr

    # Степени для элементарных матфункций(sin, cos, log, ...)
    def sq_for_math_func(self, expression):
        j = 0
        res = ''

        while j < len(expression):
            flag = False
            atom = ''
            if expression[j] not in self.PER:
                res += expression[j]

            while j < len(expression) and expression[j] in self.PER and atom not in self.MATHFUNC:
                atom += expression[j]
                j += 1
                flag = True
            else:
                if flag:
                    j -= 1
                if atom in self.MATHFUNC and j + 1 < len(expression) and expression[j+1] == '*':
                    j += 1
                    res += '(' + atom
                    get_gr1 = self.stack_for_math_funk(expression, j + 2)
                    get_gr2 = self.stack_for_math_funk(expression, get_gr1 + 1)
                    res += expression[get_gr1 + 1:get_gr2 + 1] + ')' + expression[j:get_gr1+1]
                    j = get_gr2
                else:
                    res += atom
            j += 1

        return res

    # Выставление умножения между цифрой и переменной/функцией/скобкой
    def addit_mult(self, expression):

        el = 0
        while el < len(expression) - 1:
            if expression[el] in self.DIGIT and (expression[el + 1] in self.PER or expression[el + 1] in '(['):
                expression = expression[:el + 1] + '*' + expression[el + 1:]
            if (expression[el] in self.PER or expression[el] in ')]') and expression[el + 1] in self.DIGIT:
                expression = expression[:el + 1] + '*' + expression[el + 1:]
            el += 1

        return expression

    def get_result(self):
        expression = self.navigate_for_main_tags().strip()
        expression = expression.replace('{', '(').replace('}', ')')
        expression = self.sq_for_math_func(expression)
        expression = self.addit_mult(expression)
        return expression

