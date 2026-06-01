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