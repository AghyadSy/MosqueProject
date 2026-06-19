# 04 - Dashboard UI Refresh Notes

هذا الملف ليس موجّهًا مباشرة لمنطق Flutter، لكنه يشرح التغييرات البصرية التي صارت في واجهة الويب حتى تكون الصورة الكاملة واضحة.

## ما الذي تغيّر؟

تم تحديث شكل لوحة التحكم في الويب لتصبح:
- أنظف
- أكثر حداثة
- مبنية على الأبيض والأخضر الغامق
- أكثر وضوحًا في الجداول والبطاقات والأزرار

## الملفات التي تغيّرت بصريًا

### القالب العام
- `core/templates/dashboard/base.html`
- `static/dashboard-modern.css`

### صفحة تسجيل الدخول
- `core/templates/dashboard/login.html`

### الصفحة الرئيسية
- `core/templates/dashboard/index.html`

### صفحات الجداول
- `core/templates/dashboard/users/users.html`
- `core/templates/dashboard/students/show.html`
- `core/templates/dashboard/group_session/edit.html`
- `core/templates/dashboard/students_attend/show.html`

## تفاصيل بصرية مهمة

### 1. Theme جديد
- اعتماد لون أخضر غامق رئيسي.
- اعتماد خلفيات بيضاء ونظيفة.
- تحسين الظلال والزوايا والأزرار.

### 2. Layout
- تحسين الـ sidebar.
- إزالة عناصر تجريبية قديمة من الـ topbar.
- تحسين الـ footer والـ modals.

### 3. Tables
- الجداول صارت أوضح.
- أزرار العمليات أصبحت على شكل pills.
- الحالات صارت تظهر بشكل badges أو status pills.

### 4. Login Screen
- تم تحويل شاشة الدخول إلى تصميم حديث أكثر.
- أصبح فيها قسم branding واضح وقسم form أنظف.

## هل هذا يهم Flutter؟

بشكل مباشر لا، لأن Flutter لن يستهلك HTML.

لكن هذا الملف مفيد إذا كان مطور Flutter يريد:
- فهم الهوية البصرية الجديدة
- تقليد نفس الـ theme في التطبيق
- توحيد الألوان والأسلوب بين الويب والموبايل

## الألوان المقترحة لتقليد الهوية في Flutter

### Primary
- `#0F3B2E`

### Secondary
- `#14523E`

### Accent
- `#1F7A5A`

### Background Light
- `#F6FBF8`

### Border Soft
- `#D9E8E0`

## ملاحظة

إذا كان الهدف توحيد هوية الموبايل مع الويب، يفضّل أن يأخذ مطور Flutter هذه الألوان كـ design tokens أولية.
