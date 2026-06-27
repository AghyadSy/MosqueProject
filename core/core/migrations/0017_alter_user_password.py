from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_hadith'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=128),
        ),
    ]
