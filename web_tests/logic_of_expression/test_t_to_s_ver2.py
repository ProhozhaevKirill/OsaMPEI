import re
import numpy as np
import sympy as sp

class GetLexeme:
    PER = 'abcdefghijklmnopqrstuvwxyz'
    DIGIT = '.1234567890'
    MATHFUNC = np.array(['log', 'ln',
                         'sin', 'cos', 'tan', 'cot',
                         'arсsin', 'arccos', 'arctan', 'arccot',
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
        all_expr = all_expr.replace('cdot', '*')

        all_expr = all_expr.replace('$', '')
        all_expr = all_expr.replace('right)', ')').replace('left(', '(')

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
                            all_expr = all_expr[:i] + '{' + all_expr[i+1] + '}{' + all_expr[i+1] + '}' + all_expr[i+2:]
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
        # print(all_tex_teg)
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
        print(expression)

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
        # print(1, expression)
        expression = expression.replace('{', '(').replace('}', ')')
        # print(2, expression)
        expression = self.sq_for_math_func(expression)
        # print(3, expression)
        expression = self.addit_mult(expression)
        # print(4, expression)

        return expression


# -----------------------------------------------------------------------------------------------------------------
# expressions = np.array([
    # По-моему не рабочее говно
    # r'7\ln5',
    
    
    # # Смешанные с основной разработки
    # r'1 - \sqrt[3]{56} - \frac{4-1}{5-1}',
    # r'1 - \frac{\frac{4}{2}-1}{5-1} - \sqrt{\sqrt[5]{66} * 56} + \sqrt{34}',
    # r'1 - \sqrt{\sqrt[5]{66} * 56} + \sqrt{34}',
    # r'\sqrt{\sqrt[5]{66} * 56}',
    # r'\sqrt[4]{44} + \frac{12}{3}',
    # r'1 + \sqrt[3]{\frac{4}{5}} - 5',
    # r'\sqrt{((66))**(1/5) * 56}',
    # r'\frac{1}{\frac{2}{3}}',
    # r'\sqrt{1-2\sin(x)+\sin(x)^2}',
    #
    # # Простые базовые выражения
    # r"x + y - z",
    # r"x^2 + 2*x*y + y^2",
    # r"sin(x) + cos(y)",
    # r"tan(x) - \frac{1}{cot(y)}",
    # r"\sqrt{x^2 + y^2}",
    # r"log(x) + ln(y)",
    # r"e^{x+y} + \frac{1}{e^{z}}",
    # r"\frac{x}{y} + \frac{z}{w}",
    # r"\sqrt{\frac{x^2}{y^2}}",
    # r"x! + y! - z!",
    #
    # # Сложные вложенные выражения
    # r"\frac{\sin(x)}{\cos(y)} + \tan(z)",
    # r"\sqrt{e^{x^2 + y^2}}",
    # r"\frac{\ln(x)}{\sqrt{y + z}}",
    # r"\frac{\sqrt{\sin(x) + \cos(y)}}{z}",
    # r"\sqrt{x + \frac{1}{y + z}}",
    # r"\frac{\sqrt{x^2 + y^2}}{z^2}",
    # r"e^{\frac{\ln(x)}{\sqrt{y}}}",
    # r"\sin(\sqrt{x + \cos(y)}) + z",
    # r"\tan^{-1}(x) + \cot^{-1}(y)",
    # r"\frac{\sqrt{x}}{\log(y) + e^z}",
    #
    # # Еще больше конструкций с тегами
    # r"\frac{\sqrt{\sin(x)}}{\cos^2(y)}",
    # r"\sqrt{\frac{x}{\ln(y)}} + e^z",
    # r"x + \frac{\sqrt{y}}{z + \ln(w)}",
    # r"\frac{\frac{x}{\sqrt{y}}}{\sqrt{z}}",
    # r"x^3 + \frac{\sqrt{y + z}}{e^w}",
    # r"\ln(\sqrt{x^2 + y^2 + z^2})",
    # r"x + \sqrt{\frac{y}{\sqrt{z}}}",
    # r"\sin(x) + \cos(\ln(y)) + \tan(z)",
    # r"\frac{\ln(x + \sqrt{y})}{e^z}",
    # r"x + \frac{\sqrt{y}}{\sqrt{z}} - \ln(w)",
    #
    # # Еще более сложные конструкции
    # r"x + \frac{\sin(y)}{\cos(z + \sqrt{w})}",
    # r"x^2 + \frac{\sqrt{\ln(y)}}{\tan(z)}",
    # r"x + y - z + \sqrt{w + e^{x - y}} - 2y",
    # r"\frac{\sqrt{x + \ln(y)}}{\cos(z)}",
    # r"x + \frac{\sin(y)}{\sqrt{z}} - \ln(w)",
    # r"\sqrt{x + \frac{\tan(y)}{\cos(z)}}",
    # r"\frac{\sqrt{\sin(x)}}{\tan(y + \ln(z))}",
    # r"\frac{x}{y + \frac{z}{w}}",
    # r"\tan^{-1}(\frac{x}{y}) + \cot^{-1}(z)",
    # r"x^2 + y^2 - \sqrt{z^2 + w^2}",
    #
    # # Дополнительные усложненные проверки
    # r"\tan^{-1}(x + \sqrt{y}) + \cot^{-1}(\frac{z}{w})",  # Вложенные функции внутри аргументов
    # r"\sqrt{\ln(\sqrt{x + y})} + \frac{1}{\tan(z)}",  # Вложенные корни и логарифмы
    # r"\sin(\tan^{-1}(\frac{x}{y})) + \cos(\cot^{-1}(z))",  # Аргументы функций внутри других функций
    # r"\sqrt{\frac{\ln(x + \sqrt{y})}{\tan(z)}} + \frac{1}{\cos(w)}",  # Несколько вложенных операций
    # r"\ln(\sqrt{x}) + \frac{\tan(y)}{\cos(\sqrt{z})}",  # Вложенные корни в тригонометрических функциях
    # r"\frac{\tan^{-1}(x)}{\sqrt{\cot^{-1}(y) + z}}",  # Обратные функции внутри знаменателя
    # r"x + \sqrt{\frac{\sin(y)}{\ln(z + w)}}",  # Сложные комбинации вложений
    # # r"\tan^{-1}(x + \cot^{-1}(y)) + \frac{\sqrt{z}}{\ln(w)}",  # Вложенные функции и дроби
    # r"\sqrt{x + \frac{\tan(y)}{\cos(z)}}",  # Вложенные тригонометрические функции
    # r"x + \frac{\tan^{-1}(y)}{\cot^{-1}(z + \sqrt{w})}",  # Аргументы с корнями и обратными функциями
    # r"x + \frac{\sqrt{\tan(y)}}{\cos(\ln(z + w))}",  # Вложенные логарифмы и тригонометрические функции
    # r"x^2 + y^2 - \sqrt{\tan^{-1}(z^2) + \cot^{-1}(w^2)}",  # Обратные функции внутри корня
    # r"\frac{\ln(x + \sqrt{y})}{\tan(z)} + \frac{\sqrt{w}}{\cos(v)}",  # Сложные дроби и вложенные выражения
    # r"x + \tan^{-1}(\frac{y}{\sqrt{z}}) - \cot^{-1}(w)",  # Вложенные дроби в обратных функциях
    # r"x + \sqrt{\frac{\tan(y)}{\cos(\ln(z))}}",  # Вложенные логарифмы в тригонометрических функциях
    # r"\frac{\tan^{-1}(\frac{x}{y})}{\cot^{-1}(z)} + \sqrt{w + \ln(v)}",  # Сложные дроби и вложенные корни
    # r"x + \frac{\sin(y)}{\sqrt{\tan^{-1}(z + \ln(w))}}",  # Аргументы в сложных функциях
    # r"x + \tan^{-1}(\frac{\sqrt{y}}{\cos(z)}) + \cot^{-1}(w)",  # Вложенные дроби и тригонометрические функции
    # r"x^3 + \sqrt{\tan^{-1}(\frac{y}{z}) + \cot^{-1}(w)}",  # Обратные функции внутри корня
    # r"x + \frac{\tan(y)}{\cos(\ln(z + \sqrt{w}))} - \cot^{-1}(v)",  # Сложные вложения с дробями

# ])
#
# numOfFalse = np.array([])
# for i, primerExpr in enumerate(expressions):
#     print('-------------------------------------------------------------')
#     print(f"Изначальная {i + 1}: {primerExpr}")
#
#     try:
#         obj2 = Tex2Sympy(primerExpr)
#         res = obj2.get_result()
#
#         print(f"Конвертированная: {res}")
#         print('-------------------------------------------------------------')
#
#         # Проверка результата
#         if sp.simplify(res):
#             print('OK!')
#         else:
#             print('NOT OK!')
#
#     except Exception as e:
#         print(f"NOT OK! Error: {e}")
#         numOfFalse = np.append(numOfFalse, i+1)
#     print()
#
# print(numOfFalse)
# print(len(numOfFalse))
# for j in numOfFalse:
#     print(expressions[int(j)-1])

# Не обрабатывает вложенные степенные элементарные нелинейные функции
# \tan^{-1}(x + \cot^{-1}(y)) + \frac{\sqrt{z}}{\ln(w)}

# expr = '\frac45'
# expr = '(\arcsin{\frac{34}{x^2}})* (\frac{34}{x^2}) - (\arcsin{\frac{34}{x^2}})* (\frac{34}{x^2}) + 1'
# obj = Tex2Sympy(expr)
# res = obj.get_result()
# print(res)
#
# if sp.simplify(res):
#     print(sp.simplify(res))
#     print('OK!')
# else:
#     print('NOT OK!')
