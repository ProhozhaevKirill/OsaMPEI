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


def anonymous_required(view_func):
    """
    Декоратор для страниц, доступных только анонимным пользователям
    (например, страницы логина/регистрации)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        print(f"DEBUG anonymous_required: path={request.path}, authenticated={request.user.is_authenticated}, user={request.user}")
        if request.user.is_authenticated:
            # Если пользователь уже авторизован, перенаправляем на главную
            from django.shortcuts import redirect
            if hasattr(request.user, 'role') and request.user.role:
                role = getattr(request.user, 'role', 'no_role')
                print(f"DEBUG anonymous_required: user has role={role}")
                if request.user.role == 'student':
                    print("DEBUG anonymous_required: redirecting to /Home/")
                    return redirect('/Home/')
                elif request.user.role == 'teacher':
                    print("DEBUG anonymous_required: redirecting to /TestsCreate/listTests/")
                    return redirect('/TestsCreate/listTests/')
            print("DEBUG anonymous_required: user has no role, allowing access to complete registration")
            # Если у пользователя нет роли, разрешаем доступ к странице для завершения регистрации
            return view_func(request, *args, **kwargs)
        print("DEBUG anonymous_required: allowing anonymous access")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
