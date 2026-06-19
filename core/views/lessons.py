from django.contrib import messages
from django.shortcuts import redirect, render

from ..decorators import default_par, login_required
from ..models import Lesson, Student, User


def _get_accessible_students(user):
    if user.permission == 2:
        return user.students()
    return Student.objects.all()


def _get_lesson_queryset(user):
    queryset = Lesson.objects.prefetch_related('attended_students').select_related('created_by')
    if user.permission == 2:
        queryset = queryset.filter(created_by=user)
    return queryset


def _get_lesson_or_redirect(request, id):
    user = User.user(request)
    lesson = _get_lesson_queryset(user).filter(id=id).first()
    if lesson is None:
        messages.info(request, 'الدرس غير موجود أو غير مسموح لك الوصول إليه')
        return None
    return lesson


def _normalize_student_ids(request, user):
    selected_ids = request.POST.getlist('attend_student_ids')
    accessible_ids = {student.id for student in _get_accessible_students(user)}

    normalized_ids = []
    for student_id in selected_ids:
        try:
            parsed_id = int(student_id)
        except (TypeError, ValueError):
            continue
        if parsed_id in accessible_ids and parsed_id not in normalized_ids:
            normalized_ids.append(parsed_id)
    return normalized_ids


def _lesson_context(request, lesson=None):
    return {
        'default': default_par(request),
        'lesson': lesson,
        'students': _get_accessible_students(User.user(request)),
        'selected_student_ids': list(lesson.attended_students.values_list('id', flat=True)) if lesson else [],
    }


@login_required(2)
def add(request):
    user = User.user(request)
    if request.method != 'POST':
        return redirect('/lessons/show')

    name = request.POST.get('name', '').strip()
    date = request.POST.get('date')
    if not name or not date:
        messages.info(request, 'اسم الدرس والتاريخ مطلوبان')
        return redirect('/lessons/show')

    lesson = Lesson.objects.create(
        name=name,
        date=date,
        created_by=user,
    )
    lesson.attended_students.set(_normalize_student_ids(request, user))
    messages.info(request, 'تمت إضافة الدرس بنجاح')
    return redirect('/lessons/show')


@login_required(2)
def show(request):
    user = User.user(request)
    lessons = _get_lesson_queryset(user)
    return render(request, 'dashboard/lessons/show.html', {
        'default': default_par(request),
        'lessons': lessons,
        'students': _get_accessible_students(user),
    })


@login_required(2)
def edit(request, id):
    lesson = _get_lesson_or_redirect(request, id)
    if lesson is None:
        return redirect('/lessons/show')

    user = User.user(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        date = request.POST.get('date')
        if not name or not date:
            messages.info(request, 'اسم الدرس والتاريخ مطلوبان')
            return render(request, 'dashboard/lessons/edit.html', _lesson_context(request, lesson))

        lesson.name = name
        lesson.date = date
        lesson.save()
        lesson.attended_students.set(_normalize_student_ids(request, user))
        messages.info(request, 'تم تعديل الدرس بنجاح')
        return redirect('/lessons/show')

    return render(request, 'dashboard/lessons/edit.html', _lesson_context(request, lesson))


@login_required(2)
def delete(request, id):
    if request.method != 'POST':
        return redirect('/lessons/show')

    lesson = _get_lesson_or_redirect(request, id)
    if lesson is None:
        return redirect('/lessons/show')

    lesson.delete()
    messages.info(request, 'تم حذف الدرس بنجاح')
    return redirect('/lessons/show')
