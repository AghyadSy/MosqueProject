# 08 - Points System & Student Activities Handoff

هذا الملف يشرح لمطور Flutter كيفية ربط نظام نقاط الطلاب الجديد وجميع ميزات الاختبارات، الملاحظات، وسلوكيات الطلاب داخل التطبيق.

## نظرة عامة
- تم إضافة نظام نقاط مركزي مستقل.
- كل إضافة أو خصم يتم تسجيله كسجل عملية مستقل.
- كل طالب أصبح لديه `total_points`.
- تم إضافة أربع ميزات جديدة لتتبع تقدم الطلاب بشكل مفصّل:
  1. **الاختبارات**: تتبع اختبارات الوقف (external) والداخلية.
  2. **الملاحظات**: تتبع الملاحظات الجيدة والسيئة مع نقاط.
  3. **سلوكيات الطالب**: تتبع سلوك الطالب اليومي (حفظ، حضور، ملابس، مشاركة، عقوبات).
  4. **سلوك حسن**: تتبع سلوك الطالب الحسن الأسبوعي.
- كل ميزة تحسب نقاط تلقائياً وتحدث `total_points` للطالب.
- يتم إنشاء `StudentPointTransaction` تلقائياً لكل عملية، ويمكن جلب هذه العمليات من `GET /api/points/transactions?student_id=X`.
- لإحصاء نقاط كل طالب وبيانات الإضافات والخصومات، استخدم:
  - قائمة الطلاب مع مجموع نقاطهم: `POST /api/students`
  - تفاصيل الإضافات والخصومات لطالب معين: `GET /api/points/transactions?student_id=X`
  - تقرير كامل لنقاط الطالب: `POST /api/points/reports` مع `{"student_id": X}`
- الحفظ يدعم طريقتين:
  - إدخال عدد الصفحات مباشرة.
  - اختيار سورة، ثم جلب عدد الصفحات تلقائياً من قاعدة بيانات السور.

## ما الذي يظهر في التطبيق
- إجمالي نقاط الطالب.
- سجل كامل لعمليات الإضافة والخصم.
- شاشة/تبويب لإضافة عملية نقاط جديدة.
- شاشة تقارير تعرض:
  - إجمالي نقاط الطالب.
  - إجمالي نقاط الحلقة.
  - ترتيب الطلاب.
  - سجل العمليات.
  - إحصائيات الحفظ بالصفحات.
  - إحصائيات الحفظ بالسور.
  - ملخص يومي وأسبوعي وشهري.
- شاشات جديدة للاختبارات، الملاحظات، السلوكيات، وسلوك حسن.

---

## الجزء الأول: نظام النقاط الأساسي

### 1. Get Point Rules
#### Endpoint
- `GET /api/points/rules`

#### الاستخدام
- استدعِ هذا المسار أولاً عند فتح شاشة نظام النقاط.
- يعيد جميع قواعد الإضافة والخصم الجاهزة من الباك.
- استخدم `code` كمعرف منطقي داخل التطبيق.

#### مثال Response Data
```json
{
  "rules": [
    {
      "id": 2,
      "code": "memorization_pages",
      "name": "الحفظ",
      "category": "الحفظ",
      "direction": "addition",
      "calculation_method": "memorization",
      "default_points": "0.00",
      "config": {
        "thresholds": {
          "1": "5",
          "2": "15",
          "3": "25",
          "4": "40"
        },
        "extra_page_rate": "10"
      },
      "is_active": true,
      "sort_order": 20
    }
  ]
}
```

---

### 2. Get Surahs For Memorization
#### Endpoint
- `GET /api/points/surahs`

#### الاستخدام
- استخدمه عندما يختار المستخدم "الحفظ بالسورة".
- يمكن عرض السور grouped by `juz`.
- القيمة `pages` مفيدة للعرض فقط، لأن الباك سيحتسبها أيضاً عند الإرسال.

#### مثال Response Data
```json
{
  "surahs": [
    {
      "id": 12,
      "name": "النبأ",
      "surah_number": 78,
      "juz": "عم",
      "pages": "1.50",
      "is_active": true,
      "metadata": {}
    }
  ]
}
```

---

### 3. Create Point Transaction
#### Endpoint
- `POST /api/points/transactions`

#### ملاحظات عامة
- هذا هو المسار الأساسي لإضافة نقاط أو خصم.
- أرسل إما:
  - `rule_id`
  - أو `rule_code`
- للحفظ:
  - أرسل `memorized_pages` إذا كان الإدخال يدوي بعدد الصفحات.
  - أو أرسل `surah_id` إذا كان الإدخال باختيار سورة.

#### Example 1: إضافة نقاط ثابتة
```json
{
  "student_id": 10,
  "rule_code": "attendance_on_time",
  "notes": "حضر عند بداية الدوام"
}
```

#### Example 2: حفظ بعدد الصفحات
```json
{
  "student_id": 10,
  "rule_code": "memorization_pages",
  "memorized_pages": "2.50",
  "notes": "تسميع الحفظ اليومي"
}
```

#### Example 3: حفظ عبر سورة
```json
{
  "student_id": 10,
  "rule_code": "memorization_pages",
  "surah_id": 12,
  "notes": "حفظ سورة النبأ"
}
```

#### مثال Response Data
```json
{
  "transaction": {
    "id": 15,
    "student": 10,
    "student_name": "Ahmad",
    "rule": 2,
    "rule_name": "الحفظ",
    "rule_code": "memorization_pages",
    "category": "الحفظ",
    "points": "17.50",
    "operation_date": "2026-06-21",
    "supervisor": 2,
    "supervisor_name": "teacher",
    "input_method": "direct_pages",
    "memorized_pages": "2.50",
    "surah": null,
    "surah_name": null,
    "notes": "تسميع الحفظ اليومي",
    "metadata": {},
    "created_at": "2026-06-21T18:30:00Z",
    "updated_at": "2026-06-21T18:30:00Z"
  }
}
```

---

### 4. Update Point Transaction
#### Endpoint
- `PUT /api/points/transactions`

#### ملاحظات
- عند تعديل العملية يعاد احتساب النقاط تلقائياً.
- المجموع الكلي للطالب يتحدث تلقائياً من الباك.

#### Example
```json
{
  "transaction_id": 15,
  "student_id": 10,
  "rule_code": "memorization_pages",
  "memorized_pages": "3.50",
  "notes": "تم تعديل عدد الصفحات"
}
```

---

### 5. Delete Point Transaction
#### Endpoint
- `DELETE /api/points/transactions`

#### Body
```json
{
  "transaction_id": 15
}
```

#### ملاحظات
- الحذف يعيد احتساب مجموع الطالب تلقائياً.

---

### 6. Get Point Transactions
#### Endpoint
- `GET /api/points/transactions`

#### Query Params المدعومة
- `student_id`
- `teacher_id`
- `rule_code`
- `date_from`
- `date_to`

#### Example
```text
/api/points/transactions?student_id=10&date_from=2026-06-01&date_to=2026-06-30
```

#### الاستخدام
- مناسب لشاشة "سجل العمليات".
- الاستجابة تعيد قائمة عمليات بنفس بنية `transaction`.

---

### 7. Get Points Reports
#### Endpoint
- `POST /api/points/reports`

#### Body اختياري
```json
{}
```

#### أو مع فلترة
```json
{
  "student_id": 10,
  "date_from": "2026-06-01",
  "date_to": "2026-06-30"
}
```

#### أهم الحقول الراجعة
```json
{
  "report": {
    "student_total": "25.00",
    "group_total": "120.00",
    "students_ranking": [
      {
        "student_id": 10,
        "student_name": "Ahmad",
        "total_points": "25.00"
      }
    ],
    "operations": [],
    "memorization_by_pages": {
      "total_pages": "4.00",
      "operations_count": 2,
      "total_points": "25.00"
    },
    "memorization_by_surahs": [
      {
        "surah__id": 12,
        "surah__name": "النبأ",
        "surah__juz": "عم",
        "total_pages": "1.50",
        "total_points": "7.50",
        "times": 1
      }
    ],
    "daily_summary": [],
    "weekly_summary": [],
    "monthly_summary": []
  }
}
```

---

## الجزء الثاني: اختبارات الطلاب (Tests)

### Endpoint
- `GET /api/tests`
- `POST /api/tests`

### 1. Get Tests
#### Body اختياري
```json
{
  "student_id": 10
}
```

#### Query Params اختياري
- `student_id`: لجلب اختبارات طالب محدد فقط.

#### مثال Response Data
```json
{
  "tests": [
    {
      "id": 1,
      "student": 10,
      "student_name": "Ahmad",
      "part_name": "جزء عم",
      "test_type": "external",
      "test_type_display": "وقف",
      "attempt_number": 1,
      "evaluation": "excellent",
      "evaluation_display": "ممتاز",
      "points": "100.00",
      "teacher": 2,
      "teacher_name": "teacher",
      "test_date": "2026-06-22",
      "notes": "تقييم ممتاز في الجزء"
    }
  ]
}
```

---

### 2. Create Test
#### Body
```json
{
  "student_id": 10,
  "part_name": "جزء عم",
  "test_type": "external", // أو "internal"
  "evaluation": "excellent", // اختياري: excellent, very_good, good, average, failed
  "test_date": "2026-06-22", // اختياري (تاريخ اليوم افتراضي)
  "notes": "ملاحظات إضافية" // اختياري
}
```

#### ملاحظات
- لاختبار **external** (وقف):
  - النقاط الأساسية: 100
  - إذا كان `evaluation = failed`: خصم 25 نقطة (إجمالي: 75)
- لاختبار **internal** (داخلي):
  - المحاولة الأولى: 50 نقطة
  - المحاولة الثانية: 40 نقطة
  - المحاولات الثالثة وما بعدها: 25 نقطة
- يتم احتساب `attempt_number` تلقائياً حسب عدد الاختبارات الداخلية السابقة للطالب على نفس الجزء.

#### مثال Response Data
```json
{
  "test": {
    "id": 2,
    "student": 10,
    "student_name": "Ahmad",
    "part_name": "جزء عم",
    "test_type": "internal",
    "test_type_display": "داخلي",
    "attempt_number": 1,
    "evaluation": "very_good",
    "evaluation_display": "جيد جداً",
    "points": "50.00",
    "teacher": 2,
    "teacher_name": "teacher",
    "test_date": "2026-06-22",
    "notes": "محاولة أولى ناجحة"
  }
}
```

---

## الجزء الثالث: ملاحظات الطلاب (Notes)

### Endpoint
- `GET /api/notes`
- `POST /api/notes`

### 1. Get Notes
#### Body اختياري
```json
{
  "student_id": 10
}
```

#### Query Params اختياري
- `student_id`: لجلب ملاحظات طالب محدد فقط.

#### مثال Response Data
```json
{
  "notes": [
    {
      "id": 1,
      "student": 10,
      "student_name": "Ahmad",
      "note_type": "good",
      "note_type_display": "جيدة",
      "points": "5.00",
      "note_text": "الطالب متميز في الحفظ اليوم",
      "teacher": 2,
      "teacher_name": "teacher",
      "note_date": "2026-06-22"
    }
  ]
}
```

---

### 2. Create Note
#### Body
```json
{
  "student_id": 10,
  "note_type": "good", // أو "bad"
  "note_text": "الطالب متميز في الحفظ اليوم",
  "note_date": "2026-06-22" // اختياري
}
```

#### ملاحظات
- `good`: إضافة 5 نقاط
- `bad`: خصم 10 نقاط

#### مثال Response Data
```json
{
  "note": {
    "id": 2,
    "student": 10,
    "student_name": "Ahmad",
    "note_type": "bad",
    "note_type_display": "سيئة",
    "points": "-10.00",
    "note_text": "تأخر في الحضور",
    "teacher": 2,
    "teacher_name": "teacher",
    "note_date": "2026-06-22"
  }
}
```

---

# ---------- Student Behavior Section ----------
## الجزء الرابع: سلوكيات الطلاب (Student Behaviors)

### Endpoint
- `GET /api/behaviors`
- `POST /api/behaviors`

### 1. Get Behaviors
#### Body اختياري
```json
{
  "student_id": 10
}
```

#### Query Params اختياري
- `student_id`: لجلب سلوكيات طالب محدد فقط.

#### مثال Response Data
```json
{
  "behaviors": [
    {
      "id": 1,
      "student": 10,
      "student_name": "أحمد",
      "teacher": 2,
      "teacher_name": "أستاذ محمد",
      "has_attended": true,
      "has_clothing": true,
      "has_cap": true,
      "participation_type": "special",
      "participation_type_display": "مميز",
      "was_absent": false,
      "no_recitation": false,
      "left_early": false,
      "behavior_date": "2026-06-22",
      "total_points": "25.00"
    }
  ]
}
```

---

### 2. Create/Update Behaviors
#### Body
```json
{
  "behavior_date": "2026-06-22",
  "has_attended": [5, 12, 3],
  "has_clothing": [5, 12],
  "has_cap": [5],
  "participation_type": {
    "5": "special",
    "12": "normal"
  },
  "was_absent": [7, 8],
  "no_recitation": [9],
  "left_early": [11]
}
```

#### ملاحظات
- كل حقل يحتوي على قائمة من أرقام هوية الطلاب (student IDs) الذين تنطبق عليهم هذه الحالة.
- الحقل `participation_type` هو كائن (object) حيث المفاتيح هي أرقام هوية الطلاب والقيم هي نوع المشاركة ("special" أو "normal").
- إذا كان سجل سلوك للطالب في هذا التاريخ موجود بالفعل، سيتم تحديثه.
- يتم احتساب النقاط تلقائيًا وتحديث `total_points` للطالب تلقائيًا.

#### مثال Response Data
```json
{
  "behaviors": [
    {
      "id": 1,
      "student": 5,
      "student_name": "محمد",
      "teacher": 2,
      "teacher_name": "أستاذ محمد",
      "has_attended": true,
      "has_clothing": true,
      "has_cap": true,
      "participation_type": "special",
      "participation_type_display": "مميز",
      "was_absent": false,
      "no_recitation": false,
      "left_early": false,
      "behavior_date": "2026-06-22",
      "total_points": "25.00"
    }
  ]
}
```

## الجزء الخامس: سلوك حسن (Good Behaviors)

### Endpoint
- `GET /api/good-behaviors`
- `POST /api/good-behaviors`

### 1. Get Good Behaviors
#### Body اختياري
```json
{
  "student_id": 10
}
```

#### Query Params اختياري
- `student_id`: لجلب سلوكيات حسنة لطالب محدد فقط.

#### مثال Response Data
```json
{
  "good_behaviors": [
    {
      "id": 1,
      "student": 10,
      "student_name": "Ahmad",
      "teacher": 2,
      "teacher_name": "teacher",
      "week_start_date": "2026-06-22",
      "points": "15.00",
      "description": "حفظ سورة البقرة كاملة هذا الأسبوع",
      "created_at": "2026-06-22"
    }
  ]
}
```

---

### 2. Create Good Behavior
#### Body
```json
{
  "student_id": 10,
  "week_start_date": "2026-06-22",
  "points": "15.00", // اختياري (افتراضي 15)
  "description": "حفظ سورة البقرة كاملة هذا الأسبوع" // اختياري
}
```

#### مثال Response Data
```json
{
  "good_behavior": {
    "id": 2,
    "student": 10,
    "student_name": "Ahmad",
    "teacher": 2,
    "teacher_name": "teacher",
    "week_start_date": "2026-06-22",
    "points": "15.00",
    "description": "مشاركة متميزة في الحلقة",
    "created_at": "2026-06-22"
  }
}
```

---

## ربط الواجهة

### شاشة قائمة الطلاب
- استخدم `POST /api/students` التي تعيد قائمة الطلاب مع `total_points` لكل طالب (موجودة بالفعل في StudentListSerializer):
  ```json
  {
    "students": [
      {
        "id": 10,
        "name": "براء",
        "pages_number": 5,
        "abs_number": 2,
        "total_points": "50.00"
      }
    ]
  }
  ```

### شاشة الطالب
- اعرض `total_points` القادم من `POST /api/student-info`.
- أضف زر "إضافة نقاط" يفتح bottom sheet أو dialog.
- أضف تبويبات جديدة:
  1. **سجل النقاط**: تعرض `GET /api/points/transactions?student_id=X`
  2. **الاختبارات**: تعرض `GET /api/tests?student_id=X`
  3. **الملاحظات**: تعرض `GET /api/notes?student_id=X`
  4. **السلوكيات**: تعرض `GET /api/behaviors?student_id=X`
  5. **سلوك حسن**: تعرض `GET /api/good-behaviors?student_id=X`
  6. **التقارير**: لتجلب تقرير كامل للطالب استخدم `POST /api/points/reports` مع body:
    ```json
    {
      "student_id": 10
    }
    ```

### شاشة إضافة عملية نقاط
- حمّل القواعد من `GET /api/points/rules`.
- إذا كانت القاعدة `calculation_method = memorization`:
  - اعرض اختيار نوع الإدخال:
    - بعدد الصفحات
    - بالسورة
- عند اختيار السورة:
  - حمّل السور من `GET /api/points/surahs`
  - أرسل `surah_id` فقط.

### شاشات إضافة الميزات الجديدة
- لكل ميزة، أنشئ form تُرسل إلى الـ POST endpoint المناسب.
- استخدم الـ choices المتاحة:
  - لاختبارات: `test_type` (external/internal) و `evaluation` (excellent/very_good/good/average/failed)
  - لملاحظات: `note_type` (good/bad)
  - لسلوكيات: `memorization_type` (page/surah) و `participation_type` (special/normal)

### شاشة التقرير
- استخدم `POST /api/points/reports`.
- يمكن عرض:
  - كرت لإجمالي الطالب.
  - كرت لإجمالي الحلقة.
  - جدول ترتيب الطلاب.
  - قائمة آخر العمليات.
  - مخطط يومي/أسبوعي/شهري.

---

## أكواد القواعد الحالية
- `attendance_on_time`
- `memorization_pages`
- `dress_code`
- `hadith_recitation`
- `participation_regular`
- `participation_special`
- `good_behavior_weekly`
- `exam_first_attempt`
- `exam_second_attempt`
- `exam_third_attempt`
- `awqaf_completion`
- `absence`
- `present_without_recitation`
- `early_leave`
- `awqaf_absence_or_failure`
- `negative_behavior`

---

## ملاحظات مهمة للفرونت
- جميع المسارات محمية وتحتاج `Authorization: Bearer <token>`
- لا تحسب نقاط الحفظ داخل Flutter اعتماداً على منطق محلي فقط، لأن المرجع النهائي يجب أن يبقى من الباك.
- لا تحسب نقاط الاختبارات، الملاحظات أو السلوكيات داخل Flutter، لأن الباك يحتسبها تلقائياً ويرجع النتيجة النهائية.
- يمكن عرض preview محلي للنقاط في الواجهة، لكن اعتمد النتيجة النهائية من response.
- القيم العشرية تأتي غالباً كنصوص مثل `"17.50"` أو `"2.50"`، لذلك خزّنها كنص أو حوّلها إلى `double` بحذر.
- `total_points` للطالب يتحدث تلقائياً في الباك بعد كل عملية.

---

## توصية تنفيذ
- أنشئ `PointsApiService`.
- أنشئ models مستقلة:
  - `PointRuleModel`
  - `SurahModel`
  - `PointTransactionModel`
  - `PointsReportModel`
  - `TestModel`
  - `NoteModel`
  - `StudentBehaviorModel`
  - `GoodBehaviorModel`
- اجعل شاشة الطالب تقرأ `total_points` مباشرة من `student-info`.
