from django.contrib import messages
from django.shortcuts import redirect, render

from ..decorators import default_par, login_required
from ..models import Activity, ActivityType, Student, User


def _get_accessible_students(user):
    if user.permission == 2:
        return user.students()
    return Student.objects.all()


def _get_activity_queryset(user):
    queryset = Activity.objects.prefetch_related('attended_students').select_related('created_by')
    if user.permission == 2:
        queryset = queryset.filter(created_by=user)
    return queryset


def _get_activity_or_redirect(request, id):
    user = User.user(request)
    activity = _get_activity_queryset(user).filter(id=id).first()
    if activity is None:
        messages.info(request, 'النشاط غير موجود أو غير مسموح لك الوصول إليه')
        return None
    return activity


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


def _activity_context(request, activity=None):
    user = User.user(request)
    activity_types = [
        {'value': value, 'label': label}
        for value, label in ActivityType.choices
    ]
    return {
        'default': default_par(request),
        'activity': activity,
        'students': _get_accessible_students(user),
        'activity_types': activity_types,
        'selected_student_ids': list(activity.attended_students.values_list('id', flat=True)) if activity else [],
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

    if not name or not date:
        messages.info(request, 'اسم النشاط والتاريخ مطلوبان')
        return redirect('/activities/show')
    if activity_type not in allowed_types:
        messages.info(request, 'نوع النشاط غير صالح')
        return redirect('/activities/show')
    if activity_type == ActivityType.OTHER and not other_activity_type:
        messages.info(request, 'يرجى كتابة نوع النشاط الآخر')
        return redirect('/activities/show')

    activity = Activity.objects.create(
        name=name,
        date=date,
        image=request.POST.get('image', '').strip(),
        activity_type=activity_type,
        other_activity_type=other_activity_type,
        created_by=user,
    )
    activity.attended_students.set(_normalize_student_ids(request, user))
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

        if not name or not date:
            messages.info(request, 'اسم النشاط والتاريخ مطلوبان')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))
        if activity_type not in allowed_types:
            messages.info(request, 'نوع النشاط غير صالح')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))
        if activity_type == ActivityType.OTHER and not other_activity_type:
            messages.info(request, 'يرجى كتابة نوع النشاط الآخر')
            return render(request, 'dashboard/activities/edit.html', _activity_context(request, activity))

        activity.name = name
        activity.date = date
        activity.image = request.POST.get('image', '').strip()
        activity.activity_type = activity_type
        activity.other_activity_type = other_activity_type
        activity.save()
        activity.attended_students.set(_normalize_student_ids(request, user))
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
