from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from .models import AboutExpressions, AboutTest, Subjects, PublishedGroup, TypeAnswer, TypeNorm, TypeNormForMatrix, TaskGroup, TaskVariant, TypeNormForTaskVariant, GroupList
from users.models import StudentGroup, StudentInstitute, TeacherData
import json
from django.http import JsonResponse
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)

def parse_duration_string(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError("Неверный формат времени. Ожидается HH:MM:SS.")

        hours, minutes, seconds = map(int, parts)
        if not (0 <= minutes < 60) or not (0 <= seconds < 60) or hours < 0:
            raise ValueError("Неверное значение времени.")

        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    except Exception as e:
        raise ValueError(f"Ошибка обработки времени: {e}")


@login_required
@role_required(['teacher', 'admin'])
def create_test(request):
    all_subj = Subjects.objects.all()
    all_types_answer = TypeAnswer.objects.all()
    all_norms = TypeNorm.objects.all()

    if request.method == 'POST':
        # --- DRAFT SAVE ---
        if request.POST.get('is_draft') == 'true':
            draft_state = request.POST.get('draft_state', '{}')
            test_name = request.POST.get('name_test', '').strip() or 'Черновик'
            subj_id = request.POST.get('subj_test', '')
            try:
                subj = Subjects.objects.get(id=int(subj_id))
            except (ValueError, TypeError, Subjects.DoesNotExist):
                subj = Subjects.objects.first()
            try:
                time_h = max(0, int(request.POST.get('draft_hours', '1') or '1'))
                time_m = max(0, min(59, int(request.POST.get('draft_minutes', '30') or '30')))
            except (ValueError, TypeError):
                time_h, time_m = 1, 30
            try:
                count_attempts = max(1, int(request.POST.get('num_attempts', '1') or '1'))
            except (ValueError, TypeError):
                count_attempts = 1
            try:
                grade_5 = int(request.POST.get('grade_5_threshold', 80) or 80)
                grade_4 = int(request.POST.get('grade_4_threshold', 60) or 60)
                grade_3 = int(request.POST.get('grade_3_threshold', 35) or 35)
            except (ValueError, TypeError):
                grade_5, grade_4, grade_3 = 80, 60, 35

            teacher = TeacherData.objects.get(data_map=request.user)
            draft_slug = request.POST.get('draft_slug', '').strip()

            if draft_slug:
                try:
                    draft_test = AboutTest.objects.get(name_slug_tests=draft_slug, creator=teacher, is_draft=True)
                    draft_test.name_tests = test_name
                    draft_test.subj = subj
                    draft_test.time_to_solution = timedelta(hours=time_h, minutes=time_m)
                    draft_test.num_of_attempts = count_attempts
                    draft_test.description = request.POST.get('description_test', '')
                    draft_test.result_display_mode = request.POST.get('result_display_mode', 'only_score')
                    draft_test.grade_5_threshold = grade_5
                    draft_test.grade_4_threshold = grade_4
                    draft_test.grade_3_threshold = grade_3
                    draft_test.draft_data = draft_state
                    draft_test.save()
                    logger.info(f"Draft updated: {draft_slug}")
                    return redirect('create_tests:test_list')
                except AboutTest.DoesNotExist:
                    pass  # Fall through to create new

            draft_test = AboutTest.objects.create(
                name_tests=test_name,
                subj=subj,
                time_to_solution=timedelta(hours=time_h, minutes=time_m),
                num_of_attempts=count_attempts,
                description=request.POST.get('description_test', ''),
                creator=teacher,
                result_display_mode=request.POST.get('result_display_mode', 'only_score'),
                grade_5_threshold=grade_5,
                grade_4_threshold=grade_4,
                grade_3_threshold=grade_3,
                is_draft=True,
                draft_data=draft_state,
            )
            logger.info(f"Draft created: {draft_test.name_slug_tests}")
            return redirect('create_tests:test_list')

        try:
            logger.info("=== CREATE TEST DEBUG START ===")
            logger.info(f"POST data keys: {list(request.POST.keys())}")
            logger.info(f"POST data: {dict(request.POST)}")

            test_name = request.POST.get('name_test')
            time_to_sol_raw = request.POST.get('time_solve')
            count_attempts = request.POST.get('num_attempts')
            description_test = request.POST.get('description_test', '')
            subj_id = request.POST.get('subj_test')
            result_display_mode = request.POST.get('result_display_mode', 'only_score')

            # Получаем критерии оценивания
            grade_5_threshold = int(request.POST.get('grade_5_threshold', 80))
            grade_4_threshold = int(request.POST.get('grade_4_threshold', 60))
            grade_3_threshold = int(request.POST.get('grade_3_threshold', 35))

            logger.info(f"Basic fields - name: '{test_name}', time: '{time_to_sol_raw}', attempts: '{count_attempts}', subj_id: '{subj_id}'")

            subj = Subjects.objects.get(id=subj_id)
            time_to_sol = parse_duration_string(time_to_sol_raw)

            # Проверяем новый формат task_groups_data
            task_groups_data_raw = request.POST.get('task_groups_data', '[]')
            logger.info(f"Raw task_groups_data: {task_groups_data_raw}")

            task_groups_data = json.loads(task_groups_data_raw)
            logger.info(f"Parsed task_groups_data: {task_groups_data}")

            # Если есть данные в новом формате, используем их
            if task_groups_data:
                # Преобразуем новый формат в старый для совместимости
                points = []
                expressions = []
                answers = []
                boolAns = []
                epsilons = []
                types = []
                norms = []
                numbers = []
                block_nums = []

                for group_index, group in enumerate(task_groups_data):
                    group_points = group.get('points', '1')
                    variants = group.get('variants', [])

                    for variant_index, variant in enumerate(variants):
                        expressions.append(variant.get('expression', ''))

                        # Обрабатываем варианты ответов
                        variant_answers = variant.get('answers', '')
                        variant_epsilons = variant.get('epsilons', '')
                        variant_boolAnswers = variant.get('boolAnswers', '')

                        # Если это строки с разделителями, то это уже готовые данные
                        # Если это массивы, то нужно объединить
                        if isinstance(variant_answers, list):
                            answers.append(';'.join(str(ans) for ans in variant_answers))
                        else:
                            answers.append(str(variant_answers))

                        if isinstance(variant_epsilons, list):
                            epsilons.append(';'.join(str(eps) for eps in variant_epsilons))
                        else:
                            epsilons.append(str(variant_epsilons))

                        # Для правильных ответов нужна особая обработка
                        if isinstance(variant_boolAnswers, list):
                            # Преобразуем в бинарную строку: True/1 -> "1", False/0 -> "0"
                            bool_binary = []
                            for val in variant_boolAnswers:
                                if str(val).lower() in ['true', '1', 'yes']:
                                    bool_binary.append('1')
                                else:
                                    bool_binary.append('0')
                            boolAns.append(';'.join(bool_binary))
                        else:
                            # Одиночное значение
                            if str(variant_boolAnswers).lower() in ['true', '1', 'yes']:
                                boolAns.append('1')
                            else:
                                boolAns.append('0')

                        # Проверяем, что типы и нормы не пустые
                        variant_type = variant.get('types', '')
                        variant_norm = variant.get('norms', '')
                        types.append(variant_type if variant_type else None)
                        norms.append(variant_norm if variant_norm else None)
                        points.append(group_points)

                        # Номер варианта внутри группы (1, 2, 3...)
                        numbers.append(variant_index + 1)
                        # Номер группы (блока) заданий (1, 2, 3...)
                        block_nums.append(group_index + 1)

                logger.info(f"Converted data - expressions count: {len(expressions)}, answers: {answers}")
                logger.info(f"boolAns: {boolAns}")

            else:
                # Старая система
                points_raw = request.POST.get('point_solve', '[]')
                expressions_raw = request.POST.get('user_expression', '[]')
                answers_raw = request.POST.get('user_ans', '[]')
                boolAns_raw = request.POST.get('user_bool_ans', '[]')
                epsilons_raw = request.POST.get('user_eps', '[]')
                types_raw = request.POST.get('user_type', '[]')
                norms_raw = request.POST.get('user_norm', '[]')

                logger.info(f"Raw data - points: {points_raw}, expressions: {expressions_raw}")

                points = json.loads(points_raw)
                expressions = json.loads(expressions_raw)
                answers = json.loads(answers_raw)
                boolAns = json.loads(boolAns_raw)
                epsilons = json.loads(epsilons_raw)
                types = json.loads(types_raw)
                norms = json.loads(norms_raw)

            logger.info(f"Parsed data - expressions count: {len(expressions)}, points count: {len(points)}")

            # Получаем данные преподавателя
            teacher = TeacherData.objects.get(data_map=request.user)

            # Сохраняем тест (slug создается автоматически в модели)
            new_test = AboutTest.objects.create(
                name_tests=test_name,
                time_to_solution=time_to_sol,
                num_of_attempts=count_attempts,
                subj=subj,
                description=description_test,
                creator=teacher,
                result_display_mode=result_display_mode,
                grade_5_threshold=grade_5_threshold,
                grade_4_threshold=grade_4_threshold,
                grade_3_threshold=grade_3_threshold,
            )

            # Проверяем, есть ли хотя бы одно валидное выражение
            valid_expressions = []
            for i, (expr, ans, bool_ans, eps, type_id, point, norm_id) in enumerate(zip(expressions, answers, boolAns, epsilons, types, points, norms)):
                if expr.strip() and type_id and type_id != '' and type_id is not None:  # Проверяем выражение и тип
                    valid_expressions.append((expr, ans, bool_ans, eps, type_id, point, norm_id))

            logger.info(f"Found {len(valid_expressions)} valid expressions out of {len(expressions)}")

            # Получаем номера блоков и задач из формы (только для старого формата)
            if not task_groups_data:
                numbers_raw = request.POST.get('number', '[]')
                block_nums_raw = request.POST.get('block_expression_num', '[]')

                logger.info(f"Numbers raw: {numbers_raw}, Block nums raw: {block_nums_raw}")

                try:
                    numbers = json.loads(numbers_raw)
                    block_nums = json.loads(block_nums_raw)
                except json.JSONDecodeError:
                    numbers = [i+1 for i in range(len(expressions))]  # По умолчанию 1, 2, 3...
                    block_nums = [1] * len(expressions)  # По умолчанию все в блоке 1

            # Добавляем выражения
            if valid_expressions:
                for i, (expr, ans, bool_ans, eps, type_id, point, norm_id) in enumerate(valid_expressions):
                    try:
                        logger.info(f"Processing expression {i+1}: {expr[:50]}...")
                        logger.info(f"Data: ans='{ans}', bool_ans='{bool_ans}', eps='{eps}', type_id='{type_id}', point='{point}', norm_id='{norm_id}'")

                        flag_select = ';' in bool_ans
                        logger.info(f"flag_select = {flag_select}")

                        # Проверяем, что type_id не пустой и не None
                        if not type_id or type_id == '' or type_id is None:
                            logger.error(f"Empty type_id for expression {i+1}")
                            continue

                        try:
                            type_obj = TypeAnswer.objects.get(id=int(type_id))
                        except (ValueError, TypeError, TypeAnswer.DoesNotExist):
                            logger.error(f"Invalid type_id '{type_id}' for expression {i+1}")
                            continue
                        logger.info(f"type_obj = {type_obj}")

                        # Получаем номер задания и номер блока
                        task_number = numbers[i] if i < len(numbers) else i + 1
                        block_number = block_nums[i] if i < len(block_nums) else 1

                        expr_instance = AboutExpressions.objects.create(
                            user_expression=expr,
                            user_ans=ans,
                            true_ans=bool_ans,
                            user_eps=eps or "0",
                            user_type=type_obj,
                            points_for_solve=int(point) if point else 1,
                            exist_select=flag_select,
                            number=task_number,
                            block_expression_num=block_number
                        )
                        logger.info(f"Created expression instance: {expr_instance} with number={task_number}, block={block_number}")

                        new_test.expressions.add(expr_instance)
                        logger.info(f"Added expression {i+1} successfully")

                        # Добавляем норму матрицы, если тип ответа - матрицы (type_code = 4) и указана норма
                        if type_obj.type_code == 4 and norm_id and norm_id != '' and norm_id is not None:
                            try:
                                norm_obj = TypeNorm.objects.get(id=norm_id)
                                TypeNormForMatrix.objects.create(
                                    num_expr=expr_instance,
                                    matrix_norms=norm_obj
                                )
                                logger.info(f"Created norm relation for expression {i+1}")
                            except (TypeNorm.DoesNotExist, ValueError):
                                logger.warning(f"Invalid norm ID {norm_id} for expression {i+1}")
                                pass  # Игнорируем неправильные ID норм
                    except Exception as e:
                        logger.error(f"Error processing expression {i+1}: {str(e)}")
                        raise
            else:
                logger.warning("No valid expressions found")
                # Удаляем тест, если нет валидных выражений
                new_test.delete()
                return render(request, 'create_tests/writing_tests.html', {
                    'all_subj': all_subj,
                    'all_types_answer': all_types_answer,
                    'all_norms': all_norms,
                    'error_msg': 'Не найдено ни одного валидного задания. Проверьте, что все поля заполнены корректно.'
                })

            new_test.save()
            logger.info("=== CREATE TEST DEBUG END ===")
            return redirect('create_tests:test_list')

        except Exception as e:
            logger.error(f"CREATE TEST ERROR: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            return render(request, 'create_tests/writing_tests.html', {
                'all_subj': all_subj,
                'all_types_answer': all_types_answer,
                'all_norms': all_norms,
                'error_msg': str(e)
            })

    return render(request, 'create_tests/writing_tests.html',
                {'all_subj': all_subj,
                        'all_types_answer': all_types_answer,
                        'all_norms': all_norms},
                )


@login_required
@role_required(['teacher', 'admin'])
def edit_draft(request, slug_name):
    draft = get_object_or_404(AboutTest, name_slug_tests=slug_name, is_draft=True)
    teacher = get_object_or_404(TeacherData, data_map=request.user)
    if draft.creator != teacher:
        return redirect('create_tests:test_list')

    all_subj = Subjects.objects.all()
    all_types_answer = TypeAnswer.objects.all()
    all_norms = TypeNorm.objects.all()

    return render(request, 'create_tests/writing_tests.html', {
        'all_subj': all_subj,
        'all_types_answer': all_types_answer,
        'all_norms': all_norms,
        'draft_slug': slug_name,
        'draft_data_json': draft.draft_data or '{}',
    })


@login_required
@role_required(['teacher', 'admin'])
def test_list(request):
    all_groups = StudentGroup.objects.all().select_related('institute')
    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    # Получаем текущего учителя
    current_teacher = get_object_or_404(TeacherData, data_map=request.user)

    # Параметр фильтрации: 'my' для моих тестов, 'all' для всех тестов
    filter_type = request.GET.get('filter', 'my')

    if filter_type == 'my':
        # Показываем только тесты текущего преподавателя
        tests = AboutTest.objects.filter(creator=current_teacher).select_related('creator')
        # Если у преподавателя нет собственных тестов, показываем все тесты и меняем фильтр
        if not tests.exists():
            tests = AboutTest.objects.all().select_related('creator')
            filter_type = 'all'  # Меняем тип фильтра для корректного отображения в UI
    else:
        # Показываем все тесты с информацией о создателе
        tests = AboutTest.objects.all().select_related('creator')

    published = PublishedGroup.objects.select_related('group_name', 'test_name')
    published_groups = [pg.group_name for pg in published]

    # Получаем сохраненные списки групп для текущего преподавателя
    from .models import GroupList
    saved_group_lists = GroupList.objects.filter(teacher=current_teacher).prefetch_related('groups')

    return render(request, 'create_tests/all_test_for_teach.html', {
        'tests': tests,
        'all_groups': all_groups,
        'institutes': institutes,
        'groups': published_groups,
        'published': published,
        'saved_group_lists': saved_group_lists,
        'current_teacher': current_teacher,
        'filter_type': filter_type,
    })


@login_required
@role_required(['teacher', 'admin'])
def some_test(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)

    # Получаем текущего преподавателя для проверки прав доступа
    current_teacher = get_object_or_404(TeacherData, data_map=request.user)

    # Получаем данные для модального окна публикации
    all_groups = StudentGroup.objects.all().select_related('institute')
    institutes = StudentInstitute.objects.all().prefetch_related('studentgroup_set')

    # Получаем сохраненные списки групп для текущего преподавателя
    from .models import GroupList
    saved_group_lists = GroupList.objects.filter(teacher=current_teacher).prefetch_related('groups')

    # Проверяем, какую систему использует тест
    task_groups = test.task_groups.all()

    if task_groups.exists():
        # Новая система: TaskGroup и TaskVariant
        task_groups_data = []
        for group in task_groups.order_by('number'):
            variants_data = []
            for variant in group.variants.all():
                # Получаем норму матрицы, если есть
                norm_for_variant = TypeNormForTaskVariant.objects.filter(task_variant=variant).first()

                variants_data.append({
                    'id': variant.id,
                    'user_expression': variant.user_expression,
                    'user_ans': variant.user_ans,
                    'true_ans': variant.true_ans,
                    'user_eps': variant.user_eps,
                    'user_type': variant.user_type,
                    'exist_select': variant.exist_select,
                    'matrix_norm': norm_for_variant.matrix_norms if norm_for_variant else None,
                })

            task_groups_data.append({
                'id': group.id,
                'number': group.number,
                'points_for_solve': group.points_for_solve,
                'variants': variants_data
            })

        # Подсчет количества заданий и общего количества вариантов для новой системы
        total_tasks = len(task_groups_data)  # Количество групп заданий
        total_variants = sum(len(group['variants']) for group in task_groups_data)  # Общее количество вариантов

        return render(request, 'create_tests/some_test.html', {
            'test': test,
            'task_groups_data': task_groups_data,
            'total_tasks': total_tasks,
            'total_variants': total_variants,
            'uses_new_system': True,
            'institutes': institutes,
            'all_groups': all_groups,
            'saved_group_lists': saved_group_lists,
            'current_teacher': current_teacher
        })
    else:
        # Старая система: AboutExpressions
        from collections import defaultdict

        expressions_by_block = defaultdict(list)
        for expr in test.expressions.all().order_by('block_expression_num', 'number'):
            block_num = expr.block_expression_num if hasattr(expr, 'block_expression_num') and expr.block_expression_num else 1
            expressions_by_block[block_num].append(expr)

        # Преобразуем в формат для отображения
        task_groups_data = []
        for block_num in sorted(expressions_by_block.keys()):
            expressions = expressions_by_block[block_num]
            if not expressions:
                continue

            variants_data = []
            for expr in expressions:
                # Получаем норму матрицы, если есть
                norm_for_matrix = TypeNormForMatrix.objects.filter(num_expr=expr).first()

                variants_data.append({
                    'id': expr.id,
                    'user_expression': expr.user_expression,
                    'user_ans': expr.user_ans,
                    'true_ans': expr.true_ans,
                    'user_eps': expr.user_eps,
                    'user_type': expr.user_type,
                    'exist_select': expr.exist_select,
                    'matrix_norm': norm_for_matrix.matrix_norms if norm_for_matrix else None,
                })

            task_groups_data.append({
                'id': f'block_{block_num}',
                'number': block_num,
                'points_for_solve': expressions[0].points_for_solve,
                'variants': variants_data
            })

        # Подсчет количества заданий и общего количества вариантов для старой системы
        total_tasks = len(task_groups_data)  # Количество блоков заданий
        total_variants = sum(len(group['variants']) for group in task_groups_data)  # Общее количество выражений

        return render(request, 'create_tests/some_test.html', {
            'test': test,
            'task_groups_data': task_groups_data,
            'total_tasks': total_tasks,
            'total_variants': total_variants,
            'uses_new_system': False,
            'institutes': institutes,
            'all_groups': all_groups,
            'saved_group_lists': saved_group_lists,
            'current_teacher': current_teacher
        })


@login_required
@role_required(['teacher', 'admin'])
def delete_test(request, slug_name):
    if request.method == "POST":
        try:
            test = get_object_or_404(AboutTest, name_slug_tests=slug_name)

            # Удаляем связанные данные в зависимости от системы
            task_groups = test.task_groups.all()

            if task_groups.exists():
                # Новая система: удаляем TaskGroup и TaskVariant (каскадно)
                for task_group in task_groups:
                    # TaskVariant удалятся автоматически через каскадное удаление
                    # TypeNormForTaskVariant тоже удалятся автоматически
                    task_group.delete()
            else:
                # Старая система: удаляем AboutExpressions
                expressions = test.expressions.all()
                for expr in expressions:
                    # TypeNormForMatrix удалятся автоматически через каскадное удаление
                    expr.delete()

            # Удаляем связанные результаты студентов
            from solving_tests.models import StudentResult
            StudentResult.objects.filter(test=test).delete()

            # Удаляем связанные публикации
            PublishedGroup.objects.filter(test_name=test).delete()

            # Теперь удаляем сам тест
            test.delete()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"error": "Неверный метод запроса"}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def publish_test(request, slug_name):
    if request.method == "POST":
        try:
            test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
            teacher = get_object_or_404(TeacherData, data_map=request.user)
            data = json.loads(request.body)
            group_ids = data.get('groups', [])

            # Удаляем предыдущие публикации
            PublishedGroup.objects.filter(test_name=test).delete()

            # Создаем новые записи публикации
            for group_id in group_ids:
                group = get_object_or_404(StudentGroup, id=group_id)
                PublishedGroup.objects.create(
                    test_name=test,
                    teacher_name=teacher,
                    group_name=group
                )

            test.is_published = 1
            test.save()
            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Publish error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def unpublish_test(request, slug_name):
    if request.method == "POST":
        try:
            test = AboutTest.objects.get(name_slug_tests=slug_name)
            PublishedGroup.objects.filter(test_name=test).delete()
            test.is_published = False
            test.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@role_required(['teacher', 'admin'])
def create_draft_test(request):
    # Создаем пустой черновик и редиректим на редактирование
    try:
        teacher = TeacherData.objects.get(data_map=request.user)
        draft_test = AboutTest.objects.create(
            name_tests='Новый черновик',
            num_of_attempts=1,
            description='',
            time_to_solution=timedelta(minutes=30),
            is_draft=True,
            creator=teacher
        )
    except TeacherData.DoesNotExist:
        draft_test = AboutTest.objects.create(
            name_tests='Новый черновик',
            num_of_attempts=1,
            description='',
            time_to_solution=timedelta(minutes=30),
            is_draft=True
        )
    return redirect('create_tests:edit_test', slug_name=draft_test.name_slug_tests)


@login_required
@role_required(['teacher', 'admin'])
def edit_test(request, slug_name):
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    all_subj = Subjects.objects.all()
    all_types_answer = TypeAnswer.objects.all()
    all_norms = TypeNorm.objects.all()

    if request.method == 'POST':
        try:
            logger.info(f"POST data received: {request.POST}")

            # Обновляем основные поля теста
            test.name_tests = request.POST.get('name_test', test.name_tests)
            test.num_of_attempts = int(request.POST.get('num_attempts', test.num_of_attempts))
            test.description = request.POST.get('description_test', test.description)
            test.result_display_mode = request.POST.get('result_display_mode', test.result_display_mode)

            # Обновляем предмет
            subj_id = request.POST.get('subj_test')
            if subj_id:
                test.subj = Subjects.objects.get(id=subj_id)

            # Обновляем время (парсим из строки формата HH:MM:SS)
            time_to_sol_raw = request.POST.get('time_solve')
            if time_to_sol_raw:
                test.time_to_solution = parse_duration_string(time_to_sol_raw)

            # Проверяем новый формат task_groups_data
            task_groups_data_raw = request.POST.get('task_groups_data', '[]')
            logger.info(f"Raw task_groups_data: {task_groups_data_raw}")

            task_groups_data = json.loads(task_groups_data_raw)
            logger.info(f"Parsed task_groups_data: {task_groups_data}")

            # Если есть данные в новом формате, сохраняем в TaskGroup/TaskVariant
            if task_groups_data:
                logger.info("Saving test in new TaskGroup/TaskVariant format")

                # Удаляем старые TaskGroup и AboutExpressions
                test.task_groups.all().delete()
                test.expressions.all().delete()

                for group_index, group in enumerate(task_groups_data):
                    group_points = int(group.get('points', '1'))
                    variants = group.get('variants', [])

                    if not variants:
                        continue

                    # Создаем TaskGroup
                    task_group = TaskGroup.objects.create(
                        number=group_index + 1,
                        points_for_solve=group_points
                    )

                    # Добавляем TaskGroup к тесту
                    test.task_groups.add(task_group)

                    # Создаем TaskVariant для каждого варианта
                    for variant_index, variant in enumerate(variants):
                        expression = variant.get('expression', '')
                        if not expression.strip():
                            continue

                        # Обрабатываем варианты ответов
                        variant_answers = variant.get('answers', '')
                        variant_epsilons = variant.get('epsilons', '')
                        variant_boolAnswers = variant.get('boolAnswers', '')

                        # Преобразуем ответы в строки
                        if isinstance(variant_answers, list):
                            user_ans = ';'.join(str(ans) for ans in variant_answers)
                        else:
                            user_ans = str(variant_answers)

                        if isinstance(variant_epsilons, list):
                            user_eps = ';'.join(str(eps) for eps in variant_epsilons)
                        else:
                            user_eps = str(variant_epsilons) or "0"

                        # Для правильных ответов
                        if isinstance(variant_boolAnswers, list):
                            bool_binary = []
                            for val in variant_boolAnswers:
                                if str(val).lower() in ['true', '1', 'yes']:
                                    bool_binary.append('1')
                                else:
                                    bool_binary.append('0')
                            true_ans = ';'.join(bool_binary)
                        else:
                            if str(variant_boolAnswers).lower() in ['true', '1', 'yes']:
                                true_ans = '1'
                            else:
                                true_ans = '0'

                        type_id = variant.get('types', '')
                        norm_id = variant.get('norms', '')

                        if not type_id:
                            continue

                        flag_select = ';' in true_ans
                        try:
                            type_obj = TypeAnswer.objects.get(id=int(type_id))
                        except (ValueError, TypeError, TypeAnswer.DoesNotExist):
                            logger.error(f"Invalid type_id '{type_id}' for variant {variant_index + 1}")
                            continue

                        # Создаем TaskVariant
                        task_variant = TaskVariant.objects.create(
                            task_group=task_group,
                            user_expression=expression,
                            user_ans=user_ans,
                            true_ans=true_ans,
                            user_eps=user_eps,
                            user_type=type_obj,
                            exist_select=flag_select
                        )

                        # Добавляем норму матрицы, если нужно
                        if type_obj.type_code == 4 and norm_id:
                            try:
                                norm_obj = TypeNorm.objects.get(id=norm_id)
                                TypeNormForTaskVariant.objects.create(
                                    task_variant=task_variant,
                                    matrix_norms=norm_obj
                                )
                                logger.info(f"Created norm relation for variant {variant_index + 1}")
                            except (TypeNorm.DoesNotExist, ValueError):
                                logger.warning(f"Invalid norm ID {norm_id} for variant {variant_index + 1}")

                logger.info(f"Created {len(task_groups_data)} task groups in new format")
            else:
                # Старая система или отсутствие данных - используем AboutExpressions
                points_raw = request.POST.get('point_solve', '[]')
                expressions_raw = request.POST.get('user_expression', '[]')
                answers_raw = request.POST.get('user_ans', '[]')
                boolAns_raw = request.POST.get('user_bool_ans', '[]')
                epsilons_raw = request.POST.get('user_eps', '[]')
                types_raw = request.POST.get('user_type', '[]')
                norms_raw = request.POST.get('user_norm', '[]')
                numbers_raw = request.POST.get('number', '[]')
                block_nums_raw = request.POST.get('block_expression_num', '[]')

                logger.info(f"Raw data - points: {points_raw}, expressions: {expressions_raw}")

                points = json.loads(points_raw)
                expressions = json.loads(expressions_raw)
                answers = json.loads(answers_raw)
                boolAns = json.loads(boolAns_raw)
                epsilons = json.loads(epsilons_raw)
                types = json.loads(types_raw)
                norms = json.loads(norms_raw)

                try:
                    numbers = json.loads(numbers_raw)
                    block_nums = json.loads(block_nums_raw)
                except json.JSONDecodeError:
                    numbers = [i+1 for i in range(len(expressions))]  # По умолчанию 1, 2, 3...
                    block_nums = [1] * len(expressions)  # По умолчанию все в блоке 1

                logger.info(f"Parsed data - expressions count: {len(expressions)}, points count: {len(points)}")

                # Проверяем, есть ли хотя бы одно валидное выражение
                valid_expressions = []
                for i, (expr, ans, bool_ans, eps, type_id, point, norm_id) in enumerate(zip(expressions, answers, boolAns, epsilons, types, points, norms)):
                    if expr.strip() and type_id:  # Проверяем и выражение, и тип
                        valid_expressions.append((expr, ans, bool_ans, eps, type_id, point, norm_id))

                logger.info(f"Found {len(valid_expressions)} valid expressions out of {len(expressions)}")

                # Удаляем старые выражения только если есть валидные новые данные
                if valid_expressions:
                    logger.info("Deleting old expressions...")
                    test.expressions.all().delete()
                    test.task_groups.all().delete()  # Также удаляем task_groups при сохранении в старом формате

                    # Добавляем новые выражения
                    for i, (expr, ans, bool_ans, eps, type_id, point, norm_id) in enumerate(valid_expressions):
                        try:
                            logger.info(f"Processing expression {i+1}: {expr[:50]}...")
                            logger.info(f"Data: ans='{ans}', bool_ans='{bool_ans}', eps='{eps}', type_id='{type_id}', point='{point}', norm_id='{norm_id}'")

                            flag_select = ';' in bool_ans
                            logger.info(f"flag_select = {flag_select}")

                            try:
                                type_obj = TypeAnswer.objects.get(id=int(type_id))
                                logger.info(f"type_obj = {type_obj}")
                            except (ValueError, TypeError, TypeAnswer.DoesNotExist):
                                logger.error(f"Invalid type_id '{type_id}' for expression {i+1}")
                                continue

                            # Получаем номер задания и номер блока
                            task_number = numbers[i] if i < len(numbers) else i + 1
                            block_number = block_nums[i] if i < len(block_nums) else 1

                            expr_instance = AboutExpressions.objects.create(
                                user_expression=expr,
                                user_ans=ans,
                                true_ans=bool_ans,
                                user_eps=eps or "0",
                                user_type=type_obj,
                                points_for_solve=int(point) if point else 1,
                                exist_select=flag_select,
                                number=task_number,
                                block_expression_num=block_number
                            )
                            logger.info(f"Created expression instance: {expr_instance} with number={task_number}, block={block_number}")

                            test.expressions.add(expr_instance)
                            logger.info(f"Added expression {i+1} successfully")

                            # Добавляем норму матрицы, если тип ответа - матрицы (type_code = 4) и указана норма
                            if type_obj.type_code == 4 and norm_id:
                                try:
                                    norm_obj = TypeNorm.objects.get(id=norm_id)
                                    TypeNormForMatrix.objects.create(
                                        num_expr=expr_instance,
                                        matrix_norms=norm_obj
                                    )
                                    logger.info(f"Created norm relation for expression {i+1}")
                                except (TypeNorm.DoesNotExist, ValueError):
                                    logger.warning(f"Invalid norm ID {norm_id} for expression {i+1}")
                                    pass  # Игнорируем неправильные ID норм
                        except Exception as e:
                            logger.error(f"Error processing expression {i+1}: {str(e)}")
                            raise
                else:
                    logger.warning("No valid expressions found, keeping existing expressions")

            test.save()
            logger.info("Test saved successfully")
            return redirect('create_tests:test_list')

        except Exception as e:
            messages.error(request, f"Ошибка при сохранении: {str(e)}")
            return redirect('create_tests:edit_test', slug_name=slug_name)

    # GET запрос - подготовка данных для отображения
    # Группируем выражения по block_expression_num (номер задания)
    from collections import defaultdict

    task_groups_data = []
    expressions_by_block = defaultdict(list)

    # Сначала группируем все выражения по номеру блока
    for expr in test.expressions.all().order_by('block_expression_num', 'number'):
        block_num = expr.block_expression_num if hasattr(expr, 'block_expression_num') and expr.block_expression_num else 1
        expressions_by_block[block_num].append(expr)

    # Теперь обрабатываем каждую группу (задание)
    for block_num in sorted(expressions_by_block.keys()):
        variants_data = []
        block_expressions = expressions_by_block[block_num]

        # Получаем первое выражение для баллов (все варианты одного задания имеют одинаковые баллы)
        first_expr = block_expressions[0]
        points_for_solve = first_expr.points_for_solve

        # Обрабатываем каждый вариант в этом блоке
        for expr in block_expressions:
            # Разбираем данные выражения для отображения
            ans_list = expr.user_ans.split(';') if ';' in expr.user_ans else [expr.user_ans]
            eps_list = expr.user_eps.split(';') if ';' in expr.user_eps else [expr.user_eps]
            bool_list = expr.true_ans.split(';') if ';' in expr.true_ans else [expr.true_ans]

            # Получаем норму матрицы для этого выражения
            norm_for_matrix = TypeNormForMatrix.objects.filter(num_expr=expr).first()
            norm_id = norm_for_matrix.matrix_norms.id if norm_for_matrix and norm_for_matrix.matrix_norms else ''

            # Подготавливаем список ответов
            answers_data = []
            for i, (ans, eps, bool_val) in enumerate(zip(ans_list, eps_list, bool_list)):
                answers_data.append({
                    'user_ans': ans,
                    'user_eps': eps,
                    'user_type_id': expr.user_type.id if expr.user_type else '',
                    'user_norm_id': norm_id,
                    'is_correct': bool_val == '1'
                })

            variants_data.append({
                'user_expression': expr.user_expression,
                'answers': answers_data,
                'variant_number': expr.number if hasattr(expr, 'number') and expr.number else 1
            })

        task_groups_data.append({
            'block_number': block_num,
            'points_for_solve': points_for_solve,
            'variants': variants_data
        })

    # Если нет данных, создаем пустую структуру для новых тестов
    if not task_groups_data:
        task_groups_data = []

    # Разбираем время для отображения
    total_seconds = int(test.time_to_solution.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    context = {
        'test': test,
        'task_groups_data': task_groups_data,
        'all_subj': all_subj,
        'all_types_answer': all_types_answer,
        'all_norms': all_norms,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
    }
    return render(request, 'create_tests/editing_tests.html', context)


@login_required
@role_required(['teacher', 'admin'])
def save_group_set(request):
    """Сохранение набора групп в базу данных"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            groups_ids = request.POST.getlist('groups')

            # Получаем текущего преподавателя
            teacher = TeacherData.objects.get(data_map=request.user)

            # Валидация данных
            if not name:
                return JsonResponse({'success': False, 'error': 'Название набора не может быть пустым'})

            if not groups_ids:
                return JsonResponse({'success': False, 'error': 'Необходимо выбрать хотя бы одну группу'})

            # Проверяем, что все группы существуют
            groups = StudentGroup.objects.filter(id__in=groups_ids)
            if len(groups) != len(groups_ids):
                return JsonResponse({'success': False, 'error': 'Некоторые группы не найдены'})

            # Проверяем, что набор с таким именем у данного преподавателя не существует
            if GroupList.objects.filter(name=name, teacher=teacher).exists():
                return JsonResponse({'success': False, 'error': 'Набор с таким названием уже существует'})

            # Создаем набор групп
            group_list = GroupList.objects.create(
                name=name,
                teacher=teacher
            )

            # Добавляем группы к набору
            group_list.groups.set(groups)

            return JsonResponse({
                'success': True,
                'message': 'Набор групп успешно сохранен',
                'group_list_id': group_list.id
            })

        except TeacherData.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Преподаватель не найден'})
        except Exception as e:
            logger.error(f"Ошибка при сохранении набора групп: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при сохранении'})

    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
@role_required(['teacher', 'admin'])
def get_group_lists(request):
    """Получение всех сохраненных списков групп преподавателя"""
    try:
        teacher = TeacherData.objects.get(data_map=request.user)
        group_lists = GroupList.objects.filter(teacher=teacher).prefetch_related('groups')

        lists_data = []
        for group_list in group_lists:
            lists_data.append({
                'id': group_list.id,
                'name': group_list.name,
                'groups_count': group_list.groups.count(),
                'groups': list(group_list.groups.values('id', 'name'))
            })

        return JsonResponse({
            'success': True,
            'group_lists': lists_data
        })

    except TeacherData.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Преподаватель не найден'})
    except Exception as e:
        logger.error(f"Ошибка при получении списков групп: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Произошла ошибка при загрузке списков'})


@login_required
@role_required(['teacher', 'admin'])
def get_group_list(request, list_id):
    """Получение информации о сохраненном списке групп"""
    try:
        teacher = TeacherData.objects.get(data_map=request.user)
        group_list = get_object_or_404(GroupList, id=list_id, teacher=teacher)

        return JsonResponse({
            'success': True,
            'name': group_list.name,
            'groups': list(group_list.groups.values_list('id', flat=True))
        })

    except TeacherData.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Преподаватель не найден'})
    except Exception as e:
        logger.error(f"Ошибка при получении списка групп: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Произошла ошибка при загрузке списка'})


@login_required
@role_required(['teacher', 'admin'])
def delete_group_list(request, list_id):
    """Удаление сохраненного списка групп"""
    if request.method == 'POST':
        try:
            teacher = TeacherData.objects.get(data_map=request.user)
            group_list = get_object_or_404(GroupList, id=list_id, teacher=teacher)

            group_list_name = group_list.name
            group_list.delete()

            return JsonResponse({
                'success': True,
                'message': f'Список "{group_list_name}" успешно удален'
            })

        except TeacherData.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Преподаватель не найден'})
        except Exception as e:
            logger.error(f"Ошибка при удалении списка групп: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при удалении списка'})

    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


def get_randomized_test_for_teacher(test, teacher_id, seed=None):
    """
    Генерирует рандомизированный вариант теста для преподавателя
    Использует логику аналогичную студентам, но со случайным seed
    """
    import random
    import time

    # Создаем seed на основе текущего времени и ID преподавателя (если не передан)
    if seed is None:
        seed = int(time.time()) + teacher_id
    random.seed(seed)

    randomized_expressions = []

    # Проверяем, использует ли тест новую систему TaskGroup
    task_groups = test.task_groups.all()

    if task_groups.exists():
        # Новая система: используем TaskGroup и TaskVariant
        for task_group in task_groups.order_by('number', 'id'):
            variants = task_group.variants.order_by('id')
            if variants:
                # Выбираем случайный вариант из группы
                selected_variant = random.choice(list(variants))

                # Получаем норму матрицы для TaskVariant
                norm_for_task = TypeNormForTaskVariant.objects.filter(task_variant=selected_variant).first()

                randomized_expressions.append({
                    'user_expression': selected_variant.user_expression,
                    'user_ans': selected_variant.user_ans,
                    'true_ans': selected_variant.true_ans,
                    'user_eps': selected_variant.user_eps,
                    'user_type': selected_variant.user_type,
                    'points_for_solve': task_group.points_for_solve,
                    'exist_select': selected_variant.exist_select,
                    'matrix_norm': norm_for_task.matrix_norms if norm_for_task else None,
                    'number': task_group.number,
                    'block_expression_num': task_group.number
                })
    else:
        # Старая система: используем AboutExpressions
        from collections import defaultdict
        blocks = defaultdict(list)

        for ex in test.expressions.order_by('block_expression_num', 'id'):
            blocks[ex.block_expression_num].append(ex)

        # Из каждого блока выбираем случайное задание
        selected_expressions = []
        for block_num, expressions in blocks.items():
            if expressions:
                # Выбираем случайное задание из блока
                selected_expression = random.choice(expressions)
                selected_expressions.append(selected_expression)

        # Сортируем по полю number для правильного порядка
        selected_expressions.sort(key=lambda x: x.number)

        # Формируем окончательный список
        for ex in selected_expressions:
            norm_for_matrix = TypeNormForMatrix.objects.filter(num_expr=ex).first()
            randomized_expressions.append({
                'user_expression': ex.user_expression,
                'user_ans': ex.user_ans,
                'true_ans': ex.true_ans,
                'user_eps': ex.user_eps,
                'user_type': ex.user_type,
                'points_for_solve': ex.points_for_solve,
                'exist_select': ex.exist_select,
                'matrix_norm': norm_for_matrix.matrix_norms if norm_for_matrix else None,
                'number': ex.number,
                'block_expression_num': ex.block_expression_num
            })

    return randomized_expressions


@login_required
@role_required(['teacher', 'admin'])
def solve_test_teacher(request, slug_name):
    """Решение теста преподавателем"""
    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    teacher = request.user

    # Seed сохраняется в сессию на GET, читается на POST — чтобы выбранные варианты совпадали
    session_key = f'teacher_test_seed_{slug_name}'
    if request.method == 'POST':
        seed = request.session.get(session_key)
    else:
        import time
        seed = int(time.time()) + teacher.id
        request.session[session_key] = seed

    # Получаем рандомизированный вариант теста для преподавателя
    expressions_data = get_randomized_test_for_teacher(test, teacher.id, seed=seed)

    if request.method == 'POST':
        raw = request.POST.get('binaryAnswers', '[]')
        try:
            teacher_answers = json.loads(raw)
        except json.JSONDecodeError:
            teacher_answers = []

        n = len(expressions_data)
        if len(teacher_answers) < n:
            teacher_answers += [''] * (n - len(teacher_answers))
        elif len(teacher_answers) > n:
            teacher_answers = teacher_answers[:n]

        result_score = 0
        all_points = sum(expr['points_for_solve'] for expr in expressions_data)

        # Используем ту же логику проверки, что и для студентов
        from logic_of_expression.check_sympy_expr import CheckAnswer

        task_results = []
        for i, expr_data in enumerate(expressions_data):
            user_ans = teacher_answers[i]

            if expr_data['exist_select']:
                # Multiple choice question - проверяем правильность выбранных вариантов
                # Разбираем варианты ответов и правильные ответы
                available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                correct_answers = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []

                # Получаем выбранные пользователем варианты
                if isinstance(user_ans, str):
                    selected_options = user_ans.split(';') if user_ans else []
                elif isinstance(user_ans, list):
                    selected_options = user_ans
                else:
                    selected_options = []

                # Проверяем правильность
                res = 1  # Начинаем с полного балла

                # Создаем множества для сравнения
                selected_set = set(selected_options)

                # Определяем какие варианты должны быть выбраны
                should_be_selected = set()
                for j, flag in enumerate(correct_answers):
                    if j < len(available_options) and flag == '1':
                        should_be_selected.add(available_options[j])

                # Проверяем точное совпадение
                if selected_set != should_be_selected:
                    res = 0
            else:
                # Single answer question
                if expr_data['user_type'].type_code == 4:  # Matrix type
                    if expr_data['matrix_norm']:
                        res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        eps=float(expr_data.get('user_eps') or 0),
                                        type_norm=expr_data['matrix_norm']).compare_answer()
                    else:
                        res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        eps=float(expr_data.get('user_eps') or 0)).compare_answer()
                else:
                    res = CheckAnswer(expr_data['user_ans'], user_ans, False,
                                    expression=expr_data['user_expression'],
                                    type_ans=expr_data['user_type'].type_code,
                                    eps=float(expr_data.get('user_eps') or 0)).compare_answer()

            task_results.append(res)
            result_score += res * expr_data['points_for_solve']

        score_in_pr = result_score / all_points * 100 if all_points > 0 else 0

        if score_in_pr >= 80:
            grade = 5
        elif score_in_pr >= 60:
            grade = 4
        elif score_in_pr >= 35:
            grade = 3
        else:
            grade = 2

        # Формируем детальные результаты для отображения
        detailed_results = []
        for i, expr_data in enumerate(expressions_data):
            teacher_answer = teacher_answers[i] if i < len(teacher_answers) else ''
            is_correct = task_results[i] == 1 if i < len(task_results) else None
            if expr_data['exist_select']:
                available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
                correct_answers_flags = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []
                correct_options = [
                    available_options[j]
                    for j, flag in enumerate(correct_answers_flags)
                    if j < len(available_options) and flag == '1'
                ]
                detailed_results.append({
                    'question_number': i + 1,
                    'question': expr_data['user_expression'],
                    'teacher_answer': teacher_answer,
                    'correct_answer': '; '.join(correct_options),
                    'is_multiple_choice': True,
                    'options': available_options,
                    'points': expr_data['points_for_solve'],
                    'is_correct': is_correct,
                })
            else:
                detailed_results.append({
                    'question_number': i + 1,
                    'question': expr_data['user_expression'],
                    'teacher_answer': teacher_answer,
                    'correct_answer': expr_data['user_ans'],
                    'is_multiple_choice': False,
                    'options': [],
                    'points': expr_data['points_for_solve'],
                    'is_correct': is_correct,
                })

        request.session['teacher_test_result'] = {
            'result': result_score,
            'score': grade,
            'test_name': test.name_tests,
            'all_points': all_points,
            'detailed_results': detailed_results,
        }
        request.session.pop(session_key, None)

        return redirect('create_tests:show_result_teacher', slug_name=slug_name)

    # Подготавливаем данные для отображения
    expressions_with_options = []
    for i, expr_data in enumerate(expressions_data):
        options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
        expressions_with_options.append({
            'expression': expr_data,
            'options': options,
            'exist_select': expr_data['exist_select'],
            'display_number': i + 1,
            'original_number': expr_data.get('number', i + 1)
        })

    return render(request, 'create_tests/solve_test_teacher.html', {
        'test': test,
        'expressions_with_options': expressions_with_options,
    })


@login_required
@role_required(['teacher', 'admin'])
def show_result_teacher(request, slug_name):
    """Показ результатов прохождения теста преподавателем"""
    test_result = request.session.get('teacher_test_result')

    if not test_result:
        return redirect('create_tests:test_list')

    test = AboutTest.objects.get(name_slug_tests=slug_name)

    # Подсчитываем общее количество баллов (используем ту же логику что и для студентов)
    task_groups = test.task_groups.all()

    if task_groups.exists():
        # Новая система: используем TaskGroup
        from django.db.models import Sum
        count = task_groups.aggregate(Sum('points_for_solve'))['points_for_solve__sum'] or 0
    else:
        # Старая система: используем AboutExpressions
        from collections import defaultdict

        groups = defaultdict(list)
        for expr in test.expressions.all():
            groups[expr.block_expression_num].append(expr)

        count = 0
        for block_num, expr_list in groups.items():
            if expr_list:
                count += expr_list[0].points_for_solve

    return render(request, 'create_tests/result_teacher.html', {
        'test_name': test_result['test_name'],
        'result': test_result['result'],
        'score': test_result['score'],
        'count': count,
        'slug_name': slug_name,
        'detailed_results': test_result.get('detailed_results', []),
    })


@login_required
@role_required(['teacher', 'admin'])
def test_results_list(request, slug_name):
    """Список студентов, прошедших тест, с их результатами"""
    from solving_tests.models import StudentResult
    from users.models import CustomUser
    import datetime

    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)

    all_results = StudentResult.objects.filter(test=test).select_related(
        'student', 'student__studentdata', 'student__studentdata__group'
    )

    student_ids = all_results.values_list('student', flat=True).distinct()

    students_data = []
    for sid in student_ids:
        s_results = all_results.filter(student_id=sid)
        best = s_results.order_by('-result_points').first()
        last = s_results.order_by('-completed_at', '-started_at').first()

        score_pct = best.result_points / best.max_points * 100 if best.max_points > 0 else 0
        if score_pct >= test.grade_5_threshold:
            grade = 5
        elif score_pct >= test.grade_4_threshold:
            grade = 4
        elif score_pct >= test.grade_3_threshold:
            grade = 3
        else:
            grade = 2

        try:
            sd = best.student.studentdata
            student_name = f"{sd.last_name} {sd.first_name} {sd.middle_name}".strip()
            group = sd.group
        except Exception:
            student_name = best.student.email
            group = None

        last_date = last.completed_at or last.started_at

        students_data.append({
            'student': best.student,
            'student_name': student_name,
            'group': group,
            'best_result': best,
            'last_date': last_date,
            'attempts_count': s_results.count(),
            'grade': grade,
        })

    sort_by = request.GET.get('sort', 'group')
    order = request.GET.get('order', 'asc')
    reverse = (order == 'desc')

    if sort_by == 'group':
        students_data.sort(key=lambda x: x['group'].name if x['group'] else '', reverse=reverse)
    elif sort_by == 'date':
        students_data.sort(
            key=lambda x: x['last_date'] if x['last_date'] else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
            reverse=reverse
        )
    elif sort_by == 'name':
        students_data.sort(key=lambda x: x['student_name'], reverse=reverse)
    elif sort_by == 'score':
        students_data.sort(key=lambda x: x['best_result'].result_points, reverse=reverse)

    return render(request, 'create_tests/test_results_list.html', {
        'test': test,
        'students_data': students_data,
        'sort_by': sort_by,
        'order': order,
    })


@login_required
@role_required(['teacher', 'admin'])
def test_results_detail(request, slug_name, student_id):
    """Детальные ответы конкретного студента на тест"""
    from solving_tests.models import StudentResult
    from solving_tests.views import get_randomized_test_for_student
    from users.models import CustomUser
    import ast

    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = get_object_or_404(CustomUser, id=student_id)

    results = StudentResult.objects.filter(student=student, test=test).order_by('-result_points')
    best_result = results.first()

    if not best_result:
        return redirect('create_tests:test_results_list', slug_name=slug_name)

    expressions_data = get_randomized_test_for_student(test, student.id, best_result.attempt_number)

    try:
        student_answers = json.loads(best_result.res_answer)
    except (json.JSONDecodeError, ValueError):
        try:
            student_answers = ast.literal_eval(best_result.res_answer)
        except (ValueError, SyntaxError):
            student_answers = []

    from logic_of_expression.check_sympy_expr import CheckAnswer as _CheckAnswer

    detailed_results = []
    for i, expr_data in enumerate(expressions_data):
        student_answer = student_answers[i] if i < len(student_answers) else ''
        if expr_data['exist_select']:
            available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
            correct_answers_flags = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []
            correct_options = [
                available_options[j]
                for j, flag in enumerate(correct_answers_flags)
                if j < len(available_options) and flag == '1'
            ]
            if isinstance(student_answer, str):
                selected_options = student_answer.split(';') if student_answer else []
            elif isinstance(student_answer, list):
                selected_options = student_answer
            else:
                selected_options = []
            is_correct = set(selected_options) == set(correct_options)
            detailed_results.append({
                'question_number': i + 1,
                'question': expr_data['user_expression'],
                'student_answer': student_answer,
                'correct_answer': '; '.join(correct_options),
                'is_multiple_choice': True,
                'options': available_options,
                'points': expr_data['points_for_solve'],
                'is_correct': is_correct,
            })
        else:
            from solving_tests.models import FreeAnswerGrade
            is_free_answer = expr_data['user_type'] and expr_data['user_type'].type_code == 5
            if is_free_answer:
                fg = FreeAnswerGrade.objects.filter(student_result=best_result, question_index=i).first()
                is_correct = fg.is_correct if fg else None
            else:
                try:
                    if expr_data['user_type'].type_code == 4 and expr_data.get('matrix_norm'):
                        res = _CheckAnswer(expr_data['user_ans'], student_answer, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        eps=float(expr_data.get('user_eps') or 0),
                                        type_norm=expr_data['matrix_norm']).compare_answer()
                    else:
                        res = _CheckAnswer(expr_data['user_ans'], student_answer, False,
                                        expression=expr_data['user_expression'],
                                        type_ans=expr_data['user_type'].type_code,
                                        eps=float(expr_data.get('user_eps') or 0)).compare_answer()
                    is_correct = res == 1
                except Exception:
                    is_correct = None
            detailed_results.append({
                'question_number': i + 1,
                'question_index': i,
                'question': expr_data['user_expression'],
                'student_answer': student_answer,
                'correct_answer': None if is_free_answer else expr_data['user_ans'],
                'is_multiple_choice': False,
                'is_free_answer': is_free_answer,
                'options': [],
                'points': expr_data['points_for_solve'],
                'is_correct': is_correct,
            })

    try:
        sd = student.studentdata
        student_name = f"{sd.last_name} {sd.first_name} {sd.middle_name}".strip()
        group = sd.group
    except Exception:
        student_name = student.email
        group = None

    # Подсчитываем, сколько свободных ответов ещё не проверено
    free_q_count = sum(1 for q in detailed_results if q.get('is_free_answer'))
    ungraded_count = sum(
        1 for q in detailed_results
        if q.get('is_free_answer') and q.get('is_correct') is None
    )

    return render(request, 'create_tests/test_results_detail.html', {
        'test': test,
        'slug_name': slug_name,
        'student_name': student_name,
        'student_id': student_id,
        'group': group,
        'best_result': best_result,
        'all_results': results,
        'detailed_results': detailed_results,
        'free_q_count': free_q_count,
        'ungraded_count': ungraded_count,
    })


@login_required
@role_required(['teacher', 'admin'])
def grade_free_answer(request, slug_name, student_id):
    """AJAX-эндпоинт: преподаватель ставит оценку на вопрос со свободным ответом"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from solving_tests.models import StudentResult, FreeAnswerGrade
    from solving_tests.views import get_randomized_test_for_student
    from users.models import CustomUser
    from logic_of_expression.check_sympy_expr import CheckAnswer as _CheckAnswer
    import ast

    try:
        data = json.loads(request.body)
        question_index = int(data.get('question_index'))
        is_correct = data.get('is_correct')  # True, False или None
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    test = get_object_or_404(AboutTest, name_slug_tests=slug_name)
    student = get_object_or_404(CustomUser, id=student_id)

    best_result = StudentResult.objects.filter(student=student, test=test).order_by('-result_points').first()
    if not best_result:
        return JsonResponse({'error': 'No result found'}, status=404)

    # Сохраняем оценку
    FreeAnswerGrade.objects.update_or_create(
        student_result=best_result,
        question_index=question_index,
        defaults={'is_correct': is_correct},
    )

    # Пересчитываем баллы студента
    expressions_data = get_randomized_test_for_student(test, student.id, best_result.attempt_number)
    try:
        student_answers = json.loads(best_result.res_answer)
    except (json.JSONDecodeError, ValueError):
        try:
            student_answers = ast.literal_eval(best_result.res_answer)
        except (ValueError, SyntaxError):
            student_answers = []

    result_score = 0.0
    for i, expr_data in enumerate(expressions_data):
        user_ans = student_answers[i] if i < len(student_answers) else ''

        if expr_data['user_type'] and expr_data['user_type'].type_code == 5:
            fg = FreeAnswerGrade.objects.filter(student_result=best_result, question_index=i).first()
            if fg and fg.is_correct:
                result_score += expr_data['points_for_solve']
        elif expr_data['exist_select']:
            available_options = expr_data['user_ans'].split(';') if expr_data['user_ans'] else []
            correct_answers = expr_data['true_ans'].split(';') if expr_data['true_ans'] else []
            if isinstance(user_ans, list):
                selected_set = set(user_ans)
            else:
                selected_set = set(user_ans.split(';') if user_ans else [])
            should_be_selected = {
                available_options[j] for j, flag in enumerate(correct_answers)
                if j < len(available_options) and flag == '1'
            }
            if selected_set == should_be_selected:
                result_score += expr_data['points_for_solve']
        else:
            try:
                if expr_data['user_type'].type_code == 4 and expr_data.get('matrix_norm'):
                    res = _CheckAnswer(expr_data['user_ans'], user_ans, False,
                                       expression=expr_data['user_expression'],
                                       type_ans=expr_data['user_type'].type_code,
                                       eps=float(expr_data.get('user_eps') or 0),
                                       type_norm=expr_data['matrix_norm']).compare_answer()
                else:
                    res = _CheckAnswer(expr_data['user_ans'], user_ans, False,
                                       expression=expr_data['user_expression'],
                                       type_ans=expr_data['user_type'].type_code,
                                       eps=float(expr_data.get('user_eps') or 0)).compare_answer()
                result_score += res * expr_data['points_for_solve']
            except Exception:
                pass

    best_result.result_points = result_score
    best_result.save()

    return JsonResponse({'success': True, 'new_score': result_score, 'max_score': best_result.max_points})