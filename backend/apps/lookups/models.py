from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

hex_color = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use a hex colour such as #2563EB.")
code_format = RegexValidator(
    r"^[a-z0-9_]+$", "Use lowercase letters, numbers and underscores only (e.g. billing_issue)."
)


class LookupType(TimeStampedModel):
    """
    A group of configurable values, e.g. "Ticket category" or "Ticket priority".

    This is the generic "master data" pattern: one collection describes the
    kinds of options, another stores the options themselves. Adding a new kind
    of configurable list only needs a new LookupType row.
    """

    code = models.CharField(max_length=50, unique=True, validators=[code_format])
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    is_system = models.BooleanField(
        default=False, help_text="System types are used by the application and cannot be deleted."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LookupValueQuerySet(models.QuerySet):
    def of_type(self, type_code: str):
        return self.filter(lookup_type__code=type_code)

    def active(self):
        return self.filter(is_active=True)


class LookupValue(TimeStampedModel):
    """One selectable option inside a LookupType (e.g. "Billing & Payments")."""

    lookup_type = models.ForeignKey(LookupType, on_delete=models.PROTECT, related_name="values")
    code = models.CharField(max_length=50, validators=[code_format])
    label = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(
        max_length=50, blank=True, help_text="Material Symbols icon name, e.g. 'payments'."
    )
    color = models.CharField(max_length=7, blank=True, validators=[hex_color])
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False, help_text="Pre-selected when nothing is chosen (one per type)."
    )

    objects = LookupValueQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "label"]
        constraints = [
            models.UniqueConstraint(fields=["lookup_type", "code"], name="unique_lookup_value_code"),
        ]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            # Only one default per type.
            LookupValue.objects.filter(lookup_type_id=self.lookup_type_id, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
