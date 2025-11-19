# Юнит-тесты для системы проверки ответов

## Описание

Комплексная система юнит-тестов для проверки всех типов ответов в системе тестирования:

1. **Целые числа** (тип 1)
2. **Нецелые числа** (тип 2)
3. **Строки** (тип 3)
4. **Матрицы** (тип 4)

## Структура файлов

- `test_answer_types.py` - основной файл с тестами
- `test_runner_example.py` - примеры запуска и демонстрации
- `README_tests.md` - данная документация

## Уровни вложенности тестов

### Уровень 1 - Базовые тесты
- Основная функциональность
- Простые случаи
- Корректные входные данные

### Уровень 2 - Средние тесты
- Различные форматы ввода
- Обработка пробелов
- Граничные значения
- Точность вычислений

### Уровень 3 - Сложные тесты
- Некорректные данные
- Экстремальные случаи
- Производительность
- Граничные условия

## Запуск тестов

### Все тесты сразу
```bash
python test_answer_types.py
```

### Конкретный класс тестов
```bash
python -m unittest test_answer_types.TestIntegerAnswers
python -m unittest test_answer_types.TestFloatAnswers
python -m unittest test_answer_types.TestStringAnswers
python -m unittest test_answer_types.TestMatrixAnswers
```

### Конкретный тест
```bash
python -m unittest test_answer_types.TestIntegerAnswers.test_positive_integers
```

### С увеличенной детализацией
```bash
python -m unittest test_answer_types -v
```

## Демонстрация и примеры

```bash
# Демонстрация валидатора
python test_runner_example.py demo

# Запуск конкретных тестов
python test_runner_example.py specific

# Тест производительности
python test_runner_example.py performance
```

## Классы тестов

### TestIntegerAnswers
- 27 тестов для целых чисел
- Положительные/отрицательные числа
- Большие числа
- Обработка пробелов
- Невалидные форматы
- Ведущие нули
- Научная нотация

### TestFloatAnswers
- 33 теста для дробных чисел
- Базовые дробные числа
- Проверка точности (epsilon)
- Научная нотация
- Бесконечность и NaN
- Очень маленькие числа
- Различные значения epsilon

### TestStringAnswers
- 30 тестов для строк
- Точное совпадение
- Чувствительность к регистру
- Пустые строки
- Специальные символы
- Unicode символы
- Многострочные строки
- Очень длинные строки

### TestMatrixAnswers
- 39 тестов для матриц
- Простые матрицы 2x2, 3x3
- Различные форматы записи
- Матрицы из одного элемента
- Точность матриц
- Отрицательные числа
- Прямоугольные матрицы
- Неправильные размеры
- Большие матрицы
- Научная нотация
- Невалидные форматы

### TestComplexScenarios
- 12 комплексных тестов
- Определение типа
- Граничные значения
- Стресс-тестирование

## Покрытие тестами

**Общее количество тестов: 141**

- Целые числа: 27 тестов
- Дробные числа: 33 теста
- Строки: 30 тестов
- Матрицы: 39 тестов
- Комплексные сценарии: 12 тестов

## Примеры использования

### Валидация целого числа
```python
from test_answer_types import AnswerValidator

validator = AnswerValidator()
result = validator.validate_integer("42", "42")  # True
result = validator.validate_integer("42", "43")  # False
```

### Валидация дробного числа с точностью
```python
result = validator.validate_float("3.14", "3.15", "0.01")  # True
result = validator.validate_float("3.14", "3.15", "0.001")  # False
```

### Валидация строки с учетом регистра
```python
result = validator.validate_string("Hello", "hello", True)   # False
result = validator.validate_string("Hello", "hello", False)  # True
```

### Валидация матрицы
```python
result = validator.validate_matrix("1 2; 3 4", "1 2; 3 4")  # True
result = validator.validate_matrix("[1 2; 3 4]", "1 2; 3 4")  # True
```

## Зависимости

Для запуска тестов необходимо установить:

```bash
pip install numpy
```

Стандартные библиотеки Python:
- unittest
- re
- typing
- decimal

## Результаты тестирования

При успешном выполнении всех тестов вы увидите:
```
Ran 141 tests in X.XXXs

OK
```

При наличии ошибок будут показаны детали неудачных тестов.