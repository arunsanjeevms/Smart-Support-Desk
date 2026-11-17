from rest_framework import serializers

from .writers import EXPORT_FORMATS


class EmailExportSerializer(serializers.Serializer):
    """Body of ``POST <table>/export/email/``."""

    file_type = serializers.ChoiceField(choices=list(EXPORT_FORMATS.keys()), default="pdf")
    recipients = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        max_length=10,
        error_messages={"empty": "Add at least one recipient email address."},
    )
    subject = serializers.CharField(max_length=150, required=False, allow_blank=True)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate_recipients(self, value):
        # Keep the order but drop duplicates (case-insensitive).
        seen, unique = set(), []
        for email in value:
            if email.lower() not in seen:
                seen.add(email.lower())
                unique.append(email)
        return unique
