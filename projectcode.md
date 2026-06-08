## generate_projectcode.py
```
"""generate_projectcode.py

This script walks through the Django project directory, collects the contents of all
text-based source files (Python, HTML, CSS, JavaScript, etc.), and writes them into a
single Markdown file named ``projectcode.md``. Each file's content is wrapped in a
Markdown code block and preceded by a heading that shows the file's relative path.

Binary files (images, archives, SQLite database, etc.) are automatically skipped.
The script also skips the output file itself to avoid recursion.
"""

import os


def is_binary(file_path: str) -> bool:
    """Return True if the file appears to be binary.

    The function attempts to read the file as UTF‑8 text. If a ``UnicodeDecodeError``
    or any other exception occurs, the file is considered binary and will be
    ignored.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return False
    except Exception:
        return True


def main() -> None:
    # Determine the root directory (the directory containing this script).
    root = os.path.abspath(os.path.dirname(__file__))
    output_path = os.path.join(root, "projectcode.md")

    # File extensions that are definitely binary and should be ignored.
    exclude_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".zip", ".sqlite", ".db"}

    # Open the output file for writing (this will truncate any existing content).
    with open(output_path, "w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                # Skip known binary extensions.
                if ext in exclude_exts:
                    continue

                file_path = os.path.join(dirpath, filename)

                # Skip the output file itself to avoid infinite recursion.
                if os.path.abspath(file_path) == os.path.abspath(output_path):
                    continue

                # Skip files that cannot be read as text.
                if is_binary(file_path):
                    continue

                # Compute the relative path for heading.
                rel_path = os.path.relpath(file_path, root)

                # Exclude static/dashboard and static/bootstrap directories.
                # This check works for any depth under the project root.
                if rel_path.startswith(os.path.join("static", "dashboard")) or rel_path.startswith(os.path.join("static", "bootstrap")) or rel_path.startswith(os.path.join(".git")):
                    continue

                # Write a heading with the relative path and then the file content.
                out.write(f"## {rel_path}\n")
                out.write("```\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"[Error reading file: {e}]")
                out.write("\n```\n\n")


if __name__ == "__main__":
    main()

```

## manage.py
```
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_alrahmanmosque.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

## api\admin.py
```
from django.contrib import admin

# Register your models here.

```

## api\apps.py
```
from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

```

## api\models.py
```
from django.db import models

# Create your models here.

```

## api\renderers.py
```
from rest_framework.renderers import JSONRenderer

class ForceAsciiJSONRenderer(JSONRenderer):
    ensure_ascii = True
    charset = 'utf-8'
    media_type = 'application/json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Explicitly call super and ensure it's ASCII
        response = super().render(data, accepted_media_type, renderer_context)
        return response
```

## api\serializers.py
```
from datetime import datetime

from rest_framework import serializers
from core.models import (
    User, Student, GroupSession, StudentAttend,
    Page, MemorizedPages
)

# ---------- Login ----------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    permission = serializers.IntegerField(default=2)

# ---------- Student ----------
class StudentListSerializer(serializers.ModelSerializer):
    pages_number = serializers.SerializerMethodField()
    abs_number = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'name', 'pages_number', 'abs_number']

    def get_pages_number(self, obj):
        return MemorizedPages.objects.filter(student=obj).count()

    def get_abs_number(self, obj):
        return StudentAttend.objects.filter(student=obj, is_attend=False).count()

class StudentDetailSerializer(serializers.ModelSerializer):
    # Map model fields to old API keys
    phone = serializers.CharField(source='phone_number')
    school = serializers.CharField(source='school_name')
    father_do = serializers.CharField(source='father_name')
    birth_day = serializers.DateField(source='birth_date')

    pages = serializers.SerializerMethodField()
    abs_number = serializers.SerializerMethodField()
    abs_date = serializers.SerializerMethodField()
    pages_number = serializers.SerializerMethodField()

    # Fields not in model – return empty defaults
    sign_date = serializers.SerializerMethodField()
    archives = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id',
            'name', 'address', 'phone', 'school', 'father_do',
            'birth_day', 'sign_date', 'archives',
            'pages_number', 'pages',
            'activities', 'lessons',
            'abs_number', 'abs_date', 'notes'
        ]

    def get_pages_number(self, obj):
        return MemorizedPages.objects.filter(student=obj).count()

    def get_abs_number(self, obj):
        return StudentAttend.objects.filter(student=obj, is_attend=False).count()

    def get_abs_date(self, obj):
        l = list(StudentAttend.objects.filter(
            student=obj, is_attend=False
        ).values_list('date', flat=True).distinct())
        r = []
        for x in l:
            r.append(x.isoformat())
        return r
    
    def get_att_number(self, obj):
        return StudentAttend.objects.filter(student=obj, is_attend=False).count()

    def get_abs_date(self, obj):
        l = list(StudentAttend.objects.filter(
            student=obj, is_attend=False
        ).values_list('date', flat=True).distinct())
        r = []
        for x in l:
            r.append(x.isoformat())
        return r

    def get_pages(self, obj):
        mem_pages = obj.memorizedpages_set.select_related('page').order_by('-date')
        grouped = {}
        for mp in mem_pages:
            section = mp.page.section
            key = mp.date   # date alone is enough now
            if section not in grouped:
                grouped[section] = {}
            if key not in grouped[section]:
                grouped[section][key] = []
            grouped[section][key].append(mp.page.name)

        result = []
        for section, entries in grouped.items():
            memorize_list = []
            for date_val, page_names in entries.items():
                memorize_list.append({
                    "date": date_val.isoformat(),
                    "evaluation": "",        # always empty, as requested
                    "pages": page_names
                })
            result.append({
                "page_archive": section,
                "is_tested": False,
                "memorize": memorize_list,
                "pages_numbers":MemorizedPages.objects.filter(student=obj, page__section=section).count()
            })
        return result

    # Placeholder methods
    def get_sign_date(self, obj):
        return datetime.today().isoformat()

    def get_archives(self, obj):
        return []

    def get_activities(self, obj):
        return []

    def get_lessons(self, obj):
        return []

    def get_notes(self, obj):
        return []

# ---------- Teacher (Admin) ----------
class TeacherSerializer(serializers.ModelSerializer):
    abs = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'abs']

    def get_abs(self, obj):
        students = obj.students()
        return StudentAttend.objects.filter(
            student__in=students, is_attend=False
        ).count()

# ---------- Attendance ----------
class StudentAttendSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = StudentAttend
        fields = ['id', 'student', 'student_name', 'date', 'is_attend']

# Minimal placeholders for other sections (unused now)
class ActivitySerializer(serializers.Serializer):
    pass

class LessonSerializer(serializers.Serializer):
    pass

class HadithSerializer(serializers.Serializer):
    pass
```

## api\tests.py
```
from django.test import TestCase

# Create your tests here.

```

## api\urls.py
```
from django.urls import path
from .views import (
    LoginView, AllStudentsView, StudentInfoView,
    AdminsInfoView, AdminStudentsView,
    AttendStudentsView, AttendStudentsGetView,
    AttendStudentsDeleteView, AttendStudentsGetAllView,
    PagesView,
    VersionView,
    PlaceholderView
)

urlpatterns = [
    path('login', LoginView.as_view()),
    path('students', AllStudentsView.as_view()),
    path('student-info', StudentInfoView.as_view()),
    path('admins-info', AdminsInfoView.as_view()),
    path('admin-students', AdminStudentsView.as_view()),

    # Attendance
    path('add/attend', AttendStudentsView.as_view()),
    path('get/attend', AttendStudentsGetView.as_view()),
    path('attend', AttendStudentsDeleteView.as_view()),
    path('get/all/attend', AttendStudentsGetAllView.as_view()),

    # Pages
    path('pages', PagesView.as_view()),

    # System
    path('version', VersionView.as_view()),

    # Other placeholder endpoints (to avoid 404)
    path('ahadith', PlaceholderView.as_view()),
    path('activities', PlaceholderView.as_view()),
    path('get/activities', PlaceholderView.as_view()),
    path('add/activities', PlaceholderView.as_view()),
    path('lessons', PlaceholderView.as_view()),
    path('get/lessons', PlaceholderView.as_view()),
    path('add/lessons', PlaceholderView.as_view()),
    path('archive', PlaceholderView.as_view()),
    path('notes', PlaceholderView.as_view()),
    path('<str:type>/messages', PlaceholderView.as_view()),
]
```

## api\views.py
```
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date

from core.models import (
    User, Student, GroupSession, StudentAttend,
    Page, MemorizedPages
)
from .serializers import (
    LoginSerializer, StudentListSerializer, StudentDetailSerializer,
    TeacherSerializer
)

# ---------- Authentication ----------
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_202_ACCEPTED)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = User.objects.filter(
            username=username, password=password
        ).first()
        if user is None:
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_200_OK)

# ---------- Students ----------
class AllStudentsView(APIView):
    def post(self, request):
        admin_name = request.data.get('admin_name')
        teacher = User.objects.filter(username=admin_name).first()
        if not teacher:
            return Response({'students': []})
        students = teacher.students()
        serializer = StudentListSerializer(students, many=True)
        return Response({'students': serializer.data})

class StudentInfoView(APIView):
    def post(self, request):
        student_name = request.data.get('name')
        student = Student.objects.filter(name=student_name).first()
        if not student:
            return Response({'data': {}})
        serializer = StudentDetailSerializer(student)
        print(serializer.data)
        return Response({'data': serializer.data})

# ---------- Teacher list with absences ----------
class AdminsInfoView(APIView):
    def get(self, request):
        teachers = User.objects.all()
        serializer = TeacherSerializer(teachers, many=True)
        return Response({'admins': serializer.data})

# ---------- Students of a specific teacher ----------
class AdminStudentsView(APIView):
    def post(self, request):
        admin_name = request.data.get('admin_name')
        teacher = User.objects.filter(username=admin_name).first()
        if not teacher:
            return Response({'students': []})
        students = teacher.students()
        return Response({'students': [s.name for s in students]})

# ---------- Attendance ----------
class AttendStudentsView(APIView):
    def post(self, request):
        admin_name = request.data.get('admin_name')
        attend_list = request.data.get('attend', [])
        today = date.today()
        teacher = User.objects.get(username=admin_name)
        students = teacher.students()
        # Delete previous records for this teacher+date
        StudentAttend.objects.filter(
            student__in=students, date=today
        ).delete()
        # Create new records
        for student in students:
            is_att = student.name in attend_list
            StudentAttend.objects.create(
                student=student, date=today, is_attend=is_att
            )
        return Response(status=status.HTTP_200_OK)

class AttendStudentsGetView(APIView):
    def post(self, request):
        admin_name = request.data.get('admin_name')
        today = date.today()
        teacher = User.objects.get(username=admin_name)
        students = teacher.students()
        if not StudentAttend.objects.filter(
            student__in=students, date=today
        ).exists():
            return Response(status=404)
        attends = StudentAttend.objects.filter(
            student__in=students, date=today, is_attend=True
        )
        absents = StudentAttend.objects.filter(
            student__in=students, date=today, is_attend=False
        )
        return Response({
            'attend': [a.student.name for a in attends],
            'abs': [a.student.name for a in absents]
        })

class AttendStudentsDeleteView(APIView):
    def delete(self, request):
        admin_name = request.data.get('admin_name')
        del_date = request.data.get('date')
        teacher = User.objects.get(username=admin_name)
        students = teacher.students()
        StudentAttend.objects.filter(
            student__in=students, date=del_date
        ).delete()
        return Response(status=status.HTTP_200_OK)

class AttendStudentsGetAllView(APIView):
    def post(self, request):
        admin_name = request.data.get('admin_name')
        teacher = User.objects.get(username=admin_name)
        students = teacher.students()
        result = []
        for d in StudentAttend.objects.filter(
            student__in=students
        ).dates('date', 'day', order='DESC'):
            day_att = StudentAttend.objects.filter(
                student__in=students, date=d, is_attend=True
            )
            day_abs = StudentAttend.objects.filter(
                student__in=students, date=d, is_attend=False
            )
            result.append({
                'date': d,
                'attends': [a.student.name for a in day_att],
                'abs': [a.student.name for a in day_abs]
            })
        return Response({'data': result})

class PagesView(APIView):
    def post(self, request):
        student_name = request.data.get('student')
        pages = request.data.get('pages', [])        # list of page numbers/names
        evaluation = request.data.get('evaluation', '')
        # page_archive is now the section number (int)
        page_archive = request.data.get('page_archive')   # e.g., 1
        student = Student.objects.filter(name=student_name).first()
        today = date.today()
        for p in pages:
            # Find the Page by name and section
            page = Page.objects.filter(name=p, section=page_archive).first()
            
            if page:
                MemorizedPages.objects.create(
                    student=student, page=page, date=today
                )
        return Response("تمت الاضافة بنجاح", status=200)

    def delete(self, request):
        student_name = request.data.get('name')
        page_archive = request.data.get('page_archive')   # section number
        del_date = request.data.get('date')
        page_name = request.data.get('page')             # a single page name to delete

        student = Student.objects.get(name=student_name)
        MemorizedPages.objects.filter(
            student=student,
            date=del_date,
            page__name=str(page_name),
            page__section=page_archive
        ).delete()
        return Response(status=200)
# ---------- Version ----------
class VersionView(APIView):
    def get(self, request):
        return Response("1.0.0")

# ---------- Placeholder views for other endpoints (return empty or simple responses) ----------
class PlaceholderView(APIView):
    def get(self, request):
        return Response({})
    def post(self, request):
        return Response({})
    def put(self, request):
        return Response({})
    def delete(self, request):
        return Response({})
```

## api\__init__.py
```

```

## api\migrations\__init__.py
```

```

## core\admin.py
```
from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(GroupSession)
admin.site.register(StudentAttend)
admin.site.register(MemorizedPages)
```

## core\apps.py
```
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

```

## core\decorators.py
```
import functools
from django.shortcuts import redirect
from django.contrib import messages
from .models import User

def default_par(request):
    return {
        'user': User.user(request),
    }

# def login_required(view_func):
#     @functools.wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         user = User.user(request)
#         if  user == None:
#             messages.info(request, "يجب عليك تسجيل الدخول")
#             return redirect('/login')
#         if user.permission > 2:
#             messages.info(request, "غير مسموح لك بهذه العملية")
#             return redirect('/login')
#         return view_func(request, *args, **kwargs)
#     return wrapper

def login_required(permision):
    def w(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = User.user(request)
            if  user == None:
                messages.info(request, "يجب عليك تسجيل الدخول")
                return redirect('/login')
            if user.permission > permision:
                messages.info(request, "غير مسموح لك بهذه العملية")
                return redirect('/')
            return view_func(request, *args, **kwargs)
        return wrapper
    return w
```

## core\models.py
```
from datetime import date
from django.db import models
from django.core.validators import RegexValidator

class User(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    permission = models.IntegerField()

    def login(self, request):
        request.session['username'] = self.username
        request.session['password'] = self.password

    def logout(self, request):
        request.session['username'] = None
        request.session['password'] = None
    
    def user(request):
        return User.objects.filter(username = request.session.get('username'), password = request.session.get('password')).first()
    
    def students(self):
        s = []
        for g in GroupSession.objects.filter(teacher=self).all() :
            s.append(g.student)
        return s

    def __str__(self):
        return self.username

class Student(models.Model):
    name = models.CharField(max_length=50)
    father_name = models.CharField(max_length=50)

    address = models.CharField(max_length=255)
    school_name = models.CharField(max_length=50)
    birth_date = models.DateField()

    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    disabled = models.BooleanField(default=False)

    def teacher(self):
        if GroupSession.objects.filter(student=self).first():
            return GroupSession.objects.filter(student=self).first().teacher
        return None

    def __str__(self):
        return self.name

class GroupSession(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student,on_delete=models.CASCADE)

    def __str__(self):
        return self.teacher.username + " --- " + self.student.name

class StudentAttend(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    is_attend = models.BooleanField(default=True)

    def students_of_teacher(teacher):
        d = []
        for s in StudentAttend.objects.all():
            if s.student.teacher() == teacher:
                d.append(s.id)
        return d


    def group_by_date():
        # data = [
        #    {
            #     'date',
            #     'data':[
            #         {
            #           'teacher','attend':[],'absent':[]  
            #         }
            #     ]
        #    }
        # ]
        data = []
        is_date_in_attend = []
        for a in StudentAttend.objects.all().order_by('-date'):
            is_date = None
            if a.date not in is_date_in_attend:
                is_date_in_attend.append(a.date)

        for date in is_date_in_attend:
            sub_data = []
            for teacher in User.objects.all():
                s = StudentAttend.students_of_teacher(teacher)
                attend = StudentAttend.objects.filter(date=date, is_attend=1, id__in=s).all()
                absent = StudentAttend.objects.filter(date=date, is_attend=0, id__in=s).all()
                sub_data.append(
                    {
                        'teacher':teacher,
                        'attend':attend,
                        'absent':absent
                    }
                )
            data.append({
                'date':date,
                'data':sub_data
            })
        return data


    def __str__(self):
        return self.student.name + " --- " + self.date.strftime("%Y-%m-%d")

class Page(models.Model):
    name = models.CharField(max_length=50)
    quant = models.FloatField()
    section = models.IntegerField()

    def __str__(self):
        return self.name

class MemorizedPages(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return self.page.name + " --- " + self.student.name


# for section in range(1,28):
#     for p in range(1,21):
#         if Page.objects.filter(name=str(p), quant=1, section=section).first() == None:
#             print("already")
#             page = Page(name=str(p), quant=1, section=section)
#             page.save()
```

## core\tests.py
```
from django.test import TestCase
```

## core\urls.py
```
from django.urls import path
from .views import auth, users, students, group_session, student_attend

urlpatterns = [
     path('', auth.index, name='index'),
     path('login/', auth.login, name='login'),
     path('logout/', auth.logout, name='logout'),

     path('users/add/', users.add_user, name='add_user'),
     path('users/show', users.show_users, name='show_users'),
     path('users/<int:id>/edit/', users.edit_user, name='edit_user'),
     path('users/<int:id>/delete/', users.delete_user, name='delete_user'),

     path('students/add/', students.add, name='add_user'),
     path('students/show', students.show, name='show_users'),
     path('students/<int:id>/details', students.details, name='show_users'),
     path('students/<int:id>/edit/', students.edit, name='edit_user'),
     path('students/<int:id>/delete/', students.delete, name='delete_user'),
     path('memorized/<int:id>/delete/', students.delete_memorized, name='delete_user'),
     path('students/<int:id>/disable/', students.disable, name='disable_user'),
     path('students/<int:id>/enable/', students.enable, name='enable_user'),
     path('students/<int:student_id>/addmemorize/', students.add_memorize, name='edit_user'),

     path('get_pages/<int:section>/', students.get_pages, name='edit_user'),

     path('groupsession/show', group_session.show, name='show_users'),
     path('groupsession/<int:id>/add/', group_session.add, name='add_user'),
     path('groupsession/<int:id>/edit/', group_session.edit, name='edit_user'),
     path('groupsession/<int:old_teacher_id>/changeteacher/', group_session.change_teacher, name='edit_user'),
     path('groupsession/<int:id>/delete/', group_session.delete, name='delete_user'),

     path('attend/<int:id>/add/', student_attend.add, name='add_user'),
     path('attend/show', student_attend.show, name='show_users'),
     path('attend/<str:date>/<int:teacher_id>/edit/', student_attend.edit, name='edit_user'),
     path('attend/<str:date>/<int:teacher_id>/delete/', student_attend.delete, name='delete_user'),

]
```

## core\__init__.py
```

```

## core\migrations\0001_initial.py
```
# Generated by Django 4.1.1 on 2023-05-29 09:18

import django.contrib.auth.models
from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyUser',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]

```

## core\migrations\0002_user_delete_myuser.py
```
# Generated by Django 4.1.1 on 2023-05-29 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=50)),
                ('password', models.CharField(max_length=50)),
                ('permission', models.IntegerField()),
            ],
        ),
        migrations.DeleteModel(
            name='MyUser',
        ),
    ]

```

## core\migrations\0003_student.py
```
# Generated by Django 4.1.1 on 2025-07-07 10:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_delete_myuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('father_name', models.CharField(max_length=50)),
                ('address', models.CharField(max_length=255)),
                ('school_name', models.CharField(max_length=50)),
                ('birth_date', models.DateField()),
                ('phone_number', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
            ],
        ),
    ]

```

## core\migrations\0004_student_disabled.py
```
# Generated by Django 4.1.1 on 2025-07-15 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]

```

## core\migrations\0005_groupsession.py
```
# Generated by Django 4.1.1 on 2025-07-15 12:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_student_disabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupSession',
            fields=[
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.student')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
        ),
    ]

```

## core\migrations\0006_groupsession_id_alter_groupsession_student.py
```
# Generated by Django 4.1.1 on 2025-07-19 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_groupsession'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupsession',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupsession',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.student'),
        ),
    ]

```

## core\migrations\0007_remove_groupsession_id_alter_groupsession_student.py
```
# Generated by Django 4.1.1 on 2025-07-19 10:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_groupsession_id_alter_groupsession_student'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupsession',
            name='id',
        ),
        migrations.AlterField(
            model_name='groupsession',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.student'),
        ),
    ]

```

## core\migrations\0008_groupsession_id_alter_groupsession_student.py
```
# Generated by Django 4.1.1 on 2025-07-19 10:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_groupsession_id_alter_groupsession_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupsession',
            name='id',
            field=models.BigAutoField(auto_created=True, default=0, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupsession',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.student'),
        ),
    ]

```

## core\migrations\0009_studentattend.py
```
# Generated by Django 4.1.1 on 2025-07-19 14:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_groupsession_id_alter_groupsession_student'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentAttend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.student')),
            ],
        ),
    ]

```

## core\migrations\0010_studentattend_is_attend.py
```
# Generated by Django 4.1.1 on 2025-07-19 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_studentattend'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentattend',
            name='is_attend',
            field=models.BooleanField(default=True),
        ),
    ]

```

## core\migrations\0011_page_memorizedpages.py
```
# Generated by Django 4.1.1 on 2025-09-01 13:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_studentattend_is_attend'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('quant', models.FloatField()),
                ('section', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MemorizedPages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.page')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.student')),
            ],
        ),
    ]

```

## core\migrations\0012_alter_memorizedpages_student.py
```
# Generated by Django 4.1.1 on 2025-09-01 15:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_page_memorizedpages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memorizedpages',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.student'),
        ),
    ]

```

## core\migrations\__init__.py
```

```

## core\templates\core\add_user.html
```
{% extends 'core/base.html' %}
{% block body %}
    <form action="#" method="post">
        {% csrf_token %}
        <input type="text" name="username">
        <input type="text" name="password">
        <input type="number" name="per" max="2" min="0">
        <input type="submit" value="add">
    </form>
{% endblock %}
```

## core\templates\core\base.html
```
<!DOCTYPE html>
<html lang="ar">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/style.css">
    <title>
        جامع الرحمن
    </title>
</head>

<body>
    <div class="topmenu">
        <img src='/static/Logo.jpg' alt="" class="logo">
        <h1>جامع الرحمن</h1>
        <img src='/static/icon.png' class="butmenu" id="butmenuo" onclick="opennav()">
        <ul class="ulmenu" id="ulmenu">
            <img src='/static/close.png' id="butmenuc" onclick="closenav()">
            {% if default.user != None %}
                <li><a href="/">الصفحة الرئيسية</a></li>
                <li><a href="/logout">تسجيل الخروج</a></li>
                <li><a href="/control-panel">لوحة التحكم</a></li>
                <li><a onclick="add_btn()" style="cursor: pointer;">   +  اضافة  </a></li>
                    <ul id="menu_add">
                        <li><a href="/new_student"> طالب جديد</a></li>
                        <li><a href="/new_halaqa">حلقة جديدة</a></li>
                        <li><a href="/hadith/new">حديث جديد</a></li>
                        <li><a href="/new_test">امتحان جديد</a></li>
                        <li><a href="/lessons/new_lesson">درس جديد</a></li>
                        <li><a href="/activities/new_activity">نشاط جديد</a></li>
                    </ul>
                <li><a href="/attend_admins/new">حضور المشرفين</a></li>
                <li><a href="/attend_students/new">حضور الطلاب</a></li>
                <li><a href="/attend_students/send-message">ارسال رسائل الغياب</a></li>
                <li><a href="/pages/new">تسجيل حفظ طلاب</a></li>
                <li><a href="/search">البحث عن طالب</a></li>
            {% else %}
                <li><a href="/login">تسجيل الدخول</a></li>
            {% endif %}
        </ul>
    </div>
    <script>
        var menu = document.getElementById('ulmenu');
        var bo = document.getElementById('butmenuo');
        var bc = document.getElementById('butmenuc');

        var menu_add = document.getElementById("menu_add");
        
        bc.style.display = "none";
        menu_add.style.display = "none";
        function opennav(){
                menu.style.display = "block";
                bc.style.display = "inline-block";
                bo.style.display = "none";
        }
        function closenav(){
                menu.style.display = "none";
                bc.style.display = "none";
                bo.style.display = "inline-block";
        }
        function add_btn(){
            if (menu_add.style.display == "none"){
                menu_add.style.display = "block";
            }
            else if (menu_add.style.display == "block"){
                menu_add.style.display = "none";
            }
        }
    </script>
    <div style="display: block;height: 150px;width: 100%;"></div>
    <div id="body">
        {% for message in messages %}
            {{message}}
        {% endfor %}
        {% block body %}{% endblock %}
    </div>
    <div style="padding-bottom: 100px;"></div>
</body>
</html>
```

## core\templates\core\edit_user.html
```
{% extends 'core/base.html' %}
{% block body %}
    <form action="#" method="post">
        {% csrf_token %}
        <input type="text" name="username" value="{{ edit_user.username }}">
        <input type="text" name="password" value="{{ edit_user.password }}">
        <input type="number" name="per" max="2" min="0" value="{{ edit_user.permission }}">
        <input type="submit" value="edit">
    </form>
{% endblock %}
```

## core\templates\core\index.html
```
{% extends 'core/base.html' %}
{% block body %}

{% endblock %}
```

## core\templates\core\login.html
```
{% extends 'core/base.html' %}
{% block body %}
    <form action="#" method="post">
        {% csrf_token %}
        <input type="text" name="username">
        <input type="text" name="password">
        <input type="submit" value="login">
    </form>
{% endblock %}
```

## core\templates\core\show_users.html
```
{% extends 'core/base.html' %}
{% block body %}
    <h1>المستخدمين</h1>
    <table>
        <tr>
            <td>اسم المستحدم</td>
            <td>كلمة السر</td>
            <td>الصلاحية</td>
            <td></td>
        </tr>
        {% for user in users %}
            <tr>
                <td>{{ user.username }}</td>
                <td>{{ user.password }}</td>
                <td>
                    {% if user.permission == 0 %} جميع الصلاحيات {% elif user.permission == 1 %} اداري {% elif user.permission == 2 %} مشرف حلقة {% endif %}
                </td>
                <td>
                    <a href="/users/{{ user.id }}/edit">تعديل</a>
                    {% if default.user.permission == 0 %}
                        <a href="/users/{{ user.id }}/delete">حذف</a>
                    {% endif %}
                </td>
            </tr>
        {% endfor %}
    </table>
{% endblock %}
```

## core\templates\dashboard\base.html
```
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>جامع الرحمن</title>

    <!-- Custom fonts for this template-->
    <link href="/static/dashboard/vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link
        href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i"
        rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css">


    <!-- Custom styles for this template-->
    <link href="/static/dashboard/css/sb-admin-2.min.css" rel="stylesheet">

    <!-- Custom styles for this page -->
    <link href="/static/dashboard/vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rubik:ital,wght@0,300..900;1,300..900&display=swap');
        *{font-family: "Rubik", sans-serif;}
    </style>
</head>

<body id="page-top">

    <!-- Page Wrapper -->
    <div id="wrapper">

        <!-- Sidebar -->
        <ul class="navbar-nav bg-gradient-success sidebar sidebar-dark accordion" id="accordionSidebar">

            <!-- Sidebar - Brand -->
            <a class="sidebar-brand d-flex align-items-center justify-content-center" href="/">
                <div class="sidebar-brand-icon rotate-n-15">
                    <i class="fas fa-laugh-wink"></i>
                </div>
                <div class="sidebar-brand-text mx-3"> جامع الرحمن </div>
            </a>

            <!-- Divider -->
            <hr class="sidebar-divider my-0">

            <!-- Nav Item - Dashboard -->
            <li class="nav-item">
                <a class="nav-link" href="/">
                    <i class="fas fa-fw fa-tachometer-alt"></i>
                    <span>لوحة التحكم</span></a>
            </li>

            <!-- Divider -->
            <hr class="sidebar-divider">

            <!-- Nav Item - Charts -->
            <li class="nav-item">
                <a class="nav-link" href="/users/show">
                    <span>أساتذة</span></a>
            </li>

            <li class="nav-item">
                <a class="nav-link" href="/students/show">
                    <span>الطلاب</span></a>
            </li>

            <li class="nav-item">
                <a class="nav-link" href="/groupsession/show">
                    <span>حلقات</span></a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/attend/show">
                    <span>الحضور</span></a>
            </li>

            <!-- Nav Item - Pages Collapse Menu -->
            <li class="nav-item">
                <a class="nav-link" href="#" data-toggle="collapse" data-target="#collapsePages" aria-expanded="false"
                    aria-controls="collapsePages">
                    <i class="fas fa-fw fa-folder"></i>
                    <span>Pages</span>
                </a>
                <div id="collapsePages" class="collapse" aria-labelledby="headingPages"
                    data-parent="#accordionSidebar">
                    <div class="bg-success py-2 collapse-inner rounded">
                        <a class="collapse-item" style="color: #efefef;" href="login.html">Login</a>
                        <a class="collapse-item" style="color: #efefef;" href="register.html">Register</a>
                        <a class="collapse-item" style="color: #efefef;" href="forgot-password.html">Forgot Password</a>
                        <a class="collapse-item" style="color: #efefef;" href="404.html">404 Page</a>
                        <a class="collapse-item" style="color: #efefef;" href="blank.html">Blank Page</a>
                    </div>
                </div>
            </li>

            <!-- Nav Item - Charts -->
            <li class="nav-item">
                <a class="nav-link" href="charts.html">
                    <i class="fas fa-fw fa-chart-area"></i>
                    <span>Charts</span></a>
            </li>

            <!-- Divider -->
            <hr class="sidebar-divider d-none d-md-block">

            <!-- Sidebar Toggler (Sidebar) -->
            <div class="text-center d-none d-md-inline">
                <button class="rounded-circle border-0" id="sidebarToggle"></button>
            </div>

        </ul>
        <!-- End of Sidebar -->

        <!-- Content Wrapper -->
        <div id="content-wrapper" class="d-flex flex-column" style="background-color: #f2f3f7;">

            <!-- Main Content -->
            <div id="content">

                <!-- Topbar -->
                <nav style="border-bottom: 1px solid #e3e6f0" class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top">

                    <!-- Sidebar Toggle (Topbar) -->
                    <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3">
                        <i class="fa fa-bars"></i>
                    </button>

                    <!-- Topbar Search -->
                    <form
                        class="d-none d-sm-inline-block form-inline mr-auto ml-md-3 my-2 my-md-0 mw-100 navbar-search">
                        <div class="input-group">
                            <input type="text" class="form-control bg-light border-0 small" placeholder="Search for..."
                                aria-label="Search" aria-describedby="basic-addon2">
                            <div class="input-group-append">
                                <button class="btn btn-success" type="button">
                                    <i class="fas fa-search fa-sm"></i>
                                </button>
                            </div>
                        </div>
                    </form>

                    <!-- Topbar Navbar -->
                    <ul class="navbar-nav ml-auto">

                        <!-- Nav Item - Search Dropdown (Visible Only XS) -->
                        <li class="nav-item dropdown no-arrow d-sm-none">
                            <a class="nav-link dropdown-toggle" href="#" id="searchDropdown" role="button"
                                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                <i class="fas fa-search fa-fw"></i>
                            </a>
                            <!-- Dropdown - Messages -->
                            <div class="dropdown-menu dropdown-menu-right p-3 shadow animated--grow-in"
                                aria-labelledby="searchDropdown">
                                <form class="form-inline mr-auto w-100 navbar-search">
                                    <div class="input-group">
                                        <input type="text" class="form-control bg-light border-0 small"
                                            placeholder="Search for..." aria-label="Search"
                                            aria-describedby="basic-addon2">
                                        <div class="input-group-append">
                                            <button class="btn btn-primary" type="button">
                                                <i class="fas fa-search fa-sm"></i>
                                            </button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </li>

                        <!-- Nav Item - Alerts -->
                        <li class="nav-item dropdown no-arrow mx-1">
                            <a class="nav-link dropdown-toggle" href="#" id="alertsDropdown" role="button"
                                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                <i class="fas fa-bell fa-fw"></i>
                                <!-- Counter - Alerts -->
                                <span class="badge badge-danger badge-counter">3+</span>
                            </a>
                            <!-- Dropdown - Alerts -->
                            <div class="dropdown-list dropdown-menu dropdown-menu-right shadow animated--grow-in"
                                aria-labelledby="alertsDropdown">
                                <h6 class="dropdown-header">
                                    Alerts Center
                                </h6>
                                <a class="dropdown-item d-flex align-items-center" href="#">
                                    <div class="mr-3">
                                        <div class="icon-circle bg-primary">
                                            <i class="fas fa-file-alt text-white"></i>
                                        </div>
                                    </div>
                                    <div>
                                        <div class="small text-gray-500">December 12, 2019</div>
                                        <span class="font-weight-bold">A new monthly report is ready to download!</span>
                                    </div>
                                </a>
                                <a class="dropdown-item text-center small text-gray-500" href="#">Show All Alerts</a>
                            </div>
                        </li>

                        <!-- Nav Item - Messages -->
                        <li class="nav-item dropdown no-arrow mx-1">
                            <a class="nav-link dropdown-toggle" href="#" id="messagesDropdown" role="button"
                                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                <i class="fas fa-envelope fa-fw"></i>
                                <!-- Counter - Messages -->
                                <span class="badge badge-danger badge-counter">7</span>
                            </a>
                            <!-- Dropdown - Messages -->
                            <div class="dropdown-list dropdown-menu dropdown-menu-right shadow animated--grow-in"
                                aria-labelledby="messagesDropdown">
                                <h6 class="dropdown-header">
                                    Message Center
                                </h6>
                                <a class="dropdown-item d-flex align-items-center" href="#">
                                    <div class="dropdown-list-image mr-3">
                                        <img class="rounded-circle" src="img/undraw_profile_1.svg"
                                            alt="...">
                                        <div class="status-indicator bg-success"></div>
                                    </div>
                                    <div class="font-weight-bold">
                                        <div class="text-truncate">Hi there! I am wondering if you can help me with a
                                            problem I've been having.</div>
                                        <div class="small text-gray-500">Emily Fowler · 58m</div>
                                    </div>
                                </a>
                                <a class="dropdown-item text-center small text-gray-500" href="#">Read More Messages</a>
                            </div>
                        </li>

                        <div class="topbar-divider d-none d-sm-block"></div>

                        <!-- Nav Item - User Information -->
                        <li class="nav-item dropdown no-arrow">
                            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button"
                                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                <span class="mr-2 d-none d-lg-inline text-gray-600 small">{{ default.user.username }}</span>
                                <img class="img-profile rounded-circle"
                                    src="/static/profile.png?">
                            </a>
                            <!-- Dropdown - User Information -->
                            <div class="dropdown-menu dropdown-menu-right shadow animated--grow-in"
                                aria-labelledby="userDropdown">
                                <a class="dropdown-item" href="#">
                                    <i class="fas fa-user fa-sm fa-fw mr-2 text-gray-400"></i>
                                    Profile
                                </a>
                                <a class="dropdown-item" href="#">
                                    <i class="fas fa-cogs fa-sm fa-fw mr-2 text-gray-400"></i>
                                    Settings
                                </a>
                                <a class="dropdown-item" href="#">
                                    <i class="fas fa-list fa-sm fa-fw mr-2 text-gray-400"></i>
                                    Activity Log
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item" href="/logout" data-toggle="modal" data-target="#logoutModal">
                                    <i class="fas fa-sign-out-alt fa-sm fa-fw mr-2 text-gray-400"></i>
                                    Logout
                                </a>
                            </div>
                        </li>

                    </ul>

                </nav>
                <!-- End of Topbar -->

                <!-- Begin Page Content -->
                <div class="container-fluid">

                    <!-- Page Heading -->
                    <div class="row">
                        {% for message in messages %}
                            <div class="alert alert-{{message.tags}} alert-dismissible show fade col-12">
                                <p style="text-align: center;" class="mb-0">{{message}}</p>
                                <button class="btn-close" data-bs-dismiss='alert'></button>
                            </div>
                        {% endfor %}
                    </div>
                    {% block body %}{% endblock %}

                </div>
                <!-- /.container-fluid -->

            </div>
            <!-- End of Main Content -->

            <!-- Footer -->
            <footer class="sticky-footer bg-white">
                <div class="container my-auto">
                    <div class="copyright text-center my-auto">
                        <span>Copyright &copy; Your Website 2020</span>
                    </div>
                </div>
            </footer>
            <!-- End of Footer -->

        </div>
        <!-- End of Content Wrapper -->

    </div>
    <!-- End of Page Wrapper -->

    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <div class="modal fade" id="logoutModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
        aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">Ready to Leave?</h5>
                    <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">×</span>
                    </button>
                </div>
                <div class="modal-body">Select "Logout" below if you are ready to end your current session.</div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">Cancel</button>
                    <a class="btn btn-danger" href="/logout">Logout</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap core JavaScript-->
    <script src="/static/dashboard/vendor/jquery/jquery.min.js"></script>
    <script src="/static/dashboard/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>

    <!-- Core plugin JavaScript-->
    <script src="/static/dashboard/vendor/jquery-easing/jquery.easing.min.js"></script>

    <!-- Custom scripts for all pages-->
    <script src="/static/dashboard/js/sb-admin-2.min.js"></script>

    <!-- Page level plugins -->

    <!-- Page level custom scripts -->
    <!--<script src="/static/dashboard/js/demo/chart-area-demo.js"></script> -->
    <!-- <script src="/static/dashboard/js/demo/chart-pie-demo.js"></script> -->
    <!-- <script src="/static/dashboard/js/demo/chart-bar-demo.js"></script> -->


    <!-- Page level plugins -->
    <script src="/static/dashboard/vendor/datatables/jquery.dataTables.min.js"></script>
    <script src="/static/dashboard/vendor/datatables/dataTables.bootstrap4.min.js"></script>

    <!-- Page level custom scripts -->
    <script src="/static/dashboard/js/demo/datatables-demo.js"></script>

    <script src="/static/bootstrap/js/bootstrap.bundle.min.js"></script>


</body>

</html>
```

## core\templates\dashboard\forgot-password.html
```
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>SB Admin 2 - Forgot Password</title>

    <!-- Custom fonts for this template-->
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link
        href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i"
        rel="stylesheet">

    <!-- Custom styles for this template-->
    <link href="css/sb-admin-2.min.css" rel="stylesheet">

</head>

<body class="bg-gradient-primary">

    <div class="container">

        <!-- Outer Row -->
        <div class="row justify-content-center">

            <div class="col-xl-10 col-lg-12 col-md-9">

                <div class="card o-hidden border-0 shadow-lg my-5">
                    <div class="card-body p-0">
                        <!-- Nested Row within Card Body -->
                        <div class="row">
                            <div class="col-lg-6 d-none d-lg-block bg-password-image"></div>
                            <div class="col-lg-6">
                                <div class="p-5">
                                    <div class="text-center">
                                        <h1 class="h4 text-gray-900 mb-2">Forgot Your Password?</h1>
                                        <p class="mb-4">We get it, stuff happens. Just enter your email address below
                                            and we'll send you a link to reset your password!</p>
                                    </div>
                                    <form class="user">
                                        <div class="form-group">
                                            <input type="email" class="form-control form-control-user"
                                                id="exampleInputEmail" aria-describedby="emailHelp"
                                                placeholder="Enter Email Address...">
                                        </div>
                                        <a href="login.html" class="btn btn-primary btn-user btn-block">
                                            Reset Password
                                        </a>
                                    </form>
                                    <hr>
                                    <div class="text-center">
                                        <a class="small" href="register.html">Create an Account!</a>
                                    </div>
                                    <div class="text-center">
                                        <a class="small" href="login.html">Already have an account? Login!</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>

        </div>

    </div>

    <!-- Bootstrap core JavaScript-->
    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>

    <!-- Core plugin JavaScript-->
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>

    <!-- Custom scripts for all pages-->
    <script src="js/sb-admin-2.min.js"></script>

</body>

</html>
```

## core\templates\dashboard\index.html
```
{% extends 'dashboard/base.html' %}
{% block body %}
<style>
.dot {
    height: 10px;
    width: 10px;
    border-radius: 50%;
    display: inline-block;
}
@keyframes a-pulse {
    0% { box-shadow:0 0 5px rgb(30, 121, 18), inset 0 0 2px rgb(44, 206, 22); }
    50% { box-shadow:0 0 10px 2px rgb(44, 206, 22), inset 0 0 25px rgb(44, 206, 22); }
    100% { box-shadow:0 0 5px rgb(44, 206, 22), inset 0 0 2px rgb(44, 206, 22); }
}
@keyframes i-pulse {
    0% { box-shadow:0 0 5px rgb(206, 22, 22), inset 0 0 2px rgb(206, 22, 22); }
    50% { box-shadow:0 0 10px 2px rgb(206, 22, 22), inset 0 0 25px rgb(206, 22, 22); }
    100% { box-shadow:0 0 5px rgb(206, 22, 22), inset 0 0 2px rgb(206, 22, 22); }
}

.active {
    background-color: rgb(44, 206, 22);
    box-shadow: 0 0 5px rgb(44, 206, 22), inset 0 0 2px rgb(44, 206, 22);
    animation: a-pulse 2s ease-in-out 2s infinite;
}
.inactive {
    background-color: rgb(206, 22, 22);
    box-shadow: 0 0 5px rgb(206, 22, 22), inset 0 0 2px rgb(206, 22, 22);
    animation: i-pulse 2s ease-in-out 2s infinite;
}
</style>

<!-- Page Heading -->
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">لوحة التحكم</h1>
    <a href="#" class="d-none d-sm-inline-block btn btn-sm btn-primary shadow-sm"><i
            class="fas fa-download fa-sm text-white-50"></i> Generate Report</a>
</div>

<!-- Content Row -->
<div class="row">

    <!-- Earnings (Monthly) Card Example -->
    <div class="col-xl-4 col-md-6 mb-4">
        <div class="card border-left-primary shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                            عدد الطلاب</div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ students_num }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="bi bi-person-fill fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Earnings (Monthly) Card Example -->
    <div class="col-xl-4 col-md-6 mb-4">
        <div class="card border-left-success shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                            عدد صفحات الحفظ</div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{all_pages_sums}}</div>
                    </div>
                    <div class="col-auto">
                        <i class="bi bi-book-half fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>    

    <!-- Pending Requests Card Example -->
    <div class="col-xl-4 col-md-6 mb-4">
        <div class="card border-left-warning shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                            عدد الاساتذة</div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ teacher_num }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="bi bi-person-fill fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Content Row -->

<div class="row">

    <!-- Area Chart -->
    <div class="col-lg-5 mb-4">

        <div class="card shadow mb-4 h-100">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">من قام بتسجيل الحضور من المشرفين (اليوم)</h6>
            </div>
            <div class="card-body" style="max-height: 400px;overflow-y: scroll;">
                {% for t in teachers_dosnt_make_attend %}
                    <div style="display: flex;flex-direction: row-reverse;margin: 5px;align-items: center;padding: 10px 0px 10px 0px;">
                        <span class="dot inactive"></span>
                        <p class="m-0 mx-3">{{ t.username }}</p>
                    </div>
                {% endfor %}
                {% for t in teachers_make_attend %}
                    <div style="display: flex;flex-direction: row-reverse;margin: 5px;align-items: center;padding: 10px 0px 10px 0px;">
                        <span class="dot active"></span>
                        <p class="m-0 mx-3">{{ t.username }}</p>
                    </div>
                {% endfor %}
                
            </div>
        </div>
    </div>

    <!-- Pie Chart -->
    <div class="col-xl-7 col-lg-7">
        <div class="card shadow mb-4">
            <!-- Card Header - Dropdown -->
            <div
                class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                <h6 class="m-0 font-weight-bold text-primary">نسبة الحضور الى الغياب</h6>
                <div class="dropdown no-arrow">
                    <a class="dropdown-toggle" href="#" role="button" id="dropdownMenuLink"
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <i class="fas fa-ellipsis-v fa-sm fa-fw text-gray-400"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-right shadow animated--fade-in"
                        aria-labelledby="dropdownMenuLink">
                        <div class="dropdown-header">Dropdown Header:</div>
                        <a class="dropdown-item" href="#">Action</a>
                        <a class="dropdown-item" href="#">Another action</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="#">Something else here</a>
                    </div>
                </div>
            </div>
            <!-- Card Body -->
            <div class="card-body">
                <div class="chart-pie pt-4 pb-2">
                    <canvas id="myPieChart"></canvas>
                </div>
                <div class="mt-4 text-center small">
                    <span class="mr-2">
                        <i class="fas fa-circle" style="color: rgb(206, 22, 22);"></i> حضور
                    </span>
                    <span class="mr-2">
                        <i class="fas fa-circle" style="color: rgb(30, 121, 18);"></i> غياب
                    </span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Content Row -->
<div class="row">

    <!-- Content Column -->

        <div class="col-xl-12 col-lg-12">
            <div class="card shadow mb-4">
                <!-- Card Header - Dropdown -->
                <div
                    class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                    <h6 class="m-0 font-weight-bold text-primary">مخطط الحفظ لاخر 30 يوم</h6>
                    <div class="dropdown no-arrow">
                        <a class="dropdown-toggle" href="#" role="button" id="dropdownMenuLink"
                            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            <i class="fas fa-ellipsis-v fa-sm fa-fw text-gray-400"></i>
                        </a>
                        <div class="dropdown-menu dropdown-menu-right shadow animated--fade-in"
                            aria-labelledby="dropdownMenuLink">
                            <div class="dropdown-header">Dropdown Header:</div>
                            <a class="dropdown-item" href="#">Action</a>
                            <a class="dropdown-item" href="#">Another action</a>
                            <div class="dropdown-divider"></div>
                            <a class="dropdown-item" href="#">Something else here</a>
                        </div>
                    </div>
                </div>
                <!-- Card Body -->
                <div class="card-body">
                    <div class="chart-area">
                        <canvas id="myAreaChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-lg-4 mb-4">

            <!-- Project Card Example -->
            <div class="card shadow mb-4 h-100">
                <div class="card-header py-3">
                    <h6 class="m-0 font-weight-bold text-primary">طلاب من دون اساتذة</h6>
                </div>
                <div class="card-body" style="max-height: 400px;overflow-y: scroll;">
                    {% for s in students_without_teacher %}
                        <div style="display: flex;flex-direction: row-reverse;margin: 5px;align-items: center;padding: 10px 0px 10px 0px;">
                            <span class="dot inactive"></span>
                            <p class="m-0 mx-3">{{ s.name }}</p>
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
</div>

<script src="/static/dashboard/vendor/chart.js/Chart.min.js"></script>


<script>

// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

// Area Chart Example
var ctx = document.getElementById("myAreaChart");
var myLineChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [{% for d in dates %}"{{d|date:"Y-m-d" }}",{% endfor %}],
    datasets: [{
      label: "الحفظ",
      lineTension: 0.3,
      backgroundColor: "rgba(78, 115, 223, 0.05)",
      borderColor: "rgba(78, 115, 223, 1)",
      pointRadius: 3,
      pointBackgroundColor: "rgba(78, 115, 223, 1)",
      pointBorderColor: "rgba(78, 115, 223, 1)",
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
      pointHoverBorderColor: "rgba(78, 115, 223, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: {{sums}},
    }],
  },
  options: {
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 10,
        right: 25,
        top: 25,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 7
        }
      }],
      yAxes: [{
        ticks: {
          maxTicksLimit: 5,
          padding: 10,
          // Include a dollar sign in the ticks
          callback: function(value, index, values) {
            return number_format(value);
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(234, 236, 244)",
          drawBorder: false,
          borderDash: [2],
          zeroLineBorderDash: [2]
        }
      }],
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function(tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ' : ' + number_format(tooltipItem.yLabel);
        }
      }
    }
  }
});

    // Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ["حضور", "غياب"],
    datasets: [{
      data: [{{at_sum}}, {{ab_sum}}],
      backgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
      hoverBackgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
      hoverBorderColor: "rgba(234, 236, 244, 1)",
    }],
  },
  options: {
    maintainAspectRatio: false,
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      caretPadding: 10,
    },
    legend: {
      display: false
    },
    cutoutPercentage: 80,
  },
});

</script>
{% endblock %}
```

## core\templates\dashboard\login.html
```
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>جامع الرحمن - تسجيل الدخول</title>

    <!-- Custom fonts for this template-->
    <link href="/static/dashboard/vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link
        href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i"
        rel="stylesheet">
        <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css">


    <!-- Custom styles for this template-->
    <link href="/static/dashboard/css/sb-admin-2.min.css" rel="stylesheet">

</head>

<body class="bg-gradient-success">

    <div class="container">

        <!-- Outer Row -->
        <div class="row justify-content-center">

            <div class="col-xl-10 col-lg-12 col-md-9">

                <div class="card o-hidden border-0 shadow-lg my-5">
                    <div class="card-body p-0">
                        <!-- Nested Row within Card Body -->
                        <div class="row">
                            {% for message in messages %}
                                <div class="alert alert-danger alert-dismissible show fade col-12">
                                    <p style="text-align: center;" class="mb-0">{{message}}</p>
                                    <button class="btn-close" data-bs-dismiss='alert'></button>
                                </div>
                            {% endfor %}
                        </div>
                        <div class="row d-flex justify-content-center">
                            <div class="col-6 align-self-center">
                                <img src="/static/Logo.jpg" style="max-height: 600px;" alt="">
                            </div>
                            <div class="col-6 align-self-center">
                                <div class="p-5">
                                    <div class="text-center">
                                        <h1 class="h4 text-gray-900 mb-4">Welcome Back!</h1>
                                    </div>
                                    <form class="user" action="#" method="post">
                                        {% csrf_token %}
                                        <div class="form-group">
                                            <input type="text" name="username" class="form-control form-control-user"
                                                id="exampleInputEmail" aria-describedby="emailHelp"
                                                placeholder="Enter Name">
                                        </div>
                                        <div class="form-group">
                                            <input type="password" class="form-control form-control-user"
                                                id="exampleInputPassword" name="password" placeholder="Password">
                                        </div>
                                        <input href="#" class="btn btn-success btn-user btn-block" type="submit" />
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>

        </div>

    </div>

    <!-- Bootstrap core JavaScript-->
    <script src="/static/dashboard/vendor/jquery/jquery.min.js"></script>
    <script src="/static/dashboard/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="/static/bootstrap/js/bootstrap.bundle.min.js"></script>

    <!-- Core plugin JavaScript-->
    <script src="/static/dashboard/vendor/jquery-easing/jquery.easing.min.js"></script>

    <!-- Custom scripts for all pages-->
    <script src="/static/dashboard/js/sb-admin-2.min.js"></script>

</body>

</html>
```

## core\templates\dashboard\group_session\edit.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center"></h6>
        <h3>حلقة {{ teacher.username }}</h3>
        <div>
            <button class="btn btn-primary align-self-center" href="#" data-toggle="modal" data-target="#add_user">اضافة طالب</button>
            <a class="btn btn-success align-self-center"  href="#" data-toggle="modal" data-target="#change">تغيير المشرف</a>
        </div>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>اسم الطالب</th>
                        <th>action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for g in group_session %}
                        <tr>
                            <td>{{ g.student.name }}</td>
                            <td>
                                <a class="text-danger" href="/groupsession/{{ g.id }}/delete">حذف</a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal-->
<div class="modal fade" id="add_user" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">اضافة طالب</h5>
                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">×</span>
                </button>
            </div>
            <form action="/groupsession/{{ teacher.id }}/add/" method="post">
                <div class="modal-body">
                        {% csrf_token %}
                        <select class="form-select" name="student">
                            {% for s in students_without_group %}
                                <option value="{{s.id}}">{{s.name}}</option>
                            {% endfor %}
                        </select>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
                    <input href="#" class="btn btn-success btn-user" type="submit" value="اضافة"/>
                </div>
            </form>
        </div>
    </div>
</div>

<div class="modal fade" id="change" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">تغيير الحلقة</h5>
                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">×</span>
                </button>
            </div>
            <form action="/groupsession/{{ teacher.id }}/changeteacher/" method="post">
                <div class="modal-body">
                        {% csrf_token %}
                        <select class="form-select" name="teacher_id">
                            {% for teacher in teachers %}
                                <option value="{{teacher.id}}">{{teacher.username}}</option>
                            {% endfor %}
                        </select>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
                    <input href="#" class="btn btn-success btn-user" type="submit" value="اضافة"/>
                </div>
            </form>
        </div>
    </div>
</div>

{% endblock %}
```

## core\templates\dashboard\group_session\show.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">حلقات</h6>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>استاذ الحلقة</th>
                        <th>الطلاب</th>
                        <th>action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for teacher in teachers %}
                        <tr>
                            <td>{{ teacher.username }}</td>
                            <td>
                                {% for s in teacher.students %}
                                    {{ s.name }}   --
                                {% endfor %}
                            </td>
                            
                            <td>
                                <a href="/groupsession/{{ teacher.id }}/edit">تعديل الطلاب</a>---                        
                                <a class="text-success" href="/attend/{{ teacher.id }}/add">تسجيل الحضور</a>                            
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal-->
<div class="modal fade" id="add_user" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">اضافة استاذ</h5>
                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">×</span>
                </button>
            </div>
            <form action="/users/add/" method="post">
                <div class="modal-body">
                        {% csrf_token %}
                        <div class="form-group">
                            <input type="text" name="username" class="form-control form-control-user" placeholder="الاسم">
                        </div>
                        <div class="form-group">
                            <input type="text" name="password" class="form-control form-control-user" placeholder="كلمة السر">
                        </div>
                        <div class="form-group">
                            <input type="number" name="per" max=2 min=0 class="form-control form-control-user" placeholder="الصلاحية">
                        </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
                    <input href="#" class="btn btn-success btn-user" type="submit" value="اضافة"/>
                </div>
            </form>
        </div>
    </div>
</div>

{% endblock %}
```

## core\templates\dashboard\students\add_memorize.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">تسجيل حفظ {{ student.name }}</h6>
    </div>
    <form action="#" method="post">
        <div class="modal-body">
                {% csrf_token %}
                <p class="form-group">تاريخ</p>
                <div class="form-group">
                    <input type="date" name="date" class="form-control form-control-user" placeholder="تاريخ الحفظ" required>
                </div>
                <p class="form-group">رقم الجزء</p>
                <div class="form-group">
                    <input type="number" oninput="get_pages(event)" name="section" class="form-control form-control-user" placeholder="الجزء">
                </div>
                <p class="form-group">الصفحة</p>
                <select class="form-select" name="page_id" id="pages">
                    <!-- <option value="{{teacher.id}}">{{teacher.username}}</option> -->
                </select>
        </div>
        <div class="modal-footer">
            <input href="#" class="btn btn-success btn-user" type="submit" value="تسجيل"/>
        </div>
    </form>
</div>

<script>
    function get_pages(e){
        console.log(e.srcElement.value);
        if (e.srcElement.value > 30 || e.srcElement.value < 1){ return false }
        fetch('/get_pages/'+e.srcElement.value)
        .then(response => response.json()) // Parse the response as JSON
        .then(data => {
            console.log(data.pages);
            const selectElement = document.getElementById('pages');
            while (selectElement.options.length > 0) {
                selectElement.remove(0);
            }
            
            data.pages.forEach(p => {
                console.log(p.page_id)
                var newOption = new Option(p.page_name, p.page_id); // text, value
                selectElement.add(newOption);
            });
        
        })
        .catch(error => console.error('Error:', error));
    }
</script>
{% endblock %}
```

## core\templates\dashboard\students\details.html
```
{% extends 'dashboard/base.html' %}
{% block body %}
<div class="row">
    <div class="col-lg-4 mb-4">
        <div class="card shadow mb-4 h-100">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">معلومات الطالب</h6>
            </div>
            <div class="card-body" style="max-height: 400px;overflow-y: scroll;">
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : الاسم</p>
                    <p>{{ student.name }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : اسم الأب</p>
                    <p>{{ student.father_name }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : اسم المدرسة</p>
                    <p>{{ student.school_name }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : عنوان السكن</p>
                    <p>{{ student.address }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : رقم الأهل</p>
                    <p>{{ student.phone_number }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : المشرف</p>
                    <p>{{ student.teacher.username }}</p>
                </div>
                <div style="display: flex;justify-content: space-between;flex-direction: row-reverse;">
                    <p> : تاريخ الميلاد</p>
                    <p>{{ student.birth_date }}</p>
                </div>
                    
            </div>
        </div>
    </div>
    <div class="col-xl-8 col-lg-8 mb-4">
        <div class="card shadow h-100">
            <!-- Card Header - Dropdown -->
            <div
                class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                <h6 class="m-0 font-weight-bold text-primary">مخطط الحفظ لاخر 30 يوم</h6>
                <div class="dropdown no-arrow">
                    <a class="dropdown-toggle" href="#" role="button" id="dropdownMenuLink"
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <i class="fas fa-ellipsis-v fa-sm fa-fw text-gray-400"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-right shadow animated--fade-in"
                        aria-labelledby="dropdownMenuLink">
                        <div class="dropdown-header">Dropdown Header:</div>
                        <a class="dropdown-item" href="#">Action</a>
                        <a class="dropdown-item" href="#">Another action</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="#">Something else here</a>
                    </div>
                </div>
            </div>
            <!-- Card Body -->
            <div class="card-body">
                <div class="chart-area">
                    <canvas id="myAreaChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
<div class="card shadow mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center text-primary">الحفظ</h6>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>التاريخ</th>
                        <th>اسم الصفحة</th>
                        <th>action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in pages %}
                        <tr>
                            <td>{{ p.date  }}</td>
                            <td>{{ p.page.name }}</td>
                            <td>
                                <a href="/memorized/{{ p.id }}/delete" class="text-danger">حذف</a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
<div class="card shadow mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center text-primary">الحضور</h6>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>التاريخ</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for a in attends %}
                        <tr>
                            <td>{{ a.date  }}</td>
                            <td>
                                {% if a.is_attend == 0 %} غياب {% endif %}
                                {% if a.is_attend == 1 %} حاضر {% endif %}
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script src="/static/dashboard/vendor/chart.js/Chart.min.js"></script>
<script>

// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

// Area Chart Example
var ctx = document.getElementById("myAreaChart");
var myLineChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [{% for d in dates %}"{{d|date:"Y-m-d" }}",{% endfor %}],
    datasets: [{
      label: "الحفظ",
      lineTension: 0.3,
      backgroundColor: "rgba(78, 115, 223, 0.05)",
      borderColor: "rgba(78, 115, 223, 1)",
      pointRadius: 3,
      pointBackgroundColor: "rgba(78, 115, 223, 1)",
      pointBorderColor: "rgba(78, 115, 223, 1)",
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
      pointHoverBorderColor: "rgba(78, 115, 223, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: {{sums}},
    }],
  },
  options: {
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 10,
        right: 25,
        top: 25,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 7
        }
      }],
      yAxes: [{
        ticks: {
          maxTicksLimit: 5,
          padding: 10,
          // Include a dollar sign in the ticks
          callback: function(value, index, values) {
            return  number_format(value);
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(234, 236, 244)",
          drawBorder: false,
          borderDash: [2],
          zeroLineBorderDash: [2]
        }
      }],
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function(tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ':' + number_format(tooltipItem.yLabel);
        }
      }
    }
  }
});

    // Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ["حضور", "غياب"],
    datasets: [{
      data: [60, 30],
      backgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
      hoverBackgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
      hoverBorderColor: "rgba(234, 236, 244, 1)",
    }],
  },
  options: {
    maintainAspectRatio: false,
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      caretPadding: 10,
    },
    legend: {
      display: false
    },
    cutoutPercentage: 80,
  },
});

</script>
{% endblock %}
```

## core\templates\dashboard\students\edit.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">تعديل طالب</h6>
    </div>
    <form action="#" method="post">
        <div class="modal-body">
                {% csrf_token %}
                <div class="form-group">
                    <input type="text" name="name" class="form-control form-control-user" placeholder="الاسم" value="{{ student.name }}">
                </div>
                <div class="form-group">
                    <input type="text" name="father_name" class="form-control form-control-user" placeholder="اسم الأب" value="{{ student.father_name }}">
                </div>
                <div class="form-group">
                    <input type="text" name="school_name" class="form-control form-control-user" placeholder="اسم المدرسة" value="{{ student.school_name }}">
                </div>
                <div class="form-group">
                    <input type="text" name="address" class="form-control form-control-user" placeholder="عنوان السكن" value="{{ student.address }}">
                </div>
                <div class="form-group">
                    <input type="date" name="birth_date" class="form-control form-control-user" placeholder="تاريخ الميلاد" value="{{ student.birth_date|date:"Y-m-d" }}">
                </div>
                <div class="form-group">
                    <input type="text" name="phone_number" class="form-control form-control-user" placeholder="رقم الأهل" value="{{ student.phone_number }}">
                </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
            <input href="#" class="btn btn-success btn-user" type="submit" value="تعديل"/>
        </div>
    </form>
</div>

{% endblock %}
```

## core\templates\dashboard\students\show.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">الطلاب</h6>
        <button class="btn btn-primary align-self-center" href="#" data-toggle="modal" data-target="#add_user">اضافة طالب <i class="bi bi-person-fill-add mx-2"></i></button>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>رقم الأهل</th>
                        <th>action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                        <tr>
                            <td>
                                {% if student.disabled == True %} <del> {% endif %} 
                                {{ student.name }}  
                                {% if student.disabled == True %} </del> {% endif %}
                            </td>
                            <td>{{ student.phone_number }}</td>
                            
                            <td>
                                {% if student.disabled == True %} <a href="/students/{{ student.id }}/enable" class="text-danger">اعادة تفعيل</a> {% endif %} 
                                {% if student.disabled == False %} <a href="/students/{{ student.id }}/disable" class="text-secondary">الغاء تفعيل</a> {% endif %}                                 

                                {% if default.user.permission == 0 %}
                                    --<a class="text-danger" href="/students/{{ student.id }}/delete">حذف</a>
                                {% endif %}
                                --<a href="/students/{{ student.id }}/edit">تعديل</a>
                                --<a href="/students/{{ student.id }}/addmemorize" class="text-success">تسجيل حفظ</a>
                                --<a href="/students/{{ student.id }}/details" class="text-success">معلومات</a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal-->
<div class="modal fade" id="add_user" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">اضافة طالب</h5>
                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">×</span>
                </button>
            </div>
            <form action="/students/add/" method="post">
                <div class="modal-body">
                        {% csrf_token %}
                        <div class="form-group">
                            <input type="text" name="name" class="form-control form-control-user" placeholder="الاسم">
                        </div>
                        <div class="form-group">
                            <input type="text" name="father_name" class="form-control form-control-user" placeholder="اسم الأب">
                        </div>
                        <div class="form-group">
                            <input type="text" name="school_name" class="form-control form-control-user" placeholder="اسم المدرسة">
                        </div>
                        <div class="form-group">
                            <input type="text" name="address" class="form-control form-control-user" placeholder="عنوان السكن">
                        </div>
                        <div class="form-group">
                            <input type="date" name="birth_date" class="form-control form-control-user" placeholder="تاريخ الميلاد">
                        </div>
                        <div class="form-group">
                            <input type="text" name="phone_number" class="form-control form-control-user" placeholder="رقم الأهل">
                        </div>
                        <p class="form-group">المشرف</p>
                        <select class="form-select" name="teacher_id">
                            <option value="later">لاحقا</option>
                            {% for teacher in teachers %}
                                <option value="{{teacher.id}}">{{teacher.username}}</option>
                            {% endfor %}
                        </select>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
                    <input href="#" class="btn btn-success btn-user" type="submit" value="اضافة"/>
                </div>
            </form>
        </div>
    </div>
</div>

{% endblock %}
```

## core\templates\dashboard\students_attend\add.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center"> تسجيل حضور</h6>
    </div>
    <form action="#" method="post">
        <div class="modal-body" style="display: flex;justify-content: center;align-items: center;flex-direction: column;">
                {% csrf_token %}
                <div class="form-group">
                    <input type="date" required name="date" class="form-control form-control-user" placeholder="تاريخ الميلاد" value="{{ student.birth_date|date:"Y-m-d" }}">
                </div>
                {% for student in students %}
                <div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="{{ student.student.id }}" id="flexRadioDefault2" value="0">
                        <label class="form-check-label" for="flexRadioDefault2">
                        غائب
                        </label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="{{student.student.id}}" id="flexRadioDefault1" value="1" checked>
                        <label class="form-check-label" for="flexRadioDefault1">
                        حاضر
                        </label>
                    </div>
                    <label for="" style="display: inline-block;margin:10px;margin-right: 20px;margin-left: 0px;font-size: large;color: #474747;">{{student.student.name}}</label>
                </div>
                {% endfor %}
        </div>
        <div class="modal-footer">
            <input href="#" class="btn btn-success btn-user" type="submit" value="تسجيل"/>
        </div>
    </form>
</div>

{% endblock %}
```

## core\templates\dashboard\students_attend\edit.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center"> تعديل حضور</h6>
    </div>
    <form action="#" method="post">
        <div class="modal-body" style="display: flex;justify-content: center;align-items: center;flex-direction: column;">
                {% csrf_token %}
                <div class="form-group">
                    <h3>{{ students.0.date|date:'d-m-Y' }}</h3>
                </div>
                {% for student in students %}
                <div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="{{ student.student.id }}" id="flexRadioDefault2" value="0" {% if student.is_attend == False%}checked{% endif %}>
                        <label class="form-check-label" for="flexRadioDefault2">
                        غائب
                        </label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="{{student.student.id}}" id="flexRadioDefault1" value="1" {% if student.is_attend == True%}checked{% endif %}>
                        <label class="form-check-label" for="flexRadioDefault1">
                        حاضر
                        </label>
                    </div>
                    <label for="" style="display: inline-block;margin:10px;margin-right: 20px;margin-left: 0px;font-size: large;color: #474747;">{{student.student.name}}</label>
                </div>
                {% endfor %}
        </div>
        <div class="modal-footer">
            <input href="#" class="btn btn-success btn-user" type="submit" value="تسجيل"/>
        </div>
    </form>
</div>

{% endblock %}
```

## core\templates\dashboard\students_attend\show.html
```
{% extends 'dashboard/base.html' %}
{% block body %}
<style>
    .accordion-button:not(.collapsed){
        color: white;
        background-color: var(--success);
    }
</style>
<div class="row">

    <!-- Area Chart -->
    <div class="col-xl-12 col-lg-12">
        <div class="card mb-4">
            <!-- Card Header - Dropdown -->
            <div
                class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                <h6 class="m-0 font-weight-bold text-success">الحضور</h6>
                <div class="dropdown no-arrow">
                    <a class="dropdown-toggle" href="#" role="button" id="dropdownMenuLink"
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <i class="fas fa-ellipsis-v fa-sm fa-fw text-gray-400"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-right shadow animated--fade-in"
                        aria-labelledby="dropdownMenuLink">
                        <div class="dropdown-header">Dropdown Header:</div>
                        <a class="dropdown-item" href="#">Action</a>
                        <a class="dropdown-item" href="#">Another action</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="#">Something else here</a>
                    </div>
                </div>
            </div>
            <!-- Card Body -->
            <div class="card-body">
                <div class="chart-area">
                    <canvas id="myAreaChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
<div class="accordion" id="accordionPanelsStayOpenExample">
    {% for d in data %}
        <div class="accordion-item m-2" style="border: none;">
        <h2 class="accordion-header" id="h-{{ d.date |date:'Y-m-d' }}" style="border: 1px solid #e3e6f0;">
            <button class="accordion-button collapsed" style="box-shadow: none;" type="button" data-bs-toggle="collapse" data-bs-target="#d-{{ d.date |date:'Y-m-d'}}" aria-expanded="false" aria-controls="d-{{ d.date |date:'Y-m-d' }}">
            {{ d.date|date:'d-m-Y' }}
            </button>
        </h2>
        <div id="d-{{ d.date |date:'Y-m-d'}}" class="accordion-collapse collapse" aria-labelledby="h-{{ d.date |date:'Y-m-d' }}" data-bs-parent="#accordionPanelsStayOpenExample">
            <div class="accordion-body p-0" style="border: 1px solid #e3e6f0;">
                <table class="table table-striped m-0">
                    <thead >
                      <tr>
                        <td scope="col">الاستاذ</td>
                        <td scope="col">الحضور</td>
                        <td scope="col">الغياب</td>
                        <td scope="col">action</td>
                      </tr>
                    </thead>
                    <tbody>
                        {% for t in d.data %}
                            <tr>
                                <th scope="row">{{t.teacher.username}}</th>
                                <td>
                                    {% for att in t.attend %}
                                        {{att.student.name}} <br>
                                    {% endfor %}
                                </td>
                                <td>
                                    {% for ab in t.absent %}
                                        {{ab.student.name}} <br>
                                    {% endfor %}
                                </td>
                                <td>
                                    <a href="/attend/{{ d.date|date:'Y-m-d' }}/{{t.teacher.id}}/delete" class="text-danger">حذف </a>---                        
                                    <a class="text-success" href="/attend/{{ d.date|date:'Y-m-d' }}/{{t.teacher.id}}/edit">تعديل </a>    
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        </div>
    {% endfor %}
</div>

<script src="/static/dashboard/vendor/chart.js/Chart.min.js"></script>

<script>

    // Set new default font family and font color to mimic Bootstrap's default styling
    Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
    Chart.defaults.global.defaultFontColor = '#858796';
    
    function number_format(number, decimals, dec_point, thousands_sep) {
      // *     example: number_format(1234.56, 2, ',', ' ');
      // *     return: '1 234,56'
      number = (number + '').replace(',', '').replace(' ', '');
      var n = !isFinite(+number) ? 0 : +number,
        prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
        sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
        dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
        s = '',
        toFixedFix = function(n, prec) {
          var k = Math.pow(10, prec);
          return '' + Math.round(n * k) / k;
        };
      // Fix for IE parseFloat(0.55).toFixed(0) = 0;
      s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
      if (s[0].length > 3) {
        s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
      }
      if ((s[1] || '').length < prec) {
        s[1] = s[1] || '';
        s[1] += new Array(prec - s[1].length + 1).join('0');
      }
      return s.join(dec);
    }
    
    // Area Chart Example
    var ctx = document.getElementById("myAreaChart");
    var myLineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [{% for d in char_data.dates %}"{{d}}",{% endfor %}],
        datasets: [{
          label: "Earnings",
          lineTension: 0.3,
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(78, 115, 223, 1)",
          pointBorderColor: "rgba(78, 115, 223, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: {{char_data.data}},
        }],
      },
      options: {
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 25,
            top: 25,
            bottom: 0
          }
        },
        scales: {
          xAxes: [{
            time: {
              unit: 'date'
            },
            gridLines: {
              display: false,
              drawBorder: false
            },
            ticks: {
              maxTicksLimit: 7
            }
          }],
          yAxes: [{
            ticks: {
              maxTicksLimit: 5,
              padding: 10,
              // Include a dollar sign in the ticks
              callback: function(value, index, values) {
                return number_format(value);
              }
            },
            gridLines: {
              color: "rgb(234, 236, 244)",
              zeroLineColor: "rgb(234, 236, 244)",
              drawBorder: false,
              borderDash: [2],
              zeroLineBorderDash: [2]
            }
          }],
        },
        legend: {
          display: false
        },
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          titleMarginBottom: 10,
          titleFontColor: '#6e707e',
          titleFontSize: 14,
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          intersect: false,
          mode: 'index',
          caretPadding: 10,
          callbacks: {
            label: function(tooltipItem, chart) {
              var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
              return datasetLabel + ': $' + number_format(tooltipItem.yLabel);
            }
          }
        }
      }
    });
    
        // Set new default font family and font color to mimic Bootstrap's default styling
    Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
    Chart.defaults.global.defaultFontColor = '#858796';
    
    // Pie Chart Example
    var ctx = document.getElementById("myPieChart");
    var myPieChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ["حضور", "غياب"],
        datasets: [{
          data: [60, 30],
          backgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
          hoverBackgroundColor: ['rgb(30, 121, 18)', 'rgb(206, 22, 22)'],
          hoverBorderColor: "rgba(234, 236, 244, 1)",
        }],
      },
      options: {
        maintainAspectRatio: false,
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          caretPadding: 10,
        },
        legend: {
          display: false
        },
        cutoutPercentage: 80,
      },
    });
    
    </script>
{% endblock %}
```

## core\templates\dashboard\users\edit_user.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">تعديل استاذ</h6>
    </div>
    <form action="#" method="post">
        <div class="modal-body">
                {% csrf_token %}
                <div class="form-group">
                    <input type="text" name="username" class="form-control form-control-user" placeholder="الاسم" value="{{ edit_user.username }}">
                </div>
                <div class="form-group">
                    <input type="text" name="password" class="form-control form-control-user" placeholder="كلمة السر" value="{{ edit_user.password }}">
                </div>
                <div class="form-group">
                    <input type="number" name="per" max=2 min=0 class="form-control form-control-user" value="{{ edit_user.permission }}" placeholder="الصلاحية">
                </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
            <input href="#" class="btn btn-success btn-user" type="submit" value="تعديل"/>
        </div>
    </form>
</div>

{% endblock %}
```

## core\templates\dashboard\users\users.html
```
{% extends 'dashboard/base.html' %}
{% block body %}

<div class="card mb-4">
    <div class="card-header py-3 d-flex justify-content-between">
        <h6 class="m-0 font-weight-bold align-self-center">أساتذة</h6>
        <button class="btn btn-primary align-self-center" href="#" data-toggle="modal" data-target="#add_user"> اضافة استاذ<i class="bi bi-person-fill-add mx-2"></i></button>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>كلمة السر</th>
                        <th>نوع الحساب</th>
                        <th>action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                        <tr>
                            <td>{{ user.username }}</td>
                            <td>{{ user.password }}</td>
                            <td>
                                {% if user.permission == 0 %} جميع الصلاحيات {% elif user.permission == 1 %} اداري {% elif user.permission == 2 %} مشرف حلقة {% endif %}
                            </td>
                            <td>
                                {% if default.user.permission == 0 %}
                                    <a class="text-danger" href="/users/{{ user.id }}/delete">حذف</a>
                                {% endif %}
                                <a href="/users/{{ user.id }}/edit">تعديل</a>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal-->
<div class="modal fade" id="add_user" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">اضافة استاذ</h5>
                <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">×</span>
                </button>
            </div>
            <form action="/users/add/" method="post">
                <div class="modal-body">
                        {% csrf_token %}
                        <div class="form-group">
                            <input type="text" name="username" class="form-control form-control-user" placeholder="الاسم">
                        </div>
                        <div class="form-group">
                            <input type="text" name="password" class="form-control form-control-user" placeholder="كلمة السر">
                        </div>
                        <div class="form-group">
                            <input type="number" name="per" max=2 min=0 class="form-control form-control-user" placeholder="الصلاحية">
                        </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" type="button" data-dismiss="modal">اغلاق</button>
                    <input href="#" class="btn btn-success btn-user" type="submit" value="اضافة"/>
                </div>
            </form>
        </div>
    </div>
</div>

{% endblock %}
```

## core\views\auth.py
```
from datetime import datetime
from tkinter import PAGES
from django.contrib import messages
from django.shortcuts import render, redirect
from ..models import MemorizedPages, Student, User,StudentAttend
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

    teachers_make_attend = []
    teachers_dosnt_make_attend = []
    for teacher in User.objects.all():
        students = teacher.students()

        if not StudentAttend.objects.filter(student__in=students, date = datetime.now()).all().exists():
            teachers_dosnt_make_attend.append(teacher)
        else:
            teachers_make_attend.append(teacher) 

    students_without_teacher = []
    for s in Student.objects.all():
        if s.teacher() == None:
            students_without_teacher.append(s)

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

```

## core\views\group_session.py
```
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
    g = GroupSession.objects.filter(id=id).first()
    g.delete()
    messages.info(request, 'تمت حذف الطالب بنجاح')
    return redirect(f'/groupsession/{g.teacher.id}/edit')

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
```

## core\views\students.py
```
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
```

## core\views\student_attend.py
```
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
```

## core\views\users.py
```
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
```

## django_alrahmanmosque\asgi.py
```
"""
ASGI config for django_alrahmanmosque project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_alrahmanmosque.settings')

application = get_asgi_application()

```

## django_alrahmanmosque\settings.py
```
"""
Django settings for django_alrahmanmosque project.

Generated by 'django-admin startproject' using Django 4.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-k0kezn01%)3m4dfc8a-+q&(x$3ws2ngryen9qoyac33g#9%g!+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '192.168.1.200',
    '127.0.0.1'
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'api'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_alrahmanmosque.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_alrahmanmosque.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'api.renderers.ForceAsciiJSONRenderer',
    ],
}


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

```

## django_alrahmanmosque\urls.py
```
"""django_alrahmanmosque URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include('api.urls')),
]

```

## django_alrahmanmosque\wsgi.py
```
"""
WSGI config for django_alrahmanmosque project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_alrahmanmosque.settings')

application = get_wsgi_application()

```

## django_alrahmanmosque\__init__.py
```

```

## static\style.css
```
body{
    margin: 0px;
    padding: 0px;
}
#body{
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}
#title{
    background-color: rgb(24, 121, 0);
    padding: 10px;
    color: white;
}
.topmenu{
    width: 100%;
    height: 100px;
    position: fixed;
    background-color: white;
    box-shadow: 0px 2px 7px 1px grey;
}
.topmenu h1{
    display: inline-block;
    position: absolute;
    top: 29px;
    color: black;
    font-size: x-large;
}
.logo{
    height: 100px;
    padding: 0px;
    margin: 0px;
}
.ulmenu{
    width: 50%;
    right: 0px;
    top: 0px;
    position: fixed;
    display: none;
    list-style: none;
    background-color: white;
    height: 100%;
    padding: 0px;
    margin: 0px;
    box-shadow: -1px 0px  11px 4px grey;
    overflow-y: scroll;
}

#menu_add{
    list-style: none;
    padding: 0px;
}
#menu_add li{
    border-bottom: 1px solid grey;
    text-align: center;
    background-color: rgb(177, 196, 255);
}
#menu_add li:hover{
    background-color: gray;
}
.ulmenu li{
    border-bottom: 1px solid grey;
    text-align: center;
}
.ulmenu li:hover{
    background-color: grey;
}
.ulmenu li button:hover{
    background-color: grey;
}
.ulmenu li a,.ulmenu li button{
    display: block;
    text-decoration: none;
    width: 100%;
    padding: 20px 0px;
    font-size: larger;
    color: black;
}
.butmenu{
    position: absolute;
    height: 50%;
    top: 30%;
    right: 0px;
}
#butmenuc{
    width: 50px;
    height: 50px;
    text-align: center;
}
table,tr,td{
    border: 1px solid black;
    padding: 10px;
    font-size: large;
}
table{
    width: 90%;
    padding: 1px;
    
}
tr:nth-child(even) {
    background-color: #b3b3b3;
}
tr:nth-child(odd) {
    background-color: white;
}
form{
    font-size: x-large;
    padding: 20px;
    padding-right: 50px;
    padding-left: 50px;
    border: 1px solid black;
    border-radius: 15px;
}
#edite{
    color: black;
    text-decoration: none;
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    color: white;
    display: inline-block;
    text-align: center;
    background-color: red;
    border: 1px solid red;
}
#edite:hover{
    background-color: white;
    border: 1px solid red;
    color: red;
}
#edite_admin{
    color: black;
    text-decoration: none;
    padding: 5px;
    border-radius: 5px;
    margin: 5px;
    color: white;
    display: inline-block;
    text-align: center;
    background-color: green;
    border: 1px solid green;
    font-size: medium;
}
#edite_admin:hover{
    background-color: white;
    border: 1px solid green;
    color: green;
}
#save-files{
    font-size: larger;
    padding: 20px;
    border-radius: 360px;
    background-color: orangered;
    color: white;
    text-decoration: none;
    position: fixed;
    bottom: 5px;
    left: 5px;
    width: auto;
}
#card{
    width: 250px;
    padding: 50px;
    border: 1px solid black;
    margin-bottom: 30px;
    border-radius: 50px;
    font-size: larger;
}
#paragraph{
    width: 90%;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    border-radius: 20px;
    background-color: rgb(228, 229, 255);
}
#top_img{
    width: 100%;
}
#title-2{
    float: right;
    padding-bottom: 10px;
    border-bottom: 5px solid green;
    width: auto;
}
#p{
    width: 95%;
    display: inline-block;
    font-size: larger;
    margin: 2%;
}
#img_activity{
    width: 200px;
}
```

