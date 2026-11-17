from django.contrib import admin

from .models import LookupType, LookupValue


class LookupValueInline(admin.TabularInline):
    model = LookupValue
    extra = 1
    fields = ("label", "code", "icon", "color", "sort_order", "is_active", "is_default")
    ordering = ("sort_order", "label")


@admin.register(LookupType)
class LookupTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_system", "updated_at")
    search_fields = ("name", "code")
    inlines = [LookupValueInline]

    def get_readonly_fields(self, request, obj=None):
        return ("code", "is_system") if obj and obj.is_system else ()

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.is_system)


@admin.register(LookupValue)
class LookupValueAdmin(admin.ModelAdmin):
    list_display = ("label", "lookup_type", "code", "sort_order", "is_active", "is_default")
    list_filter = ("lookup_type", "is_active")
    search_fields = ("label", "code", "description")
    ordering = ("lookup_type", "sort_order", "label")
