import threading
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Grade submitted and expired attempts in parallel, including with closed browsers.'

    def add_arguments(self, parser):
        parser.add_argument('--watch', action='store_true')
        parser.add_argument('--interval', type=float, default=1)
        parser.add_argument('--workers', type=int, default=getattr(settings, 'ATTEMPT_GRADING_WORKERS', 2))

    def handle(self, *args, **options):
        if not 1 <= options['workers'] <= 8:
            raise CommandError('--workers must be between 1 and 8')
        from solving_tests.expiry_worker import run
        try:
            run(threading.Event(), max(0.2, options['interval']),
                workers=options['workers'], once=not options['watch'])
        except KeyboardInterrupt:
            pass
