from datetime import date
from rest_framework import exceptions, permissions, status
from rest_framework.views import APIView

from core.models import (
    User, Student, StudentAttend, Hadith,
    Page, MemorizedPages
)
from .authentication import ApiTokenAuthentication
from .models import ApiAccessToken
from .responses import api_success, api_error
from .serializers import (
    AttendanceDeleteSerializer,
    AttendanceUpsertSerializer,
    HadithSerializer,
    LoginSerializer,
    MemorizedPageDeleteSerializer,
    PagesCreateSerializer,
    SectionStudentSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
    StudentLookupSerializer,
    TeacherSerializer,
)

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
            return Student.objects.filter(groupsession__teacher=self.request.user).distinct()
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
