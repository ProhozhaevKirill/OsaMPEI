import logging

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

RESOURCES_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
UPLOAD_URL = f'{RESOURCES_URL}/upload'
REQUEST_TIMEOUT = (3.05, 10)


def _ensure_folder(headers, path):
    resp = requests.put(RESOURCES_URL, headers=headers, params={'path': path}, timeout=REQUEST_TIMEOUT)
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
        folder = settings.YANDEX_DISK_FOLDER.rstrip('/')
        _ensure_folder(headers, folder)

        payload = {
            'result_id': student_result.id,
            'student_id': student_result.student_id,
            'student_email': student_result.student.email,
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

        file_name = f'result_{student_result.id}_attempt_{student_result.attempt_number}.json'
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
