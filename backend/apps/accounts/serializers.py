from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.serializers import MongoModelSerializer

User = get_user_model()


class UserSummarySerializer(MongoModelSerializer):
    """Compact user representation embedded in tickets and activity entries."""

    full_name = serializers.CharField(source="display_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "initials", "role"]
        read_only_fields = fields


class UserSerializer(MongoModelSerializer):
    full_name = serializers.CharField(source="display_name", read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    is_agent = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name", "initials",
            "job_title", "role", "role_label", "is_agent", "is_active", "date_joined", "last_login",
        ]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150, error_messages={"blank": "Enter your username or email."}
    )
    password = serializers.CharField(
        trim_whitespace=False, write_only=True, error_messages={"blank": "Enter your password."}
    )

    def validate(self, attrs):
        identifier = attrs["username"].strip()
        # Allow signing in with an email address as well as the username.
        if "@" in identifier:
            match = User.objects.filter(email__iexact=identifier).only("username").first()
            if match:
                identifier = match.username
        user = authenticate(self.context.get("request"), username=identifier, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Incorrect username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        attrs["user"] = user
        return attrs


class RegisterSerializer(MongoModelSerializer):
    """Self sign-up. New accounts are always Requesters; agents are created by an admin."""

    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "confirm_password"]
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": False},
            "email": {"required": True},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        candidate = User(username=attrs["username"], email=attrs["email"],
                         first_name=attrs.get("first_name", ""), last_name=attrs.get("last_name", ""))
        try:
            validate_password(attrs["password"], user=candidate)
        except Exception as exc:  # django ValidationError -> field error
            raise serializers.ValidationError({"password": list(getattr(exc, "messages", [str(exc)]))})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(role=User.Role.REQUESTER, **validated_data)
