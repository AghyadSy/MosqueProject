from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import GroupSession, MemorizedPages, StudentAttend, User, Student, Page
from ..decorators import login_required,default_par

@login_required(2)
def add(request):
    if request.method == "POST":
        name = request.POST['name']
        father_name = request.POST['father_name']
        address = request.POST['address']
        school_name = request.POST['school_name']
        birth_date = request.POST['birth_date']
        phone_number = request.POST['phone_number']
        student = Student(name = name, father_name = father_name, address = address, school_name = school_name, birth_date = birth_date, phone_number = phone_number)
        student.save()
        teacher_id = request.POST['teacher_id']
        if teacher_id != "later":
            g = GroupSession(teacher = User.objects.filter(id=teacher_id).first(), student=student)
            g.save()
        messages.info(request, 'تمت اضافة الطالب بنجاح')
    return redirect('/students/show')

@login_required(2)
def add_memorize(request, student_id):
    student = Student.objects.filter(id=student_id).first()
    if request.method == "POST":
        page = Page.objects.filter(id=request.POST['page_id']).first()
        date = request.POST['date']
        if MemorizedPages.objects.filter(student=student, page=page).first() != None:
            messages.info(request, 'الصفحة مسجلة من قبل')
        else:
            m = MemorizedPages(student=student, page=page, date=date)
            m.save()
            messages.info(request, 'تم تسجيل الحفظ')
    return render(request, 'dashboard/students/add_memorize.html',{
        'default':default_par(request),
        'student' : student,
    })

@login_required(2)
def get_pages(request, section):
    pages = Page.objects.filter(section=section).all()
    data = {
        'pages': []
    }
    for p in pages:
        data['pages'].append({
            'page_id':p.id,
            'page_name':p.name
        })
    return JsonResponse(data)

@login_required(2)
def edit(request, id):
    student = Student.objects.filter(id = id).first()
    if request.method == "POST":
        student.name = request.POST['name']
        student.father_name = request.POST['father_name']
        student.address = request.POST['address']
        student.school_name = request.POST['school_name']
        student.phone_number = request.POST['phone_number']
        student.birth_date = request.POST['birth_date']
        student.save()
        messages.info(request, 'تمت تعديل الطالب بنجاح')
        return redirect('/students/show')

    return render(request, 'dashboard/students/edit.html', {
        'default' : default_par(request),
        'student' : student,
    })

@login_required(2)
def show(request):
    user = User.user(request)
    if user.permission == 2 :
        students = user.students()
    else:    
        students = Student.objects.all()

    return render(request, 'dashboard/students/show.html',{
        'default':default_par(request),
        'students' : students,
        'teachers':User.objects.all()
    })

@login_required(2)
def details(request, id):
    student = Student.objects.filter(id=id).first()
    pages = MemorizedPages.objects.filter(student=student).all()
    attends = StudentAttend.objects.filter(student=student).all()

    dates = []
    for p in pages:
        if p.date not in dates:
            dates.append(p.date)
    
    sums = []
    for d in dates:
        s = 0
        for p in pages.filter(date=d).all():
            s += p.page.quant
        sums.append(s)

    return render(request, 'dashboard/students/details.html',{
        'default':default_par(request),
        'student' : student,
        'pages':pages,
        'attends':attends,
        'dates':dates,
        'sums':sums,
    })


@login_required(2)
def disable(request, id):
    student = Student.objects.filter(id = id).first()
    student.disabled = True
    student.save()
    messages.info(request, 'تم الغاء تفعيل الطالب')
    return redirect('/students/show')

@login_required(2)
def enable(request, id):
    student = Student.objects.filter(id = id).first()
    student.disabled = False
    student.save()
    messages.info(request, 'تم الغاء تفعيل الطالب')
    return redirect('/students/show')

@login_required(0)
def delete(request, id):
    student = Student.objects.filter(id = id).first()
    student.delete()
    messages.info(request, 'تمت حذف الطالب بنجاح')
    return redirect('/students/show')

@login_required(2)
def delete_memorized(request, id):
    p = MemorizedPages.objects.filter(id = id).first()
    p.delete()
    messages.info(request, 'تمت حذف الصفحة بنجاح')
    return redirect(f'/students/{p.student.id}/details')