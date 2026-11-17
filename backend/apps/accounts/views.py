from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exports import ExportColumn, ExportMixin

from .permissions import IsAgent
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


def _auth_payload(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key, "user": UserSerializer(user).data}


class LoginView(APIView):
    """Exchange a username/email and password for an API token."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return Response(_auth_payload(user))


class RegisterView(APIView):
    """Create a Requester account and sign the person in straight away."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class DemoAccountsView(APIView):
    """
    Demo accounts offered as one-click sign-in on the login page.

    Controlled by the ``DEMO_MODE`` setting and only lists accounts that
    exist (i.e. after ``python manage.py seed_demo``).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        config = settings.SUPPORT_DESK
        if not config["DEMO_MODE"]:
            return Response([])
        usernames = [a["username"] for a in config["DEMO_ACCOUNTS"]]
        existing = {
            u.username: u for u in User.objects.filter(username__in=usernames, is_active=True)
        }
        return Response([
            {**account, "full_name": existing[account["username"]].display_name}
            for account in config["DEMO_ACCOUNTS"]
            if account["username"] in existing
        ])


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(ExportMixin, viewsets.ReadOnlyModelViewSet):
    """User directory for the support team (searchable, sortable, exportable)."""

    serializer_class = UserSerializer
    permission_classes = [IsAgent]
    lookup_value_regex = "[0-9a-f]{24}"
    search_fields = ["username", "email", "first_name", "last_name", "job_title"]
    ordering_fields = ["username", "email", "first_name", "last_name", "role", "date_joined", "last_login"]
    ordering = ["first_name", "last_name"]

    export_title = "Users"
    export_columns = [
        ExportColumn("Name", "display_name", 24, strong=True),
        ExportColumn("Username", "username", 18),
        ExportColumn("Email", "email", 30),
        ExportColumn("Role", "get_role_display", 16),
        ExportColumn("Job title", "job_title", 22),
        ExportColumn("Active", "is_active", 10),
        ExportColumn("Joined", "date_joined", 20),
        ExportColumn("Last sign-in", "last_login", 20),
    ]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get("role")
        if role in User.Role.values:
            queryset = queryset.filter(role=role)
        return queryset

    def get_export_filter_summary(self):
        summary = super().get_export_filter_summary()
        role = self.request.query_params.get("role")
        if role in User.Role.values:
            summary.append(f"Role: {User.Role(role).label}")
        return summary
