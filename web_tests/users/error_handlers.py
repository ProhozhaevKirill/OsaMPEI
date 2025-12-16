from django.shortcuts import render


def handler403(request, exception):
    """
    Обработчик ошибки 403 (Доступ запрещен)
    """
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
        'requested_path': request.path,
    }

    return render(request, 'errors/403.html', context, status=403)


def handler404(request, exception):
    """
    Обработчик ошибки 404 (Страница не найдена)
    """
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
        'requested_path': request.path,
    }

    return render(request, 'errors/404.html', context, status=404)


def handler500(request):
    """
    Обработчик ошибки 500 (Внутренняя ошибка сервера)
    """
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
    }

    return render(request, 'errors/500.html', context, status=500)