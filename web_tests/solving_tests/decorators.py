from functools import wraps
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def role_required(allowed_roles):
    """
    Декоратор для проверки ролей пользователей.
    Возвращает 403 вместо редиректов для лучшего UX.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required  # Используем стандартный декоратор Django для аутентификации
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # Суперпользователь имеет доступ ко всему
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Проверяем роль пользователя
            if hasattr(user, 'role') and user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # Возвращаем красивую страницу 403 вместо редиректа
            context = {
                'user': user,
                'required_roles': allowed_roles,
                'user_role': getattr(user, 'role', 'Неопределена'),
                'requested_path': request.path,
            }

            return render(request, 'errors/403.html', context, status=403)
        return _wrapped_view
    return decorator
