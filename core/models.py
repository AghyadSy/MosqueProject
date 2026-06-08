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
    birth_date = models.DateField(null=True)

    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        null=True,
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
        
        s = GroupSession.objects.filter(teacher__username=teacher).values("student")
        d = StudentAttend.objects.filter(student__in=s).all()
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

        all_attendance = list(
            StudentAttend.objects
            .select_related('student')
            .order_by('date')
        )

        sessions = list(
            GroupSession.objects
            .values('teacher_id', 'student_id')
        )

        all_teachers = list(User.objects.all())

        teacher_students = {}
        for session in sessions:
            tid = session['teacher_id']
            if tid not in teacher_students:
                teacher_students[tid] = set()
            teacher_students[tid].add(session['student_id'])

        date_index = {}
        for record in all_attendance:
            if record.date not in date_index:
                date_index[record.date] = {}
            date_index[record.date][record.student_id] = record

        unique_dates = sorted(date_index.keys())

        data = []
        for date in unique_dates:
            day_records = date_index[date]
            sub_data = []

            for teacher in all_teachers:
                student_ids = teacher_students.get(teacher.id, set())
                attend = []
                absent = []

                for sid in student_ids:
                    record = day_records.get(sid)
                    if record is not None:
                        if record.is_attend:
                            attend.append(record)
                        else:
                            absent.append(record)

                sub_data.append({
                    'teacher': teacher,
                    'attend': attend,
                    'absent': absent,
                })

            data.append({
                'date': date,
                'data': sub_data,
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