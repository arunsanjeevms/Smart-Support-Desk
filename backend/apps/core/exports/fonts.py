"""Registers the Poppins font for PDF reports (with a Helvetica fallback)."""

from pathlib import Path

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path(__file__).resolve().parent / "fonts"

_POPPINS = {
    "regular": ("Poppins", "Poppins-Regular.ttf"),
    "medium": ("Poppins-Medium", "Poppins-Medium.ttf"),
    "semibold": ("Poppins-SemiBold", "Poppins-SemiBold.ttf"),
}
_FALLBACK = {"regular": "Helvetica", "medium": "Helvetica-Bold", "semibold": "Helvetica-Bold"}
_cache: dict[str, str] | None = None


def report_fonts() -> dict[str, str]:
    """Font names to use in the PDF, keyed by weight: regular / medium / semibold."""
    global _cache
    if _cache is not None:
        return _cache
    try:
        for name, filename in _POPPINS.values():
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
        # Lets <b> inside paragraphs switch to the semibold face.
        addMapping("Poppins", 0, 0, "Poppins")
        addMapping("Poppins", 1, 0, "Poppins-SemiBold")
        addMapping("Poppins", 0, 1, "Poppins")
        addMapping("Poppins", 1, 1, "Poppins-SemiBold")
        _cache = {weight: name for weight, (name, _) in _POPPINS.items()}
    except Exception:  # fonts missing or unreadable - still produce a report
        _cache = dict(_FALLBACK)
    return _cache
