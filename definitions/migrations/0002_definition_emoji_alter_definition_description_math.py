# Generated by Django 5.0.1 on 2024-01-03 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='definition',
            name='emoji',
            field=models.CharField(blank=True, max_length=40, verbose_name='Эмоджи'),
        ),
        migrations.AlterField(
            model_name='definition',
            name='description_math',
            field=models.TextField(blank=True, verbose_name='Формулировка математическая'),
        ),
    ]