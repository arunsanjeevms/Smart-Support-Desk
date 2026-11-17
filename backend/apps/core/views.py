from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Lightweight check used by the UI and CI to confirm the API and MongoDB are up."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            connection.database.command("ping")
            database = "up"
        except Exception:  # pragma: no cover - only when MongoDB is down
            database = "down"
        status_code = 200 if database == "up" else 503
        return Response({"status": "ok" if database == "up" else "degraded", "database": database}, status=status_code)
