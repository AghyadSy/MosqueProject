from datetime import datetime
from tkinter import PAGES
from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import MemorizedPages, Student, User,StudentAttend
from ..decorators import login_required,default_par

@login_required(2)
def index(request):
    print("index 1")
    students_num = len(Student.objects.all())
    teachers_num = len(User.objects.all())
    print("index 2")
    pages = MemorizedPages.objects.all().order_by('date')
    dates = []
    for p in pages:
        if p.date not in dates:
            dates.append(p.date)
    all_pages_sums = 0
    sums = []
    print("index 3")
    for d in dates:
        s = 0
        for p in pages.filter(date=d).all():
            s += p.page.quant
        sums.append(s)
        all_pages_sums += s
    print("index 4")
    data = StudentAttend.group_by_date()
    print("index 4.5")
    at_sum = 0
    ab_sum = 0
    for date in data:
        for d in date['data']:
            at_sum += len(d['attend'])
            ab_sum += len(d['absent'])
    print("index 5")
    teachers_make_attend = []
    teachers_dosnt_make_attend = []
    for teacher in User.objects.all():
        students = teacher.students()

        if not StudentAttend.objects.filter(student__in=students, date = datetime.now()).all().exists():
            teachers_dosnt_make_attend.append(teacher)
        else:
            teachers_make_attend.append(teacher) 
    print("index 6")
    students_without_teacher = []
    for s in Student.objects.all():
        if s.teacher() == None:
            students_without_teacher.append(s)
    print("index 7")
    return render(request, 'dashboard/index.html',{
        'default':default_par(request),
        'teacher_num':teachers_num,
        'students_num':students_num,
        'dates':dates,
        'sums':sums,
        'at_sum':at_sum,
        'ab_sum':ab_sum,
        'teachers_make_attend':teachers_make_attend,
        'teachers_dosnt_make_attend':teachers_dosnt_make_attend,
        'all_pages_sums':all_pages_sums,
        'students_without_teacher':students_without_teacher,
    })

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(username = username, password = password).first()

        if user is not None:
            user.login(request)
            return redirect('/')
        else:
            messages.info(request, 'المعلومات غير صحيحة')
    return render(request, 'dashboard/login.html', {
        'default':default_par(request),
    })

@login_required(2)
def logout(request):
    user = User.user(request)
    user.logout(request)
    return redirect('/login')
