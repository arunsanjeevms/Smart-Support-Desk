"""Turn a list of rows into PDF or Excel bytes."""

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from typing import Callable, Sequence
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .columns import ExportColumn

BRAND = "Smart Support Desk"
HEADER_HEX = "1E3A5F"
ZEBRA_HEX = "F4F6FA"
BORDER_HEX = "D9DEE7"
MUTED_HEX = "667085"


def display_text(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %H:%M")
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    return "" if value is None else str(value)


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def build_xlsx(title: str, subtitle: str, columns: Sequence[ExportColumn], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = (title[:28] or "Report").replace("/", "-")

    last_col = get_column_letter(len(columns))
    ws["A1"] = f"{BRAND} - {title}"
    ws["A1"].font = Font(size=14, bold=True, color=HEADER_HEX)
    ws["A2"] = subtitle
    ws["A2"].font = Font(size=10, italic=True, color=MUTED_HEX)
    ws.merge_cells(f"A1:{last_col}1")
    ws.merge_cells(f"A2:{last_col}2")

    header_row = 4
    thin = Side(style="thin", color=BORDER_HEX)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill("solid", fgColor=HEADER_HEX)
    zebra_fill = PatternFill("solid", fgColor=ZEBRA_HEX)

    for idx, column in enumerate(columns, start=1):
        cell = ws.cell(row=header_row, column=idx, value=column.header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")
        cell.border = border
        ws.column_dimensions[get_column_letter(idx)].width = column.width

    for r, row in enumerate(rows, start=header_row + 1):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)
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
class _NumberedCanvas(pdf_canvas.Canvas):
    """Canvas that prints 'Page x of y' once the total page count is known."""

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
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total):
        width, _ = self._pagesize
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor(f"#{MUTED_HEX}"))
        self.drawString(15 * mm, 8 * mm, BRAND)
        self.drawRightString(width - 15 * mm, 8 * mm, f"Page {self._pageNumber} of {total}")


def build_pdf(title: str, subtitle: str, columns: Sequence[ExportColumn], rows: list[list]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
        title=f"{BRAND} - {title}",
        author=BRAND,
    )

    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=15, leading=19,
        textColor=colors.HexColor(f"#{HEADER_HEX}"),
    )
    meta_style = ParagraphStyle(
        "meta", fontName="Helvetica", fontSize=8.5, leading=11,
        textColor=colors.HexColor(f"#{MUTED_HEX}"),
    )
    head_style = ParagraphStyle(
        "head", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=colors.white,
    )
    cell_style = ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10)

    total_weight = sum(c.width for c in columns) or 1
    col_widths = [doc.width * c.width / total_weight for c in columns]

    data = [[Paragraph(escape(c.header), head_style) for c in columns]]
    for row in rows:
        data.append(
            [Paragraph(escape(display_text(v)).replace("\n", "<br/>"), cell_style) for v in row]
        )
    if not rows:
        data.append(
            [Paragraph("No records match the current filters.", cell_style)]
            + [""] * (len(columns) - 1)
        )

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{HEADER_HEX}")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(f"#{BORDER_HEX}")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(f"#{ZEBRA_HEX}")))
    if not rows:
        style.append(("SPAN", (0, 1), (-1, 1)))
    table.setStyle(TableStyle(style))

    story = [
        Paragraph(escape(title), title_style),
        Spacer(1, 2 * mm),
        Paragraph(escape(subtitle), meta_style),
        Spacer(1, 5 * mm),
        table,
    ]
    doc.build(story, canvasmaker=_NumberedCanvas)
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
