from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.db.models import Sum
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


POINTS_DECIMAL_PLACES = Decimal('0.01')
DEFAULT_MEMORIZATION_THRESHOLDS = {
    1: Decimal('5'),
    2: Decimal('15'),
    3: Decimal('25'),
    4: Decimal('40'),
}
DEFAULT_EXTRA_PAGE_RATE = Decimal('10')


def normalize_decimal(value, default='0'):
    if value in (None, ''):
        value = default
    return Decimal(str(value)).quantize(POINTS_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def calculate_memorization_points(page_count, thresholds=None, extra_page_rate=None):
    page_count = normalize_decimal(page_count)
    if page_count <= 0:
        return normalize_decimal(0)

    thresholds = thresholds or DEFAULT_MEMORIZATION_THRESHOLDS
    normalized_thresholds = {
        int(key): Decimal(str(value))
        for key, value in thresholds.items()
    }
    extra_page_rate = Decimal(str(extra_page_rate or DEFAULT_EXTRA_PAGE_RATE))

    whole_pages = int(page_count)
    fractional_pages = page_count - Decimal(whole_pages)

    base_points = Decimal('0')
    if whole_pages > 0:
        if whole_pages in normalized_thresholds:
            base_points = normalized_thresholds[whole_pages]
        else:
            highest_defined = max(normalized_thresholds.keys())
            base_points = normalized_thresholds[highest_defined]
            if whole_pages > highest_defined:
                base_points += Decimal(whole_pages - highest_defined) * extra_page_rate

    fractional_points = fractional_pages * extra_page_rate
    return normalize_decimal(base_points + fractional_points)

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
    total_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def teacher(self):
        if GroupSession.objects.filter(student=self).first():
            return GroupSession.objects.filter(student=self).first().teacher
        return None

    def __str__(self):
        return self.name

    def refresh_total_points(self):
        total = self.point_transactions.aggregate(total=Sum('points')).get('total') or Decimal('0')
        normalized_total = normalize_decimal(total)
        Student.objects.filter(id=self.id).update(total_points=normalized_total)
        self.total_points = normalized_total
        return self.total_points

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


class PointRuleDirection(models.TextChoices):
    ADDITION = 'addition', 'إضافة'
    DEDUCTION = 'deduction', 'خصم'


class PointCalculationMethod(models.TextChoices):
    FIXED = 'fixed', 'قيمة ثابتة'
    MEMORIZATION = 'memorization', 'احتساب الحفظ'


class PointTransactionInputMethod(models.TextChoices):
    MANUAL = 'manual', 'يدوي'
    DIRECT_PAGES = 'direct_pages', 'عدد الصفحات'
    SURAH = 'surah', 'السورة'
    SYSTEM = 'system', 'آلي'


class PointRule(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    direction = models.CharField(
        max_length=20,
        choices=PointRuleDirection.choices,
        default=PointRuleDirection.ADDITION,
    )
    calculation_method = models.CharField(
        max_length=30,
        choices=PointCalculationMethod.choices,
        default=PointCalculationMethod.FIXED,
    )
    default_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name

    def calculate_points(self, memorized_pages=None):
        if self.calculation_method == PointCalculationMethod.MEMORIZATION:
            thresholds = self.config.get('thresholds') or DEFAULT_MEMORIZATION_THRESHOLDS
            extra_page_rate = self.config.get('extra_page_rate', DEFAULT_EXTRA_PAGE_RATE)
            points = calculate_memorization_points(
                page_count=memorized_pages,
                thresholds=thresholds,
                extra_page_rate=extra_page_rate,
            )
        else:
            points = normalize_decimal(self.default_points)

        if self.direction == PointRuleDirection.DEDUCTION:
            points *= Decimal('-1')
        return normalize_decimal(points)


class Juz(models.Model):
    juz_number = models.PositiveIntegerField(unique=True)
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()
    total_pages = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['juz_number']

    def __str__(self):
        return f'جزء {self.juz_number}'


class SurahPageData(models.Model):
    name = models.CharField(max_length=100)
    surah_name_arabic = models.CharField(max_length=100, default='')
    surah_number = models.PositiveIntegerField()
    juz = models.CharField(max_length=100)
    juz_number = models.PositiveIntegerField(null=True, blank=True)
    start_page = models.PositiveIntegerField(null=True, blank=True)
    end_page = models.PositiveIntegerField(null=True, blank=True)
    start_page_decimal = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    end_page_decimal = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    pages = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['surah_number']
        unique_together = [('surah_number', 'juz')]

    def __str__(self):
        return f'{self.name} - جزء {self.juz}'


class StudentPointTransaction(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='point_transactions',
    )
    rule = models.ForeignKey(
        PointRule,
        on_delete=models.PROTECT,
        related_name='transactions',
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='point_transactions',
    )
    surah = models.ForeignKey(
        SurahPageData,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transactions',
    )
    input_method = models.CharField(
        max_length=30,
        choices=PointTransactionInputMethod.choices,
        default=PointTransactionInputMethod.MANUAL,
    )
    operation_date = models.DateField(default=date.today)
    memorized_pages = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-operation_date', '-id']

    def __str__(self):
        return f'{self.student.name} - {self.rule.name} - {self.points}'

    def clean(self):
        if self.rule.calculation_method == PointCalculationMethod.MEMORIZATION:
            if self.surah_id and not self.memorized_pages:
                self.memorized_pages = self.surah.pages
            if not self.memorized_pages:
                raise ValidationError('عمليات الحفظ تحتاج إلى عدد صفحات أو سورة.')
        elif self.surah_id and not self.memorized_pages:
            self.memorized_pages = self.surah.pages

    def recalculate_points(self, force=False):
        self.clean()
        # Recalculate points unless we force it or points are not the default (0)
        if force or (self.points == Decimal('0') or self.points is None):
            self.points = self.rule.calculate_points(memorized_pages=self.memorized_pages)
        if self.surah_id and not self.memorized_pages:
            self.memorized_pages = self.surah.pages
        self.points = normalize_decimal(self.points)
        return self.points

    @staticmethod
    def refresh_student_total(student_id):
        total = StudentPointTransaction.objects.filter(student_id=student_id).aggregate(
            total=Sum('points')
        ).get('total') or Decimal('0')
        Student.objects.filter(id=student_id).update(total_points=normalize_decimal(total))

    def save(self, *args, **kwargs):
        previous_student_id = None
        recalculate_needed = False
        if self.pk:
            previous_student_id = StudentPointTransaction.objects.filter(id=self.pk).values_list(
                'student_id',
                flat=True,
            ).first()
            # Get the old values to check if we need to recalculate
            old_transaction = StudentPointTransaction.objects.filter(id=self.pk).first()
            if old_transaction:
                # If rule or memorized pages changed, we need to recalculate
                if (old_transaction.rule_id != self.rule_id or 
                    old_transaction.memorized_pages != self.memorized_pages):
                    recalculate_needed = True
        
        # Decide whether to recalculate
        if recalculate_needed or not self.pk:
            self.recalculate_points(force=recalculate_needed)
        super().save(*args, **kwargs)
        self.refresh_student_total(self.student_id)
        if previous_student_id and previous_student_id != self.student_id:
            self.refresh_student_total(previous_student_id)

    def delete(self, *args, **kwargs):
        student_id = self.student_id
        super().delete(*args, **kwargs)
        self.refresh_student_total(student_id)


class ActivityType(models.TextChoices):
    TRIP = 'trip', 'رحلة'
    SWIMMING = 'swimming', 'مسبح'
    FOOTBALL = 'football', 'كرة قدم'
    HORSE_RIDING = 'horse_riding', 'ركوب خيل'
    OTHER = 'other', 'نشاط آخر'


class Activity(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    image = models.FileField(upload_to='activities/', blank=True, null=True)
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
    )
    other_activity_type = models.CharField(max_length=200, blank=True, default='')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities_created',
    )
    attended_students = models.ManyToManyField(
        Student,
        blank=True,
        related_name='activities',
    )

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.name


class Lesson(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons_created',
    )
    attended_students = models.ManyToManyField(
        Student,
        blank=True,
        related_name='lessons',
    )

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.name


class ActivityTeacherAssignment(models.Model):
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_assignments',
    )
    students = models.ManyToManyField(
        Student,
        blank=True,
        related_name='activity_teacher_assignments',
    )

    class Meta:
        ordering = ['teacher__username', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['activity', 'teacher'],
                name='unique_activity_teacher_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.activity.name} - {self.teacher.username}'


class LessonTeacherAssignment(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_assignments',
    )
    students = models.ManyToManyField(
        Student,
        blank=True,
        related_name='lesson_teacher_assignments',
    )

    class Meta:
        ordering = ['teacher__username', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['lesson', 'teacher'],
                name='unique_lesson_teacher_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.lesson.name} - {self.teacher.username}'


class TestType(models.TextChoices):
    EXTERNAL = 'external', 'وقف'
    INTERNAL = 'internal', 'داخلي'


class TestEvaluation(models.TextChoices):
    EXCELLENT = 'excellent', 'ممتاز'
    VERY_GOOD = 'very_good', 'جيد جداً'
    GOOD = 'good', 'جيد'
    AVERAGE = 'average', 'وسط'
    FAILED = 'failed', 'رسوب'


class Test(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='tests',
    )
    part_name = models.CharField(max_length=200)
    test_type = models.CharField(
        max_length=20,
        choices=TestType.choices,
        default=TestType.INTERNAL,
    )
    attempt_number = models.IntegerField(default=1)  # For internal tests only
    evaluation = models.CharField(
        max_length=20,
        choices=TestEvaluation.choices,
        null=True,
        blank=True,
    )
    points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tests',
    )
    test_date = models.DateField(default=date.today)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-test_date', '-id']

    def __str__(self):
        return f'{self.student.name} - {self.part_name} ({self.get_test_type_display()})'


class NoteType(models.TextChoices):
    GOOD = 'good', 'جيدة'
    BAD = 'bad', 'سيئة'


class Note(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    note_type = models.CharField(
        max_length=10,
        choices=NoteType.choices,
        default=NoteType.GOOD,
    )
    points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    note_text = models.TextField()
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    note_date = models.DateField(default=date.today)

    class Meta:
        ordering = ['-note_date', '-id']

    def __str__(self):
        return f'{self.student.name} - {self.get_note_type_display()}'


class MemorizationType(models.TextChoices):
    PAGE = 'page', 'صفحة'
    SURAH = 'surah', 'سورة'


class StudentBehavior(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='behaviors',
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_behaviors',
    )

    # Attendance
    has_attended = models.BooleanField(default=False)

    # Clothing & Cap
    has_clothing = models.BooleanField(default=False)
    has_cap = models.BooleanField(default=False)

    # Participation
    participation_type = models.CharField(
        max_length=20,
        choices=[('special', 'مميز'), ('normal', 'عادي')],
        null=True,
        blank=True,
    )

    # Penalties
    was_absent = models.BooleanField(default=False)
    no_recitation = models.BooleanField(default=False)
    left_early = models.BooleanField(default=False)

    behavior_date = models.DateField(default=date.today)
    total_points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        ordering = ['-behavior_date', '-id']

    def __str__(self):
        return f'{self.student.name} - {self.behavior_date}'

    def calculate_points(self):
        total = Decimal('0')

        # Attendance: +5 points if has_attended
        if self.has_attended:
            total += Decimal('5.00')

        # Clothing: +2.5 points if has_clothing
        if self.has_clothing:
            total += Decimal('2.50')

        # Cap: +2.5 points if has_cap
        if self.has_cap:
            total += Decimal('2.50')

        # Participation: +15 if special, +5 if normal
        if self.participation_type == 'special':
            total += Decimal('15.00')
        elif self.participation_type == 'normal':
            total += Decimal('5.00')

        # Penalties
        if self.was_absent:
            total -= Decimal('10.00')
        if self.no_recitation:
            total -= Decimal('5.00')
        if self.left_early:
            total -= Decimal('5.00')

        self.total_points = normalize_decimal(total)
        return self.total_points

    def save(self, *args, **kwargs):
        self.calculate_points()
        super().save(*args, **kwargs)

        # Clear old transactions for this behavior
        StudentPointTransaction.objects.filter(
            student=self.student,
            operation_date=self.behavior_date,
            metadata__has_key='student_behavior_id',
            metadata__student_behavior_id=self.id,
        ).delete()

        # Attendance transaction
        if self.has_attended:
            try:
                rule = PointRule.objects.get(code='attendance_on_time')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('5.00'),
                    notes='حضور صلاة العصر',
                    metadata={'student_behavior_id': self.id, 'type': 'attendance'},
                )
            except PointRule.DoesNotExist:
                pass

        # Clothing transaction
        if self.has_clothing:
            try:
                rule = PointRule.objects.get(code='dress_code')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('2.50'),
                    notes='اللباس',
                    metadata={'student_behavior_id': self.id, 'type': 'clothing'},
                )
            except PointRule.DoesNotExist:
                pass

        # Cap transaction
        if self.has_cap:
            try:
                rule = PointRule.objects.get(code='dress_code')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('2.50'),
                    notes='الطاقية',
                    metadata={'student_behavior_id': self.id, 'type': 'cap'},
                )
            except PointRule.DoesNotExist:
                pass

        # Participation transaction
        if self.participation_type:
            try:
                if self.participation_type == 'special':
                    rule = PointRule.objects.get(code='participation_special')
                    points = Decimal('15.00')
                else:
                    rule = PointRule.objects.get(code='participation_regular')
                    points = Decimal('5.00')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=points,
                    notes='مشاركة ' + ('مميزة' if self.participation_type == 'special' else 'عادية'),
                    metadata={'student_behavior_id': self.id, 'type': 'participation'},
                )
            except PointRule.DoesNotExist:
                pass

        # Absence penalty transaction
        if self.was_absent:
            try:
                rule = PointRule.objects.get(code='absence')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('-10.00'),
                    notes='غياب',
                    metadata={'student_behavior_id': self.id, 'type': 'absence_penalty'},
                )
            except PointRule.DoesNotExist:
                pass

        # No recitation penalty transaction
        if self.no_recitation:
            try:
                rule = PointRule.objects.get(code='present_without_recitation')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('-5.00'),
                    notes='حضور بلا تسميع',
                    metadata={'student_behavior_id': self.id, 'type': 'no_recitation_penalty'},
                )
            except PointRule.DoesNotExist:
                pass

        # Left early penalty transaction
        if self.left_early:
            try:
                rule = PointRule.objects.get(code='early_leave')
                StudentPointTransaction.objects.create(
                    student=self.student,
                    rule=rule,
                    supervisor=self.teacher,
                    operation_date=self.behavior_date,
                    points=Decimal('-5.00'),
                    notes='خروج قبل الوقت',
                    metadata={'student_behavior_id': self.id, 'type': 'left_early_penalty'},
                )
            except PointRule.DoesNotExist:
                pass

        # Refresh student's total points
        self.student.refresh_total_points()


class GoodBehavior(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='good_behaviors',
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='good_behaviors',
    )
    week_start_date = models.DateField()
    points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15,
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateField(default=date.today)

    class Meta:
        ordering = ['-week_start_date', '-id']

    def __str__(self):
        return f'{self.student.name} - سلوك حسن ({self.week_start_date})'


class SystemSettings(models.Model):
    version = models.CharField(max_length=50, default='1.0.0')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'System Settings'
        
    def __str__(self):
        return f'System Settings v{self.version}'
    
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={'version': '1.0.0'})
        return obj
