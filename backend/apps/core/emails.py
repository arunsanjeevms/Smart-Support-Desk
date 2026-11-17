"""
HTML e-mails with a plain-text alternative.

Templates live in ``apps/core/templates/emails/``: each e-mail has a
``<name>.html`` (extends ``base.html``) and a ``<name>.txt`` version.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

BRAND = "Smart Support Desk"


def tint(hex_color: str, amount: float = 0.1) -> str:
    """Very light version of a colour, for badge backgrounds."""
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return "#F2F4F7"
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(255 - (255 - c) * amount) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def shade(hex_color: str, amount: float = 0.22) -> str:
    """Slightly darker version of a colour, so small text stays readable."""
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return "#344054"
    r, g, b = (round(int(value[i : i + 2], 16) * (1 - amount)) for i in (0, 2, 4))
    return f"#{r:02X}{g:02X}{b:02X}"


def badge(label: str, color: str) -> dict:
    """Context for a coloured pill (status, priority) in an e-mail."""
    return {"label": label, "text": shade(color), "background": tint(color), "border": tint(color, 0.3)}


def build_email(*, template: str, subject: str, to: list[str], context: dict, reply_to=None) -> EmailMultiAlternatives:
    context = {
        "brand": BRAND,
        "app_url": settings.SUPPORT_DESK["FRONTEND_URL"],
        "subject": subject,
        **context,
    }
    text = render_to_string(f"emails/{template}.txt", context).strip() + "\n"
    html = render_to_string(f"emails/{template}.html", context)
    message = EmailMultiAlternatives(subject=subject, body=text, to=to, reply_to=reply_to)
    message.attach_alternative(html, "text/html")
    return message
