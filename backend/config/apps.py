"""
Django's admin, auth and contenttypes apps default to integer primary keys.
MongoDB documents use ObjectId keys, so these subclasses switch the default
auto field before the apps are loaded.
"""

from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig

OBJECT_ID_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoAdminConfig(AdminConfig):
    default_auto_field = OBJECT_ID_FIELD


class MongoAuthConfig(AuthConfig):
    default_auto_field = OBJECT_ID_FIELD


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = OBJECT_ID_FIELD
