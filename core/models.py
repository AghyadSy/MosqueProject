from datetime import date
from django.db import models
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.validators import RegexValidator

class User(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    permission = models.IntegerField()

    def login(self, request):
        request.session['user_id'] = self.id

    def logout(self, request):
        request.session.pop('user_id', None)
    
    def user(request):
        return User.objects.filter(id=request.session.get('user_id')).first()

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def verify_password(self, raw_password):
        if not raw_password:
            return False

        if self.password == raw_password:
            # Migrate legacy plain-text passwords on successful login.
            self.password = make_password(raw_password)
            self.save(update_fields=['password'])
            return True

        return check_password(raw_password, self.password)

    @classmethod
    def authenticate(cls, username, raw_password):
        user = cls.objects.filter(username=username).first()
        if user is None:
            return None
        if user.verify_password(raw_password):
            return user
        return None

    def save(self, *args, **kwargs):
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def students(self):
        s = []
        for g in GroupSession.objects.filter(teacher=self).all() :
            s.append(g.student)
        return s

    def __str__(self):
        return self.username

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

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

class Hadith(models.Model):
    title = models.CharField(max_length=200)
    narrator = models.CharField(max_length=200)
    alhadith = models.TextField()        # the full hadith text
    producer = models.CharField(max_length=200)

    def __str__(self):
        return self.title
