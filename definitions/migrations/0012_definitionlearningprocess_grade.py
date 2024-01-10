# Generated by Django 5.0.1 on 2024-01-10 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0011_client_description_math_is_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='definitionlearningprocess',
            name='grade',
            field=models.CharField(blank=True, choices=[('excellent', 'отлично'), ('good', 'хорошо'), ('satisfactory', 'удовлетворительно'), ('bad', 'неудовлетворительно')], default='', max_length=20, verbose_name='Оценка'),
        ),
    ]