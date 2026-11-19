from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAgent
from apps.accounts.serializers import UserSummarySerializer
from apps.attachments import services as attachment_services
from apps.attachments.serializers import AttachmentSerializer
from apps.attachments.validators import allowed_extensions, attachment_settings
from apps.core.exports import ExportColumn, ExportMixin
from apps.core.exports.writers import EXPORT_FORMATS
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue
from apps.lookups.serializers import LookupOptionSerializer
from apps.similarity import services as similarity
from apps.similarity.constants import QUERY_MIN_LENGTH as SIMILAR_QUERY_MIN_LENGTH
from apps.similarity.engines import similarity_settings
from apps.similarity.serializers import SimilarQuerySerializer, category_payload, similar_payload

from . import services
from .constants import (
    DESCRIPTION_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH,
    RESOLUTION_MIN_LENGTH,
    STATUS_PRESENTATION,
    STATUS_TRANSITIONS,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    ActivityType,
    TicketStatus,
)
from .models import Ticket, TicketActivity
from .serializers import (
    CommentSerializer,
    TicketActivitySerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketUpdateSerializer,
)

User = get_user_model()
OBJECT_ID_RE = "[0-9a-f]{24}"


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


class TicketViewSet(
    ExportMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Tickets API.

    * Requesters see and create their own tickets.
    * Agents see every ticket and can update status, resolution, assignment.

    List filters (all optional, combine freely):
    ``status`` (comma separated), ``category`` / ``priority`` (value id),
    ``assigned_to`` (``me``, ``unassigned`` or an agent id),
    ``created_from`` / ``created_to`` (YYYY-MM-DD), plus ``search`` and ``ordering``.
    """

    lookup_value_regex = OBJECT_ID_RE
    http_method_names = ["get", "post", "patch", "head", "options"]
    throttle_scope = None  # set per action (see ``similar``)
    search_fields = [
        "reference", "title", "description", "category__label",
        "created_by__first_name", "created_by__last_name", "created_by__username",
    ]
    ordering_fields = [
        "reference", "title", "status", "created_at", "updated_at", "resolved_at",
        "category__label", "priority__sort_order", "created_by__first_name", "assigned_to__first_name",
    ]
    ordering = ["-created_at"]

    export_title = "Tickets"
    export_columns = [
        ExportColumn("Reference", "reference", 11, strong=True),
        ExportColumn("Title", "title", 34),
        ExportColumn("Category", "category.label", 18),
        ExportColumn("Priority", "priority.label", 10, color=lambda t: t.priority.color if t.priority else None),
        ExportColumn("Status", "get_status_display", 12,
                     color=lambda t: STATUS_PRESENTATION[TicketStatus(t.status)]["color"]),
        ExportColumn("Raised by", "created_by.display_name", 18),
        ExportColumn("Assigned to", "assigned_to.display_name", 18),
        ExportColumn("Created", "created_at", 16),
        ExportColumn("Resolved", "resolved_at", 16),
        ExportColumn("Resolution note", "resolution_note", 40),
    ]

    # ---- queryset & filters --------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related(
            "category", "priority", "created_by", "assigned_to", "resolved_by"
        )
        if not user.is_agent:
            queryset = queryset.filter(created_by=user)
        if self.action in ("list", "export", "email_export", "stats"):
            queryset = self._apply_filters(queryset)
        return queryset

    def _apply_filters(self, queryset):
        params = self.request.query_params
        statuses = [s for s in params.get("status", "").split(",") if s in TicketStatus.values]
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        for field in ("category", "priority"):
            value = params.get(field)
            if value and len(value) == 24:
                queryset = queryset.filter(**{f"{field}_id": value})
        assigned = params.get("assigned_to")
        if assigned == "me":
            queryset = queryset.filter(assigned_to=self.request.user)
        elif assigned == "unassigned":
            queryset = queryset.filter(assigned_to__isnull=True)
        elif assigned and len(assigned) == 24:
            queryset = queryset.filter(assigned_to_id=assigned)
        tz = timezone.get_current_timezone()
        created_from = _parse_date(params.get("created_from"))
        if created_from:
            queryset = queryset.filter(created_at__gte=datetime.combine(created_from, time.min, tzinfo=tz))
        created_to = _parse_date(params.get("created_to"))
        if created_to:
            queryset = queryset.filter(created_at__lte=datetime.combine(created_to, time.max, tzinfo=tz))
        return queryset

    def get_export_filter_summary(self):
        params = self.request.query_params
        summary = super().get_export_filter_summary()
        statuses = [TicketStatus(s).label for s in params.get("status", "").split(",") if s in TicketStatus.values]
        if statuses:
            summary.append(f"Status: {', '.join(statuses)}")
        for field, label in (("category", "Category"), ("priority", "Priority")):
            value = params.get(field)
            if value and len(value) == 24:
                option = LookupValue.objects.filter(pk=value).first()
                if option:
                    summary.append(f"{label}: {option.label}")
        if params.get("assigned_to") == "me":
            summary.append("Assigned to me")
        elif params.get("assigned_to") == "unassigned":
            summary.append("Unassigned")
        if not self.request.user.is_agent:
            summary.append("My tickets only")
        return summary

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "create":
            return TicketCreateSerializer
        if self.action in ("update", "partial_update"):
            return TicketUpdateSerializer
        return TicketDetailSerializer

    # ---- create / update ----------------------------------------------------
    def create(self, request, *args, **kwargs):
        if request.user.is_agent:
            raise PermissionDenied("Tickets are raised by requesters. The support team works on them.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = services.create_ticket(created_by=request.user, **serializer.validated_data)
        data = TicketDetailSerializer(ticket, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if not request.user.is_agent:
            raise PermissionDenied("Only the support team can update a ticket.")
        ticket = self.get_object()
        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        services.update_ticket(ticket=ticket, actor=request.user, changes=serializer.validated_data)
        ticket.refresh_from_db()
        return Response(TicketDetailSerializer(ticket, context=self.get_serializer_context()).data)

    # ---- extra endpoints ----------------------------------------------------
    @action(detail=True, methods=["get"])
    def activities(self, request, pk=None):
        ticket = self.get_object()
        entries = (
            ticket.activities.select_related("actor", "ticket")
            .prefetch_related("attachments__uploaded_by")
            .order_by("created_at")
        )
        return Response(TicketActivitySerializer(entries, many=True, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def comments(self, request, pk=None):
        """JSON ``{message}``, or multipart with ``message`` and/or ``files``."""
        ticket = self.get_object()
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data.get("message", "")
        files = request.FILES.getlist("files")
        if not message and not files:
            raise ValidationError({"message": ["Write a comment first, or attach a file."]})
        if message:
            entry = services.add_comment(ticket=ticket, author=request.user, message=message, files=files)
        else:
            entry = attachment_services.add_attachments(ticket=ticket, user=request.user, files=files)[0].activity
        entry = TicketActivity.objects.select_related("actor", "ticket").get(pk=entry.pk)
        data = TicketActivitySerializer(entry, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def attachments(self, request, pk=None):
        """List the ticket's files, or upload new ones (multipart field ``files``)."""
        ticket = self.get_object()
        context = self.get_serializer_context()
        if request.method == "POST":
            saved = attachment_services.add_attachments(
                ticket=ticket, user=request.user, files=request.FILES.getlist("files")
            )
            return Response(AttachmentSerializer(saved, many=True, context=context).data, status=status.HTTP_201_CREATED)
        files = ticket.attachments.select_related("uploaded_by").order_by("created_at")
        return Response(AttachmentSerializer(files, many=True, context=context).data)

    @action(detail=False, methods=["post"], throttle_scope="similar")
    def similar(self, request):
        """
        Up to three resolved tickets that look like the given title/description.

        Open to everyone signed in, because a requester raising a new ticket
        should benefit from fixes found for other people. Only the problem and
        its resolution are shared, never who raised it. Purely advisory:
        nothing is changed. POST keeps the typed text out of URLs and logs.
        """
        if not similarity_settings()["ENABLED"]:
            raise NotFound("Similar ticket suggestions are switched off.")
        serializer = SimilarQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = similarity.find_similar(
            title=data.get("title", ""),
            description=data.get("description", ""),
            exclude_id=data.get("exclude"),
        )
        return Response(similar_payload(result))

    @action(detail=False, methods=["post"], url_path="suggest-category", throttle_scope="suggest")
    def suggest_category(self, request):
        """
        The likely category for the title/description being typed, from similar
        past tickets (or the category descriptions). Advisory: the form never
        picks it by itself, and only the category - no ticket details - is returned.
        """
        config = similarity_settings()
        if not (config["ENABLED"] and config["CATEGORY_SUGGESTIONS"]):
            raise NotFound("Category suggestions are switched off.")
        serializer = SimilarQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = similarity.suggest_category(title=data.get("title", ""), description=data.get("description", ""))
        return Response(category_payload(result))

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Numbers for the dashboard, scoped to what the user is allowed to see."""
        queryset = self.get_queryset()
        by_status = {row["status"]: row["total"] for row in queryset.values("status").annotate(total=Count("id"))}
        by_category = {
            str(row["category"]): row["total"] for row in queryset.values("category").annotate(total=Count("id"))
        }
        categories = LookupValue.objects.of_type(LookupTypeCode.TICKET_CATEGORY).order_by("sort_order", "label")

        week_ago = timezone.now() - timedelta(days=7)
        resolved = list(queryset.filter(status=TicketStatus.RESOLVED).values_list("created_at", "resolved_at"))
        durations = [(done - created).total_seconds() for created, done in resolved if created and done]
        avg_hours = round(sum(durations) / len(durations) / 3600, 1) if durations else None

        payload = {
            "total": sum(by_status.values()),
            "by_status": [
                {**{"value": s.value, "label": s.label}, **STATUS_PRESENTATION[s], "count": by_status.get(s.value, 0)}
                for s in TicketStatus
            ],
            "by_category": [
                {**LookupOptionSerializer(c).data, "count": by_category.get(str(c.pk), 0)}
                for c in categories if by_category.get(str(c.pk), 0) or c.is_active
            ],
            "created_last_7_days": queryset.filter(created_at__gte=week_ago).count(),
            "resolved_last_7_days": queryset.filter(resolved_at__gte=week_ago).count(),
            "average_resolution_hours": avg_hours,
            "recent": TicketListSerializer(queryset.order_by("-created_at")[:5], many=True).data,
        }
        if request.user.is_agent:
            payload["assigned_to_me_open"] = queryset.filter(
                assigned_to=request.user, status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]
            ).count()
            payload["unassigned_open"] = queryset.filter(
                assigned_to__isnull=True, status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]
            ).count()
        return Response(payload)


class ActivityViewSet(ExportMixin, viewsets.ReadOnlyModelViewSet):
    """Audit log of every ticket event, for the support team."""

    serializer_class = TicketActivitySerializer
    permission_classes = [IsAgent]
    lookup_value_regex = OBJECT_ID_RE
    search_fields = ["message", "note", "ticket__reference", "ticket__title", "actor__first_name", "actor__last_name"]
    ordering_fields = ["created_at", "activity_type", "ticket__reference", "actor__first_name"]
    ordering = ["-created_at"]

    export_title = "Activity log"
    export_columns = [
        ExportColumn("When", "created_at", 18),
        ExportColumn("Ticket", "ticket.reference", 11, strong=True),
        ExportColumn("Ticket title", "ticket.title", 30),
        ExportColumn("Activity", "get_activity_type_display", 20),
        ExportColumn("Details", "message", 36),
        ExportColumn("By", "actor.display_name", 18),
        ExportColumn("Note", "note", 40),
    ]

    def get_queryset(self):
        queryset = TicketActivity.objects.select_related("ticket", "actor").prefetch_related("attachments__uploaded_by")
        activity_type = self.request.query_params.get("activity_type")
        if activity_type in ActivityType.values:
            queryset = queryset.filter(activity_type=activity_type)
        return queryset

    def get_export_filter_summary(self):
        summary = super().get_export_filter_summary()
        activity_type = self.request.query_params.get("activity_type")
        if activity_type in ActivityType.values:
            summary.append(f"Activity: {ActivityType(activity_type).label}")
        return summary


class ConfigView(APIView):
    """
    Everything the UI needs to build its forms, filters and badges.

    The frontend never hard-codes statuses, categories or priorities - it reads
    them from here, so new values added in the admin appear immediately.
    """

    def get(self, request):
        def options(type_code):
            values = LookupValue.objects.of_type(type_code).active().order_by("sort_order", "label")
            return LookupOptionSerializer(values, many=True).data

        agents = User.objects.filter(role=User.Role.AGENT, is_active=True).order_by("first_name")
        return Response({
            "statuses": [
                {"value": s.value, "label": s.label, **STATUS_PRESENTATION[s],
                 "transitions": [t.value for t in STATUS_TRANSITIONS[s]]}
                for s in TicketStatus
            ],
            "categories": options(LookupTypeCode.TICKET_CATEGORY),
            "priorities": options(LookupTypeCode.TICKET_PRIORITY),
            "activity_types": [{"value": a.value, "label": a.label} for a in ActivityType],
            "roles": [{"value": r.value, "label": r.label} for r in User.Role],
            "agents": UserSummarySerializer(agents, many=True).data if request.user.is_agent else [],
            "export_formats": [{"value": f.key, "label": f.label} for f in EXPORT_FORMATS.values()],
            "attachments": {
                "max_file_mb": attachment_settings()["MAX_FILE_MB"],
                "max_files": attachment_settings()["MAX_FILES"],
                "allowed_extensions": allowed_extensions(),
            },
            "similarity": {
                "enabled": similarity_settings()["ENABLED"],
                "max_results": similarity_settings()["MAX_RESULTS"],
                "min_length": SIMILAR_QUERY_MIN_LENGTH,
                "category_suggestions": similarity_settings()["ENABLED"]
                and similarity_settings()["CATEGORY_SUGGESTIONS"],
            },
            "validation": {
                "title_min": TITLE_MIN_LENGTH,
                "title_max": TITLE_MAX_LENGTH,
                "description_min": DESCRIPTION_MIN_LENGTH,
                "description_max": DESCRIPTION_MAX_LENGTH,
                "resolution_min": RESOLUTION_MIN_LENGTH,
            },
        })
