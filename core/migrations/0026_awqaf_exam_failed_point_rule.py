from django.db import migrations


AWQAF_EXAM_FAILED_RULE = {
    'code': 'awqaf_exam_failed',
    'name': 'رسوب في سبر الأوقاف',
    'category': 'سبر الأوقاف',
    'direction': 'addition',
    'calculation_method': 'fixed',
    'default_points': '75.00',
    'sort_order': 115,
}


def seed_awqaf_exam_failed_rule(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    PointRule.objects.update_or_create(
        code=AWQAF_EXAM_FAILED_RULE['code'],
        defaults=AWQAF_EXAM_FAILED_RULE,
    )


def remove_awqaf_exam_failed_rule(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    PointRule.objects.filter(code=AWQAF_EXAM_FAILED_RULE['code']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_note_point_rules'),
    ]

    operations = [
        migrations.RunPython(seed_awqaf_exam_failed_rule, remove_awqaf_exam_failed_rule),
    ]
