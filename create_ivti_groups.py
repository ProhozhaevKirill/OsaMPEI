#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_tests.settings')
django.setup()

from users.models import StudentInstitute, StudentGroup

def create_ivti_groups():
    # Найдем институт ИВТИ
    try:
        ivti = StudentInstitute.objects.get(name__icontains='ИВТИ')
        print(f"Найден институт: {ivti.name}")
    except StudentInstitute.DoesNotExist:
        print("Институт ИВТИ не найден. Создаем...")
        ivti = StudentInstitute.objects.create(name='ИВТИ')
        print(f"Создан институт: {ivti.name}")

    # Определяем параметры групп
    group_numbers = list(range(1, 19)) + [21]  # 1-18 + группа 21
    years = [2021, 2022, 2023, 2024, 2025]  # последние 5 лет

    # Определяем курс и уровень образования по году поступления
    current_year = 2025

    created_groups = []

    for year in years:
        course = current_year - year + 1  # 1 курс = поступили в 2025, 2 курс = 2024, и т.д.

        # Определяем уровень образования
        if course <= 4:
            education_level = 'bachelor'
        else:
            education_level = 'master'
            course = course - 4  # для магистратуры курсы 1-2

        # Для магистратуры ограничиваем курсы 1-2
        if education_level == 'master' and course > 2:
            continue

        for group_num in group_numbers:
            group_name = f"А{group_num}{str(year)[-1]}"  # А + номер группы + последняя цифра года

            # Проверяем, существует ли уже такая группа
            if not StudentGroup.objects.filter(name=group_name).exists():
                try:
                    group = StudentGroup.objects.create(
                        name=group_name,
                        name_inst=ivti,
                        education_level=education_level,
                        course=course
                    )
                    created_groups.append(group_name)
                    print(f"Создана группа: {group_name} ({group.get_education_level_display()}, {group.get_course_display()})")
                except Exception as e:
                    print(f"Ошибка при создании группы {group_name}: {e}")
            else:
                print(f"Группа {group_name} уже существует")

    print(f"\nСоздано групп: {len(created_groups)}")
    print(f"Общее количество групп ИВТИ: {StudentGroup.objects.filter(name_inst=ivti).count()}")

if __name__ == "__main__":
    create_ivti_groups()