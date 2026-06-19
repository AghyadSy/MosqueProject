from django.contrib import messages
from django.shortcuts import redirect, render

from ..decorators import default_par, login_required
from ..models import Lesson, LessonTeacherAssignment, Student, User


def _get_accessible_students(user):
    if user.permission == 2:
        return user.students()
    return Student.objects.all()


def _get_accessible_teachers(user):
    if user.permission == 2:
        return User.objects.filter(id=user.id)
    return User.objects.all()


def _get_lesson_queryset(user):
    queryset = Lesson.objects.prefetch_related(
        'attended_students',
        'teacher_assignments__teacher',
        'teacher_assignments__students',
    ).select_related('created_by')
    if user.permission == 2:
        queryset = queryset.filter(teacher_assignments__teacher=user)
    return queryset


def _build_teacher_sections(user, selected_teacher_ids=None, teacher_student_map=None):
    selected_teacher_ids = selected_teacher_ids or []
    teacher_student_map = teacher_student_map or {}
    sections = []
    for teacher in _get_accessible_teachers(user):
        sections.append({
            'teacher': teacher,
            'students': teacher.students(),
            'is_selected': teacher.id in selected_teacher_ids,
            'selected_student_ids': teacher_student_map.get(teacher.id, []),
        })
    return sections


def _get_lesson_or_redirect(request, id):
    user = User.user(request)
    lesson = _get_lesson_queryset(user).filter(id=id).first()
    if lesson is None:
        messages.info(request, 'الدرس غير موجود أو غير مسموح لك الوصول إليه')
        return None
    return lesson


def _normalize_teacher_groups(request, user):
    selected_teacher_ids = request.POST.getlist('teacher_ids')
    accessible_teacher_ids = {teacher.id for teacher in _get_accessible_teachers(user)}
    teacher_groups = []

    for teacher_id in selected_teacher_ids:
        try:
            parsed_teacher_id = int(teacher_id)
        except (TypeError, ValueError):
            continue
        if parsed_teacher_id not in accessible_teacher_ids:
            continue

        teacher = User.objects.filter(id=parsed_teacher_id).first()
        teacher_student_ids = {student.id for student in teacher.students()}
        raw_student_ids = request.POST.getlist(f'teacher_{parsed_teacher_id}_student_ids')
        normalized_student_ids = []

        for student_id in raw_student_ids:
            try:
                parsed_student_id = int(student_id)
            except (TypeError, ValueError):
                continue
            if parsed_student_id in teacher_student_ids and parsed_student_id not in normalized_student_ids:
                normalized_student_ids.append(parsed_student_id)

        teacher_groups.append({
            'teacher': teacher,
            'student_ids': normalized_student_ids,
        })

    return teacher_groups


def _sync_teacher_assignments(lesson, teacher_groups):
    lesson.teacher_assignments.all().delete()
    all_student_ids = []

    for group in teacher_groups:
        assignment = LessonTeacherAssignment.objects.create(
            lesson=lesson,
            teacher=group['teacher'],
        )
        if group['student_ids']:
            assignment.students.set(group['student_ids'])
            for student_id in group['student_ids']:
                if student_id not in all_student_ids:
                    all_student_ids.append(student_id)

    lesson.attended_students.set(all_student_ids)


def _lesson_context(request, lesson=None):
    selected_teacher_ids = list(lesson.teacher_assignments.values_list('teacher_id', flat=True)) if lesson else []
    teacher_student_map = {
        assignment.teacher_id: list(assignment.students.values_list('id', flat=True))
        for assignment in lesson.teacher_assignments.all()
    } if lesson else {}
    return {
        'default': default_par(request),
        'lesson': lesson,
        'students': _get_accessible_students(User.user(request)),
        'teacher_sections': _build_teacher_sections(User.user(request), selected_teacher_ids, teacher_student_map),
        'selected_student_ids': list(lesson.attended_students.values_list('id', flat=True)) if lesson else [],
        'selected_teacher_ids': selected_teacher_ids,
        'teacher_student_map': teacher_student_map,
    }


@login_required(2)
def add(request):
    user = User.user(request)
    if request.method != 'POST':
        return redirect('/lessons/show')

    name = request.POST.get('name', '').strip()
    date = request.POST.get('date')
    teacher_groups = _normalize_teacher_groups(request, user)
    if not name or not date:
        messages.info(request, 'اسم الدرس والتاريخ مطلوبان')
        return redirect('/lessons/show')
    if not teacher_groups:
        messages.info(request, 'يجب اختيار أستاذ واحد على الأقل')
        return redirect('/lessons/show')

    lesson = Lesson.objects.create(
        name=name,
        date=date,
        created_by=user,
    )
    _sync_teacher_assignments(lesson, teacher_groups)
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
        'teacher_sections': _build_teacher_sections(user),
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
        teacher_groups = _normalize_teacher_groups(request, user)
        if not name or not date:
            messages.info(request, 'اسم الدرس والتاريخ مطلوبان')
            return render(request, 'dashboard/lessons/edit.html', _lesson_context(request, lesson))
        if not teacher_groups:
            messages.info(request, 'يجب اختيار أستاذ واحد على الأقل')
            return render(request, 'dashboard/lessons/edit.html', _lesson_context(request, lesson))

        lesson.name = name
        lesson.date = date
        lesson.save()
        _sync_teacher_assignments(lesson, teacher_groups)
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
