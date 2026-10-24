import threading
from django.contrib.staticfiles.management.commands.runserver import Command as StaticCommand


class Command(StaticCommand):
    def inner_run(self, *args, **options):
        # Import numerical libraries on the main thread before URL checks run.
        # Importing NumPy simultaneously in two threads can leave it half initialized.
        from solving_tests import attempts  # noqa: F401
        from solving_tests.expiry_worker import run
        stop = threading.Event()
        worker = threading.Thread(target=run, args=(stop,), daemon=True, name='attempt-expiry')
        worker.start()
        try:
            return super().inner_run(*args, **options)
        finally:
            stop.set()
            worker.join(timeout=5)
