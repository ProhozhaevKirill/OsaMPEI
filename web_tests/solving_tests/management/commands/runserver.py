import threading
from django.conf import settings
from django.core.management.base import CommandError
from django.contrib.staticfiles.management.commands.runserver import Command as StaticCommand


class Command(StaticCommand):
    def run(self, **options):
        # Django's autoreloader imports URL modules on its main thread while
        # inner_run executes on django-main-thread. Initialize numerical
        # libraries before either thread starts importing the grading code.
        from solving_tests import attempts  # noqa: F401
        return super().run(**options)

    def inner_run(self, *args, **options):
        from solving_tests.expiry_worker import run
        workers = getattr(settings, 'ATTEMPT_GRADING_WORKERS', 2)
        if not 1 <= workers <= 8:
            raise CommandError('ATTEMPT_GRADING_WORKERS must be between 1 and 8')
        stop = threading.Event()
        worker = threading.Thread(target=run, args=(stop,), kwargs={'workers': workers},
                                  daemon=True, name='attempt-grading')
        worker.start()
        try:
            return super().inner_run(*args, **options)
        finally:
            stop.set()
            worker.join(timeout=5)
