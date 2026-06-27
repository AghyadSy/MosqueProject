from django.db import migrations


NOTE_POINT_RULES = [
    {
        'code': 'good_note',
        'name': 'ملاحظة جيدة',
        'category': 'الملاحظات',
        'direction': 'addition',
        'calculation_method': 'fixed',
        'default_points': '5.00',
        'sort_order': 170,
    },
    {
        'code': 'bad_note',
        'name': 'ملاحظة سيئة',
        'category': 'الملاحظات',
        'direction': 'deduction',
        'calculation_method': 'fixed',
        'default_points': '10.00',
        'sort_order': 180,
    },
]


def seed_note_point_rules(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    for rule in NOTE_POINT_RULES:
        PointRule.objects.update_or_create(
            code=rule['code'],
            defaults=rule,
        )


def remove_note_point_rules(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    PointRule.objects.filter(code__in=[rule['code'] for rule in NOTE_POINT_RULES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_remove_studentbehavior_memorization_pages_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_note_point_rules, remove_note_point_rules),
    ]
