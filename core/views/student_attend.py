from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import GroupSession, User, StudentAttend
from ..decorators import login_required,default_par

@login_required(2)
def add(request, id):
    teacher = User.objects.filter(id=id).first()
    students = GroupSession.objects.filter(teacher=teacher).all()
    if request.method == "POST":
        date = request.POST['date']

        for student in students:
            if StudentAttend.objects.filter(date=date, student__id=student.student.id).first() == None:
                a = request.POST.get(str(student.student.id))
                st = StudentAttend(student=student.student, date=date, is_attend=a)
                st.save()

        messages.info(request, 'تم تسجيل الحضور بنجاح')
        return redirect('/groupsession/show')
    return render(request, 'dashboard/students_attend/add.html', {
        'default' : default_par(request),
        'students':students,
    })

@login_required(1)
def edit(request, date, teacher_id):
    s = StudentAttend.students_of_teacher(User.objects.filter(id=teacher_id).first())
    students = StudentAttend.objects.filter(date=date, id__in=s).all()

    if not students.exists():
        messages.info(request, 'قم بتسجيل الحضور اولا قبل التعديل')
        return redirect('/attend/show')
    if request.method == "POST":
        for student in students:
            a = request.POST.get(str(student.student.id))
            s = StudentAttend.objects.filter(id=student.id).first()
            s.is_attend = a
            s.save()
        
        messages.info(request, 'تمت تعديل المستخدم بنجاح')
        return redirect('/attend/show')
    return render(request, 'dashboard/students_attend/edit.html', {
        'default' : default_par(request),
        'students' : students,
    })

@login_required(2)
def show(request):
    teachers = User.objects.all()
    data = StudentAttend.group_by_date()
    char_data = {
        'dates':[],
        'data':[]
    }
    for date in data:
        sum = 0
        for d in date['data']:
            sum += len(d['attend'])
        char_data['dates'].append(str(date['date'].strftime("%Y/%m/%d")))
        char_data['data'].append(sum)

    print(char_data)
    return render(request, 'dashboard/students_attend/show.html',{
        'default':default_par(request),
        'users' : teachers,
        'data':data,
        'char_data':char_data,
    })

@login_required(1)
def delete(request, date, teacher_id):
    s = StudentAttend.students_of_teacher(User.objects.filter(id=teacher_id).first())
    students = StudentAttend.objects.filter(date=date, id__in=s)
    for s in students:
        s.delete()
    messages.info(request, 'تمت حذف الحضور بنجاح')
    return redirect('/attend/show')