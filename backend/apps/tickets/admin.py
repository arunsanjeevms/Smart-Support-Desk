from django.contrib import admin

from .models import Ticket, TicketActivity


class TicketActivityInline(admin.TabularInline):
    model = TicketActivity
    extra = 0
    fields = ("created_at", "activity_type", "message", "actor", "note")
    readonly_fields = fields
    ordering = ("created_at",)
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "category", "priority", "status", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "category", "priority")
    search_fields = ("reference", "title", "description")
    readonly_fields = ("reference", "created_at", "updated_at", "resolved_at", "resolved_by")
    inlines = [TicketActivityInline]


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ("created_at", "ticket", "activity_type", "message", "actor")
    list_filter = ("activity_type",)
    search_fields = ("message", "note")
