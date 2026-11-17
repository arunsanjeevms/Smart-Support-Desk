from bson import ObjectId
from bson.errors import InvalidId
from django_mongodb_backend.fields import ObjectIdAutoField
from django_mongodb_backend.fields import ObjectIdField as ModelObjectIdField
from rest_framework import serializers


class ObjectIdField(serializers.Field):
    """Represents a MongoDB ObjectId as a 24 character hex string."""

    default_error_messages = {"invalid": "'{value}' is not a valid id."}

    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        try:
            return ObjectId(str(data))
        except (InvalidId, TypeError):
            self.fail("invalid", value=data)


class MongoModelSerializer(serializers.ModelSerializer):
    """
    ModelSerializer that knows how to map MongoDB ObjectId model fields.

    DRF would otherwise treat ``ObjectIdAutoField`` like an integer AutoField.
    """

    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        ObjectIdAutoField: ObjectIdField,
        ModelObjectIdField: ObjectIdField,
    }
