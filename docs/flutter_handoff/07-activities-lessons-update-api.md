# 07 - Activities And Lessons Update API

هذا الملف يشرح التغيير الجديد على واجهات النشاطات والدروس بحيث أصبح الإيديت يدعم `teacher_groups` مثل الإنشاء.

## المسارات الجديدة المدعومة

- `PUT /api/activities`
- `PUT /api/add/activities`
- `PUT /api/lessons`
- `PUT /api/add/lessons`

## 1. Update Activity

### Body

- نوع الطلب الموصى به: `multipart/form-data`

### الحقول

- `activity_id`: معرف النشاط.
- `name`: اسم النشاط.
- `date`: تاريخ النشاط بصيغة `YYYY-MM-DD`.
- `image`: صورة جديدة اختيارية. إذا لم يتم إرسالها تبقى الصورة القديمة كما هي.
- `activity_type`: نوع النشاط.
- `other_activity_type`: مطلوب فقط عند `activity_type=other`.
- `teacher_groups`: JSON يحدد الأساتذة وطلاب كل أستاذ.

### Example

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

## 2. Update Lesson

### Body

- نوع الطلب: `application/json`

### الحقول

- `lesson_id`: معرف الدرس.
- `name`: اسم الدرس.
- `date`: تاريخ الدرس بصيغة `YYYY-MM-DD`.
- `teacher_groups`: مصفوفة الأساتذة وطلاب كل أستاذ.

### Example

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

## 3. سلوك الصلاحيات

- الأدمن يمكنه تعديل كل المجموعات داخل النشاط أو الدرس.
- الأستاذ العادي يمكنه تعديل السجل إذا كان ضمن مجموعاته الحالية.
- عند تعديل الأستاذ العادي، تبقى مجموعات الأساتذة الآخرين محفوظة ولا يتم حذفها.

## 4. ملاحظات مهمة

- بنية `teacher_groups` في الإيديت هي نفسها تمامًا في الإنشاء.
- الاستجابة بعد الإيديت تعيد نفس البنية المعتادة داخل `activity` أو `lesson`.
- تم تحديث ملف Postman collection ليتضمن:
  - `Update Activity`
  - `Update Lesson`
  - المتغيرين `activity_id` و `lesson_id`
