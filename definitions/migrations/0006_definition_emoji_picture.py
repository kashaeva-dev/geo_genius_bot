# Generated by Django 5.0.1 on 2024-01-05 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0005_definition_symbol'),
    ]

    operations = [
        migrations.AddField(
            model_name='definition',
            name='emoji_picture',
            field=models.CharField(blank=True, max_length=5, verbose_name='Эмоджи картинка'),
        ),
    ]