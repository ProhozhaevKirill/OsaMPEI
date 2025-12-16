from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth import get_user


class AuthenticationMiddleware:
    """
    Middleware для более элегантной обработки аутентификации и авторизации
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Обрабатываем исключения, связанные с доступом
        """
        if hasattr(exception, 'response') and exception.response.status_code == 403:
            return self.handle_forbidden(request)
        return None

    def handle_forbidden(self, request):
        """
        Возвращает красивую страницу 403 вместо редиректа
        """
        context = {
            'user': request.user,
            'requested_path': request.path,
            'is_authenticated': request.user.is_authenticated,
        }

        return render(request, 'errors/403.html', context, status=403)


class CleanURLMiddleware:
    """
    Middleware для очистки URL от параметров ?next=
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Удаляем параметр next из URL для более чистых ссылок
        if 'next' in request.GET and request.path == '/':
            # Если пользователь на главной странице с параметром next, убираем его
            request.META['QUERY_STRING'] = ''

        response = self.get_response(request)
        return response