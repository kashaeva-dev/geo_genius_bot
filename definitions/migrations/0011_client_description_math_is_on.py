# Generated by Django 5.0.1 on 2024-01-09 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0010_alter_learneddefinition_client_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='description_math_is_on',
            field=models.BooleanField(default=True, verbose_name='Исп. мат. определение'),
        ),
    ]