# Generated by Django 5.0.1 on 2024-01-10 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0013_error'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='is_resolved',
            field=models.BooleanField(default=False, verbose_name='Решена'),
        ),
    ]