import functools
from django.shortcuts import redirect
from django.contrib import messages
from .models import User

def default_par(request):
    return {
        'user': User.user(request),
    }

# def login_required(view_func):
#     @functools.wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         user = User.user(request)
#         if  user == None:
#             messages.info(request, "يجب عليك تسجيل الدخول")
#             return redirect('/login')
#         if user.permission > 2:
#             messages.info(request, "غير مسموح لك بهذه العملية")
#             return redirect('/login')
#         return view_func(request, *args, **kwargs)
#     return wrapper

def login_required(permision):
    def w(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = User.user(request)
            if  user == None:
                messages.info(request, "يجب عليك تسجيل الدخول")
                return redirect('/login')
            if user.permission > permision:
                messages.info(request, "غير مسموح لك بهذه العملية")
                return redirect('/')
            return view_func(request, *args, **kwargs)
        return wrapper
    return w