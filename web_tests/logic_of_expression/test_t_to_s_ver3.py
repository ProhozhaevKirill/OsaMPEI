import re
import numpy as np
import sympy as sp

class GetLexeme:
    PER = 'abcdefghijklmnopqrstuvwxyz'
    DIGIT = '.1234567890'
    MATHFUNC = np.array(['log', 'ln',
                         'sin', 'cos', 'tan', 'cot',
                         'arcsin', 'arccos', 'arctan', 'arccot',
                         'sinh', 'cosh', 'tanh', 'coth'])

    def __init__(self, texExpr):
        self.texExpr = texExpr

    # Удаление всех обратных слешей
    def remove_backslashes(self, latex_expr):
        return re.sub(r'\\([a-zA-Z]+)', r'\1', latex_expr)

    def get_task_and_tex(self):
        replace_of_screen = [
            ('\n', '\\n'), ('\a', '\\a'), ('\b', '\\b'),
            ('\f', '\\f'), ('\r', '\\r'), ('\t', '\\t'), ('\v', '\\v')
        ]

        all_expr = self.texExpr
        for old, new in replace_of_screen:
            all_expr = all_expr.replace(old, new)

        all_expr = self.remove_backslashes(all_expr)
        all_expr = all_expr.replace('dfrac', 'frac')
        all_expr = all_expr.replace('^', '**')
        all_expr = all_expr.replace('$', '')
        all_expr = all_expr.replace('right)', ')').replace('left(', '(')

        tex_formula = ''
        for word in all_expr.split():
            if 1040 <= ord(word[0]) <= 1103:  # Проверка на кириллицу
                tex_formula += f'{word} '
            else:
                tex_formula += word

        return tex_formula.strip(), all_expr.split()

    def stack_for_math_func(self, expr, start):
        stack = []
        for i, char in enumerate(expr[start:], start=start):
            if char == '(':
                stack.append('(')
            elif char == ')':
                stack.pop()
                if not stack:
                    return i
        return -1

    def get_st_fin(self, expr_obr, flag):
        stack = []
        for i, token in enumerate(expr_obr):
            if token == '{':
                stack.append('{')
            elif token == '}':
                stack.pop()
                if not stack and flag == 1:
                    return i
        return -1

    def get_all_teg(self):
        expr = self.get_task_and_tex()[0]
        all_teg_with_1_ck = ['sqrt', 'rect']
        all_teg_with_2_ck = ['frac']

        teg_with_indices = []
        atom = ''
        i = 0

        while i < len(expr):
            if expr[i] in self.PER:
                start = i
                while i < len(expr) and expr[i] in self.PER:
                    atom += expr[i]
                    i += 1
                if atom in all_teg_with_1_ck or atom in all_teg_with_2_ck:
                    teg_with_indices.append(atom)
                    end = self.get_st_fin(expr[start:], 2 if atom in all_teg_with_2_ck else 1)
                    if end != -1:
                        teg_with_indices.append((start, start + end))
                atom = ''
            i += 1
        return teg_with_indices


class Tex2Sympy(GetLexeme):

    def frac_construct(self, unexpr):
        unexpr = unexpr.replace('frac', '').replace('}{', ')/(')
        unexpr = unexpr.replace('{', '(').replace('}', ')')
        return f"({unexpr})"

    def sqrt_construct(self, unexpr):
        if '[' in unexpr and ']' in unexpr:
            degree = unexpr[unexpr.find('[') + 1: unexpr.find(']')]
            unexpr = unexpr.replace(f"[{degree}]", "")
        else:
            degree = '2'
        unexpr = unexpr.replace('sqrt', '').replace('{', '(').replace('}', ')')
        return f"{unexpr}**(1/{degree})"

    def rect_construct(self, unexpr):
        return unexpr.replace('|', 'Abs(') + ')'

    def navigate_for_main_tags(self):
        expr = self.get_task_and_tex()[0]
        all_tex_teg = self.get_all_teg()

        for tag, (start, end) in reversed(all_tex_teg):
            tag_content = expr[start:end]
            if tag == 'frac':
                processed_tag = self.frac_construct(tag_content)
            elif tag == 'sqrt':
                processed_tag = self.sqrt_construct(tag_content)
            elif tag == 'rect':
                processed_tag = self.rect_construct(tag_content)
            else:
                processed_tag = tag_content
            expr = expr[:start] + processed_tag + expr[end:]
        return expr

    def sq_for_math_func(self, expression):
        res = ''
        i = 0
        while i < len(expression):
            atom = ''
            while i < len(expression) and expression[i] in self.PER:
                atom += expression[i]
                i += 1
            if atom in self.MATHFUNC and i < len(expression) and expression[i] == '*':
                res += f"({atom}{expression[i:]})"
                break
            res += atom
            if i < len(expression):
                res += expression[i]
            i += 1
        return res

    def addit_mult(self, expression):
        i = 0
        while i < len(expression) - 1:
            if (expression[i] in self.DIGIT and
               (expression[i + 1] in self.PER or expression[i + 1] in '([')):
                expression = expression[:i + 1] + '*' + expression[i + 1:]
            i += 1
        return expression

    def get_result(self):
        expression = self.navigate_for_main_tags().strip()
        expression = expression.replace('{', '(').replace('}', ')')
        expression = self.addit_mult(expression)
        expression = self.sq_for_math_func(expression)
        return expression


expressions = np.array([
    # Смешанные с основной разработки
    r'1 - \sqrt[3]{56} - \frac{4-1}{5-1}',
    r'1 - \frac{\frac{4}{2}-1}{5-1} - \sqrt{\sqrt[5]{66} * 56} + \sqrt{34}',
    r'1 - \sqrt{\sqrt[5]{66} * 56} + \sqrt{34}',
    r'\sqrt{\sqrt[5]{66} * 56}',
    r'\sqrt[4]{44} + \frac{12}{3}',
    r'1 + \sqrt[3]{\frac{4}{5}} - 5',
    r'\sqrt{((66))**(1/5) * 56}',
    r'\frac{1}{\frac{2}{3}}',
    r'\sqrt{1-2\sin(x)+\sin(x)^2}',

    # Простые базовые выражения
    r"x + y - z",
    r"x^2 + 2*x*y + y^2",
    r"sin(x) + cos(y)",
    r"tan(x) - \frac{1}{cot(y)}",
    r"\sqrt{x^2 + y^2}",
    r"log(x) + ln(y)",
    r"e^{x+y} + \frac{1}{e^{z}}",
    r"\frac{x}{y} + \frac{z}{w}",
    r"\sqrt{\frac{x^2}{y^2}}",
    r"x! + y! - z!",

    # Сложные вложенные выражения
    r"\frac{\sin(x)}{\cos(y)} + \tan(z)",
    r"\sqrt{e^{x^2 + y^2}}",
    r"\frac{\ln(x)}{\sqrt{y + z}}",
    r"\frac{\sqrt{\sin(x) + \cos(y)}}{z}",
    r"\sqrt{x + \frac{1}{y + z}}",
    r"\frac{\sqrt{x^2 + y^2}}{z^2}",
    r"e^{\frac{\ln(x)}{\sqrt{y}}}",
    r"\sin(\sqrt{x + \cos(y)}) + z",
    r"\tan^{-1}(x) + \cot^{-1}(y)",
    r"\frac{\sqrt{x}}{\log(y) + e^z}",

    # Еще больше конструкций с тегами
    r"\frac{\sqrt{\sin(x)}}{\cos^2(y)}",
    r"\sqrt{\frac{x}{\ln(y)}} + e^z",
    r"x + \frac{\sqrt{y}}{z + \ln(w)}",
    r"\frac{\frac{x}{\sqrt{y}}}{\sqrt{z}}",
    r"x^3 + \frac{\sqrt{y + z}}{e^w}",
    r"\ln(\sqrt{x^2 + y^2 + z^2})",
    r"x + \sqrt{\frac{y}{\sqrt{z}}}",
    r"\sin(x) + \cos(\ln(y)) + \tan(z)",
    r"\frac{\ln(x + \sqrt{y})}{e^z}",
    r"x + \frac{\sqrt{y}}{\sqrt{z}} - \ln(w)",

    # Еще более сложные конструкции
    r"x + \frac{\sin(y)}{\cos(z + \sqrt{w})}",
    r"x^2 + \frac{\sqrt{\ln(y)}}{\tan(z)}",
    r"x + y - z + \sqrt{w + e^{x - y}}",
    r"\frac{\sqrt{x + \ln(y)}}{\cos(z)}",
    r"x + \frac{\sin(y)}{\sqrt{z}} - \ln(w)",
    r"\sqrt{x + \frac{\tan(y)}{\cos(z)}}",
    r"\frac{\sqrt{\sin(x)}}{\tan(y + \ln(z))}",
    r"\frac{x}{y + \frac{z}{w}}",
    r"\tan^{-1}(\frac{x}{y}) + \cot^{-1}(z)",
    r"x^2 + y^2 - \sqrt{z^2 + w^2}",
])

# expressions = np.array([expressions[27]])

numOfFalse = np.array([])
for i, primerExpr in enumerate(expressions):
    print('-------------------------------------------------------------')
    print(f"Изначальная {i + 1}: {primerExpr}")

    try:
        obj2 = Tex2Sympy(primerExpr)
        res = obj2.get_result()

        print(f"Конвертированная: {res}")
        print('-------------------------------------------------------------')

        # Проверка результата
        if sp.simplify(res):
            print('OK!')
        else:
            print('NOT OK!')

    except Exception as e:
        print(f"NOT OK! Error: {e}")
        numOfFalse = np.append(numOfFalse, i+1)
    print()

print(numOfFalse)
print(len(numOfFalse))
for j in numOfFalse:
    print(expressions[int(j)-1])

# expr = r'\\frac{4\\sqrt2}{3}'
# obj = Tex2Sympy(expr)
# print(obj.get_result()())