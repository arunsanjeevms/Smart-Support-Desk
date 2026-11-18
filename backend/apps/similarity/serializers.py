from rest_framework import serializers

from apps.core.serializers import ObjectIdField
from apps.lookups.serializers import LookupOptionSerializer
from apps.tickets.constants import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH

from .constants import QUERY_MIN_LENGTH
from .engines import ticket_text
from .services import CategoryResult, Match, SimilarResult


class SimilarQuerySerializer(serializers.Serializer):
    """What the user has typed so far on the New ticket form (or an existing ticket)."""

    title = serializers.CharField(
        required=False, allow_blank=True, max_length=TITLE_MAX_LENGTH,
        error_messages={"max_length": f"The title cannot be longer than {TITLE_MAX_LENGTH} characters."},
    )
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=DESCRIPTION_MAX_LENGTH,
        error_messages={"max_length": f"The description cannot be longer than {DESCRIPTION_MAX_LENGTH} characters."},
    )
    # Leave this ticket out of the results (used on an existing ticket's page).
    exclude = ObjectIdField(required=False, allow_null=True)

    def validate(self, attrs):
        text = ticket_text(attrs.get("title", ""), attrs.get("description", ""))
        if len(text) < QUERY_MIN_LENGTH:
            raise serializers.ValidationError(
                "Add a title or a short description first, so there is something to compare."
            )
        return attrs


class SimilarTicketSerializer(serializers.Serializer):
    """
    A suggested resolved ticket. Only what helps solve the problem is shared:
    no details about the person who raised it.
    """

    def to_representation(self, match: Match):
        ticket = match.ticket
        resolver = ticket.resolved_by
        return {
            "id": str(ticket.pk),
            "reference": ticket.reference,
            "title": ticket.title,
            "description": ticket.description,
            "resolution_note": ticket.resolution_note,
            "category": LookupOptionSerializer(ticket.category).data,
            "resolved_at": serializers.DateTimeField().to_representation(ticket.resolved_at)
            if ticket.resolved_at else None,
            "resolved_by": {"full_name": resolver.display_name, "initials": resolver.initials} if resolver else None,
            "score": match.score,
            "match": match.strength,
        }


def similar_payload(result: SimilarResult) -> dict:
    return {
        "results": SimilarTicketSerializer(result.matches, many=True).data,
        "engine": result.engine,
        "model": result.model,
        "compared": result.compared,
        "min_score": result.min_score,
    }


def category_payload(result: CategoryResult) -> dict:
    suggestion = result.suggestion
    return {
        "suggestion": {
            "category": LookupOptionSerializer(suggestion.category).data,
            "confidence": suggestion.confidence,
            "basis": suggestion.basis,
            "matches": suggestion.matches,
        } if suggestion else None,
        "engine": result.engine,
        "model": result.model,
    }
