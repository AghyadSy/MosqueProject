from django.contrib import messages
from django.shortcuts import redirect, render

from ..decorators import default_par, login_required
from ..models import Activity, ActivityTeacherAssignment, ActivityType, Student, User


def _get_accessible_students(user):
    if user.permission == 2:
        return user.students()
    return Student.objects.all()


def _get_accessible_teachers(user):
    if user.permission == 2:
        return User.objects.filter(id=user.id)
    return User.objects.all()


def _get_activity_queryset(user):
    queryset = Activity.objects.prefetch_related(
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


def _get_activity_or_redirect(request, id):
    user = User.user(request)
    activity = _get_activity_queryset(user).filter(id=id).first()
    if activity is None:
        messages.info(request, 'النشاط غير موجود أو غير مسموح لك الوصول إليه')
        return None
    return activity


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


def _sync_teacher_assignments(activity, teacher_groups):
    activity.teacher_assignments.all().delete()
    all_student_ids = []

    for group in teacher_groups:
        assignment = ActivityTeacherAssignment.objects.create(
            activity=activity,
            teacher=group['teacher'],
        )
        if group['student_ids']:
            assignment.students.set(group['student_ids'])
            for student_id in group['student_ids']:
                if student_id not in all_student_ids:
                    all_student_ids.append(student_id)

    activity.attended_students.set(all_student_ids)


def _activity_context(request, activity=None):
    user = User.user(request)
    selected_teacher_ids = list(activity.teacher_assignments.values_list('teacher_id', flat=True)) if activity else []
    teacher_student_map = {
        assignment.teacher_id: list(assignment.students.values_list('id', flat=True))
        for assignment in activity.teacher_assignments.all()
    } if activity else {}
    activity_types = [
        {'value': value, 'label': label}
        for value, label in ActivityType.choices
    ]
    return {
        'default': default_par(request),
        'activity': activity,
        'students': _get_accessible_students(user),
        'teacher_sections': _build_teacher_sections(user, selected_teacher_ids, teacher_student_map),
        'activity_types': activity_types,
        'selected_student_ids': list(activity.attended_students.values_list('id', flat=True)) if activity else [],
        'selected_teacher_ids': selected_teacher_ids,
        'teacher_student_map': teacher_student_map,
    }


@login_required(2)
def add(request):
    user = User.user(request)
    if request.method != 'POST':
        return redirect('/activities/show')

    name = request.POST.get('name', '').strip()
    date = request.POST.get('date')
    activity_type = request.POST.get('activity_type', '')
    other_activity_type = request.POST.get('other_activity_type', '').strip()
    allowed_types = {value for value, _ in ActivityType.choices}
    teacher_groups = _normalize_teacher_groups(request, user)

    if not name or not date:
        messages.info(request, 'اسم النشاط والتاريخ مطلوبان')
        return redirect('/activities/show')
    if activity_type not in allowed_types:
        messages.info(request, 'نوع النشاط غير صالح')
        return redirect('/activities/show')
    if activity_type == ActivityType.OTHER and not other_activity_type:
        messages.info(request, 'يرجى كتابة نوع النشاط الآخر')
        return redirect('/activities/show')
    if not teacher_groups:
        messages.info(request, 'يجب اختيار أستاذ واحد على الأقل')
        return redirect('/activities/show')

    activity = Activity.objects.create(
        name=name,
        date=date,
        image=request.FILES.get('image'),
        activity_type=activity_type,
        other_activity_type=other_activity_type,
        created_by=user,
    )
    _sync_teacher_assignments(activity, teacher_groups)
    messages.info(request, 'تمت إضافة النشاط بنجاح')
    return redirect('/activities/show')


@login_required(2)
def show(request):
    user = User.user(request)
    activities = _get_activity_queryset(user)
    return render(request, 'dashboard/activities/show.html', {
        'default': default_par(request),
        'activities': activities,
        'students': _get_accessible_students(user),
        'teacher_sections': _build_teacher_sections(user),
        'activity_types': [
            {'value': value, 'label': label}
            for value, label in ActivityType.choices
        ],
    })


@login_required(2)
def edit(request, id):
    activity = _get_activity_or_redirect(request, id)
    if activity is None:
        return redirect('/activities/show')

    user = User.user(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        date = request.POST.get('date')
        activity_type = request.POST.get('activity_type', '')
        other_activity_type = request.POST.get('other_activity_type', '').strip()
        allowed_types = {value for value, _ in ActivityType.choices}
        teacher_groups = _normalize_teacher_groups(request, user)

        if not name or not date:
            messages.info(request, 'اسم النشاط والتاريخ مطلوبان')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))
        if activity_type not in allowed_types:
            messages.info(request, 'نوع النشاط غير صالح')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))
        if activity_type == ActivityType.OTHER and not other_activity_type:
            messages.info(request, 'يرجى كتابة نوع النشاط الآخر')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))
        if not teacher_groups:
            messages.info(request, 'يجب اختيار أستاذ واحد على الأقل')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))

        activity.name = name
        activity.date = date
        if request.FILES.get('image'):
            activity.image = request.FILES.get('image')
        activity.activity_type = activity_type
        activity.other_activity_type = other_activity_type
        activity.save()
        _sync_teacher_assignments(activity, teacher_groups)
        messages.info(request, 'تم تعديل النشاط بنجاح')
        return redirect('/activities/show')

    return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))


@login_required(2)
def delete(request, id):
    if request.method != 'POST':
        return redirect('/activities/show')

    activity = _get_activity_or_redirect(request, id)
    if activity is None:
        return redirect('/activities/show')

    activity.delete()
    messages.info(request, 'تم حذف النشاط بنجاح')
    return redirect('/activities/show')
