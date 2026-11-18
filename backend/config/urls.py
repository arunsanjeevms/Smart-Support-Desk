"""
URL map of the backend.

    /admin/          Django admin (manage users, categories, priorities, tickets)
    /api/health/     API + database health check
    /api/auth/...    login, register, logout, current user
    /api/config/     statuses, categories, priorities, ... for the UI
    /api/tickets/    tickets (+ /export, /export/email, /stats, /similar, /<id>/activities, /<id>/comments)
    /api/activities/ audit log
    /api/users/      user directory
    /api/lookups/... configurable lists and their values
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import UserViewSet
from apps.core.views import HealthView
from apps.lookups.views import LookupTypeViewSet, LookupValueViewSet
from apps.tickets.views import ActivityViewSet, ConfigView, TicketViewSet

admin.site.site_header = "Smart Support Desk administration"
admin.site.site_title = "Smart Support Desk"
admin.site.index_title = "Configuration & data"

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")
router.register("activities", ActivityViewSet, basename="activity")
router.register("users", UserViewSet, basename="user")
router.register("lookups/types", LookupTypeViewSet, basename="lookup-type")
router.register("lookups/values", LookupValueViewSet, basename="lookup-value")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/config/", ConfigView.as_view(), name="config"),
    path("api/", include(router.urls)),
]
