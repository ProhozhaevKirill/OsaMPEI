"""Exercise fresh interpreters: an in-process NumPy import hides startup races."""
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test import TransactionTestCase


class RunserverStartupTests(TransactionTestCase):
    def test_fresh_autoreloader_starts_and_reloads_without_partial_numpy_import(self):
        database = connection.settings_dict['NAME']
        self.assertTrue(database.startswith('test_'), 'Only the disposable test database may be used')
        # Repeat with clean interpreters so the test suite's already loaded
        # NumPy cannot mask the race between the URL loader and inner_run.
        for cycle in range(2):
            with self.subTest(cycle=cycle), tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                config = directory / 'startup_probe_settings.py'
                config.write_text("from web_tests.test_settings import *\nprint('STARTUP_VERSION_1', flush=True)\n")
                with socket.socket() as sock:
                    sock.bind(('127.0.0.1', 0))
                    port = sock.getsockname()[1]
                env = os.environ.copy()
                env.update(DB_NAME=database, PYTHONUNBUFFERED='1')
                env['PYTHONPATH'] = str(directory) + os.pathsep + str(settings.BASE_DIR) + os.pathsep + env.get('PYTHONPATH', '')
                env.pop('RUN_MAIN', None)
                env.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
                log_path = directory / 'runserver.log'
                with log_path.open('wb') as log:
                    kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
                    process = subprocess.Popen([sys.executable, 'manage.py', 'runserver',
                        f'127.0.0.1:{port}', '--settings=startup_probe_settings'],
                        cwd=settings.BASE_DIR, env=env, stdout=log, stderr=log, **kwargs)
                    try:
                        self.wait_for_server(process, port, log_path, 'STARTUP_VERSION_1')
                        # Let StatReloader record the original file timestamp.
                        time.sleep(1.2)
                        config.write_text("from web_tests.test_settings import *\nprint('STARTUP_VERSION_2', flush=True)\n")
                        self.wait_for_server(process, port, log_path, 'STARTUP_VERSION_2')
                    finally:
                        if os.name == 'nt':
                            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            os.killpg(process.pid, signal.SIGTERM)
                        process.wait(timeout=10)
                output = log_path.read_text(encoding='utf-8', errors='replace')
                self.assertIn('Watching for file changes', output)
                self.assertNotIn('ImportError', output)
                self.assertNotIn('partially initialized', output)

    def wait_for_server(self, process, port, log_path, marker):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and process.poll() is None:
            output = log_path.read_text(encoding='utf-8', errors='replace')
            self.assertNotIn('Traceback (most recent call last)', output, output)
            if marker in output:
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=0.5) as response:
                        if response.status == 200:
                            return
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    pass
            time.sleep(0.2)
        self.fail('runserver did not become ready:\n' + log_path.read_text(encoding='utf-8', errors='replace'))
