from django.contrib import admin

from definitions.models import Definition, Client, DefinitionUsage, LearnedDefinition, DefinitionLearningProcess


class DefinitionInline(admin.TabularInline):
    model = DefinitionUsage
    fk_name = 'definition'
    extra = 0


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_initial', 'emoji', 'used_definitions_list')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    inlines = (DefinitionInline,)


admin.site.register(Client)
admin.site.register(DefinitionUsage)
admin.site.register(LearnedDefinition)
admin.site.register(DefinitionLearningProcess)
