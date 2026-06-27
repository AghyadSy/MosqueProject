from django.db import migrations


def update_memorization_extra_rate(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    rule = PointRule.objects.filter(code='memorization_pages').first()
    if rule:
        config = rule.config
        config['extra_page_rate'] = '10'
        rule.config = config
        rule.save()


def revert_memorization_extra_rate(apps, schema_editor):
    PointRule = apps.get_model('core', 'PointRule')
    rule = PointRule.objects.filter(code='memorization_pages').first()
    if rule:
        config = rule.config
        config['extra_page_rate'] = '5'
        rule.config = config
        rule.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_awqaf_exam_failed_point_rule'),
    ]

    operations = [
        migrations.RunPython(update_memorization_extra_rate, revert_memorization_extra_rate),
    ]
