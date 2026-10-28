"""Server-owned attempt deadlines, immutable questions and versioned drafts."""
import json
import logging
from types import SimpleNamespace

from django.db import transaction
from django.db.models import Max, Q
from django.urls import reverse
from django.utils import timezone

from create_tests.answer_storage import split_answers, display_answer
from create_tests.models import PublishedGroup
from logic_of_expression.check_sympy_expr import CheckAnswer
from users.models import CustomUser, StudentData
from .models import TestAttempt, StudentResult, FreeAnswerGrade

logger = logging.getLogger(__name__)


class RevisionConflict(Exception):
    pass


def freeze_questions(expressions):
    result = []
    for expression in expressions:
        item = {key: value for key, value in expression.items() if key not in ('user_type', 'matrix_norm')}
        kind, norm = expression.get('user_type'), expression.get('matrix_norm')
        item.update(type_code=kind.type_code if kind else 1, type_name=kind.name if kind else '',
                    norm_code=norm.type_code if norm else None, norm_name=norm.name if norm else '')
        result.append(item)
    return result


def thaw_questions(questions):
    return [dict(item, user_type=SimpleNamespace(type_code=item['type_code'], name=item['type_name']),
                 matrix_norm=SimpleNamespace(type_code=item['norm_code'], name=item['norm_name'])
                 if item['norm_code'] else None) for item in questions]


def may_start(student, test):
    group_id = StudentData.objects.filter(data_map=student).values_list('group_id', flat=True).first()
    return test.is_available_now() and PublishedGroup.objects.filter(test_name=test, group_name_id=group_id).exists()


@transaction.atomic
def start_attempt(student, test, *, new=False):
    # Serialize starts for one student, including when there is no attempt row yet.
    CustomUser.objects.select_for_update().get(pk=student.pk)
    latest = TestAttempt.objects.filter(student=student, test=test).order_by('-attempt_number').first()
    if latest and latest.result_id is None:
        if latest.deadline <= timezone.now() and not latest.submitted_at:
            submit_attempt(latest.pk)
            latest.refresh_from_db()
        return latest
    if latest and not new:
        return latest
    if not may_start(student, test):
        raise PermissionError('Тест сейчас недоступен.')
    previous = StudentResult.objects.filter(student=student, test=test)
    number = max(previous.aggregate(n=Max('attempt_number'))['n'] or 0,
                 latest.attempt_number if latest else 0) + 1
    if test.num_of_attempts > 0 and number > test.num_of_attempts:
        raise PermissionError('Доступные попытки закончились.')
    from .views import get_randomized_test_for_student
    questions = freeze_questions(get_randomized_test_for_student(test, student.pk, number))
    now = timezone.now()
    return TestAttempt.objects.create(student=student, test=test, attempt_number=number,
        started_at=now, deadline=now + test.time_to_solution, questions=questions,
        answers=[''] * len(questions))


def evaluate(questions, answers, free_grades=None):
    points, details = 0, []
    free_grades = free_grades or {}
    for index, expression in enumerate(thaw_questions(questions)):
        answer = answers[index] if index < len(answers) else ''
        options = split_answers(expression['user_ans']) if expression['exist_select'] else []
        correct = [option for option, flag in zip(options, expression['true_ans'].split(';')) if flag == '1']
        free = not expression['exist_select'] and expression['type_code'] == 5
        if free:
            is_correct = free_grades.get(index)
        elif expression['exist_select']:
            is_correct = set(split_answers(answer) if answer else []) == set(correct)
        else:
            from .views import _safe_epsilon
            is_correct = bool(CheckAnswer(expression['user_ans'], answer, False,
                expression=expression['user_expression'], type_ans=expression['type_code'],
                eps=_safe_epsilon(expression.get('user_eps')), type_norm=expression['matrix_norm']).compare_answer())
        points += expression['points_for_solve'] if is_correct else 0
        details.append({'question_number': index + 1, 'question': expression['user_expression'],
            'student_answer': display_answer(answer, expression['exist_select']),
            'images': expression.get('images', []),
            'correct_answer': None if free else ('; '.join(correct) if options else expression['user_ans']),
            'is_multiple_choice': expression['exist_select'], 'is_free_answer': free,
            'options': options, 'points': expression['points_for_solve'], 'is_correct': is_correct})
    return points, details


def _finish_locked(attempt, now, evaluation=None):
    if attempt.result_id:
        return
    points, details = evaluation if evaluation is not None else evaluate(attempt.questions, attempt.answers)
    completed = min(attempt.submitted_at or now, attempt.deadline)
    result = StudentResult.objects.create(student=attempt.student, test=attempt.test,
        attempt_number=attempt.attempt_number, result_points=points,
        max_points=sum(q['points_for_solve'] for q in attempt.questions),
        res_answer=json.dumps(attempt.answers, ensure_ascii=False), started_at=attempt.started_at,
        completed_at=completed, time_spent=completed - attempt.started_at, is_completed=True)
    FreeAnswerGrade.objects.bulk_create([FreeAnswerGrade(student_result=result, question_index=index)
        for index, detail in enumerate(details) if detail['is_free_answer']])
    attempt.result = result
    attempt.grading_details = details
    attempt.save(update_fields=['result', 'grading_details'])
    from .yandex_disk import upload_test_attempt_log
    transaction.on_commit(lambda: upload_test_attempt_log(result, details))


@transaction.atomic
def finish_attempt(attempt_id, *, evaluation=None, expected_revision=None):
    attempt = TestAttempt.objects.select_for_update().select_related('student', 'test').get(pk=attempt_id)
    if evaluation is not None and (not attempt.submitted_at or attempt.revision != expected_revision):
        raise RevisionConflict('Attempt changed while grading.')
    _finish_locked(attempt, timezone.now(), evaluation)
    return attempt


def _submit_locked(attempt, now):
    if not attempt.result_id and not attempt.submitted_at:
        attempt.submitted_at = min(now, attempt.deadline)
        attempt.save(update_fields=['submitted_at'])


@transaction.atomic
def submit_attempt(attempt_id):
    attempt = TestAttempt.objects.select_for_update().select_related('test').get(pk=attempt_id)
    _submit_locked(attempt, timezone.now())
    return attempt


def validate_changes(changes, length):
    if not isinstance(changes, dict) or len(changes) > length:
        raise ValueError('Некорректные ответы.')
    for key, value in changes.items():
        if not isinstance(key, str) or not key.isdecimal() or not 0 <= int(key) < length:
            raise ValueError('Некорректный номер задания.')
        if not isinstance(value, str) or len(value) > 100000:
            raise ValueError('Ответ слишком длинный или имеет неверный формат.')
        # Validate packed checkbox answers now, before they can reach grading.
        if value.startswith('@answers:'):
            split_answers(value)


@transaction.atomic
def update_attempt(attempt_id, revision, changes, *, finish=False):
    attempt = TestAttempt.objects.select_for_update().select_related('student', 'test').get(pk=attempt_id)
    now = timezone.now()
    if attempt.result_id or attempt.submitted_at:
        return attempt
    if now >= attempt.deadline:
        _submit_locked(attempt, now)
        return attempt
    if type(revision) is not int or revision != attempt.revision:
        raise RevisionConflict
    validate_changes(changes, len(attempt.questions))
    for key, value in changes.items():
        attempt.answers[int(key)] = value
    if changes:
        attempt.revision += 1
        attempt.save(update_fields=['answers', 'revision'])
    if finish:
        _submit_locked(attempt, now)
    return attempt


def attempt_state(attempt):
    return {'attempt_id': attempt.pk, 'answers': attempt.answers, 'revision': attempt.revision,
        'server_now': timezone.now().timestamp() * 1000, 'deadline': attempt.deadline.timestamp() * 1000,
        'submitted': bool(attempt.submitted_at or attempt.result_id), 'completed': bool(attempt.result_id), 'result_url': reverse('solving_tests:attempt_result',
            args=[attempt.test.name_slug_tests, attempt.pk])}


def expire_attempts():
    ids = TestAttempt.objects.filter(Q(submitted_at__isnull=False) | Q(deadline__lte=timezone.now()), result__isnull=True).values_list('pk', flat=True)
    for attempt_id in list(ids):
        try:
            finish_attempt(attempt_id)
        except Exception:
            logger.exception('Не удалось завершить попытку %s', attempt_id)
