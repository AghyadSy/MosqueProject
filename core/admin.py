import json

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from .models import (
    GroupSession,
    Hadith,
    MemorizedPages,
    Page,
    PointRule,
    Student,
    StudentAttend,
    StudentPointTransaction,
    SurahPageData,
    User,
    Test,
    Note,
    StudentBehavior,
    GoodBehavior,
)


class SurahImportForm(forms.Form):
    json_file = forms.FileField(label='ملف JSON')


def normalize_surah_payload(payload):
    normalized_records = []
    if isinstance(payload, dict):
        iterator = []
        for surah_name, data in payload.items():
            row = dict(data)
            row['name'] = surah_name
            iterator.append(row)
    elif isinstance(payload, list):
        iterator = payload
    else:
        raise ValueError('صيغة ملف السور غير مدعومة')

    for row in iterator:
        name = str(row.get('name', '')).strip()
        juz = str(row.get('juz', '')).strip()
        surah_number = row.get('surah_number')
        pages = row.get('pages')
        if not name or not juz or surah_number is None or pages is None:
            raise ValueError('كل سجل سورة يجب أن يحتوي الاسم ورقم السورة والجزء وعدد الصفحات')
        normalized_records.append({
            'name': name,
            'surah_number': int(surah_number),
            'juz': juz,
            'pages': pages,
            'metadata': row.get('metadata', {}),
            'is_active': row.get('is_active', True),
        })
    return normalized_records


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'permission']
    search_fields = ['username']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'father_name', 'school_name', 'disabled', 'total_points']
    search_fields = ['name', 'father_name', 'school_name']
    list_filter = ['disabled']


@admin.register(GroupSession)
class GroupSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'teacher', 'student']
    search_fields = ['teacher__username', 'student__name']


@admin.register(StudentAttend)
class StudentAttendAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'date', 'is_attend']
    list_filter = ['date', 'is_attend']
    search_fields = ['student__name']


@admin.register(MemorizedPages)
class MemorizedPagesAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'page', 'date']
    list_filter = ['date', 'page__section']
    search_fields = ['student__name', 'page__name']


@admin.register(Hadith)
class HadithAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'narrator', 'producer']
    search_fields = ['title', 'narrator', 'producer']


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'quant', 'section']
    list_filter = ['section']
    search_fields = ['name']


@admin.register(PointRule)
class PointRuleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'code', 'category', 'direction',
        'calculation_method', 'default_points', 'is_active', 'sort_order',
    ]
    list_filter = ['category', 'direction', 'calculation_method', 'is_active']
    search_fields = ['name', 'code', 'category']


@admin.register(StudentPointTransaction)
class StudentPointTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student', 'rule', 'points', 'operation_date',
        'supervisor', 'input_method',
    ]
    list_filter = ['operation_date', 'rule__category', 'input_method']
    search_fields = ['student__name', 'rule__name', 'notes', 'supervisor__username']
    autocomplete_fields = ['student', 'rule', 'supervisor', 'surah']


@admin.register(SurahPageData)
class SurahPageDataAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/surahpagedata/change_list.html'
    list_display = ['id', 'name', 'surah_number', 'juz', 'pages', 'is_active', 'updated_at']
    list_filter = ['juz', 'is_active']
    search_fields = ['name', 'juz']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='core_surahpagedata_import_json',
            ),
        ]
        return custom_urls + urls

    def import_json_view(self, request):
        form = SurahImportForm(request.POST or None, request.FILES or None)
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'form': form,
            'title': 'استيراد أو تحديث السور من JSON',
        }

        if request.method == 'POST' and form.is_valid():
            json_file = form.cleaned_data['json_file']
            try:
                payload = json.load(json_file)
                records = normalize_surah_payload(payload)
                created_count = 0
                updated_count = 0
                for record in records:
                    _, created = SurahPageData.objects.update_or_create(
                        surah_number=record['surah_number'],
                        juz=record['juz'],
                        defaults=record,
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                self.message_user(request, f'فشل استيراد الملف: {exc}', level=messages.ERROR)
            else:
                self.message_user(
                    request,
                    f'تم استيراد السور بنجاح. المضافة: {created_count}، المحدثة: {updated_count}',
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect('../')

        return TemplateResponse(request, 'admin/core/surahpagedata/import_json.html', context)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'part_name', 'test_type', 'attempt_number', 'evaluation', 'points', 'teacher', 'test_date']
    list_filter = ['test_type', 'evaluation', 'test_date']
    search_fields = ['student__name', 'part_name', 'teacher__username']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'note_type', 'points', 'note_text', 'teacher', 'note_date']
    list_filter = ['note_type', 'note_date']
    search_fields = ['student__name', 'note_text', 'teacher__username']


@admin.register(StudentBehavior)
class StudentBehaviorAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'teacher', 'total_points', 'behavior_date']
    list_filter = ['behavior_date']
    search_fields = ['student__name', 'teacher__username']


@admin.register(GoodBehavior)
class GoodBehaviorAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'teacher', 'week_start_date', 'points', 'created_at']
    list_filter = ['week_start_date', 'created_at']
    search_fields = ['student__name', 'teacher__username', 'description']
