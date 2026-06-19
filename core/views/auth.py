from datetime import datetime
from tkinter import PAGES
from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import Activity, Lesson, MemorizedPages, Student, StudentAttend, User
from ..decorators import login_required,default_par

@login_required(2)
def index(request):
    students_num = len(Student.objects.all())
    teachers_num = len(User.objects.all())
    pages = MemorizedPages.objects.all().order_by('date')
    dates = []
    for p in pages:
        if p.date not in dates:
            dates.append(p.date)
    all_pages_sums = 0
    sums = []
    for d in dates:
        s = 0
        for p in pages.filter(date=d).all():
            s += p.page.quant
        sums.append(s)
        all_pages_sums += s
    data = StudentAttend.group_by_date()
    at_sum = 0
    ab_sum = 0
    for date in data:
        for d in date['data']:
            at_sum += len(d['attend'])
            ab_sum += len(d['absent'])

    today = datetime.now().date()
    teachers_make_attend = User.objects.filter(groupsession__student__studentattend__date=today).distinct()
    teachers_dosnt_make_attend = User.objects.exclude(groupsession__student__studentattend__date=today).distinct()

    students_without_teacher = Student.objects.filter(groupsession__isnull=True).all()
    latest_activities = Activity.objects.prefetch_related('attended_students').select_related('created_by')[:5]
    latest_lessons = Lesson.objects.prefetch_related('attended_students').select_related('created_by')[:5]

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
        'activities_count': Activity.objects.count(),
        'lessons_count': Lesson.objects.count(),
        'latest_activities': latest_activities,
        'latest_lessons': latest_lessons,
    })

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = User.authenticate(username=username, raw_password=password)

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
    if user is not None:
        user.logout(request)
    return redirect('/login')
