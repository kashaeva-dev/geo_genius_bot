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
    description_math = models.TextField(verbose_name='Формулировка математическая')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    used_definitions = models.ManyToManyField(
        'self',
        verbose_name='Использованные определения',
        blank=True,
        symmetrical=False,
        through='DefinitionUsage',
    )
    is_initial = models.BooleanField(verbose_name='Исходное определение', default=False)

    class Meta:
        verbose_name = 'Определение'
        verbose_name_plural = 'Определения'
        
    def __str__(self):
        return f'{self.definition}'


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

    class Meta:
        verbose_name = 'Использование определения'
        verbose_name_plural = 'Использованиe определений'

    def __str__(self):
        return f'{self.definition} -> {self.used_definition}'
