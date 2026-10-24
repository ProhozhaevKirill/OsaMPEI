"""Shared loop for the local development server and the production worker."""
import logging

from django.db import close_old_connections


def run(stop, interval=1):
    from .attempts import expire_attempts
    while not stop.is_set():
        try:
            close_old_connections()
            expire_attempts()
        except Exception:
            logging.getLogger(__name__).exception('Ошибка обработки истёкших попыток')
        finally:
            close_old_connections()
        stop.wait(interval)
