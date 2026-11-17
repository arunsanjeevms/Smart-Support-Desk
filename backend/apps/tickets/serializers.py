from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from apps.core.serializers import MongoModelSerializer, ObjectIdField
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue
from apps.lookups.serializers import LookupOptionSerializer

from .constants import (
    ACTIVITY_ICONS,
    DESCRIPTION_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH,
    RESOLUTION_MIN_LENGTH,
    STATUS_TRANSITIONS,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    TicketStatus,
)
from .models import Ticket, TicketActivity

User = get_user_model()


class LookupValueField(serializers.Field):
    """
    Accepts the id of an *active* value from a given lookup type and returns
    the LookupValue instance. Represented as the compact option object.
    """

    default_error_messages = {
        "required": "Please choose a {name}.",
        "invalid": "Please choose a valid {name}.",
        "inactive": "This {name} is no longer available. Please choose another one.",
    }

    def __init__(self, *, type_code: str, name: str, **kwargs):
        self.type_code = type_code
        self.name = name
        super().__init__(**kwargs)

    def fail(self, key, **kwargs):
        super().fail(key, name=self.name, **kwargs)

    def to_representation(self, value):
        return LookupOptionSerializer(value).data if value else None

    def to_internal_value(self, data):
        if data in (None, ""):
            if self.allow_null:
                return None
            self.fail("required")
        object_id = ObjectIdField().run_validation(data) if not isinstance(data, LookupValue) else data.pk
        value = LookupValue.objects.of_type(self.type_code).filter(pk=object_id).first()
        if value is None:
            self.fail("invalid")
        if not value.is_active:
            self.fail("inactive")
        return value


class AgentField(serializers.Field):
    """Accepts a support agent's id (or null to unassign)."""

    def to_representation(self, value):
        return UserSummarySerializer(value).data if value else None

    def to_internal_value(self, data):
        if data in (None, ""):
            return None
        object_id = ObjectIdField().run_validation(data)
        agent = User.objects.filter(pk=object_id, role=User.Role.AGENT, is_active=True).first()
        if agent is None:
            raise serializers.ValidationError("Tickets can only be assigned to an active support agent.")
        return agent


def status_payload(value: str) -> dict:
    return {"value": value, "label": TicketStatus(value).label}


# ---------------------------------------------------------------------------
# Read serializers
# ---------------------------------------------------------------------------
class TicketListSerializer(MongoModelSerializer):
    category = LookupOptionSerializer(read_only=True)
    priority = LookupOptionSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    assigned_to = UserSummarySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "reference", "title", "category", "priority", "status", "status_label",
            "created_by", "assigned_to", "created_at", "updated_at", "resolved_at",
        ]
        read_only_fields = fields


class TicketDetailSerializer(TicketListSerializer):
    resolved_by = UserSummarySerializer(read_only=True)
    allowed_statuses = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            "description", "resolution_note", "resolved_by", "allowed_statuses", "can_manage",
        ]
        read_only_fields = fields

    def _is_agent(self) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.is_agent)

    def get_can_manage(self, obj) -> bool:
        return self._is_agent()

    def get_allowed_statuses(self, obj) -> list[dict]:
        if not self._is_agent():
            return []
        return [status_payload(s) for s in STATUS_TRANSITIONS[TicketStatus(obj.status)]]


class TicketActivitySerializer(MongoModelSerializer):
    actor = UserSummarySerializer(read_only=True)
    activity_label = serializers.CharField(source="get_activity_type_display", read_only=True)
    icon = serializers.SerializerMethodField()
    ticket = serializers.SerializerMethodField()

    class Meta:
        model = TicketActivity
        fields = [
            "id", "ticket", "actor", "activity_type", "activity_label", "icon", "message",
            "from_status", "to_status", "note", "created_at",
        ]
        read_only_fields = fields

    def get_icon(self, obj) -> str:
        return ACTIVITY_ICONS.get(obj.activity_type, "history")

    def get_ticket(self, obj) -> dict:
        ticket = obj.ticket
        return {"id": str(ticket.pk), "reference": ticket.reference, "title": ticket.title}


# ---------------------------------------------------------------------------
# Write serializers
# ---------------------------------------------------------------------------
class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        error_messages={
            "required": "Please enter a title.",
            "blank": "Please enter a title.",
            "min_length": f"The title should be at least {TITLE_MIN_LENGTH} characters.",
            "max_length": f"The title cannot be longer than {TITLE_MAX_LENGTH} characters.",
        },
    )
    description = serializers.CharField(
        min_length=DESCRIPTION_MIN_LENGTH,
        max_length=DESCRIPTION_MAX_LENGTH,
        error_messages={
            "required": "Please describe the issue.",
            "blank": "Please describe the issue.",
            "min_length": f"Please add a little more detail (at least {DESCRIPTION_MIN_LENGTH} characters).",
            "max_length": f"The description cannot be longer than {DESCRIPTION_MAX_LENGTH} characters.",
        },
    )
    category = LookupValueField(type_code=LookupTypeCode.TICKET_CATEGORY, name="category")
    priority = LookupValueField(
        type_code=LookupTypeCode.TICKET_PRIORITY, name="priority", required=False, allow_null=True
    )

    def validate_title(self, value):
        if not any(ch.isalpha() for ch in value):
            raise serializers.ValidationError("The title should describe the problem in words.")
        return value

    def validate(self, attrs):
        if not attrs.get("priority"):
            attrs["priority"] = (
                LookupValue.objects.of_type(LookupTypeCode.TICKET_PRIORITY).active().filter(is_default=True).first()
            )
        return attrs


class TicketUpdateSerializer(serializers.Serializer):
    """What a support agent can change on a ticket."""

    status = serializers.ChoiceField(
        choices=TicketStatus.choices, required=False,
        error_messages={"invalid_choice": "'{input}' is not a valid status."},
    )
    resolution_note = serializers.CharField(required=False, allow_blank=True, max_length=DESCRIPTION_MAX_LENGTH)
    assigned_to = AgentField(required=False, allow_null=True)
    category = LookupValueField(type_code=LookupTypeCode.TICKET_CATEGORY, name="category", required=False)
    priority = LookupValueField(
        type_code=LookupTypeCode.TICKET_PRIORITY, name="priority", required=False, allow_null=True
    )

    def validate(self, attrs):
        ticket: Ticket = self.instance
        if not attrs:
            raise serializers.ValidationError("Nothing to update.")

        new_status = attrs.get("status", ticket.status)
        if new_status != ticket.status and new_status not in STATUS_TRANSITIONS[TicketStatus(ticket.status)]:
            raise serializers.ValidationError(
                {"status": [f"A ticket cannot move from {ticket.get_status_display()} to "
                            f"{TicketStatus(new_status).label}."]}
            )

        note = attrs.get("resolution_note", ticket.resolution_note or "").strip()
        if new_status == TicketStatus.RESOLVED:
            if not note:
                raise serializers.ValidationError(
                    {"resolution_note": ["Add a resolution note before marking the ticket as resolved."]}
                )
            if len(note) < RESOLUTION_MIN_LENGTH:
                raise serializers.ValidationError(
                    {"resolution_note": [f"The resolution note should be at least {RESOLUTION_MIN_LENGTH} characters."]}
                )
        return attrs


class CommentSerializer(serializers.Serializer):
    message = serializers.CharField(
        min_length=2, max_length=2000,
        error_messages={"blank": "Write a comment first.", "required": "Write a comment first."},
    )
