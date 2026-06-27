from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_update_memorization_extra_rate'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(default='1.0.0', max_length=50)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'System Settings',
            },
        ),
    ]