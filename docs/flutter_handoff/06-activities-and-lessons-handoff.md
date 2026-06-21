# 06 - Activities And Lessons Handoff

هذا الملف يشرح الـ APIs الجديدة الخاصة بالنشاطات والدروس لمطور Flutter، مع الفلاتر المدعومة والعقود الرسمية الحالية.

## المتطلبات العامة

- كل المسارات التالية محمية وتحتاج:
  - `Authorization: Bearer <token>`
- المشرف يرى فقط البيانات التي أنشأها هو.
- الأدمن الأعلى يمكنه رؤية كل البيانات.

## 1. Activities

### Create Activity
- `POST /api/activities`

### Body

- نوع الطلب الموصى به: `multipart/form-data`

### Fields

- `name`: اسم النشاط.
- `date`: تاريخ النشاط بصيغة `YYYY-MM-DD`.
- `image`: ملف صورة فعلي مرفوع من التطبيق.
- `activity_type`: نوع النشاط.
- `other_activity_type`: مطلوب فقط عندما تكون قيمة `activity_type` هي `other`.
- `teacher_groups`: JSON يحدد أكثر من أستاذ، وكل أستاذ معه طلابه.

### Example `teacher_groups`

```json
[
  {
    "teacher_id": 2,
    "student_ids": [1, 2]
  },
  {
    "teacher_id": 3,
    "student_ids": [7, 8]
  }
]
```

### قيم `activity_type`

- واحد من القيم التالية:
  - `trip`
  - `swimming`
  - `football`
  - `horse_riding`
  - `other`

### Example Response Data

```json
{
  "activity": {
    "id": 4,
    "name": "رحلة صيفية",
    "date": "2026-06-19",
    "image": "https://example.com/media/activities/trip.jpg",
    "activity_type": "trip",
    "activity_type_label": "رحلة",
    "other_activity_type": "",
    "resolved_activity_type": "رحلة",
    "attend_student_ids": [1, 2, 3],
    "attended_students": [
      {
        "id": 1,
        "name": "Ahmad"
      }
    ],
    "teacher_groups": [
      {
        "id": 5,
        "teacher": {
          "id": 2,
          "username": "teacher_1"
        },
        "student_ids": [1, 2],
        "students": [
          {
            "id": 1,
            "name": "Ahmad"
          }
        ]
      }
    ]
  }
}
```

### Update Activity
- `PUT /api/activities`

### Body

- نوع الطلب الموصى به: `multipart/form-data`

### Fields

- `activity_id`: معرف النشاط المطلوب تعديله.
- نفس الحقول المستخدمة في الإنشاء:
  - `name`
  - `date`
  - `image`
  - `activity_type`
  - `other_activity_type`
  - `teacher_groups`

### Example

```text
PUT /api/activities
```

```json
{
  "activity_id": 4,
  "name": "رحلة صيفية معدلة",
  "date": "2026-06-20",
  "activity_type": "trip",
  "teacher_groups": [
    {
      "teacher_id": 2,
      "student_ids": [1, 2]
    },
    {
      "teacher_id": 3,
      "student_ids": [7]
    }
  ]
}
```

### سلوك التعديل

- الأدمن يمكنه تعديل كل `teacher_groups` دفعة واحدة.
- الأستاذ العادي يمكنه تعديل النشاط إذا كان ضمن `teacher_groups` الخاصة به.
- عند تعديل الأستاذ العادي، تبقى مجموعات الأساتذة الآخرين كما هي ولا يتم حذفها.

### Get Activities
- `GET /api/activities`

### الفلاتر المدعومة

- `activity_type`
- `teacher_id`
- `student_id`
- `date_from`
- `date_to`

### Example

```text
GET /api/activities?activity_type=trip&teacher_id=2&date_from=2026-06-01&date_to=2026-06-30
```

### ملاحظات التوافق

- ما زال المساران التاليان يعملان لنفس الغرض:
  - `GET أو POST /api/get/activities`
  - `POST /api/add/activities`
- كما أن `PUT /api/add/activities` يعمل أيضًا لنفس عملية التعديل.

## 2. Lessons

### Create Lesson
- `POST /api/lessons`

### Body

```json
{
  "name": "درس التجويد",
  "date": "2026-06-20",
  "teacher_groups": [
    {
      "teacher_id": 2,
      "student_ids": [1, 3]
    },
    {
      "teacher_id": 3,
      "student_ids": [7]
    }
  ]
}
```

### الحقول

- `name`: اسم الدرس.
- `date`: تاريخ الدرس بصيغة `YYYY-MM-DD`.
- `teacher_groups`: مجموعة الأساتذة مع طلاب كل أستاذ ضمن هذا الدرس.

### Example Response Data

```json
{
  "lesson": {
    "id": 8,
    "name": "درس التجويد",
    "date": "2026-06-20",
    "attend_student_ids": [1, 3],
    "attended_students": [
      {
        "id": 1,
        "name": "Ahmad"
      }
    ],
    "teacher_groups": [
      {
        "id": 9,
        "teacher": {
          "id": 2,
          "username": "teacher_1"
        },
        "student_ids": [1, 3],
        "students": [
          {
            "id": 1,
            "name": "Ahmad"
          }
        ]
      }
    ]
  }
}
```

### Update Lesson
- `PUT /api/lessons`

### Body

```json
{
  "lesson_id": 8,
  "name": "درس التجويد المعدل",
  "date": "2026-06-21",
  "teacher_groups": [
    {
      "teacher_id": 2,
      "student_ids": [1, 3]
    },
    {
      "teacher_id": 3,
      "student_ids": [7]
    }
  ]
}
```

### الحقول

- `lesson_id`: معرف الدرس المطلوب تعديله.
- نفس الحقول المستخدمة في الإنشاء:
  - `name`
  - `date`
  - `teacher_groups`

### سلوك التعديل

- الأدمن يمكنه تعديل كل `teacher_groups` داخل الدرس.
- الأستاذ العادي يمكنه تعديل الدرس إذا كان مخصصًا له ضمن المجموعات.
- عند تعديل الأستاذ العادي، تبقى مجموعات الأساتذة الآخرين محفوظة كما هي.

### Get Lessons
- `GET /api/lessons`

### الفلاتر المدعومة

- `teacher_id`
- `student_id`
- `date_from`
- `date_to`

### Example

```text
GET /api/lessons?teacher_id=2&student_id=1&date_from=2026-06-01
```

### ملاحظات التوافق

- ما زال المساران التاليان يعملان لنفس الغرض:
  - `GET أو POST /api/get/lessons`
  - `POST /api/add/lessons`
- كما أن `PUT /api/add/lessons` يعمل أيضًا لنفس عملية التعديل.

## 3. Student Info Update

- `POST /api/student-info` أصبح الآن يعيد:
  - `activities`
  - `lessons`

- كل عنصر ضمن `activities` و`lessons` يأخذ نفس البنية المعتمدة أعلاه.

## 4. توصيات Flutter

- خزّن `activity_type` كقيمة ثابتة داخل التطبيق، واعرض `resolved_activity_type` مباشرة للمستخدم.
- إذا تم اختيار `other` في واجهة الإضافة، أظهر حقل نصي إضافي وأرسله في `other_activity_type`.
- عند إنشاء نشاط من Flutter استخدم `multipart/form-data` لأن الصورة الآن ملف فعلي.
- أرسل `teacher_groups` كنص JSON إذا كانت مكتبة الرفع لا تدعم nested objects مباشرة داخل `multipart`.
