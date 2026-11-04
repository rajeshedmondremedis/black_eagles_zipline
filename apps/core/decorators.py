from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in, is active,
    and has administrative privileges (staff or superuser).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/admin-panel/login/?next={request.path}")
        if not (request.user.is_active and (request.user.is_staff or request.user.is_superuser)):
            messages.error(request, "Access denied. Administrative privileges are required.")
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

