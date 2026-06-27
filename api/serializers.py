import json
from datetime import datetime

from rest_framework import serializers
from core.models import (
    Activity, ActivityTeacherAssignment, ActivityType, Hadith, Juz, Lesson,
    LessonTeacherAssignment, MemorizedPages, Page, PointCalculationMethod,
    PointRule, Student, StudentAttend, StudentPointTransaction, SurahPageData,
    User, Test, Note, StudentBehavior, GoodBehavior,
    TestType, TestEvaluation, NoteType, MemorizationType
)

# ---------- Login ----------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class StudentLookupSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)


class SectionStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    page_archive = serializers.IntegerField(min_value=1)


class AttendanceUpsertSerializer(serializers.Serializer):
    attend_student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )


class AttendanceDeleteSerializer(serializers.Serializer):
    date = serializers.DateField()


class FlexibleJSONField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = data.strip()
            if not data:
                return None
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError('صيغة JSON غير صالحة') from exc
        return super().to_internal_value(data)


class ActivityFilterSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    activity_type = serializers.ChoiceField(
        choices=ActivityType.choices,
        required=False,
    )
    teacher_id = serializers.IntegerField(min_value=1, required=False)
    student_id = serializers.IntegerField(min_value=1, required=False)


class LessonFilterSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    teacher_id = serializers.IntegerField(min_value=1, required=False)
    student_id = serializers.IntegerField(min_value=1, required=False)


class SurahFilterSerializer(serializers.Serializer):
    surah_number = serializers.IntegerField(min_value=1, required=False)
    juz = serializers.CharField(required=False)
    juz_number = serializers.IntegerField(min_value=1, required=False)
    is_active = serializers.BooleanField(required=False)


class JuzFilterSerializer(serializers.Serializer):
    juz_number = serializers.IntegerField(min_value=1, required=False)
    start_page = serializers.IntegerField(min_value=1, required=False)
    end_page = serializers.IntegerField(min_value=1, required=False)
    is_active = serializers.BooleanField(required=False)


class PagesCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    page_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        required=False,
    )
    surah_id = serializers.IntegerField(min_value=1, required=False)
    surah_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        required=False,
    )
    juz_id = serializers.IntegerField(min_value=1, required=False)
    page_number_start = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False
    )
    page_number_end = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False
    )
    evaluation = serializers.ChoiceField(
        choices=['excellent', 'very_good', 'good', 'average', 'failed'],
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        # At least one way to specify pages must be provided
        if (not attrs.get('page_ids') and
                not attrs.get('surah_id') and
                not attrs.get('surah_ids') and
                not attrs.get('juz_id')):
            raise serializers.ValidationError(
                'يجب إرسال page_ids أو surah_id أو surah_ids أو juz_id'
            )
        return attrs


class MemorizedPageDeleteSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    memorized_page_id = serializers.IntegerField(min_value=1)


class TeacherGroupInputSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField(min_value=1)
    student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )


class ActivityCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    date = serializers.DateField()
    image = serializers.FileField(required=False, allow_null=True)
    activity_type = serializers.ChoiceField(
        choices=Activity._meta.get_field('activity_type').choices
    )
    other_activity_type = serializers.CharField(required=False, allow_blank=True, max_length=200)
    teacher_groups = FlexibleJSONField(required=False)
    attend_student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
    )

    def validate(self, attrs):
        if attrs['activity_type'] == 'other' and not attrs.get('other_activity_type', '').strip():
            raise serializers.ValidationError({
                'other_activity_type': ['هذا الحقل مطلوب عندما يكون نوع النشاط "نشاط آخر"'],
            })

        teacher_groups = attrs.get('teacher_groups')
        if teacher_groups is not None:
            serializer = TeacherGroupInputSerializer(data=teacher_groups, many=True)
            serializer.is_valid(raise_exception=True)
            attrs['teacher_groups'] = serializer.validated_data

        if not attrs.get('teacher_groups') and 'attend_student_ids' not in attrs:
            raise serializers.ValidationError({
                'teacher_groups': ['يجب إرسال teacher_groups أو attend_student_ids'],
            })
        return attrs


class LessonCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    date = serializers.DateField()
    teacher_groups = FlexibleJSONField(required=False)
    attend_student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
    )

    def validate(self, attrs):
        teacher_groups = attrs.get('teacher_groups')
        if teacher_groups is not None:
            serializer = TeacherGroupInputSerializer(data=teacher_groups, many=True)
            serializer.is_valid(raise_exception=True)
            attrs['teacher_groups'] = serializer.validated_data

        if not attrs.get('teacher_groups') and 'attend_student_ids' not in attrs:
            raise serializers.ValidationError({
                'teacher_groups': ['يجب إرسال teacher_groups أو attend_student_ids'],
            })
        return attrs


# ---------- Student ----------
class StudentListSerializer(serializers.ModelSerializer):
    pages_number = serializers.SerializerMethodField()
    abs_number = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'name', 'pages_number', 'abs_number', 'total_points']

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
            'total_points',
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
        activities = Activity.objects.filter(
            teacher_assignments__students=obj
        ).prefetch_related(
            'attended_students',
            'teacher_assignments__teacher',
            'teacher_assignments__students',
        ).distinct()
        return ActivitySerializer(activities, many=True).data

    def get_lessons(self, obj):
        lessons = Lesson.objects.filter(
            teacher_assignments__students=obj
        ).prefetch_related(
            'attended_students',
            'teacher_assignments__teacher',
            'teacher_assignments__students',
        ).distinct()
        return LessonSerializer(lessons, many=True).data

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

class SimpleStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name']


class SimpleTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ActivityTeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = SimpleTeacherSerializer(read_only=True)
    students = SimpleStudentSerializer(many=True, read_only=True)
    student_ids = serializers.SerializerMethodField()

    class Meta:
        model = ActivityTeacherAssignment
        fields = ['id', 'teacher', 'student_ids', 'students']

    def get_student_ids(self, obj):
        return list(obj.students.values_list('id', flat=True))


class LessonTeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = SimpleTeacherSerializer(read_only=True)
    students = SimpleStudentSerializer(many=True, read_only=True)
    student_ids = serializers.SerializerMethodField()

    class Meta:
        model = LessonTeacherAssignment
        fields = ['id', 'teacher', 'student_ids', 'students']

    def get_student_ids(self, obj):
        return list(obj.students.values_list('id', flat=True))


class ActivitySerializer(serializers.ModelSerializer):
    attended_students = SimpleStudentSerializer(many=True, read_only=True)
    attend_student_ids = serializers.SerializerMethodField()
    teacher_groups = ActivityTeacherAssignmentSerializer(source='teacher_assignments', many=True, read_only=True)
    activity_type_label = serializers.CharField(source='get_activity_type_display', read_only=True)
    resolved_activity_type = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            'id',
            'name',
            'date',
            'image',
            'activity_type',
            'activity_type_label',
            'other_activity_type',
            'resolved_activity_type',
            'attend_student_ids',
            'attended_students',
            'teacher_groups',
        ]

    def get_attend_student_ids(self, obj):
        return list(obj.attended_students.values_list('id', flat=True))

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_resolved_activity_type(self, obj):
        if obj.activity_type == 'other' and obj.other_activity_type:
            return obj.other_activity_type
        return obj.get_activity_type_display()


class LessonSerializer(serializers.ModelSerializer):
    attended_students = SimpleStudentSerializer(many=True, read_only=True)
    attend_student_ids = serializers.SerializerMethodField()
    teacher_groups = LessonTeacherAssignmentSerializer(source='teacher_assignments', many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id',
            'name',
            'date',
            'attend_student_ids',
            'attended_students',
            'teacher_groups',
        ]

    def get_attend_student_ids(self, obj):
        return list(obj.attended_students.values_list('id', flat=True))

class HadithSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hadith
        fields = ['title', 'narrator', 'alhadith', 'producer']


class PointRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointRule
        fields = [
            'id', 'code', 'name', 'category', 'direction',
            'calculation_method', 'default_points', 'config', 'is_active',
            'sort_order',
        ]


class SurahPageDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurahPageData
        fields = ['id', 'name', 'surah_name_arabic', 'surah_number', 'juz', 'juz_number',
                  'start_page', 'end_page', 'start_page_decimal', 'end_page_decimal',
                  'pages', 'is_active', 'metadata']


class JuzSerializer(serializers.ModelSerializer):
    surahs = SurahPageDataSerializer(source='surahpagedata_set', many=True, read_only=True)

    class Meta:
        model = Juz
        fields = ['id', 'juz_number', 'start_page', 'end_page', 'total_pages',
                  'is_active', 'surahs']


class PointsTransactionBaseSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    rule_id = serializers.IntegerField(min_value=1, required=False)
    rule_code = serializers.CharField(required=False, allow_blank=False, max_length=100)
    operation_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    memorized_pages = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    surah_id = serializers.IntegerField(min_value=1, required=False)
    metadata = FlexibleJSONField(required=False)

    def validate(self, attrs):
        if not attrs.get('rule_id') and not attrs.get('rule_code'):
            raise serializers.ValidationError({
                'rule_id': ['يجب إرسال rule_id أو rule_code'],
            })
        return attrs


class PointsTransactionCreateSerializer(PointsTransactionBaseSerializer):
    pass


class PointsTransactionUpdateSerializer(PointsTransactionBaseSerializer):
    transaction_id = serializers.IntegerField(min_value=1)


class PointsTransactionDeleteSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField(min_value=1)


class PointsTransactionFilterSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1, required=False)
    teacher_id = serializers.IntegerField(min_value=1, required=False)
    rule_code = serializers.CharField(required=False, allow_blank=False, max_length=100)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly'],
        required=False,
    )


class StudentPointTransactionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.username', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_code = serializers.CharField(source='rule.code', read_only=True)
    category = serializers.CharField(source='rule.category', read_only=True)
    surah_name = serializers.CharField(source='surah.surah_name_arabic', read_only=True)

    class Meta:
        model = StudentPointTransaction
        fields = [
            'id', 'student', 'student_name', 'rule', 'rule_name', 'rule_code',
            'category', 'points', 'operation_date', 'supervisor', 'supervisor_name',
            'input_method', 'memorized_pages', 'surah', 'surah_name', 'notes',
            'metadata', 'created_at', 'updated_at',
        ]


class PointsReportSerializer(serializers.Serializer):
    student_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    group_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    students_ranking = serializers.ListField()
    operations = serializers.ListField()
    memorization_by_pages = serializers.DictField()
    memorization_by_surahs = serializers.ListField()
    daily_summary = serializers.ListField()
    weekly_summary = serializers.ListField()
    monthly_summary = serializers.ListField()


# ========== Test Serializers ==========
class TestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    evaluation_display = serializers.CharField(source='get_evaluation_display', read_only=True)

    class Meta:
        model = Test
        fields = ['id', 'student', 'student_name', 'part_name', 'test_type', 'test_type_display', 
                  'attempt_number', 'evaluation', 'evaluation_display', 'points', 'teacher', 
                  'teacher_name', 'test_date', 'notes']


class TestCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    part_name = serializers.CharField(max_length=200)
    test_type = serializers.ChoiceField(choices=TestType.choices)
    evaluation = serializers.ChoiceField(choices=TestEvaluation.choices, required=False, allow_null=True)
    test_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


# ========== Note Serializers ==========
class NoteSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)

    class Meta:
        model = Note
        fields = ['id', 'student', 'student_name', 'note_type', 'note_type_display', 
                  'points', 'note_text', 'teacher', 'teacher_name', 'note_date']


class NoteCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    note_type = serializers.ChoiceField(choices=NoteType.choices)
    note_text = serializers.CharField()
    note_date = serializers.DateField(required=False)


# ========== StudentBehavior Serializers ==========
class StudentBehaviorSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    participation_type_display = serializers.CharField(source='get_participation_type_display', read_only=True, allow_null=True)

    class Meta:
        model = StudentBehavior
        fields = ['id', 'student', 'student_name', 'teacher', 'teacher_name',
                  'has_attended',
                  'has_clothing', 'has_cap',
                  'participation_type', 'participation_type_display',
                  'was_absent', 'no_recitation', 'left_early',
                  'behavior_date', 'total_points']


class StudentBehaviorCreateSerializer(serializers.Serializer):
    behavior_date = serializers.DateField()
    has_attended = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)
    has_clothing = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)
    has_cap = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)
    participation_type = serializers.DictField(child=serializers.ChoiceField(choices=['special', 'normal']), required=False)
    was_absent = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)
    no_recitation = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)
    left_early = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)


# ========== GoodBehavior Serializers ==========
class GoodBehaviorSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = GoodBehavior
        fields = ['id', 'student', 'student_name', 'teacher', 'teacher_name',
                  'week_start_date', 'points', 'description', 'created_at']


class GoodBehaviorCreateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    week_start_date = serializers.DateField()
    points = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=15)
    description = serializers.CharField(required=False, allow_blank=True)
