from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAgent(BasePermission):
    """Only members of the support team."""

    message = "Only the support team can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_agent)


class IsAgentOrReadOnly(BasePermission):
    """Any signed-in user can read; only agents can change data."""

    message = "Only the support team can change this data."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return request.method in SAFE_METHODS or user.is_agent
