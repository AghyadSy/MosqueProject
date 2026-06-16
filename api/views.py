from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date

from core.models import (
    User, Student, GroupSession, StudentAttend,Hadith,
    Page, MemorizedPages
)
from .serializers import (
    LoginSerializer, StudentListSerializer, StudentDetailSerializer, HadithSerializer,
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

class UnmemorizedPagesView(APIView):
    def post(self, request):
        student_name = request.data.get('student')
        section = request.data.get('page_archive')   # integer

        student = Student.objects.filter(name=student_name).first()
        if not student:
            return Response({"error": "Student not found"}, status=404)

        # All page names for this section
        all_pages = Page.objects.filter(section=section).values_list('name', flat=True)

        # Pages already memorized by this student (across all dates)
        memorized_page_names = MemorizedPages.objects.filter(
            student=student,
            page__section=section
        ).values_list('page__name', flat=True).distinct()

        # Unmemorized = all_pages - memorized
        unmemorized = [name for name in all_pages if name not in memorized_page_names]

        return Response(unmemorized)

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

class HadithView(APIView):
    def get(self, request):
        hadiths = Hadith.objects.all()
        serializer = HadithSerializer(hadiths, many=True)
        return Response({"data": serializer.data})

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