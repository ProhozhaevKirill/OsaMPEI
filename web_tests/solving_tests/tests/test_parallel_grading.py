import os
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TransactionTestCase

from solving_tests.attempts import RevisionConflict, finish_attempt, start_attempt, update_attempt
from solving_tests.expiry_worker import create_pool, grade_snapshot, run
from solving_tests.models import StudentResult, TestAttempt
from users.models import CustomUser
from django.utils import timezone
from .test_attempts import AttemptTests


def grade_together(questions, answers, directory):
    """Both real child processes must arrive before either may evaluate."""
    Path(directory, str(os.getpid())).touch()
    deadline = time.monotonic() + 20
    while len(list(Path(directory).iterdir())) < 2:
        if time.monotonic() > deadline:
            raise TimeoutError('Two grading processes did not run concurrently')
        time.sleep(0.02)
    return grade_snapshot(questions, answers)


class ParallelGradingTests(TransactionTestCase):
    setUp = AttemptTests.setUp

    def test_real_processes_grade_concurrently_with_same_results(self):
        attempt = start_attempt(self.student, self.test)
        with tempfile.TemporaryDirectory() as directory, create_pool(2) as pool:
            correct = pool.submit(grade_together, attempt.questions, ['4'], directory)
            incorrect = pool.submit(grade_together, attempt.questions, ['999'], directory)
            self.assertEqual(correct.result(timeout=45)[0], 2)
            self.assertEqual(incorrect.result(timeout=45)[0], 0)
            self.assertEqual(len(list(Path(directory).iterdir())), 2)

    def test_worker_drains_queue_and_repeated_run_does_not_duplicate_results(self):
        attempt = start_attempt(self.student, self.test)
        update_attempt(attempt.pk, 0, {'0': '4'}, finish=True)
        other = CustomUser.objects.create_user('parallel@example.com', 'pass', role='student')
        deadline = timezone.now() - timedelta(seconds=1)
        expired = TestAttempt.objects.create(student=other, test=self.test, attempt_number=1,
            started_at=deadline - timedelta(minutes=10), deadline=deadline,
            questions=attempt.questions, answers=['999'])
        with patch('solving_tests.yandex_disk.upload_test_attempt_log') as upload:
            run(threading.Event(), interval=0.02, workers=2, once=True)
            run(threading.Event(), interval=0.02, workers=2, once=True)
            self.assertEqual(upload.call_count, 2)
        attempt.refresh_from_db()
        self.assertEqual(attempt.result.result_points, 2)
        self.assertTrue(attempt.grading_details[0]['is_correct'])
        expired.refresh_from_db()
        self.assertEqual(expired.result.result_points, 0)
        self.assertEqual(expired.result.completed_at, deadline)
        self.assertEqual(StudentResult.objects.count(), 2)

    def test_outdated_evaluation_cannot_be_persisted(self):
        attempt = start_attempt(self.student, self.test)
        submitted = update_attempt(attempt.pk, 0, {'0': '4'}, finish=True)
        with self.assertRaises(RevisionConflict):
            finish_attempt(attempt.pk, evaluation=(0, []), expected_revision=submitted.revision - 1)
        self.assertFalse(StudentResult.objects.exists())


class WorkerArgumentsTests(SimpleTestCase):
    def test_rejects_invalid_worker_counts(self):
        for workers in (0, -1, 9):
            with self.assertRaises(CommandError):
                call_command('finish_expired_attempts', workers=workers)
