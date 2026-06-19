# 02 - Unified API Response And Token Usage

## الهدف من هذا التغيير

تم توحيد شكل كل responses في الـ API حتى يصبح التعامل معها داخل Flutter أبسط وأكثر استقرارًا.

## الشكل الموحد الجديد

كل endpoint يرجع نفس البنية:

```json
{
  "success": true,
  "message": "رسالة واضحة",
  "data": {},
  "errors": {}
}
```

## عند النجاح

```json
{
  "success": true,
  "message": "تم تنفيذ الطلب بنجاح",
  "data": {
    "any_key": "any_value"
  },
  "errors": {}
}
```

## عند الفشل

```json
{
  "success": false,
  "message": "فشل تنفيذ الطلب",
  "data": {},
  "errors": {
    "field_name": [
      "error message"
    ]
  }
}
```

## ماذا يفعل Flutter؟

### 1. افحص `success`
- إذا كانت `true` أكمل العمل طبيعيًا.
- إذا كانت `false` اعرض `message` أو محتوى `errors`.

### 2. اقرأ البيانات من `data`
- لا تتوقع البيانات في root مباشرة.
- دائمًا ابحث عن المحتوى داخل `data`.

### 3. اقرأ الأخطاء من `errors`
- أخطاء validation والمصادقة وعدم الصلاحية أصبحت تأتي في `errors`.

## كيف نرسل التوكن؟

استخدم هذا الهيدر في كل request محمي:

```http
Authorization: Bearer <token>
```

## أمثلة مسارات public و protected

### Public
- `GET /api/version`
- `POST /api/login`

### Protected
- `POST /api/students`
- `POST /api/student-info`
- `POST /api/admin-students`
- `POST /api/add/attend`
- `POST /api/get/attend`
- `DELETE /api/attend`
- `POST /api/get/all/attend`
- `POST /api/pages`
- `DELETE /api/pages`
- `POST /api/unmemorized-pages`
- `GET /api/ahadith`

## ملاحظات مهمة للفرونت

- لا تعتمد على status code فقط.
- الأفضل دائمًا قراءة `success`, `message`, `data`, `errors`.
- بعض الأخطاء تأتي بـ `401` أو `404` أو `400`، لكن كلها ترجع بنفس structure.

## مثال هيكل parsing في Flutter

```dart
final body = jsonDecode(response.body);

final bool success = body['success'] ?? false;
final String message = body['message'] ?? '';
final Map<String, dynamic> data = body['data'] ?? {};
final Map<String, dynamic> errors = body['errors'] ?? {};
```
