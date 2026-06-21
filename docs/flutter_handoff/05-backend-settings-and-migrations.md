# 05 - Backend Settings And Migration Notes

هذا الملف يشرح الملاحظات التشغيلية المرتبطة بالتعديلات الأخيرة.

## 1. متغيرات البيئة

تم نقل جزء من الإعدادات الحساسة إلى متغيرات بيئة.

## الملف المرجعي
- `.env.example`

## القيم الموجودة

```env
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=alrahmanmosque.pythonanywhere.com
```

## ملاحظة

- في بيئة الإنتاج يجب عدم استخدام القيمة الافتراضية للـ `SECRET_KEY`.

## القيم الحالية التي تم تجهيزها للإنتاج

```env
DJANGO_SECRET_KEY=django-insecure-k0kezn01%)3m4dfc8a-+q&(x$3ws2ngryen9qoyac33g#9%g!+
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=alrahmanmosque.pythonanywhere.com
```

## 2. Migrations جديدة

يوجد migrations مهمة أضيفت:

### داخل `core`
- `0017_alter_user_password.py`
- توسعة حقل كلمة المرور ليتوافق مع التخزين المشفر.
- `0020_pointrule_student_total_points_surahpagedata_and_more.py`
- نظام نقاط الطلاب والجداول المرتبطة به.
- `0021_goodbehavior_note_studentbehavior_test.py`
- الجداول الجديدة للاختبارات، الملاحظات، سلوكيات الطلاب، وسلوك حسن.
- `0022_alter_test_test_type.py`
- تعديل نوع الاختبار من "stop" إلى "external".

### داخل `api`
- `0001_apiaccesstoken.py`
- إنشاء جدول لتخزين توكنات الـ API.

## الأوامر المطلوبة بعد سحب التعديلات

```bash
python manage.py migrate
```

## 3. ما الذي يهم Flutter Developer؟

بشكل مباشر:
- لا شيء في UI الخاص بـ Flutter.

لكن بشكل غير مباشر:
- لا يمكن استخدام الـ login الجديد بشكل صحيح إذا لم تكن الـ migrations مطبقة.
- لا يمكن استخدام token auth إذا لم يكن جدول `ApiAccessToken` موجودًا.

## 4. Checklist سريعة قبل اختبار التطبيق

1. تأكد أن الـ backend شغّال.
2. تأكد أن `migrate` تم تشغيلها.
3. نفّذ login وخذ `token`.
4. جرّب endpoint محمي مثل `/api/students`.
