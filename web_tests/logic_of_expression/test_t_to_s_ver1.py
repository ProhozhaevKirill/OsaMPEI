import numpy as np
# import sympy

class GetLexeme:
    __PER = 'abcdefghijklmnopqrstuvwxyz'
    __DIGIT = '.1234567890'

    def __init__(self, texExpr):
        self.texExpr = texExpr

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

        all_expr = all_expr.replace('^', '**')
        all_expr = all_expr.replace('\pi', 'pi')
        all_expr = all_expr.replace('dfrac', 'frac')

        for i in range(len(replace_of_screen)):
            all_expr = all_expr.replace(replace_of_screen[i][0], replace_of_screen[i][1])

        all_expr_by_space = all_expr.split()

        tex_formula = ''
        i = 0
        while i < len(all_expr_by_space):
            if 1040 <= ord(all_expr_by_space[i][0]) <= 1103:
                all_expr_by_space[i] += ' '
            else:
                tex_formula += ' ' + all_expr_by_space[i]
            i += 1

        return tex_formula, all_expr_by_space

    def get_st_fin(self, start, flag, sq=0):

        expr_obr = self.get_task_and_tex()[0][start:]
        # print(expr_obr)

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

        return i

    def get_all_teg(self):
        expr = self.get_task_and_tex()[0]

        size = len(expr)
        all_teg_with_1_ck = np.array(['sqrt', 'rect'])
        all_teg_with_2_ck = np.array(['frac'])

        teg_with_indices = np.array([])

        atom = ''
        i = 0
        count1 = 0

        while i < size:
            if expr[i] in self.__PER:
                start = i
                while expr[i] in self.__PER:
                    count1 += 1
                    atom += expr[i]
                    i += 1
                    if expr[i] not in self.__PER:
                        len_teg_for_st = len(atom)
                        start += len_teg_for_st
                        teg_with_indices = np.append(teg_with_indices, atom)
                        if atom in all_teg_with_1_ck:
                            teg_with_indices = np.append(teg_with_indices, [start, start + self.get_st_fin(i, 1, 2)])
                        if atom in all_teg_with_2_ck:
                            teg_with_indices = np.append(teg_with_indices, [start, start + self.get_st_fin(i, 2)])
                        atom = ''
            i += 1

        teg_with_indices = np.array(teg_with_indices, dtype=object)
        for i in range(len(teg_with_indices)):
            if teg_with_indices[i][0] not in self.__PER:
                teg_with_indices[i] = int(teg_with_indices[i])

        return teg_with_indices

# -----------------------------------------------------------------------------------------------------------------
# Здесь будет обработка каждого тега конкретно, каждый метод возвращает измененную подстроку, которая потом будет
# заменяться на соответствующую подстроку в первоначальном выражении, и так для каждого тега в выражении
class Tex2Sympy(GetLexeme):

    # Обработка для дробей
    def frac_construct(self, unexpr):
        unexpr = unexpr.replace('\\frac', '')
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

        unexpr = unexpr.replace('\\sqrt', '').strip()
        unexpr = unexpr.replace('{', '(').replace('}', ')')

        processed_expr = f"({unexpr})**(1/{degree})"
        return processed_expr

    # Обработка для модулей
    def rect_construct(self, start, end):
        unexpr = self.get_task_and_tex()[0]
        return unexpr

    def navigate_for_main_tags(self):
        expr = self.get_task_and_tex()[0]
        print(111, expr)
        all_tex_teg = self.get_all_teg()
        all_tex_teg = np.reshape(all_tex_teg, ((int(len(all_tex_teg)//3)), 3))

        for i in range(len(all_tex_teg)-1, -1, -1):
            tag = all_tex_teg[i][0]
            start = all_tex_teg[i][1] - len(tag) - 1
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
                processed_tag = self.rect_construct(start, end)
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

    def get_result(self):
        expression = self.navigate_for_main_tags()

        expression = expression.replace('$', '')
        expression = expression.replace('{', ')')
        expression = expression.replace('{', '(')
        expression = expression.replace('', '')

        return expression

# -----------------------------------------------------------------------------------------------------------------

# primerExpr = '1 - \sqrt[3]{56} - \frac{4-1}{5-1}'
# primerExpr = '1 - \\frac{\\frac{4}{2}-1}{5-1} - \\sqrt{\\sqrt[5]{66} * 56} + \\sqrt{34}'
# primerExpr = '\sqrt{\sqrt[5]{66} * 56}'
# primerExpr = '\sqrt[4]{44} + \frac{12}{3}'
# primerExpr = '1 + \sqrt[3]{\frac{4}{5}} - 5'
# primerExpr = '\sqrt{((66))**(1/5) * 56}'

# primerExpr = 'e^{\frac{\ln(x)}{\sqrt{y}}}'
primerExpr = 'x + y - z'
# print(primerExpr)

obj = GetLexeme(primerExpr)
changeExample = obj.get_task_and_tex()[0]
obj2 = Tex2Sympy(primerExpr)
res = obj2.navigate_for_main_tags()

print(primerExpr)
print('-------------------------------------------------------------')
print(res)
print('-------------------------------------------------------------')

import sympy as sp
if sp.simplify(res):
    print('OK!')

