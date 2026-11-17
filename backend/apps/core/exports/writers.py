"""Turn a list of rows into a PDF report or an Excel workbook."""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from io import BytesIO
from typing import Callable, Sequence
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .columns import ExportColumn
from .fonts import report_fonts

BRAND = "Smart Support Desk"

# Report palette (matches the web app).
INK = "#101828"
TEXT = "#344054"
MUTED = "#667085"
LINE = "#EAECF0"
LINE_STRONG = "#D0D5DD"
HEAD_BG = "#F2F4F7"
ZEBRA = "#F9FAFB"
ACCENT = "#0F766E"
ACCENT_SOFT = "#F0F9F8"


@dataclass(frozen=True)
class ReportMeta:
    """Everything a report says about itself (shown in the header and footer)."""

    title: str
    generated_at: datetime
    generated_by: str
    record_count: int
    filters: list[str] = field(default_factory=list)

    @property
    def generated_text(self) -> str:
        return f"{self.generated_at:%d %b %Y, %H:%M}"

    @property
    def records_text(self) -> str:
        return f"{self.record_count:,} record{'s' if self.record_count != 1 else ''}"

    @property
    def subtitle(self) -> str:
        return "  |  ".join(
            [f"Generated {self.generated_text} by {self.generated_by}", self.records_text, *self.filters]
        )


NBSP = " "


def _pdf_date(value: date) -> str:
    # Non-breaking spaces keep "17 Nov 2026" together on one line.
    return NBSP.join([str(value.day), value.strftime("%b"), str(value.year)])


def display_text(value, for_pdf: bool = False) -> str:
    if isinstance(value, datetime):
        if for_pdf:
            return f"{_pdf_date(value)}\n{value:%H:%M}"  # date, then time underneath
        return value.strftime("%d %b %Y, %H:%M")
    if isinstance(value, date):
        return _pdf_date(value) if for_pdf else value.strftime("%d %b %Y")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:,}"
    return "" if value is None else str(value)


def readable(hex_color: str, darken: float = 0.22) -> str:
    """Darken a badge colour a little so small text stays readable on white."""
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return TEXT
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c * (1 - darken)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def build_xlsx(
    meta: ReportMeta,
    columns: Sequence[ExportColumn],
    rows: list[list],
    cell_colors: list[list[str | None]] | None = None,
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = (meta.title[:28] or "Report").replace("/", "-")

    last_col = get_column_letter(len(columns))
    ws["A1"] = f"{BRAND} - {meta.title}"
    ws["A1"].font = Font(size=14, bold=True, color=INK[1:])
    ws["A2"] = meta.subtitle
    ws["A2"].font = Font(size=10, italic=True, color=MUTED[1:])
    ws.merge_cells(f"A1:{last_col}1")
    ws.merge_cells(f"A2:{last_col}2")

    header_row = 4
    thin = Side(style="thin", color=LINE[1:])
    header_border = Border(bottom=Side(style="medium", color=ACCENT[1:]))
    zebra_fill = PatternFill("solid", fgColor=ZEBRA[1:])
    header_fill = PatternFill("solid", fgColor=HEAD_BG[1:])

    for idx, column in enumerate(columns, start=1):
        cell = ws.cell(row=header_row, column=idx, value=column.header)
        cell.font = Font(bold=True, color=TEXT[1:])
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", horizontal=column.align)
        cell.border = header_border
        ws.column_dimensions[get_column_letter(idx)].width = column.width

    for r, row in enumerate(rows, start=header_row + 1):
        for c, value in enumerate(row, start=1):
            column = columns[c - 1]
            color = cell_colors[r - header_row - 1][c - 1] if cell_colors else None
            cell = ws.cell(row=r, column=c, value=value)
            cell.border = Border(bottom=thin)
            cell.alignment = Alignment(vertical="top", wrap_text=True, horizontal=column.align)
            cell.font = Font(
                bold=column.strong or bool(color),
                color=(readable(color) if color else INK if column.strong else TEXT)[1:],
            )
            if isinstance(value, datetime):
                cell.number_format = "dd mmm yyyy hh:mm"
            elif isinstance(value, date):
                cell.number_format = "dd mmm yyyy"
            if (r - header_row) % 2 == 0:
                cell.fill = zebra_fill

    ws.row_dimensions[header_row].height = 22
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    ws.auto_filter.ref = f"A{header_row}:{last_col}{header_row + max(len(rows), 1)}"

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
PAGE_SIZE = landscape(A4)
MARGIN_X = 16 * mm
MARGIN_TOP = 27 * mm  # leaves room for the running header
MARGIN_BOTTOM = 19 * mm  # leaves room for the footer

_ALIGN = {"left": TA_LEFT, "right": TA_RIGHT, "center": TA_CENTER}

_BREAKS = re.compile(r"[ \t\r\n]+")
HEAD_SIZE = 7.2
CELL_SIZE = 8.4
CELL_PADDING = 6  # points, left and right


def _column_widths(columns, texts, cell_colors, fonts, available) -> list[float]:
    """
    Split the page width by the columns' relative weights, but never make a
    column narrower than its longest single word - so values like "SSD-1026"
    or headers like "PRIORITY" are never broken in the middle.
    """
    minimums = []
    for i, column in enumerate(columns):
        widest = max(stringWidth(word, fonts["semibold"], HEAD_SIZE) for word in column.header.upper().split())
        for row_index, row in enumerate(texts):
            colored = bool(cell_colors and cell_colors[row_index][i])
            font = fonts["semibold"] if colored else fonts["medium"] if column.strong else fonts["regular"]
            # Split on real spaces/newlines only: non-breaking spaces join a phrase
            # ("In Progress", "17 Nov 2026") into one unbreakable "word".
            for word in _BREAKS.split(row[i]):
                if word:
                    widest = max(widest, stringWidth(word, font, CELL_SIZE))
        minimums.append(min(widest, available * 0.3) + 2 * CELL_PADDING + 1)

    total_weight = sum(c.width for c in columns) or 1
    widths = [available * c.width / total_weight for c in columns]
    for _ in range(4):  # a few passes settle the redistribution
        deficit = sum(max(0.0, m - w) for m, w in zip(minimums, widths))
        if deficit <= 0.01:
            break
        widths = [max(w, m) for m, w in zip(minimums, widths)]
        slack = [max(0.0, w - m) for m, w in zip(minimums, widths)]
        total_slack = sum(slack) or 1
        widths = [w - deficit * s / total_slack for w, s in zip(widths, slack)]
    return widths


def _report_canvas(meta: ReportMeta, fonts: dict[str, str]):
    """Canvas that draws the running header/footer once the page count is known."""

    class ReportCanvas(pdf_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_pages = []

        def showPage(self):
            self._saved_pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_pages)
            for state in self._saved_pages:
                self.__dict__.update(state)
                self._draw_chrome(total)
                super().showPage()
            super().save()

        def _draw_chrome(self, total: int):
            width, height = self._pagesize
            right = width - MARGIN_X
            top = height - 11 * mm

            # Brand mark: rounded teal square with a white tick.
            size = 6.2 * mm
            self.setFillColor(colors.HexColor(ACCENT))
            self.roundRect(MARGIN_X, top - size, size, size, 1.5 * mm, stroke=0, fill=1)
            self.setStrokeColor(colors.white)
            self.setLineWidth(1.1)
            self.setLineCap(1)
            self.setLineJoin(1)
            tick = self.beginPath()
            tick.moveTo(MARGIN_X + 1.75 * mm, top - 3.25 * mm)
            tick.lineTo(MARGIN_X + 2.75 * mm, top - 4.3 * mm)
            tick.lineTo(MARGIN_X + 4.55 * mm, top - 2.15 * mm)
            self.drawPath(tick, stroke=1, fill=0)

            self.setFillColor(colors.HexColor(INK))
            self.setFont(fonts["semibold"], 9.5)
            self.drawString(MARGIN_X + size + 2.6 * mm, top - 4.3 * mm, BRAND)
            self.setFillColor(colors.HexColor(MUTED))
            self.setFont(fonts["regular"], 8)
            self.drawRightString(right, top - 4.3 * mm, f"{meta.title} report")

            self.setStrokeColor(colors.HexColor(LINE_STRONG))
            self.setLineWidth(0.6)
            self.line(MARGIN_X, top - size - 3 * mm, right, top - size - 3 * mm)

            # Footer
            footer_y = 10 * mm
            self.setStrokeColor(colors.HexColor(LINE))
            self.line(MARGIN_X, footer_y + 4.2 * mm, right, footer_y + 4.2 * mm)
            self.setFont(fonts["regular"], 7.5)
            self.setFillColor(colors.HexColor(MUTED))
            self.drawString(MARGIN_X, footer_y, f"Generated {meta.generated_text} by {meta.generated_by}")
            self.drawCentredString(width / 2, footer_y, "Confidential  ·  For internal use only")
            self.setFont(fonts["medium"], 7.5)
            self.setFillColor(colors.HexColor(TEXT))
            self.drawRightString(right, footer_y, f"Page {self._pageNumber} of {total}")

    return ReportCanvas


def build_pdf(
    meta: ReportMeta,
    columns: Sequence[ExportColumn],
    rows: list[list],
    cell_colors: list[list[str | None]] | None = None,
) -> bytes:
    fonts = report_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{meta.title} report",
        author=BRAND,
        subject=f"{meta.title} exported from {BRAND}",
        creator=BRAND,
    )

    def style(name, font="regular", size=CELL_SIZE, leading=None, color=TEXT, align="left", **extra):
        return ParagraphStyle(
            name,
            fontName=fonts[font],
            fontSize=size,
            leading=leading or size * 1.38,
            textColor=colors.HexColor(color),
            alignment=_ALIGN[align],
            **extra,
        )

    kicker_style = style("kicker", "semibold", 7.5, color=ACCENT)
    title_style = style("title", "semibold", 21, leading=26, color=INK)
    lead_style = style("lead", size=9, color=MUTED)
    label_style = style("label", "medium", 6.8, color=MUTED)
    value_style = style("value", "medium", 9.2, leading=12.5, color=INK)

    # ---- page-one header block --------------------------------------------
    story = [
        Paragraph("REPORT", kicker_style),
        Spacer(1, 1 * mm),
        Paragraph(escape(meta.title), title_style),
        Spacer(1, 0.8 * mm),
        Paragraph(f"Exported from {BRAND} with the search, filters and sort order shown below.", lead_style),
        Spacer(1, 5 * mm),
    ]

    summary_cells = [
        ("RECORDS", meta.records_text),
        ("GENERATED", meta.generated_text),
        ("PREPARED BY", meta.generated_by),
        ("FILTERS", "; ".join(meta.filters) if meta.filters else "None (all records)"),
    ]
    summary = Table(
        [[[Paragraph(label, label_style), Spacer(1, 1 * mm), Paragraph(escape(value), value_style)]
          for label, value in summary_cells]],
        colWidths=[doc.width * w for w in (0.15, 0.2, 0.2, 0.45)],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ACCENT_SOFT)),
        ("LINEABOVE", (0, 0), (-1, 0), 1.6, colors.HexColor(ACCENT)),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, colors.HexColor(LINE_STRONG)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [summary, Spacer(1, 7 * mm)]

    # ---- data table -----------------------------------------------------------
    styles_cache: dict[tuple, ParagraphStyle] = {}

    def cell_style(column: ExportColumn, color: str | None) -> ParagraphStyle:
        key = (column.align, column.strong, color)
        if key not in styles_cache:
            if color:
                styles_cache[key] = style(f"c{len(styles_cache)}", "semibold", color=readable(color), align=column.align)
            elif column.strong:
                styles_cache[key] = style(f"c{len(styles_cache)}", "medium", color=INK, align=column.align)
            else:
                styles_cache[key] = style(f"c{len(styles_cache)}", align=column.align)
        return styles_cache[key]

    head_styles = {a: style(f"h-{a}", "semibold", HEAD_SIZE, color="#475467", align=a) for a in _ALIGN}
    blank_styles = {a: style(f"blank-{a}", color="#98A2B3", align=a) for a in _ALIGN}

    texts = []
    for row_index, row in enumerate(rows):
        row_texts = []
        for col_index, value in enumerate(row):
            text = display_text(value, for_pdf=True)
            if cell_colors and cell_colors[row_index][col_index]:
                text = text.replace(" ", NBSP)  # short coloured values ("In Progress") stay on one line
            row_texts.append(text)
        texts.append(row_texts)
    data = [[Paragraph(escape(c.header.upper()), head_styles[c.align]) for c in columns]]
    for row_index, row in enumerate(texts):
        row_colors = cell_colors[row_index] if cell_colors else [None] * len(columns)
        cells = []
        for text, column, color in zip(row, columns, row_colors):
            if not text.strip():
                cells.append(Paragraph("—", blank_styles[column.align]))  # clearly "no value"
            else:
                cells.append(Paragraph(escape(text).replace("\n", "<br/>"), cell_style(column, color)))
        data.append(cells)
    if not rows:
        empty_style = style("empty", size=9, color=MUTED, align="center")
        data.append([Paragraph("No records match the current search and filters.", empty_style)]
                    + [""] * (len(columns) - 1))

    widths = _column_widths(columns, texts, cell_colors, fonts, doc.width)
    table = Table(data, colWidths=widths, repeatRows=1)
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEAD_BG)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, colors.HexColor(LINE_STRONG)),
        ("LINEBELOW", (0, 1), (-1, -1), 0.45, colors.HexColor(LINE)),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]
    for i in range(2, len(data), 2):
        table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(ZEBRA)))
    if not rows:
        table_style += [("SPAN", (0, 1), (-1, 1)), ("TOPPADDING", (0, 1), (-1, 1), 14),
                        ("BOTTOMPADDING", (0, 1), (-1, 1), 14)]
    table.setStyle(TableStyle(table_style))
    story.append(table)

    doc.build(story, canvasmaker=_report_canvas(meta, fonts))
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Registry of supported formats
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ExportFormat:
    key: str
    label: str
    extension: str
    content_type: str
    builder: Callable[..., bytes]


EXPORT_FORMATS: dict[str, ExportFormat] = {
    "pdf": ExportFormat("pdf", "PDF", "pdf", "application/pdf", build_pdf),
    "xlsx": ExportFormat(
        "xlsx",
        "Excel",
        "xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        build_xlsx,
    ),
}
