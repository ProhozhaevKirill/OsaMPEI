import subprocess

input_dot = 'schema.dot'
output_png = 'schema.png'

# Формируем команду
# Внимание: ключи здесь должны быть в нижнем регистре, как требует твой Graphviz
cmd = ['dot', '-Tpng', input_dot, '-o', output_png]

try:
    subprocess.run(cmd, check=True)
    print(f'Successfully generated {output_png}')
except subprocess.CalledProcessError as e:
    print(f'Error while generating PNG: {e}')
