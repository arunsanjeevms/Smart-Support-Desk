from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.accounts.permissions import IsAgentOrReadOnly
from apps.core.exports import ExportColumn, ExportMixin

from .models import LookupType, LookupValue
from .serializers import LookupTypeSerializer, LookupValueSerializer


class LookupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """The configurable lists that exist (categories, priorities, ...)."""

    queryset = LookupType.objects.all()
    serializer_class = LookupTypeSerializer
    lookup_value_regex = "[0-9a-f]{24}"
    pagination_class = None
    search_fields = ["code", "name"]
    ordering_fields = ["name", "code"]


class LookupValueViewSet(ExportMixin, viewsets.ModelViewSet):
    """
    Values inside a configurable list.

    Everyone signed in can read them (the UI needs categories for its forms);
    only the support team can add, edit or remove them.
    """

    serializer_class = LookupValueSerializer
    permission_classes = [IsAgentOrReadOnly]
    lookup_value_regex = "[0-9a-f]{24}"
    search_fields = ["code", "label", "description", "lookup_type__name"]
    ordering_fields = ["label", "code", "sort_order", "is_active", "updated_at", "lookup_type__name"]
    ordering = ["lookup_type__name", "sort_order", "label"]

    export_title = "Configuration values"
    export_columns = [
        ExportColumn("List", "lookup_type.name", 20),
        ExportColumn("Label", "label", 24, strong=True),
        ExportColumn("Code", "code", 18),
        ExportColumn("Description", "description", 36),
        ExportColumn("Icon", "icon", 14),
        ExportColumn("Order", "sort_order", 8, align="right"),
        ExportColumn("Active", "is_active", 9),
        ExportColumn("Default", "is_default", 9),
    ]

    def get_queryset(self):
        queryset = LookupValue.objects.select_related("lookup_type")
        params = self.request.query_params
        if params.get("type"):
            queryset = queryset.filter(lookup_type__code=params["type"])
        if params.get("is_active") in {"true", "false"}:
            queryset = queryset.filter(is_active=params["is_active"] == "true")
        return queryset

    def get_export_filter_summary(self):
        summary = super().get_export_filter_summary()
        type_code = self.request.query_params.get("type")
        if type_code:
            lookup_type = LookupType.objects.filter(code=type_code).first()
            summary.append(f"List: {lookup_type.name if lookup_type else type_code}")
        return summary

    def destroy(self, request, *args, **kwargs):
        value = self.get_object()
        try:
            value.delete()
        except ProtectedError:
            return Response(
                {
                    "message": f'"{value.label}" is used by existing tickets. '
                    "Deactivate it instead so it is hidden from new tickets.",
                    "errors": {},
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
