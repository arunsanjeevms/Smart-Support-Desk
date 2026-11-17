import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .columns import ExportColumn
from .serializers import EmailExportSerializer
from .writers import EXPORT_FORMATS, ExportFormat

logger = logging.getLogger(__name__)


class ExportMixin:
    """
    Adds two endpoints to a ViewSet:

    * ``GET  <prefix>/export/?file_type=pdf|xlsx`` - download the table
    * ``POST <prefix>/export/email/`` - e-mail the table as an attachment

    Both honour the same query parameters (search, ordering, filters) as the
    list endpoint because they use ``filter_queryset(get_queryset())``.
    """

    export_title: str = "Report"
    export_columns: list[ExportColumn] = []

    # ---- hooks a ViewSet may override --------------------------------------
    def get_export_columns(self) -> list[ExportColumn]:
        return self.export_columns

    def get_export_filter_summary(self) -> list[str]:
        """Human readable description of the active filters."""
        search = self.request.query_params.get("search")
        return [f'Search: "{search}"'] if search else []

    # ---- helpers -----------------------------------------------------------
    def _export_format(self, key: str | None) -> ExportFormat:
        fmt = EXPORT_FORMATS.get((key or "pdf").lower())
        if fmt is None:
            raise ValidationError({"file_type": [f"Choose one of: {', '.join(EXPORT_FORMATS)}."]})
        return fmt

    def _build_export(self, fmt: ExportFormat) -> tuple[bytes, str]:
        limit = settings.SUPPORT_DESK["EXPORT_MAX_ROWS"]
        columns = self.get_export_columns()
        queryset = self.filter_queryset(self.get_queryset())[:limit]
        rows = [[column.resolve(obj) for column in columns] for obj in queryset]

        now = timezone.localtime()
        user = self.request.user
        parts = [
            f"Generated {now:%d %b %Y, %H:%M} by {user.get_full_name() or user.get_username()}",
            f"{len(rows)} record{'s' if len(rows) != 1 else ''}",
            *self.get_export_filter_summary(),
        ]
        content = fmt.builder(self.export_title, "  |  ".join(parts), columns, rows)
        filename = f"{slugify(self.export_title)}-{now:%Y%m%d-%H%M}.{fmt.extension}"
        return content, filename

    # ---- endpoints ---------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request, *args, **kwargs):
        fmt = self._export_format(request.query_params.get("file_type"))
        content, filename = self._build_export(fmt)
        response = HttpResponse(content, content_type=fmt.content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=["post"], url_path="export/email")
    def email_export(self, request, *args, **kwargs):
        payload = EmailExportSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        fmt = self._export_format(data["file_type"])
        content, filename = self._build_export(fmt)
        sender = request.user.get_full_name() or request.user.get_username()
        body = data.get("message") or (
            f"Hello,\n\n{sender} shared the attached {self.export_title.lower()} report "
            f"from Smart Support Desk.\n\nRegards,\nSmart Support Desk"
        )
        email = EmailMessage(
            subject=data.get("subject") or f"Smart Support Desk - {self.export_title}",
            body=body,
            to=data["recipients"],
            reply_to=[request.user.email] if request.user.email else None,
        )
        email.attach(filename, content, fmt.content_type)
        try:
            email.send(fail_silently=False)
        except Exception as exc:  # SMTP problems should not look like a crash
            logger.exception("Export email failed")
            return Response(
                {"message": f"The email could not be sent: {exc}", "errors": {}},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {
                "message": f"{fmt.label} report sent to {', '.join(data['recipients'])}.",
                "recipients": data["recipients"],
                "file_name": filename,
            }
        )
