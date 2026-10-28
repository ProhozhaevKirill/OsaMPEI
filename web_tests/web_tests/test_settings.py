"""Regression tests use a separate MySQL test database created by Django."""
from .settings import *  # noqa: F403

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
YANDEX_DISK_TOKEN = ''
