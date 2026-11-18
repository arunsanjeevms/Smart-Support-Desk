from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from apps.core.serializers import MongoModelSerializer

from .models import TicketAttachment


def can_delete(attachment, user) -> bool:
    """The person who uploaded a file, or any support agent, may remove it."""
    return bool(user and user.is_authenticated and (user.is_agent or attachment.uploaded_by_id == user.pk))


class AttachmentSerializer(MongoModelSerializer):
    uploaded_by = UserSummarySerializer(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = [
            "id", "file_name", "extension", "content_type", "size", "is_image",
            "uploaded_by", "created_at", "download_url", "can_delete",
        ]
        read_only_fields = fields

    def get_download_url(self, obj) -> str:
        """Path relative to the API root (the app adds the base URL and the sign-in token)."""
        return f"attachments/{obj.pk}/download/"

    def get_can_delete(self, obj) -> bool:
        request = self.context.get("request")
        return can_delete(obj, request.user if request else None)
