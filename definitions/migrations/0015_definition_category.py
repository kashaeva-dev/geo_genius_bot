# Generated by Django 5.0.1 on 2024-01-10 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('definitions', '0014_error_is_resolved'),
    ]

    operations = [
        migrations.AddField(
            model_name='definition',
            name='category',
            field=models.CharField(choices=[('definition', 'определение'), ('axiom', 'аксиома'), ('theorem', 'теорема')], default='definition', max_length=100, verbose_name='Категория'),
        ),
    ]