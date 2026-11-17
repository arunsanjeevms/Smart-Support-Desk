from rest_framework import serializers

from apps.core.serializers import MongoModelSerializer, ObjectIdField

from .constants import LookupTypeCode
from .models import LookupType, LookupValue


class LookupTypeSerializer(MongoModelSerializer):
    value_count = serializers.SerializerMethodField()

    class Meta:
        model = LookupType
        fields = ["id", "code", "name", "description", "is_system", "value_count"]
        read_only_fields = fields

    def get_value_count(self, obj) -> int:
        return obj.values.count()


class LookupOptionSerializer(MongoModelSerializer):
    """Compact form used inside tickets and the /config endpoint."""

    class Meta:
        model = LookupValue
        fields = ["id", "code", "label", "description", "icon", "color", "sort_order", "is_default"]
        read_only_fields = fields


class LookupValueSerializer(MongoModelSerializer):
    lookup_type = ObjectIdField(source="lookup_type_id")
    lookup_type_code = serializers.CharField(source="lookup_type.code", read_only=True)
    lookup_type_name = serializers.CharField(source="lookup_type.name", read_only=True)

    class Meta:
        model = LookupValue
        fields = [
            "id", "lookup_type", "lookup_type_code", "lookup_type_name", "code", "label",
            "description", "icon", "color", "sort_order", "is_active", "is_default",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        # Uniqueness of (lookup_type, code) is checked in validate() so the
        # message can be friendlier than the default one.
        validators = []

    def validate_lookup_type(self, value):
        if not LookupType.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Unknown configuration type.")
        return value

    def validate(self, attrs):
        type_id = attrs.get("lookup_type_id", getattr(self.instance, "lookup_type_id", None))
        code = attrs.get("code", getattr(self.instance, "code", None))
        clash = LookupValue.objects.filter(lookup_type_id=type_id, code=code)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError({"code": ["This code is already used in this list."]})
        if self.instance and "lookup_type_id" in attrs and attrs["lookup_type_id"] != self.instance.lookup_type_id:
            raise serializers.ValidationError({"lookup_type": ["The type of an existing value cannot change."]})

        # Built-in lists (e.g. e-mail events) are defined by the application.
        type_code = LookupType.objects.filter(pk=type_id).values_list("code", flat=True).first()
        if type_code in LookupTypeCode.BUILT_IN_VALUES:
            if self.instance is None:
                raise serializers.ValidationError(
                    {"lookup_type": ["E-mail events are built in. You can rename them or switch them on and off."]}
                )
            if code != self.instance.code:
                raise serializers.ValidationError({"code": ["The code of a built-in value cannot change."]})
        return attrs
