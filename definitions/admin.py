from django.contrib import admin

from definitions.models import Definition, Client


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'description_math', 'created_at', 'is_initial')
    list_display_links = ('id', 'name')
    search_fields = ('definition',)

admin.site.register(Client)
