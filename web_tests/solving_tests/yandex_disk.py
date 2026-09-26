import logging
import re
import unicodedata

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

RESOURCES_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
UPLOAD_URL = f'{RESOURCES_URL}/upload'
REQUEST_TIMEOUT = (3.05, 10)


def _safe_path_part(value, fallback):
    """Готовит читаемую часть пути без разделителей и служебных символов."""
    value = unicodedata.normalize('NFKC', str(value or '')).strip()
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', '_', value)
    value = re.sub(r'\s+', '_', value).strip('._')
    return (value or fallback)[:100]


def _ensure_folder_tree(headers, path):
    """Создаёт все недостающие папки внутри app:/ по очереди."""
    if not path.startswith('app:/'):
        raise ValueError('YANDEX_DISK_FOLDER must start with app:/')

    current = 'app:'
    for part in path.removeprefix('app:/').split('/'):
        if not part:
            continue
        current = f'{current}/{part}'
        resp = requests.put(
            RESOURCES_URL,
            headers=headers,
            params={'path': current},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code not in (201, 409):
            resp.raise_for_status()


def upload_test_attempt_log(student_result, detailed_results):
    """Выгружает подробности одной попытки прохождения теста на Яндекс.Диск.

    Не должна мешать сдаче теста при недоступности Диска, поэтому все ошибки
    гасятся здесь и только пишутся в лог.
    """
    token = settings.YANDEX_DISK_TOKEN
    if not token:
        return

    try:
        headers = {'Authorization': f'OAuth {token}'}
        root_folder = settings.YANDEX_DISK_FOLDER.rstrip('/')

        student = student_result.student
        student_data = getattr(student, 'studentdata', None)
        group = student_data.group if student_data else None
        group_name = group.name if group else 'Без группы'
        group_id = group.id if group else 'unknown'
        student_name = student.get_full_name()

        group_folder = (
            f'group_{group_id}__'
            f'{_safe_path_part(group_name, "Без_группы")}'
        )
        test_folder = (
            f'test_{student_result.test_id}__'
            f'{_safe_path_part(student_result.test.name_tests, "Без_названия")}'
        )
        folder = f'{root_folder}/{group_folder}/{test_folder}'
        _ensure_folder_tree(headers, folder)

        payload = {
            'result_id': student_result.id,
            'student_id': student_result.student_id,
            'student_name': student_name,
            'student_email': student.email,
            'group_id': group_id,
            'group_name': group_name,
            'test_id': student_result.test_id,
            'test_name': student_result.test.name_tests,
            'attempt_number': student_result.attempt_number,
            'result_points': student_result.result_points,
            'max_points': student_result.max_points,
            'percentage_score': student_result.percentage_score,
            'started_at': student_result.started_at.isoformat(),
            'completed_at': (
                student_result.completed_at.isoformat()
                if student_result.completed_at else None
            ),
            'questions': detailed_results,
        }

        student_file_name = _safe_path_part(student_name, f'student_{student_result.student_id}')
        file_name = (
            f'{student_file_name}__student_{student_result.student_id}'
            f'__attempt_{student_result.attempt_number}'
            f'__result_{student_result.id}.json'
        )
        remote_path = f"{folder}/{file_name}"

        resp = requests.get(
            UPLOAD_URL, headers=headers,
            params={'path': remote_path, 'overwrite': 'true'},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        upload_href = resp.json()['href']

        put_resp = requests.put(
            upload_href,
            data=DjangoJSONEncoder(ensure_ascii=False, indent=2).encode(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=REQUEST_TIMEOUT,
        )
        put_resp.raise_for_status()
    except Exception:
        logger.exception("Не удалось выгрузить лог попытки теста на Яндекс.Диск")
