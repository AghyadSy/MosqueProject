from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import User
from ..decorators import login_required,default_par

@login_required(1)
def add_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        per = request.POST['per']
        user = User(username = username, password = password, permission = per)
        user.save()
        messages.info(request, 'تمت اضافة المستخدم بنجاح')
    return redirect('/users/show')

@login_required(1)
def edit_user(request, id):
    edit_user = User.objects.filter(id = id).first()
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        per = request.POST['per']
        edit_user.username = username
        edit_user.password = password
        edit_user.permission = per
        edit_user.save()
        messages.info(request, 'تمت تعديل المستخدم بنجاح')
        return redirect('/users/show')
    return render(request, 'dashboard/users/edit_user.html', {
        'default' : default_par(request),
        'edit_user' : edit_user,
    })

@login_required(1)
def show_users(request):
    users = User.objects.all()
    return render(request, 'dashboard/users/users.html',{
        'default':default_par(request),
        'users' : users
    })

@login_required(0)
def delete_user(request, id):
    edit_user = User.objects.filter(id = id).first()
    edit_user.delete()
    messages.info(request, 'تمت حذف المستخدم بنجاح')
    return redirect('/users/show')