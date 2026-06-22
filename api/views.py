from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from rest_framework import exceptions, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from core.models import (
    Activity, ActivityTeacherAssignment, Hadith, Lesson, LessonTeacherAssignment, MemorizedPages,
    Page, PointCalculationMethod, PointRule, Student, StudentAttend,
    StudentPointTransaction, SurahPageData, User, Test, Note, StudentBehavior, GoodBehavior,
    TestType, TestEvaluation, NoteType, MemorizationType, normalize_decimal
)
from .authentication import ApiTokenAuthentication
from .models import ApiAccessToken
from .responses import api_success, api_error
from .serializers import (
    ActivityCreateSerializer,
    ActivityFilterSerializer,
    ActivitySerializer,
    AttendanceDeleteSerializer,
    AttendanceUpsertSerializer,
    HadithSerializer,
    LessonCreateSerializer,
    LessonFilterSerializer,
    LessonSerializer,
    LoginSerializer,
    MemorizedPageDeleteSerializer,
    PagesCreateSerializer,
    PointRuleSerializer,
    PointsReportSerializer,
    PointsTransactionCreateSerializer,
    PointsTransactionDeleteSerializer,
    PointsTransactionFilterSerializer,
    PointsTransactionUpdateSerializer,
    SectionStudentSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
    StudentPointTransactionSerializer,
    StudentLookupSerializer,
    SurahPageDataSerializer,
    TeacherSerializer,
    TestSerializer,
    TestCreateSerializer,
    NoteSerializer,
    NoteCreateSerializer,
    StudentBehaviorSerializer,
    StudentBehaviorCreateSerializer,
    GoodBehaviorSerializer,
    GoodBehaviorCreateSerializer,
)


def format_decimal_value(value):
    if value in (None, ''):
        value = Decimal('0')
    return str(Decimal(str(value)).quantize(Decimal('0.01')))


class BaseApiView(APIView):
    def success(self, message='تم تنفيذ الطلب بنجاح', data=None, status_code=status.HTTP_200_OK):
        return api_success(message=message, data=data, status_code=status_code)

    def validate_request(self, serializer_class, payload):
        serializer = serializer_class(data=payload)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class ProtectedApiView(BaseApiView):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_authenticated_teacher(self):
        return self.request.user

    def get_accessible_students(self):
        if self.request.user.permission >= 2:
            student_ids = [student.id for student in self.request.user.students()]
            return Student.objects.filter(id__in=student_ids).distinct()
        return Student.objects.all()

    def get_student(self, student_id):
        queryset = self.get_accessible_students()
        student = queryset.filter(id=student_id).first()
        if student is None:
            raise exceptions.NotFound('الطالب غير موجود أو غير مسموح لك الوصول إليه')
        return student

    def get_memorized_page(self, student, memorized_page_id):
        memorized_page = MemorizedPages.objects.filter(
            id=memorized_page_id,
            student=student,
        ).select_related('page').first()
        if memorized_page is None:
            raise exceptions.NotFound('سجل الحفظ غير موجود أو غير مسموح لك الوصول إليه')
        return memorized_page

    def get_accessible_student_ids(self):
        return set(self.get_accessible_students().values_list('id', flat=True))

    def get_accessible_teachers(self):
        if self.request.user.permission >= 2:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    def get_point_rule(self, rule_id=None, rule_code=None):
        queryset = PointRule.objects.filter(is_active=True)
        if rule_id:
            rule = queryset.filter(id=rule_id).first()
        else:
            rule = queryset.filter(code=rule_code).first()
        if rule is None:
            raise exceptions.NotFound('قاعدة النقاط غير موجودة أو غير مفعلة')
        return rule

    def get_surah(self, surah_id):
        surah = SurahPageData.objects.filter(id=surah_id, is_active=True).first()
        if surah is None:
            raise exceptions.NotFound('السورة غير موجودة أو غير مفعلة')
        return surah

    def get_point_transaction_queryset(self):
        queryset = StudentPointTransaction.objects.select_related(
            'student',
            'rule',
            'supervisor',
            'surah',
        )
        if self.request.user.permission >= 2:
            queryset = queryset.filter(student__groupsession__teacher=self.request.user)
        return queryset

    def get_point_transaction(self, transaction_id):
        transaction = self.get_point_transaction_queryset().filter(id=transaction_id).first()
        if transaction is None:
            raise exceptions.NotFound('عملية النقاط غير موجودة أو غير مسموح لك الوصول إليها')
        return transaction

    def validate_student_ids(self, student_ids):
        accessible_ids = self.get_accessible_student_ids()
        normalized_ids = []
        invalid_ids = []

        for student_id in student_ids:
            if student_id not in accessible_ids:
                invalid_ids.append(student_id)
                continue
            if student_id not in normalized_ids:
                normalized_ids.append(student_id)

        if invalid_ids:
            raise exceptions.ValidationError({
                'attend_student_ids': [f'الطلاب التالية معرفاتهم غير مسموح بها: {sorted(invalid_ids)}'],
            })

        return normalized_ids

    def validate_teacher_groups(self, teacher_groups=None, fallback_student_ids=None):
        normalized_groups = []
        accessible_teacher_ids = set(self.get_accessible_teachers().values_list('id', flat=True))

        if teacher_groups:
            for group in teacher_groups:
                teacher_id = group['teacher_id']
                if teacher_id not in accessible_teacher_ids:
                    raise exceptions.ValidationError({
                        'teacher_groups': [f'المشرف ذو المعرف {teacher_id} غير مسموح لك استخدامه'],
                    })

                teacher = User.objects.filter(id=teacher_id).first()
                teacher_student_ids = {student.id for student in teacher.students()}
                normalized_student_ids = []
                invalid_student_ids = []
                for student_id in group.get('student_ids', []):
                    if student_id not in teacher_student_ids:
                        invalid_student_ids.append(student_id)
                        continue
                    if student_id not in normalized_student_ids:
                        normalized_student_ids.append(student_id)

                if invalid_student_ids:
                    raise exceptions.ValidationError({
                        'teacher_groups': [f'الطلاب التالية معرفاتهم لا تتبع للمشرف {teacher.username}: {sorted(invalid_student_ids)}'],
                    })

                normalized_groups.append({
                    'teacher': teacher,
                    'teacher_id': teacher.id,
                    'student_ids': normalized_student_ids,
                })

        elif fallback_student_ids is not None:
            teacher = self.get_authenticated_teacher()
            normalized_groups.append({
                'teacher': teacher,
                'teacher_id': teacher.id,
                'student_ids': self.validate_student_ids(fallback_student_ids),
            })

        if not normalized_groups:
            raise exceptions.ValidationError({
                'teacher_groups': ['يجب إضافة أستاذ واحد على الأقل مع طلابه'],
            })

        return normalized_groups

    def apply_date_filters(self, queryset, validated):
        if validated.get('date_from'):
            queryset = queryset.filter(date__gte=validated['date_from'])
        if validated.get('date_to'):
            queryset = queryset.filter(date__lte=validated['date_to'])
        return queryset


class LoginView(BaseApiView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = User.authenticate(username=username, raw_password=password)
        if user is None:
            return api_error(
                message='اسم المستخدم أو كلمة المرور غير صحيحة',
                errors={'credentials': ['بيانات الدخول غير صحيحة']},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token = ApiAccessToken.issue_for_user(user)
        return self.success(
            message='تم تسجيل الدخول بنجاح',
            data={
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'permission': user.permission,
                },
            },
        )

# ---------- Students ----------
class AllStudentsView(ProtectedApiView):
    def post(self, request):
        teacher = self.get_authenticated_teacher()
        students = teacher.students()
        serializer = StudentListSerializer(students, many=True)
        return self.success(
            message='تم جلب الطلاب بنجاح',
            data={'students': serializer.data},
        )

class StudentInfoView(ProtectedApiView):
    def post(self, request):
        validated = self.validate_request(StudentLookupSerializer, request.data)
        student = self.get_student(validated['student_id'])
        serializer = StudentDetailSerializer(student)
        return self.success(
            message='تم جلب معلومات الطالب بنجاح',
            data={'student': serializer.data},
        )

# ---------- Teacher list with absences ----------
class AdminsInfoView(ProtectedApiView):
    def get(self, request):
        teachers = User.objects.all()
        serializer = TeacherSerializer(teachers, many=True)
        return self.success(
            message='تم جلب المشرفين بنجاح',
            data={'admins': serializer.data},
        )

# ---------- Students of a specific teacher ----------
class AdminStudentsView(ProtectedApiView):
    def post(self, request):
        teacher = self.get_authenticated_teacher()
        students = teacher.students()
        return self.success(
            message='تم جلب أسماء الطلاب بنجاح',
            data={'students': [s.name for s in students]},
        )

# ---------- Attendance ----------
class AttendStudentsView(ProtectedApiView):
    def post(self, request):
        validated = self.validate_request(AttendanceUpsertSerializer, request.data)
        today = date.today()
        teacher = self.get_authenticated_teacher()
        students = teacher.students()

        StudentAttend.objects.filter(
            student__in=students, date=today
        ).delete()

        normalized_attend = set(validated['attend_student_ids'])
        teacher_student_ids = {student.id for student in students}
        invalid_student_ids = sorted(normalized_attend - teacher_student_ids)
        if invalid_student_ids:
            raise exceptions.ValidationError({
                'attend_student_ids': [f'الطلاب التالية معرفاتهم غير تابعة لهذا المشرف: {invalid_student_ids}'],
            })

        attend_count = 0
        absent_count = 0
        for student in students:
            is_att = student.id in normalized_attend
            StudentAttend.objects.create(
                student=student, date=today, is_attend=is_att
            )
            if is_att:
                attend_count += 1
            else:
                absent_count += 1

        return self.success(
            message='تم حفظ الحضور بنجاح',
            data={
                'date': today.isoformat(),
                'attend_count': attend_count,
                'absent_count': absent_count,
            },
        )

class AttendStudentsGetView(ProtectedApiView):
    def post(self, request):
        today = date.today()
        teacher = self.get_authenticated_teacher()
        students = teacher.students()
        if not StudentAttend.objects.filter(
            student__in=students, date=today
        ).exists():
            return api_error(
                message='لا توجد سجلات حضور لهذا اليوم',
                errors={'attendance': ['لا توجد بيانات مسجلة']},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        attends = StudentAttend.objects.filter(
            student__in=students, date=today, is_attend=True
        )
        absents = StudentAttend.objects.filter(
            student__in=students, date=today, is_attend=False
        )
        return self.success(
            message='تم جلب حضور اليوم بنجاح',
            data={
                'date': today.isoformat(),
                'attend': [a.student.name for a in attends],
                'abs': [a.student.name for a in absents],
            },
        )

class AttendStudentsDeleteView(ProtectedApiView):
    def delete(self, request):
        validated = self.validate_request(AttendanceDeleteSerializer, request.data)
        del_date = validated['date']
        teacher = self.get_authenticated_teacher()
        students = teacher.students()
        deleted_count, _ = StudentAttend.objects.filter(
            student__in=students, date=del_date
        ).delete()
        return self.success(
            message='تم حذف سجل الحضور بنجاح',
            data={
                'date': del_date.isoformat(),
                'deleted_count': deleted_count,
            },
        )

class AttendStudentsGetAllView(ProtectedApiView):
    def post(self, request):
        teacher = self.get_authenticated_teacher()
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
                'date': d.isoformat(),
                'attends': [a.student.name for a in day_att],
                'abs': [a.student.name for a in day_abs]
            })
        return self.success(
            message='تم جلب كل سجلات الحضور بنجاح',
            data={'records': result},
        )

class UnmemorizedPagesView(ProtectedApiView):
    def post(self, request):
        validated = self.validate_request(SectionStudentSerializer, request.data)
        student = self.get_student(validated['student_id'])
        section = validated['page_archive']

        all_pages = Page.objects.filter(section=section).values_list('name', flat=True)
        memorized_page_names = MemorizedPages.objects.filter(
            student=student,
            page__section=section
        ).values_list('page__name', flat=True).distinct()
        unmemorized = [name for name in all_pages if name not in memorized_page_names]

        return self.success(
            message='تم جلب الصفحات غير المحفوظة بنجاح',
            data={'pages': unmemorized},
        )

class PagesView(ProtectedApiView):
    def post(self, request):
        validated = self.validate_request(PagesCreateSerializer, request.data)
        student = self.get_student(validated['student_id'])
        today = date.today()
        pages = Page.objects.filter(id__in=validated['page_ids'])
        pages_by_id = {page.id: page for page in pages}
        missing_page_ids = [
            page_id for page_id in validated['page_ids']
            if page_id not in pages_by_id
        ]
        if missing_page_ids:
            raise exceptions.ValidationError({
                'page_ids': [f'الصفحات التالية غير موجودة: {missing_page_ids}'],
            })

        created_pages = []
        created_page_ids = []
        for page_id in validated['page_ids']:
            page = pages_by_id[page_id]
            if not MemorizedPages.objects.filter(
                student=student,
                page=page,
                date=today,
            ).exists():
                MemorizedPages.objects.create(
                    student=student, page=page, date=today
                )
                created_pages.append(page.name)
                created_page_ids.append(page.id)
        return self.success(
            message='تمت إضافة الصفحات بنجاح',
            data={
                'student_id': student.id,
                'date': today.isoformat(),
                'page_ids': created_page_ids,
                'pages': created_pages,
            },
        )

    def delete(self, request):
        validated = self.validate_request(MemorizedPageDeleteSerializer, request.data)
        student = self.get_student(validated['student_id'])
        memorized_page = self.get_memorized_page(student, validated['memorized_page_id'])
        deleted_page_id = memorized_page.page.id
        deleted_page_name = memorized_page.page.name
        deleted_date = memorized_page.date.isoformat()
        memorized_page.delete()
        return self.success(
            message='تم حذف الصفحة المحفوظة بنجاح',
            data={
                'student_id': student.id,
                'memorized_page_id': validated['memorized_page_id'],
                'page_id': deleted_page_id,
                'page': deleted_page_name,
                'date': deleted_date,
                'deleted_count': 1,
            },
        )


class ActivityBaseView(ProtectedApiView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Activity.objects.prefetch_related(
            'attended_students',
            'teacher_assignments__teacher',
            'teacher_assignments__students',
        )
        if self.request.user.permission >= 2:
            queryset = queryset.filter(teacher_assignments__teacher=self.request.user)
        return queryset

    def get_activity(self, activity_id):
        activity = self.get_queryset().filter(id=activity_id).distinct().first()
        if activity is None:
            raise exceptions.NotFound('النشاط غير موجود أو غير مسموح لك الوصول إليه')
        return activity

    def get_activity_id(self, payload):
        activity_id = payload.get('activity_id', payload.get('id'))
        if activity_id in (None, ''):
            raise exceptions.ValidationError({
                'activity_id': ['هذا الحقل مطلوب'],
            })
        try:
            return int(activity_id)
        except (TypeError, ValueError):
            raise exceptions.ValidationError({
                'activity_id': ['يجب أن يكون معرف النشاط رقماً صحيحاً'],
            })

    def sync_teacher_assignments(self, activity, teacher_groups):
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

    def list_activities(self, request):
        validated = self.validate_request(ActivityFilterSerializer, request.data if request.method == 'POST' else request.query_params)
        queryset = self.apply_date_filters(self.get_queryset(), validated)
        if validated.get('activity_type'):
            queryset = queryset.filter(activity_type=validated['activity_type'])
        if validated.get('teacher_id'):
            queryset = queryset.filter(teacher_assignments__teacher_id=validated['teacher_id'])
        if validated.get('student_id'):
            student = self.get_student(validated['student_id'])
            queryset = queryset.filter(teacher_assignments__students=student)
        serializer = ActivitySerializer(queryset.distinct(), many=True, context={'request': request})
        return self.success(
            message='تم جلب النشاطات بنجاح',
            data={'activities': serializer.data},
        )

    def create_activity(self, request):
        validated = self.validate_request(ActivityCreateSerializer, request.data)
        teacher_groups = self.validate_teacher_groups(
            teacher_groups=validated.get('teacher_groups'),
            fallback_student_ids=validated.get('attend_student_ids'),
        )
        activity = Activity.objects.create(
            name=validated['name'],
            date=validated['date'],
            image=validated.get('image'),
            activity_type=validated['activity_type'],
            other_activity_type=validated.get('other_activity_type', '').strip(),
            created_by=self.get_authenticated_teacher(),
        )
        self.sync_teacher_assignments(activity, teacher_groups)
        serializer = ActivitySerializer(activity, context={'request': request})
        return self.success(
            message='تمت إضافة النشاط بنجاح',
            data={'activity': serializer.data},
            status_code=status.HTTP_201_CREATED,
        )

    def update_activity(self, request):
        activity = self.get_activity(self.get_activity_id(request.data))
        validated = self.validate_request(ActivityCreateSerializer, request.data)
        teacher_groups = self.validate_teacher_groups(
            teacher_groups=validated.get('teacher_groups'),
            fallback_student_ids=validated.get('attend_student_ids'),
        )

        if self.request.user.permission >= 2:
            preserved_groups = []
            for assignment in activity.teacher_assignments.exclude(teacher=self.request.user).prefetch_related('students', 'teacher'):
                preserved_groups.append({
                    'teacher': assignment.teacher,
                    'teacher_id': assignment.teacher_id,
                    'student_ids': list(assignment.students.values_list('id', flat=True)),
                })
            teacher_groups = preserved_groups + teacher_groups

        activity.name = validated['name']
        activity.date = validated['date']
        activity.activity_type = validated['activity_type']
        activity.other_activity_type = validated.get('other_activity_type', '').strip()
        if validated.get('image') is not None:
            activity.image = validated['image']
        activity.save()

        self.sync_teacher_assignments(activity, teacher_groups)
        serializer = ActivitySerializer(activity, context={'request': request})
        return self.success(
            message='تم تعديل النشاط بنجاح',
            data={'activity': serializer.data},
        )


class ActivityView(ActivityBaseView):
    def get(self, request):
        return self.list_activities(request)

    def post(self, request):
        return self.create_activity(request)

    def put(self, request):
        return self.update_activity(request)


class ActivityListView(ActivityBaseView):
    def get(self, request):
        return self.list_activities(request)

    def post(self, request):
        return self.list_activities(request)


class ActivityCreateView(ActivityBaseView):
    def post(self, request):
        return self.create_activity(request)

    def put(self, request):
        return self.update_activity(request)


class LessonBaseView(ProtectedApiView):
    def get_queryset(self):
        queryset = Lesson.objects.prefetch_related(
            'attended_students',
            'teacher_assignments__teacher',
            'teacher_assignments__students',
        )
        if self.request.user.permission >= 2:
            queryset = queryset.filter(teacher_assignments__teacher=self.request.user)
        return queryset

    def get_lesson(self, lesson_id):
        lesson = self.get_queryset().filter(id=lesson_id).distinct().first()
        if lesson is None:
            raise exceptions.NotFound('الدرس غير موجود أو غير مسموح لك الوصول إليه')
        return lesson

    def get_lesson_id(self, payload):
        lesson_id = payload.get('lesson_id', payload.get('id'))
        if lesson_id in (None, ''):
            raise exceptions.ValidationError({
                'lesson_id': ['هذا الحقل مطلوب'],
            })
        try:
            return int(lesson_id)
        except (TypeError, ValueError):
            raise exceptions.ValidationError({
                'lesson_id': ['يجب أن يكون معرف الدرس رقماً صحيحاً'],
            })

    def sync_teacher_assignments(self, lesson, teacher_groups):
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

    def list_lessons(self, request):
        validated = self.validate_request(LessonFilterSerializer, request.data if request.method == 'POST' else request.query_params)
        queryset = self.apply_date_filters(self.get_queryset(), validated)
        if validated.get('teacher_id'):
            queryset = queryset.filter(teacher_assignments__teacher_id=validated['teacher_id'])
        if validated.get('student_id'):
            student = self.get_student(validated['student_id'])
            queryset = queryset.filter(teacher_assignments__students=student)
        serializer = LessonSerializer(queryset.distinct(), many=True, context={'request': request})
        return self.success(
            message='تم جلب الدروس بنجاح',
            data={'lessons': serializer.data},
        )

    def create_lesson(self, request):
        validated = self.validate_request(LessonCreateSerializer, request.data)
        teacher_groups = self.validate_teacher_groups(
            teacher_groups=validated.get('teacher_groups'),
            fallback_student_ids=validated.get('attend_student_ids'),
        )
        lesson = Lesson.objects.create(
            name=validated['name'],
            date=validated['date'],
            created_by=self.get_authenticated_teacher(),
        )
        self.sync_teacher_assignments(lesson, teacher_groups)
        serializer = LessonSerializer(lesson, context={'request': request})
        return self.success(
            message='تمت إضافة الدرس بنجاح',
            data={'lesson': serializer.data},
            status_code=status.HTTP_201_CREATED,
        )

    def update_lesson(self, request):
        lesson = self.get_lesson(self.get_lesson_id(request.data))
        validated = self.validate_request(LessonCreateSerializer, request.data)
        teacher_groups = self.validate_teacher_groups(
            teacher_groups=validated.get('teacher_groups'),
            fallback_student_ids=validated.get('attend_student_ids'),
        )

        if self.request.user.permission >= 2:
            preserved_groups = []
            for assignment in lesson.teacher_assignments.exclude(teacher=self.request.user).prefetch_related('students', 'teacher'):
                preserved_groups.append({
                    'teacher': assignment.teacher,
                    'teacher_id': assignment.teacher_id,
                    'student_ids': list(assignment.students.values_list('id', flat=True)),
                })
            teacher_groups = preserved_groups + teacher_groups

        lesson.name = validated['name']
        lesson.date = validated['date']
        lesson.save()

        self.sync_teacher_assignments(lesson, teacher_groups)
        serializer = LessonSerializer(lesson, context={'request': request})
        return self.success(
            message='تم تعديل الدرس بنجاح',
            data={'lesson': serializer.data},
        )


class LessonView(LessonBaseView):
    def get(self, request):
        return self.list_lessons(request)

    def post(self, request):
        return self.create_lesson(request)

    def put(self, request):
        return self.update_lesson(request)


class LessonListView(LessonBaseView):
    def get(self, request):
        return self.list_lessons(request)

    def post(self, request):
        return self.list_lessons(request)


class LessonCreateView(LessonBaseView):
    def post(self, request):
        return self.create_lesson(request)

    def put(self, request):
        return self.update_lesson(request)


class PointsBaseView(ProtectedApiView):
    def build_transaction_payload(self, validated):
        student = self.get_student(validated['student_id'])
        rule = self.get_point_rule(
            rule_id=validated.get('rule_id'),
            rule_code=validated.get('rule_code'),
        )
        surah = None
        memorized_pages = validated.get('memorized_pages')
        input_method = 'manual'

        if validated.get('surah_id'):
            surah = self.get_surah(validated['surah_id'])
            memorized_pages = surah.pages
            input_method = 'surah'
        elif memorized_pages is not None:
            input_method = 'direct_pages'

        if rule.calculation_method == PointCalculationMethod.MEMORIZATION and memorized_pages is None:
            raise exceptions.ValidationError({
                'memorized_pages': ['عمليات الحفظ تحتاج إلى عدد صفحات مباشر أو اختيار سورة'],
            })

        return {
            'student': student,
            'rule': rule,
            'surah': surah,
            'memorized_pages': memorized_pages,
            'operation_date': validated.get('operation_date', date.today()),
            'supervisor': self.get_authenticated_teacher(),
            'notes': validated.get('notes', ''),
            'metadata': validated.get('metadata') or {},
            'input_method': input_method,
        }

    def get_filtered_transactions(self, validated):
        queryset = self.get_point_transaction_queryset()
        queryset = self.apply_date_filters(queryset, validated)

        if validated.get('student_id'):
            student = self.get_student(validated['student_id'])
            queryset = queryset.filter(student=student)

        if validated.get('teacher_id'):
            teacher_queryset = self.get_accessible_teachers().filter(id=validated['teacher_id'])
            if not teacher_queryset.exists():
                raise exceptions.NotFound('المشرف غير موجود أو غير مسموح لك الوصول إليه')
            queryset = queryset.filter(student__groupsession__teacher_id=validated['teacher_id'])

        if validated.get('rule_code'):
            queryset = queryset.filter(rule__code=validated['rule_code'])

        return queryset.distinct()

    def build_period_summary(self, queryset, truncator):
        summary = queryset.annotate(period=truncator('operation_date')).values('period').annotate(
            total_points=Sum('points'),
            operations_count=Count('id'),
        ).order_by('period')
        return [
            {
                'period': item['period'].isoformat() if item['period'] else None,
                'total_points': format_decimal_value(item['total_points']),
                'operations_count': item['operations_count'],
            }
            for item in summary
        ]

    def build_reports(self, queryset, requested_student=None):
        if requested_student is not None:
            student_total = requested_student.total_points
        else:
            student_total = queryset.aggregate(total=Sum('points')).get('total') or Decimal('0')

        accessible_students = self.get_accessible_students()
        group_total = queryset.aggregate(total=Sum('points')).get('total') or Decimal('0')

        ranking_queryset = accessible_students.order_by('-total_points', 'name')
        students_ranking = [
            {
                'student_id': student.id,
                'student_name': student.name,
                'total_points': format_decimal_value(student.total_points),
            }
            for student in ranking_queryset
        ]

        memorization_queryset = queryset.filter(rule__calculation_method=PointCalculationMethod.MEMORIZATION)
        memorization_by_pages = memorization_queryset.aggregate(
            total_pages=Sum('memorized_pages'),
            operations_count=Count('id'),
            total_points=Sum('points'),
        )
        memorization_by_surahs = list(
            memorization_queryset.exclude(surah__isnull=True).values(
                'surah__id',
                'surah__name',
                'surah__juz',
            ).annotate(
                total_pages=Sum('memorized_pages'),
                total_points=Sum('points'),
                times=Count('id'),
            ).order_by('-times', 'surah__surah_number')
        )
        normalized_surahs = []
        for item in memorization_by_surahs:
            normalized_item = dict(item)
            normalized_item['total_pages'] = format_decimal_value(item.get('total_pages'))
            normalized_item['total_points'] = format_decimal_value(item.get('total_points'))
            normalized_surahs.append(normalized_item)

        operations = StudentPointTransactionSerializer(queryset[:100], many=True).data
        return {
            'student_total': format_decimal_value(student_total),
            'group_total': format_decimal_value(group_total),
            'students_ranking': students_ranking,
            'operations': operations,
            'memorization_by_pages': {
                'total_pages': format_decimal_value(memorization_by_pages.get('total_pages')),
                'operations_count': memorization_by_pages.get('operations_count') or 0,
                'total_points': format_decimal_value(memorization_by_pages.get('total_points')),
            },
            'memorization_by_surahs': normalized_surahs,
            'daily_summary': self.build_period_summary(queryset, TruncDay),
            'weekly_summary': self.build_period_summary(queryset, TruncWeek),
            'monthly_summary': self.build_period_summary(queryset, TruncMonth),
        }


class PointRulesView(PointsBaseView):
    def get(self, request):
        serializer = PointRuleSerializer(PointRule.objects.order_by('sort_order', 'id'), many=True)
        return self.success(
            message='تم جلب قواعد النقاط بنجاح',
            data={'rules': serializer.data},
        )


class SurahListView(PointsBaseView):
    def get(self, request):
        queryset = SurahPageData.objects.filter(is_active=True).order_by('surah_number')
        serializer = SurahPageDataSerializer(queryset, many=True)
        return self.success(
            message='تم جلب السور بنجاح',
            data={'surahs': serializer.data},
        )


class PointsTransactionsView(PointsBaseView):
    def get(self, request):
        validated = self.validate_request(PointsTransactionFilterSerializer, request.query_params)
        queryset = self.get_filtered_transactions(validated)
        serializer = StudentPointTransactionSerializer(queryset, many=True)
        return self.success(
            message='تم جلب سجل النقاط بنجاح',
            data={'transactions': serializer.data},
        )

    def post(self, request):
        validated = self.validate_request(PointsTransactionCreateSerializer, request.data)
        payload = self.build_transaction_payload(validated)
        transaction = StudentPointTransaction.objects.create(**payload)
        serializer = StudentPointTransactionSerializer(transaction)
        return self.success(
            message='تمت إضافة عملية النقاط بنجاح',
            data={'transaction': serializer.data},
            status_code=status.HTTP_201_CREATED,
        )

    def put(self, request):
        validated = self.validate_request(PointsTransactionUpdateSerializer, request.data)
        transaction = self.get_point_transaction(validated['transaction_id'])
        payload = self.build_transaction_payload(validated)
        for field, value in payload.items():
            setattr(transaction, field, value)
        transaction.save()
        serializer = StudentPointTransactionSerializer(transaction)
        return self.success(
            message='تم تعديل عملية النقاط بنجاح',
            data={'transaction': serializer.data},
        )

    def delete(self, request):
        validated = self.validate_request(PointsTransactionDeleteSerializer, request.data)
        transaction = self.get_point_transaction(validated['transaction_id'])
        transaction_id = transaction.id
        transaction.delete()
        return self.success(
            message='تم حذف عملية النقاط بنجاح',
            data={'transaction_id': transaction_id, 'deleted_count': 1},
        )


class PointsReportsView(PointsBaseView):
    def post(self, request):
        validated = self.validate_request(PointsTransactionFilterSerializer, request.data)
        queryset = self.get_filtered_transactions(validated)
        requested_student = None
        if validated.get('student_id'):
            requested_student = self.get_student(validated['student_id'])

        report_data = self.build_reports(queryset, requested_student=requested_student)
        serializer = PointsReportSerializer(report_data)
        return self.success(
            message='تم جلب تقارير النقاط بنجاح',
            data={'report': serializer.data},
        )

# ---------- Version ----------
class VersionView(BaseApiView):
    def get(self, request):
        return self.success(
            message='تم جلب نسخة النظام بنجاح',
            data={'version': '1.0.0'},
        )

class HadithView(ProtectedApiView):
    def get(self, request):
        hadiths = Hadith.objects.all()
        serializer = HadithSerializer(hadiths, many=True)
        return self.success(
            message='تم جلب الأحاديث بنجاح',
            data={'hadiths': serializer.data},
        )

# ---------- Test Views ----------
class TestView(ProtectedApiView):
    def get(self, request):
        # Get all tests for the teacher's students, or all if admin
        student_id = request.data.get('student_id') or request.query_params.get('student_id')
        if student_id:
            student = self.get_student(int(student_id))
            tests = Test.objects.filter(student=student).order_by('-test_date', '-id')
        else:
            accessible_students = self.get_accessible_students()
            tests = Test.objects.filter(student__in=accessible_students).order_by('-test_date', '-id')
        serializer = TestSerializer(tests, many=True)
        return self.success(message='تم جلب الاختبارات بنجاح', data={'tests': serializer.data})
    
    def post(self, request):
        validated = self.validate_request(TestCreateSerializer, request.data)
        student = self.get_student(validated['student_id'])
        teacher = self.get_authenticated_teacher()
        test_date = validated.get('test_date', date.today())
        
        # Calculate points
        test_type = validated['test_type']
        if test_type == TestType.EXTERNAL:
            points = 100
            evaluation = validated.get('evaluation')
            if evaluation == TestEvaluation.FAILED:
                points -= 25
        else:  # internal
            # Count previous attempts for the same student and part name
            previous_attempts = Test.objects.filter(
                student=student,
                part_name=validated['part_name'],
                test_type=TestType.INTERNAL
            ).count()
            attempt_number = previous_attempts + 1
            if attempt_number == 1:
                points = 50
            elif attempt_number == 2:
                points = 40
            elif attempt_number >= 3:
                points = 25
        
        test = Test.objects.create(
            student=student,
            part_name=validated['part_name'],
            test_type=test_type,
            attempt_number=attempt_number if test_type == 'internal' else 1,
            evaluation=validated.get('evaluation'),
            points=normalize_decimal(points),
            teacher=teacher,
            test_date=test_date,
            notes=validated.get('notes', '')
        )
        
        # Also add a point transaction
        StudentPointTransaction.objects.create(
            student=student,
            rule=None,  # Or create a specific rule
            supervisor=teacher,
            operation_date=test_date,
            points=normalize_decimal(points),
            notes=f"اختبار: {validated['part_name']} ({test.get_test_type_display()})"
        )
        
        student.refresh_total_points()
        
        serializer = TestSerializer(test)
        return self.success(message='تم إضافة الاختبار بنجاح', data={'test': serializer.data}, status_code=status.HTTP_201_CREATED)


# ---------- Note Views ----------
class NoteView(ProtectedApiView):
    def get(self, request):
        student_id = request.data.get('student_id') or request.query_params.get('student_id')
        if student_id:
            student = self.get_student(int(student_id))
            notes = Note.objects.filter(student=student).order_by('-note_date', '-id')
        else:
            accessible_students = self.get_accessible_students()
            notes = Note.objects.filter(student__in=accessible_students).order_by('-note_date', '-id')
        serializer = NoteSerializer(notes, many=True)
        return self.success(message='تم جلب الملاحظات بنجاح', data={'notes': serializer.data})
    
    def post(self, request):
        validated = self.validate_request(NoteCreateSerializer, request.data)
        student = self.get_student(validated['student_id'])
        teacher = self.get_authenticated_teacher()
        note_date = validated.get('note_date', date.today())
        
        # Calculate points
        note_type = validated['note_type']
        points = 5 if note_type == NoteType.GOOD else -10
        
        note = Note.objects.create(
            student=student,
            note_type=note_type,
            points=normalize_decimal(points),
            note_text=validated['note_text'],
            teacher=teacher,
            note_date=note_date
        )
        
        # Add point transaction
        StudentPointTransaction.objects.create(
            student=student,
            rule=None,
            supervisor=teacher,
            operation_date=note_date,
            points=normalize_decimal(points),
            notes=f"ملاحظة: {validated['note_text']}"
        )
        
        student.refresh_total_points()
        
        serializer = NoteSerializer(note)
        return self.success(message='تم إضافة الملاحظة بنجاح', data={'note': serializer.data}, status_code=status.HTTP_201_CREATED)


# ---------- StudentBehavior Views ----------
class StudentBehaviorView(ProtectedApiView):
    def get(self, request):
        student_id = request.data.get('student_id') or request.query_params.get('student_id')
        if student_id:
            student = self.get_student(int(student_id))
            behaviors = StudentBehavior.objects.filter(student=student).order_by('-behavior_date', '-id')
        else:
            accessible_students = self.get_accessible_students()
            behaviors = StudentBehavior.objects.filter(student__in=accessible_students).order_by('-behavior_date', '-id')
        serializer = StudentBehaviorSerializer(behaviors, many=True)
        return self.success(message='تم جلب السلوكيات بنجاح', data={'behaviors': serializer.data})
    
    def post(self, request):
        validated = self.validate_request(StudentBehaviorCreateSerializer, request.data)
        student = self.get_student(validated['student_id'])
        teacher = self.get_authenticated_teacher()
        behavior_date = validated.get('behavior_date', date.today())
        
        behavior = StudentBehavior.objects.create(
            student=student,
            teacher=teacher,
            memorization_type=validated.get('memorization_type'),
            memorization_value=validated.get('memorization_value', ''),
            memorization_pages=validated.get('memorization_pages', 0),
            has_attended=validated.get('has_attended', False),
            has_clothing=validated.get('has_clothing', False),
            has_cap=validated.get('has_cap', False),
            participation_type=validated.get('participation_type'),
            was_absent=validated.get('was_absent', False),
            no_recitation=validated.get('no_recitation', False),
            left_early=validated.get('left_early', False),
            behavior_date=behavior_date
        )
        
        serializer = StudentBehaviorSerializer(behavior)
        return self.success(message='تم إضافة سلوك الطالب بنجاح', data={'behavior': serializer.data}, status_code=status.HTTP_201_CREATED)


# ---------- GoodBehavior Views ----------
class GoodBehaviorView(ProtectedApiView):
    def get(self, request):
        student_id = request.data.get('student_id') or request.query_params.get('student_id')
        if student_id:
            student = self.get_student(int(student_id))
            good_behaviors = GoodBehavior.objects.filter(student=student).order_by('-week_start_date', '-id')
        else:
            accessible_students = self.get_accessible_students()
            good_behaviors = GoodBehavior.objects.filter(student__in=accessible_students).order_by('-week_start_date', '-id')
        serializer = GoodBehaviorSerializer(good_behaviors, many=True)
        return self.success(message='تم جلب السلوكيات الحسنة بنجاح', data={'good_behaviors': serializer.data})
    
    def post(self, request):
        validated = self.validate_request(GoodBehaviorCreateSerializer, request.data)
        student = self.get_student(validated['student_id'])
        teacher = self.get_authenticated_teacher()
        
        good_behavior = GoodBehavior.objects.create(
            student=student,
            teacher=teacher,
            week_start_date=validated['week_start_date'],
            points=normalize_decimal(validated.get('points', 15)),
            description=validated.get('description', ''),
            created_at=date.today()
        )
        
        # Add point transaction
        StudentPointTransaction.objects.create(
            student=student,
            rule=None,
            supervisor=teacher,
            operation_date=validated['week_start_date'],
            points=normalize_decimal(validated.get('points', 15)),
            notes=f"سلوك حسن: {validated.get('description', '')}"
        )
        
        student.refresh_total_points()
        
        serializer = GoodBehaviorSerializer(good_behavior)
        return self.success(message='تم إضافة سلوك حسن بنجاح', data={'good_behavior': serializer.data}, status_code=status.HTTP_201_CREATED)


# ---------- Placeholder views for other endpoints (return empty or simple responses) ----------
class PlaceholderView(ProtectedApiView):
    def get(self, request):
        return self.success(message='لا توجد بيانات حالياً', data={})
    def post(self, request):
        return self.success(message='لا توجد بيانات حالياً', data={})
    def put(self, request):
        return self.success(message='لا توجد بيانات حالياً', data={})
    def delete(self, request):
        return self.success(message='لا توجد بيانات حالياً', data={})
