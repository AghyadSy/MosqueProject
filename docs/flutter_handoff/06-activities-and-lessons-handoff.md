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

```json
{
  "name": "رحلة صيفية",
  "date": "2026-06-19",
  "image": "https://example.com/trip.jpg",
  "activity_type": "trip",
  "other_activity_type": "",
  "attend_student_ids": [1, 2, 3]
}
```

### الحقول

- `name`: اسم النشاط.
- `date`: تاريخ النشاط بصيغة `YYYY-MM-DD`.
- `image`: اختياري. يمكن أن يكون رابط صورة مباشر أو `data URI` إذا كان التطبيق يرسل Base64.
- `activity_type`: واحد من القيم التالية:
  - `trip`
  - `swimming`
  - `football`
  - `horse_riding`
  - `other`
- `other_activity_type`: مطلوب فقط عندما تكون قيمة `activity_type` هي `other`.
- `attend_student_ids`: قائمة معرفات الطلاب الذين حضروا النشاط.

### Example Response Data

```json
{
  "activity": {
    "id": 4,
    "name": "رحلة صيفية",
    "date": "2026-06-19",
    "image": "https://example.com/trip.jpg",
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
    ]
  }
}
```

### Get Activities
- `GET /api/activities`

### الفلاتر المدعومة

- `activity_type`
- `student_id`
- `date_from`
- `date_to`

### Example

```text
GET /api/activities?activity_type=trip&date_from=2026-06-01&date_to=2026-06-30
```

### ملاحظات التوافق

- ما زال المساران التاليان يعملان لنفس الغرض:
  - `GET أو POST /api/get/activities`
  - `POST /api/add/activities`

## 2. Lessons

### Create Lesson
- `POST /api/lessons`

### Body

```json
{
  "name": "درس التجويد",
  "date": "2026-06-20",
  "attend_student_ids": [1, 3]
}
```

### الحقول

- `name`: اسم الدرس.
- `date`: تاريخ الدرس بصيغة `YYYY-MM-DD`.
- `attend_student_ids`: قائمة معرفات الطلاب الذين حضروا الدرس.

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
    ]
  }
}
```

### Get Lessons
- `GET /api/lessons`

### الفلاتر المدعومة

- `student_id`
- `date_from`
- `date_to`

### Example

```text
GET /api/lessons?student_id=1&date_from=2026-06-01
```

### ملاحظات التوافق

- ما زال المساران التاليان يعملان لنفس الغرض:
  - `GET أو POST /api/get/lessons`
  - `POST /api/add/lessons`

## 3. Student Info Update

- `POST /api/student-info` أصبح الآن يعيد:
  - `activities`
  - `lessons`

- كل عنصر ضمن `activities` و`lessons` يأخذ نفس البنية المعتمدة أعلاه.

## 4. توصيات Flutter

- خزّن `activity_type` كقيمة ثابتة داخل التطبيق، واعرض `resolved_activity_type` مباشرة للمستخدم.
- إذا تم اختيار `other` في واجهة الإضافة، أظهر حقل نصي إضافي وأرسله في `other_activity_type`.
- للتعامل مع الصور بسرعة:
  - الأفضل إرسال رابط صورة جاهز إذا كان متاحًا.
  - ويمكن إرسال `data URI` إذا كان التطبيق يحول الصورة إلى Base64.
