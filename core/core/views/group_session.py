from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import GroupSession, Student, User
from ..decorators import login_required,default_par

@login_required(1)
def add(request, id):
    if request.method == "POST":
        student_id = request.POST['student']
        student = Student.objects.filter(id=student_id).first()
        teacher = User.objects.filter(id=id).first()
        g = GroupSession(teacher=teacher, student=student)
        g.save()
        
        messages.info(request, 'تمت اضافة الطالب بنجاح')
    return redirect(f'/groupsession/{teacher.id}/edit')

@login_required(2)
def edit(request, id):
    teacher = User.objects.filter(id = id).first()
    group_session = list(GroupSession.objects.filter(teacher = teacher).all())

    student_with_group = GroupSession.objects.all()
    student_ids = []
    for s in student_with_group:
        student_ids.append(s.student.id)
    students_without_group = Student.objects.exclude(id__in=student_ids)
    for s in students_without_group:
        print(s)
    return render(request, 'dashboard/group_session/edit.html', {
        'default' : default_par(request),
        'teacher': teacher,
        'group_session' : group_session,
        'students_without_group':students_without_group,
        'teachers':User.objects.all(),
    })

@login_required(2)
def show(request):
    user = User.user(request)
    if user.permission == 2 :
        teachers = [user]
    else:    
        teachers = User.objects.all()
    
    return render(request, 'dashboard/group_session/show.html',{
        'default':default_par(request),
        'teachers':teachers,
    })

@login_required(0)
def delete(request, id):
    if request.method != "POST":
        return redirect('/groupsession/show')
    g = GroupSession.objects.filter(id=id).first()
    if g is None:
        messages.info(request, 'السجل غير موجود')
        return redirect('/groupsession/show')
    teacher_id = g.teacher.id
    g.delete()
    messages.info(request, 'تمت حذف الطالب بنجاح')
    return redirect(f'/groupsession/{teacher_id}/edit')

@login_required(1)
def change_teacher(request, old_teacher_id):
    if request.method == "POST":
        teacher_id = request.POST['teacher_id']
        old_teacher = User.objects.filter(id=old_teacher_id).first()
        new_teacher = User.objects.filter(id=teacher_id).first()
        g = GroupSession.objects.filter(teacher=old_teacher).all()
        for i in g:
            i.teacher = new_teacher
            i.save()
        messages.info(request, 'تمت تعديل المشرف بنجاح')
        return redirect(f'/groupsession/{new_teacher.id}/edit')
