import json

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import (
    Activity, ActivityTeacherAssignment, GroupSession, Lesson,
    LessonTeacherAssignment, MemorizedPages, Page, PointRule, Student,
    StudentAttend, StudentPointTransaction, SurahPageData, User
)


class ApiContractTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username='admin', password='secret123', permission=0)
        self.teacher = User.objects.create(username='teacher', password='secret123', permission=2)
        self.other_teacher = User.objects.create(username='teacher2', password='secret123', permission=2)

        self.student = Student.objects.create(
            name='Ahmad',
            father_name='Ali',
            address='Damascus',
            school_name='School',
            birth_date='2010-01-01',
            phone_number='+963999999999',
        )
        self.other_student = Student.objects.create(
            name='Mahmoud',
            father_name='Omar',
            address='Homs',
            school_name='School 2',
            birth_date='2011-01-01',
            phone_number='+963988888888',
        )

        GroupSession.objects.create(teacher=self.teacher, student=self.student)
        GroupSession.objects.create(teacher=self.other_teacher, student=self.other_student)
        self.page_1 = Page.objects.create(name='Page 1', quant=1, section=1)
        self.page_2 = Page.objects.create(name='Page 2', quant=1, section=1)

    def post_json(self, path, payload, token=None):
        headers = {}
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type='application/json',
            **headers,
        )

    def delete_json(self, path, payload, token=None):
        headers = {}
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.delete(
            path,
            data=json.dumps(payload),
            content_type='application/json',
            **headers,
        )

    def put_json(self, path, payload, token=None):
        headers = {}
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.put(
            path,
            data=json.dumps(payload),
            content_type='application/json',
            **headers,
        )

    def post_multipart(self, path, payload, token=None):
        headers = {}
        if token:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.post(path, data=payload, **headers)

    def login_and_get_token(self, username='teacher', password='secret123'):
        response = self.post_json('/api/login', {
            'username': username,
            'password': password,
        })
        data = response.json()
        return response, data['data']['token']

    def test_login_returns_unified_structure(self):
        response = self.post_json('/api/login', {
            'username': 'teacher',
            'password': 'secret123',
        })

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['message'], 'تم تسجيل الدخول بنجاح')
        self.assertIn('token', payload['data'])
        self.assertEqual(payload['data']['user']['username'], 'teacher')
        self.assertEqual(payload['errors'], {})

    def test_students_endpoint_requires_token_and_returns_unified_error(self):
        response = self.post_json('/api/students', {})

        payload = response.json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(payload['success'])
        self.assertIn('message', payload)
        self.assertIn('errors', payload)
        self.assertEqual(payload['data'], {})

    def test_students_endpoint_returns_unified_success_response(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/students', {}, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['message'], 'تم جلب الطلاب بنجاح')
        self.assertEqual(len(payload['data']['students']), 1)
        self.assertEqual(payload['data']['students'][0]['name'], 'Ahmad')

    def test_token_scopes_teacher_to_his_students_only(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/student-info', {
            'student_id': self.other_student.id,
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['message'], 'لا توجد بيانات')
        self.assertEqual(payload['data'], {})

    def test_version_endpoint_is_unified_and_public(self):
        response = self.client.get('/api/version')
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['version'], '1.0.0')

    def test_student_info_requires_student_id(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/student-info', {
            'name': 'Ahmad',
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(payload['success'])
        self.assertIn('student_id', payload['errors'])

    def test_student_info_returns_data_with_student_id(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/student-info', {
            'student_id': self.student.id,
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['student']['id'], self.student.id)

    def test_attendance_accepts_student_ids_only(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/add/attend', {
            'attend_student_ids': [self.student.id],
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['attend_count'], 1)
        self.assertTrue(StudentAttend.objects.filter(student=self.student, is_attend=True).exists())

    def test_pages_accepts_page_ids_only(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/pages', {
            'student_id': self.student.id,
            'page_ids': [self.page_1.id, self.page_2.id],
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['page_ids'], [self.page_1.id, self.page_2.id])
        self.assertEqual(
            MemorizedPages.objects.filter(student=self.student).count(),
            2,
        )

    def test_delete_memorized_page_uses_memorized_page_id(self):
        _, token = self.login_and_get_token()
        memorized = MemorizedPages.objects.create(
            student=self.student,
            page=self.page_1,
            date='2026-06-19',
        )

        response = self.delete_json('/api/pages', {
            'student_id': self.student.id,
            'memorized_page_id': memorized.id,
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['memorized_page_id'], memorized.id)
        self.assertFalse(MemorizedPages.objects.filter(id=memorized.id).exists())

    def test_create_and_filter_activities(self):
        _, token = self.login_and_get_token()

        create_response = self.post_multipart('/api/activities', {
            'name': 'رحلة صيفية',
            'date': '2026-06-19',
            'activity_type': 'trip',
            'image': SimpleUploadedFile('trip.jpg', b'fake-image-content', content_type='image/jpeg'),
            'teacher_groups': json.dumps([
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                }
            ]),
        }, token=token)
        create_payload = create_response.json()

        self.assertEqual(create_response.status_code, 201)
        self.assertTrue(create_payload['success'])
        self.assertEqual(create_payload['data']['activity']['activity_type'], 'trip')
        self.assertIsNotNone(create_payload['data']['activity']['image'])
        self.assertEqual(
            create_payload['data']['activity']['attend_student_ids'],
            [self.student.id],
        )
        self.assertEqual(
            create_payload['data']['activity']['teacher_groups'][0]['teacher']['id'],
            self.teacher.id,
        )

        list_response = self.client.get(
            '/api/activities',
            {'activity_type': 'trip', 'teacher_id': self.teacher.id},
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        list_payload = list_response.json()

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_payload['data']['activities']), 1)
        self.assertEqual(list_payload['data']['activities'][0]['name'], 'رحلة صيفية')

    def test_activity_other_type_requires_custom_value(self):
        _, token = self.login_and_get_token()

        response = self.post_json('/api/activities', {
            'name': 'نشاط خاص',
            'date': '2026-06-19',
            'activity_type': 'other',
            'attend_student_ids': [self.student.id],
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertIn('other_activity_type', payload['errors'])

    def test_update_activity_accepts_teacher_groups(self):
        _, token = self.login_and_get_token(username='admin', password='secret123')

        create_response = self.post_json('/api/activities', {
            'name': 'نشاط مشترك',
            'date': '2026-06-19',
            'activity_type': 'trip',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                }
            ],
        }, token=token)
        create_payload = create_response.json()
        activity_id = create_payload['data']['activity']['id']

        update_response = self.put_json('/api/activities', {
            'activity_id': activity_id,
            'name': 'نشاط مشترك معدل',
            'date': '2026-06-20',
            'activity_type': 'trip',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                },
                {
                    'teacher_id': self.other_teacher.id,
                    'student_ids': [self.other_student.id],
                }
            ],
        }, token=token)
        payload = update_response.json()

        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['activity']['name'], 'نشاط مشترك معدل')
        self.assertEqual(len(payload['data']['activity']['teacher_groups']), 2)
        self.assertEqual(
            sorted(payload['data']['activity']['attend_student_ids']),
            sorted([self.student.id, self.other_student.id]),
        )

    def test_create_lessons_and_student_info_includes_them(self):
        _, token = self.login_and_get_token()

        lesson_response = self.post_json('/api/lessons', {
            'name': 'درس التجويد',
            'date': '2026-06-20',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                }
            ],
        }, token=token)
        lesson_payload = lesson_response.json()

        self.assertEqual(lesson_response.status_code, 201)
        self.assertTrue(lesson_payload['success'])
        self.assertEqual(lesson_payload['data']['lesson']['name'], 'درس التجويد')
        self.assertEqual(
            lesson_payload['data']['lesson']['teacher_groups'][0]['teacher']['id'],
            self.teacher.id,
        )

        activity = Activity.objects.create(
            name='كرة قدم',
            date='2026-06-21',
            activity_type='football',
            created_by=self.teacher,
        )
        activity.attended_students.add(self.student)
        activity_assignment = ActivityTeacherAssignment.objects.create(
            activity=activity,
            teacher=self.teacher,
        )
        activity_assignment.students.add(self.student)

        student_info_response = self.post_json('/api/student-info', {
            'student_id': self.student.id,
        }, token=token)
        student_payload = student_info_response.json()

        self.assertEqual(student_info_response.status_code, 200)
        self.assertEqual(len(student_payload['data']['student']['activities']), 1)
        self.assertEqual(len(student_payload['data']['student']['lessons']), 1)
        self.assertEqual(
            student_payload['data']['student']['lessons'][0]['name'],
            'درس التجويد',
        )
        self.assertEqual(
            student_payload['data']['student']['activities'][0]['teacher_groups'][0]['teacher']['id'],
            self.teacher.id,
        )

    def test_admin_can_create_lesson_for_multiple_teachers(self):
        _, token = self.login_and_get_token(username='admin', password='secret123')

        response = self.post_json('/api/lessons', {
            'name': 'درس مشترك',
            'date': '2026-06-22',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                },
                {
                    'teacher_id': self.other_teacher.id,
                    'student_ids': [self.other_student.id],
                }
            ],
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(payload['data']['lesson']['teacher_groups']), 2)
        self.assertEqual(
            sorted(payload['data']['lesson']['attend_student_ids']),
            sorted([self.student.id, self.other_student.id]),
        )

    def test_update_lesson_accepts_teacher_groups(self):
        _, token = self.login_and_get_token(username='admin', password='secret123')

        create_response = self.post_json('/api/lessons', {
            'name': 'درس مشترك',
            'date': '2026-06-22',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                }
            ],
        }, token=token)
        create_payload = create_response.json()
        lesson_id = create_payload['data']['lesson']['id']

        update_response = self.put_json('/api/lessons', {
            'lesson_id': lesson_id,
            'name': 'درس مشترك معدل',
            'date': '2026-06-23',
            'teacher_groups': [
                {
                    'teacher_id': self.teacher.id,
                    'student_ids': [self.student.id],
                },
                {
                    'teacher_id': self.other_teacher.id,
                    'student_ids': [self.other_student.id],
                }
            ],
        }, token=token)
        payload = update_response.json()

        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['lesson']['name'], 'درس مشترك معدل')
        self.assertEqual(len(payload['data']['lesson']['teacher_groups']), 2)
        self.assertEqual(
            sorted(payload['data']['lesson']['attend_student_ids']),
            sorted([self.student.id, self.other_student.id]),
        )

    def test_points_rules_and_surahs_endpoints_return_seeded_data(self):
        _, token = self.login_and_get_token(username='admin', password='secret123')

        rules_response = self.client.get(
            '/api/points/rules',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        surahs_response = self.client.get(
            '/api/points/surahs',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        rules_payload = rules_response.json()
        surahs_payload = surahs_response.json()

        self.assertEqual(rules_response.status_code, 200)
        self.assertTrue(any(rule['code'] == 'memorization_pages' for rule in rules_payload['data']['rules']))
        self.assertEqual(surahs_response.status_code, 200)
        self.assertTrue(any(surah['name'] == 'النبأ' for surah in surahs_payload['data']['surahs']))

    def test_create_points_transaction_with_direct_pages_calculates_points(self):
        _, token = self.login_and_get_token()
        rule = PointRule.objects.get(code='memorization_pages')

        response = self.post_json('/api/points/transactions', {
            'student_id': self.student.id,
            'rule_id': rule.id,
            'memorized_pages': '2.50',
            'notes': 'حفظ يومي',
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload['data']['transaction']['points'], '17.50')

        self.student.refresh_from_db()
        self.assertEqual(str(self.student.total_points), '17.50')

    def test_create_points_transaction_with_surah_uses_surah_pages(self):
        _, token = self.login_and_get_token()
        rule = PointRule.objects.get(code='memorization_pages')
        surah = SurahPageData.objects.get(name='النبأ')

        response = self.post_json('/api/points/transactions', {
            'student_id': self.student.id,
            'rule_id': rule.id,
            'surah_id': surah.id,
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload['data']['transaction']['memorized_pages'], '1.50')
        self.assertEqual(payload['data']['transaction']['points'], '7.50')

    def test_update_points_transaction_recalculates_student_total(self):
        _, token = self.login_and_get_token()
        rule = PointRule.objects.get(code='memorization_pages')
        transaction = StudentPointTransaction.objects.create(
            student=self.student,
            rule=rule,
            supervisor=self.teacher,
            memorized_pages='1.50',
            input_method='direct_pages',
        )

        response = self.put_json('/api/points/transactions', {
            'transaction_id': transaction.id,
            'student_id': self.student.id,
            'rule_id': rule.id,
            'memorized_pages': '3.50',
            'notes': 'تعديل الحفظ',
        }, token=token)
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['data']['transaction']['points'], '27.50')

        self.student.refresh_from_db()
        self.assertEqual(str(self.student.total_points), '27.50')

    def test_points_reports_include_ranking_and_memorization_stats(self):
        _, token = self.login_and_get_token(username='admin', password='secret123')
        memorization_rule = PointRule.objects.get(code='memorization_pages')
        absence_rule = PointRule.objects.get(code='absence')
        surah = SurahPageData.objects.get(name='النبأ')

        StudentPointTransaction.objects.create(
            student=self.student,
            rule=memorization_rule,
            supervisor=self.admin,
            memorized_pages='2.50',
            input_method='direct_pages',
            operation_date='2026-06-20',
        )
        StudentPointTransaction.objects.create(
            student=self.other_student,
            rule=absence_rule,
            supervisor=self.admin,
            input_method='manual',
            operation_date='2026-06-20',
        )
        StudentPointTransaction.objects.create(
            student=self.student,
            rule=memorization_rule,
            supervisor=self.admin,
            surah=surah,
            input_method='surah',
            operation_date='2026-06-21',
        )

        response = self.post_json('/api/points/reports', {}, token=token)
        payload = response.json()
        report = payload['data']['report']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(report['group_total'], '15.00')
        self.assertEqual(report['students_ranking'][0]['student_id'], self.student.id)
        self.assertEqual(report['memorization_by_pages']['total_pages'], '4.00')
        self.assertTrue(any(item['surah__name'] == 'النبأ' for item in report['memorization_by_surahs']))
