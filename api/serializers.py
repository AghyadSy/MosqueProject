from datetime import datetime

from rest_framework import serializers
from core.models import (
    User, Student, GroupSession, StudentAttend,Hadith,
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

class HadithSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hadith
        fields = ['title', 'narrator', 'alhadith', 'producer']