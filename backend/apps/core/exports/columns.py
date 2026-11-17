from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable

from django.utils import timezone


@dataclass(frozen=True)
class ExportColumn:
    """
    One column of an exported table.

    ``source`` is either a dotted attribute path (``"category.label"``) or a
    callable that receives the object. ``width`` is the Excel column width in
    characters and is also used as the relative column weight in PDFs.
    """

    header: str
    source: str | Callable[[Any], Any]
    width: int = 18

    def resolve(self, obj: Any) -> Any:
        if callable(self.source):
            value = self.source(obj)
        else:
            value = obj
            for part in self.source.split("."):
                value = getattr(value, part, None) if value is not None else None
        if callable(value):  # e.g. get_status_display
            value = value()
        return normalise(value)


def normalise(value: Any) -> Any:
    """Convert values to something both PDF and Excel writers understand."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.replace(tzinfo=None)
    if isinstance(value, date):
        return value
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return value
    return str(value)
