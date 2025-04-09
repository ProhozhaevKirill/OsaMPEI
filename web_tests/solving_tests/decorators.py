from functools import wraps
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect('/login/')  # или твой путь к логину

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if hasattr(user, 'role') and user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            return redirect('/forbidden/')  # если доступ запрещён
        return _wrapped_view
    return decorator
