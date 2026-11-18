from django.http import FileResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from . import services, storage
from .models import TicketAttachment
from .serializers import AttachmentSerializer, can_delete

OBJECT_ID_RE = "[0-9a-f]{24}"


class AttachmentViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    One attachment: details, download and delete.

    Uploading and listing happen on the ticket (``/api/tickets/{id}/attachments/``).
    Requesters only ever reach files of their own tickets; anything else is a 404.
    """

    serializer_class = AttachmentSerializer
    lookup_value_regex = OBJECT_ID_RE
    pagination_class = None
    filter_backends = []

    def get_queryset(self):
        queryset = TicketAttachment.objects.select_related("ticket", "uploaded_by")
        if not self.request.user.is_agent:
            queryset = queryset.filter(ticket__created_by=self.request.user)
        return queryset

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        attachment = self.get_object()
        response = FileResponse(
            storage.open(attachment.file_id),
            content_type=attachment.content_type,
            as_attachment=True,
            filename=attachment.file_name,
        )
        response["Content-Length"] = str(attachment.size)
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, max-age=3600"
        return response

    def destroy(self, request, *args, **kwargs):
        attachment = self.get_object()
        if not can_delete(attachment, request.user):
            raise PermissionDenied("Only the person who uploaded this file or the support team can remove it.")
        services.remove_attachment(attachment=attachment, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
