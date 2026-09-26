from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from solving_tests.yandex_disk import upload_test_attempt_log


class YandexDiskLogPathTests(SimpleTestCase):
    @override_settings(
        YANDEX_DISK_TOKEN='test-token',
        YANDEX_DISK_FOLDER='app:/test_logs',
    )
    @patch('solving_tests.yandex_disk.requests.get')
    @patch('solving_tests.yandex_disk.requests.put')
    def test_attempt_is_stored_under_group_and_test_folders(self, put, get):
        folder_response = Mock(status_code=201)
        upload_response = Mock(status_code=201)
        put.side_effect = [folder_response, folder_response, folder_response, upload_response]

        link_response = Mock()
        link_response.json.return_value = {'href': 'https://upload.example.test'}
        get.return_value = link_response

        group = SimpleNamespace(id=9, name='А-01/24')
        student = SimpleNamespace(
            email='student@example.com',
            studentdata=SimpleNamespace(group=group),
            get_full_name=lambda: 'Иванов Иван',
        )
        test = SimpleNamespace(name_tests='Контрольная № 1')
        result = SimpleNamespace(
            id=74,
            student_id=12,
            student=student,
            test_id=5,
            test=test,
            attempt_number=4,
            result_points=8.0,
            max_points=10.0,
            percentage_score=80.0,
            started_at=SimpleNamespace(isoformat=lambda: '2026-09-26T10:00:00+00:00'),
            completed_at=None,
        )

        upload_test_attempt_log(result, [])

        requested_path = get.call_args.kwargs['params']['path']
        self.assertEqual(
            requested_path,
            'app:/test_logs/group_9__А-01_24/'
            'test_5__Контрольная_No_1/'
            'Иванов_Иван__student_12__attempt_4__result_74.json',
        )
        created_folders = [call.kwargs['params']['path'] for call in put.call_args_list[:3]]
        self.assertEqual(
            created_folders,
            [
                'app:/test_logs',
                'app:/test_logs/group_9__А-01_24',
                'app:/test_logs/group_9__А-01_24/test_5__Контрольная_No_1',
            ],
        )
