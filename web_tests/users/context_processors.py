def user_role(request):
    if request.user.is_authenticated:
        return {'user_role': request.user.role}
    return {}
