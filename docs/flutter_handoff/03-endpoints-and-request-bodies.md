# 03 - Endpoints And Request Bodies After Refactor

هذا الملف يشرح العقود الحالية المهمة لمطور Flutter بعد التعديلات الأخيرة.

## 1. Login

### Endpoint
- `POST /api/login`

### Body

```json
{
  "username": "teacher",
  "password": "secret123"
}
```

### ملاحظات
- يرجع `token`.
- خزّن التوكن واستخدمه في باقي المسارات المحمية.

## 2. Get My Students

### Endpoint
- `POST /api/students`

### Body

```json
{}
```

### ملاحظات
- لم يعد هناك حاجة لإرسال `teacher_id`.
- المشرف يتم تحديده من التوكن مباشرة.

## 3. Get Student Info

### Endpoint
- `POST /api/student-info`

### Body

```json
{
  "student_id": 10
}
```

### التغيير المهم
- سابقًا كان يمكن الاعتماد على الاسم.
- الآن الاعتماد الرسمي هو `student_id`.

## 4. Get Teacher Student Names

### Endpoint
- `POST /api/admin-students`

### Body

```json
{}
```

### ملاحظات
- يرجع أسماء الطلاب التابعين للمشرف الحالي من التوكن.

## 5. Save Today Attendance

### Endpoint
- `POST /api/add/attend`

### Body

```json
{
  "attend_student_ids": [10, 11, 12]
}
```

### ملاحظات
- لا ترسل `teacher_id`.
- فقط أرسل معرفات الطلاب الحاضرين.
- الطلاب غير الموجودين في القائمة يتم اعتبارهم غياب.

## 6. Get Today Attendance

### Endpoint
- `POST /api/get/attend`

### Body

```json
{}
```

### مثال Response Data

```json
{
  "date": "2026-06-19",
  "attend": ["Ahmad", "Mahmoud"],
  "abs": ["Ali"]
}
```

## 7. Delete Attendance By Date

### Endpoint
- `DELETE /api/attend`

### Body

```json
{
  "date": "2026-06-19"
}
```

## 8. Get All Attendance Records

### Endpoint
- `POST /api/get/all/attend`

### Body

```json
{}
```

## 9. Get Unmemorized Pages

### Endpoint
- `POST /api/unmemorized-pages`

### Body

```json
{
  "student_id": 10,
  "page_archive": 1
}
```

### ملاحظات
- `page_archive` تعني رقم القسم.

## 10. Add Memorized Pages

### Endpoint
- `POST /api/pages`

### Body

```json
{
  "student_id": 10,
  "page_ids": [1, 2, 3]
}
```

### التغيير المهم
- سابقًا كان النظام يعتمد على أسماء الصفحات.
- الآن الاعتماد الرسمي هو `page_ids`.

## 11. Delete Memorized Page Record

### Endpoint
- `DELETE /api/pages`

### Body

```json
{
  "student_id": 10,
  "memorized_page_id": 25
}
```

### التغيير المهم
- الحذف الآن يعتمد على `memorized_page_id`.
- لم نعد نحتاج `page name` أو `date` أو `page_archive` للحذف.

## 12. Get App Version

### Endpoint
- `GET /api/version`

### Body
- لا يوجد

## 13. Get Hadiths

### Endpoint
- `GET /api/ahadith`

### Body
- لا يوجد

## أهم الفروقات عن القديم

### لم يعد مطلوبًا
- `admin_name`
- `teacher_id` في مسارات المشرف اليومية
- `student name` بدل `student_id`
- `page name` بدل `page_ids`

### أصبح مطلوبًا
- `Authorization: Bearer <token>`
- `student_id` في مسارات الطالب
- `page_ids` عند إضافة صفحات
- `memorized_page_id` عند حذف سجل حفظ

## توصية لمطور Flutter

- أنشئ layer واحدة للهيدر تضيف التوكن تلقائيًا.
- أنشئ models موحدة للـ response.
- لا تبنِ أي شاشة جديدة على الـ contract القديم.
