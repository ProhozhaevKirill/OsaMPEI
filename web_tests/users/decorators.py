# from django.http import HttpResponseForbidden
#
# def role_required(role):
#     def decorator(view_func):
#         def wrapper(request, *args, **kwargs):
#             if request.user.role == role:
#                 return view_func(request, *args, **kwargs)
#             return HttpResponseForbidden("У вас нет доступа к этой странице.")
#         return wrapper
#     return decorator
