import threading
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Finish expired attempts, including when all browser tabs are closed.'

    def add_arguments(self, parser):
        parser.add_argument('--watch', action='store_true')
        parser.add_argument('--interval', type=float, default=1)

    def handle(self, *args, **options):
        if options['watch']:
            from solving_tests.expiry_worker import run
            try:
                run(threading.Event(), max(0.2, options['interval']))
            except KeyboardInterrupt:
                pass
        else:
            from solving_tests.attempts import expire_attempts
            expire_attempts()
