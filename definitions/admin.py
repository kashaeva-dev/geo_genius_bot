from django.contrib import admin
from import_export.admin import ImportExportModelAdmin


from definitions.models import Definition, Client, DefinitionUsage, LearnedDefinition, DefinitionLearningProcess, \
    DefinitionSimilarity, Error


class DefinitionInline(admin.TabularInline):
    model = DefinitionUsage
    fk_name = 'definition'
    extra = 0

class SimilarDefinitionInline(admin.TabularInline):
    model = DefinitionSimilarity
    fk_name = 'definition'
    extra = 0


@admin.register(Definition)
class DefinitionAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'category', 'description', 'is_initial', 'emoji', 'used_definitions_list')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    inlines = (DefinitionInline, SimilarDefinitionInline,)


admin.site.register(Client)
admin.site.register(DefinitionUsage)
admin.site.register(LearnedDefinition)
admin.site.register(DefinitionLearningProcess)
admin.site.register(Error)
