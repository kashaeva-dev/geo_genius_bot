from django.db import models

class Client(models.Model):
    chat_id = models.CharField(max_length=20, verbose_name='Чат ID')
    firstname = models.CharField(max_length=100, verbose_name='Имя')
    lastname = models.CharField(max_length=100, verbose_name='Фамилия')
    
    
    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        
    def __str__(self):
        return f'{self.firstname} {self.lastname}'
    
class Definition(models.Model):
    name = models.CharField(max_length=100, verbose_name='Определение')
    description = models.TextField(verbose_name='Формулировка')
    description_math = models.TextField(verbose_name='Формулировка математическая', blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    used_definitions = models.ManyToManyField(
        'self',
        verbose_name='Использованные определения',
        blank=True,
        symmetrical=False,
        through='DefinitionUsage',
    )
    is_initial = models.BooleanField(verbose_name='Исх.', default=False)
    emoji = models.CharField(max_length=40, verbose_name='Эмоджи', blank=True)

    def used_definitions_list(self):
        usage_records = DefinitionUsage.objects.filter(definition=self)
        used_definitions_with_basis = []
        for usage in usage_records:
            if usage.basis > 0:
                used_definitions_with_basis.append(f"{usage.used_definition} - {usage.basis}")
            else:
                used_definitions_with_basis.append(f"{usage.used_definition}")

        return ', '.join(used_definitions_with_basis)

    used_definitions_list.short_description = 'Использует'

    class Meta:
        verbose_name = 'Определение'
        verbose_name_plural = 'Определения'
        
    def __str__(self):
        return f'{self.name}'


class DefinitionUsage(models.Model):
    definition = models.ForeignKey(Definition,
                                   on_delete=models.PROTECT,
                                   verbose_name='Определение',
                                   related_name='used_in',
                                   )
    used_definition = models.ForeignKey(Definition,
                                        on_delete=models.PROTECT,
                                        verbose_name='Использованное определение',
                                        related_name='used_definition',
                                        )
    basis = models.IntegerField(verbose_name='Основание', default=0)

    class Meta:
        verbose_name = 'Использование определения'
        verbose_name_plural = 'Использованиe определений'

    def __str__(self):
        return f'{self.definition} -> {self.used_definition}'
