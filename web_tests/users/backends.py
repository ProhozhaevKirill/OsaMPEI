from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class CaseInsensitiveEmailBackend(ModelBackend):
    """
    Кастомный backend для аутентификации, который не учитывает регистр email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            return None

        try:
            # Ищем пользователя по email без учета регистра
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Если пользователь не найден, возвращаем None
            return None
        except User.MultipleObjectsReturned:
            # Если найдено несколько пользователей (что не должно происходить из-за unique=True)
            # берем первого
            user = User.objects.filter(email__iexact=username).first()

        # Проверяем пароль
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None