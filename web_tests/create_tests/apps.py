from django.apps import AppConfig


class CreateTestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'create_tests'

    def ready(self):
        import create_tests.signals  # noqa
