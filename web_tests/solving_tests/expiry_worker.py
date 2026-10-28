"""Parallel CPU grading; only the parent process reads and writes attempts."""
import logging
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

from django.db import close_old_connections
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def initialize_grader():
    # Limit numerical-library threads inside each independent interpreter.
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[name] = '1'
    import django
    django.setup()


def grade_snapshot(questions, answers):
    # Subprocesses only compute; database writes stay in the parent.
    from .attempts import evaluate
    return evaluate(questions, answers)


def create_pool(workers):
    return ProcessPoolExecutor(max_workers=workers,
        mp_context=multiprocessing.get_context('spawn'), initializer=initialize_grader)


def run(stop, interval=1, workers=2, *, once=False):
    from .attempts import finish_attempt, submit_attempt
    from .models import TestAttempt

    if workers < 1:
        raise ValueError('workers must be positive')
    pending = {}
    retry_after = {}
    failed_once = set()
    pool = create_pool(workers)
    try:
        while not stop.is_set():
            try:
                close_old_connections()
                for attempt_id, (future, revision) in list(pending.items()):
                    if not future.done():
                        continue
                    del pending[attempt_id]
                    try:
                        finish_attempt(attempt_id, evaluation=future.result(), expected_revision=revision)
                    except BrokenProcessPool:
                        raise
                    except Exception:
                        logger.exception('Could not grade attempt %s; will retry', attempt_id)
                        retry_after[attempt_id] = time.monotonic() + 30
                        if once:
                            failed_once.add(attempt_id)

                now = time.monotonic()
                retry_after = {pk: deadline for pk, deadline in retry_after.items() if deadline > now}
                excluded = set(pending) | set(retry_after) | (failed_once if once else set())
                capacity = workers - len(pending)
                ids = list(TestAttempt.objects.filter(
                    Q(submitted_at__isnull=False) | Q(deadline__lte=timezone.now()),
                    result__isnull=True,
                ).exclude(pk__in=excluded).order_by('pk').values_list('pk', flat=True)[:capacity]) if capacity else []
                for attempt_id in ids:
                    # Freeze expired attempts before taking an immutable snapshot.
                    attempt = submit_attempt(attempt_id)
                    if not attempt.result_id:
                        future = pool.submit(grade_snapshot, attempt.questions, attempt.answers)
                        pending[attempt_id] = (future, attempt.revision)
                if once and not pending and not ids:
                    break
            except BrokenProcessPool:
                logger.exception('Grading subprocess exited; restarting process pool')
                if once:
                    raise
                pool.shutdown(wait=True, cancel_futures=True)
                pending.clear()
                pool = create_pool(workers)
            except Exception:
                logger.exception('Attempt grading worker failed')
                if once:
                    raise
            finally:
                close_old_connections()
            stop.wait(interval)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    # Interrupted work stays submitted in the DB for the next worker run.
    if once and failed_once:
        raise RuntimeError('Failed to grade attempts: ' + ', '.join(map(str, sorted(failed_once))))
