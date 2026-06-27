# 09 - Pages API & Juz/Surah Data Updates Handoff

هذا الملف يشرح لمطور Flutter كيفية استخدام التحديثات الجديدة للـ pages API وبيانات الأجزاء (Juz) والسور (Surah) مع الفلاتر الجديدة.

## نظرة عامة
- تم إضافة نموذج **Juz** جديد في قاعدة البيانات.
- تم تحديث نموذج **SurahPageData** بحقول جديدة (الاسم بالعربية، رقم الجزء، صفحات البداية والنهاية).
- تم إضافة أمر إدارة لاستيراد البيانات من ملفات JSON لأجزاء القرآن: `python manage.py import_juz_data`. (تأكد من وضع الملفات في المسار: `core/data/quran_juz_data`)
- تم تحديث **PagesView** لقبول معطيات جديدة (surah_id, juz_id, page_number_start, page_number_end).
- تم إضافة endpoints جديدة لجلب الأجزاء مع فلترة: `GET /api/points/juzs` و`POST /api/points/juz`.
- تم إضافة فلترات لجلب السور: `GET /api/points/surahs`.
- **مهم**: عند إرسال pages باستخدام أي طريقة (page_ids, surah_id, juz_id)، يتم إنشاء **StudentPointTransaction** تلقائياً مع احتساب النقاط حسب قاعدة الحفظ (PointRule ذات calculation_method = memorization).
- تم إضافة `transaction` في الرد ليعرض تفاصيل العملية النقاطية.

---

## الجزء الأول: بيانات الأجزاء (Juz) والسور (Surah)

### 1. Get All Juzs
#### Endpoint
- `GET /api/points/juzs`

#### Query Params المدعومة (فلترة)
- `juz_number`: رقم الجزء (مثال: 1)
- `start_page`: صفحة بداية الجزء (مثال: 1)
- `end_page`: صفحة نهاية الجزء (مثال: 21)
- `is_active`: حالة تفعيل الجزء (true أو false)

#### مثال Request
```text
GET /api/points/juzs?juz_number=1&is_active=true
```

#### مثال Response Data
```json
{
  "juzs": [
    {
      "id": 1,
      "juz_number": 1,
      "start_page": 1,
      "end_page": 21,
      "total_pages": 21,
      "is_active": true,
      "surahs": [
        {
          "id": 1,
          "name": "Al-Fatihah",
          "surah_name_arabic": "الفاتحة",
          "surah_number": 1,
          "juz": "1",
          "juz_number": 1,
          "start_page": 1,
          "end_page": 1,
          "start_page_decimal": 1,
          "end_page_decimal": 2,
          "pages": 1,
          "is_active": true,
          "metadata": {}
        }
      ]
    }
  ]
}
```

#### الاستخدام
- استخدمه لعرض قائمة الأجزاء في شاشة اختيار الجزء للحفظ.
- يمكن فلترة الأجزاء حسب رقم الجزء أو صفحة البداية أو النهاية.

---

### 2. Get Specific Juz Details
#### Endpoint
- `POST /api/points/juz`

#### Body
```json
{
  "juz_number": 1
}
```

#### مثال Response Data
```json
{
  "juz": {
    "id": 1,
    "juz_number": 1,
    "start_page": 1,
    "end_page": 21,
    "total_pages": 21,
    "is_active": true,
    "surahs": []
  }
}
```

---

### 3. Get All Surahs (Updated)
#### Endpoint
- `GET /api/points/surahs`

#### Query Params الجديدة (فلترة)
- `surah_number`: رقم السورة (مثال: 1)
- `juz`: رقم الجزء كنص (مثال: "1")
- `juz_number`: رقم الجزء كرقم (مثال: 1)
- `is_active`: حالة تفعيل السورة (true أو false)

#### مثال Request
```text
GET /api/points/surahs?juz_number=1&is_active=true
```

#### مثال Response Data
```json
{
  "surahs": [
    {
      "id": 1,
      "name": "Al-Fatihah",
      "surah_name_arabic": "الفاتحة",
      "surah_number": 1,
      "juz": "1",
      "juz_number": 1,
      "start_page": 1,
      "end_page": 1,
      "start_page_decimal": 1,
      "end_page_decimal": 2,
      "pages": 1,
      "is_active": true,
      "metadata": {}
    }
  ]
}
```

#### الاستخدام
- استخدمه لعرض السور، مع إمكانية الفلترة حسب رقم الجزء أو رقم السورة.
- الحقل `surah_name_arabic` مناسب للعرض في الواجهة العربية.

---

## الجزء الثاني: تحديث Pages API

### 1. Add Memorized Pages (Updated)
#### Endpoint
- `POST /api/pages`

#### ملاحظات عامة
- يمكنك إرسال الطلب بأحد الطرق التالية:
  2. **باستخدام `surah_id`**: اختيار سورة، مع إمكانية تحديد نطاق صفحات (اختياري).
  3. **باستخدام `juz_id`**: اختيار جزء، مع إمكانية تحديد نطاق صفحات (اختياري).
- **مهم**: عند إرسال أي طريقة، يتم إنشاء **StudentPointTransaction** تلقائياً مع احتساب النقاط حسب قاعدة الحفظ (PointRule ذات calculation_method = memorization).
- الرد يحتوي على `transaction` مع تفاصيل العملية النقاطية.

---

#### Example 1: باستخدام page_ids (الطريقة القديمة)
```json
{
  "student_id": 10,
  "page_ids": [1, 2, 3]
}
```

#### Example 2: باستخدام surah_id
```json
{
  "student_id": 10,
  "surah_id": 1,
  "page_number_start": 1,
  "page_number_end": 2
}
```

#### Example 3: باستخدام juz_id
```json
{
  "student_id": 10,
  "juz_id": 1,
  "page_number_start": 1,
  "page_number_end": 21
}
```

---

#### مثال Response Data
```json
{
  "message": "تمت إضافة الصفحات بنجاح",
  "data": {
    "student_id": 10,
    "date": "2026-06-26",
    "page_ids": [1, 2],
    "pages": ["صفحة 1", "صفحة 2"],
    "transaction": {
      "id": 15,
      "student": 10,
      "student_name": "أحمد",
      "rule": 2,
      "rule_name": "الحفظ",
      "rule_code": "memorization_pages",
      "category": "الحفظ",
      "points": "17.50",
      "operation_date": "2026-06-26",
      "supervisor": 2,
      "supervisor_name": "مشرف",
      "input_method": "direct_pages",
      "memorized_pages": "2.50",
      "surah": null,
      "surah_name": null,
      "notes": "",
      "metadata": {},
      "created_at": "2026-06-26T18:30:00Z",
      "updated_at": "2026-06-26T18:30:00Z"
    }
  }
}
```

---

### 2. Delete Memorized Page (لم يتغير)
#### Endpoint
- `DELETE /api/pages`

#### Body
```json
{
  "student_id": 10,
  "memorized_page_id": 15
}
```

---

## الجزء الخامس: تحديث جلب الصفحات غير المحفوظة
### تحديث /api/unmemorized-pages
- الآن يتم إرجاع الصفحات غير المحفوظة مجمعة حسب الأجزاء
- يتم إرجاع الأجزاء فقط التي تم حفظ جزء منها على الأقل
- لا يتم إرجاع الأجزاء التي لم يتم حفظ أي صفحة منها

#### مثال Request
```json
{
  "student_id": 10,
  "page_archive": 1
}
```

#### مثال Response
```json
{
  "success": true,
  "message": "تم جلب الصفحات غير المحفوظة بنجاح",
  "data": {
    "juzs": [
      {
        "juz_id": 1,
        "juz_number": 1,
        "start_page": 1,
        "end_page": 20,
        "total_pages": 20,
        "memorized_pages": 5,
        "unmemorized_pages": ["6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
        "surahs": [
          {
            "surah_number": 1,
            "name": "Al-Fatihah",
            "surah_name_arabic": "الفاتحة"
          }
        ]
      }
    ]
  },
  "errors": {}
}
```

---

## الجزء السادس: قواعد النقاط الخاصة بالحفظ

### 1. قاعدة الحفظ (memorization_pages)
#### ما هي هذه القاعدة؟
- هي القاعدة الرسمية لحساب نقاط الحفظ.
- يُستخدم تلقائياً عند إضافة أي حفظ عبر `/api/pages`.
- يحسب النقاط بناءً على عدد الصفحات المحفوظة.

#### كيف يتم الحساب؟
تحتوي القاعدة على `config` يحدد الحدود والمعدلات:
```json
{
  "thresholds": {
    "1": "5",
    "2": "15",
    "3": "25",
    "4": "40"
  },
  "extra_page_rate": "10"
}
```

**طريقة الحساب:**
1. لكل 1 صفحة: 5 نقاط
2. لكل 2 صفحات: 15 نقاط
3. لكل 3 صفحات: 25 نقاط
4. لكل 4 صفحات أو أكثر: 40 نقاط + 10 نقاط لكل صفحة إضافية.

#### مثال على الحساب:
- حفظ 1 صفحة → 5 نقاط
- حفظ 2 صفحات → 15 نقاط
- حفظ 3 صفحات → 25 نقاط
- حفظ 4 صفحات → 40 نقاط
- حفظ 5 صفحات → 40 + 10 = 50 نقاط
- حفظ 6 صفحات → 40 + 2×10 = 60 نقاط

#### كيف الحصول على القواعد؟
- استخدم نفس المسار: `GET /api/points/rules`
- ابحث عن القاعدة ذات `code = "memorization_pages"` و `calculation_method = "memorization"`.

#### مثال لاستجابة القواعد:
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

### شاشة إضافة حفظ جديدة
- أضف ثلاث خيارات للطريقة:
  1. **اختيار صفحات (Page IDs)**: الطريقة القديمة.
  2. **اختيار سورة (Surah)**: جديدة، حمّل السور من `GET /api/points/surahs`.
  3. **اختيار جزء (Juz)**: جديدة، حمّل الأجزاء من `GET /api/points/juzs`.
- بعد إرسال الطلب، استخدم الـ `transaction` في الرد ليعرض للمستخدم عدد النقاط المكتسبة.

### شاشة عرض السور أو الأجزاء
- استخدم `surah_name_arabic` لعرض الاسم بالعربية.
- استخدم `start_page` و `end_page` لعرض نطاق صفحات السورة أو الجزء.

---

## الجزء الثامن: تحديث نسخة النظام
### /api/version
- الآن النسخة مخزنة في قاعدة البيانات (SystemSettings) وليست ثابتة
- يمكن تحديث النسخة عبر الـ POST
- القيمة الافتراضية: "1.0.0"

#### مثال GET
```http
GET {{base_url}}/api/version
```

#### مثال POST (تحديث نسخة)
```http
POST {{base_url}}/api/version
Content-Type: application/json

{
  "version": "1.1.0"
}
```

#### مثال Response
```json
{
  "success": true,
  "message": "تم جلب نسخة النظام بنجاح",
  "data": {
    "version": "1.1.0"
  },
  "errors": {}
}
```
