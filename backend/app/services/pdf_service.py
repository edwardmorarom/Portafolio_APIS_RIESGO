from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


USTA_BLUE = colors.HexColor("#1D4ED8")
USTA_WINE = colors.HexColor("#8A1538")
TEXT_MAIN = colors.HexColor("#0B132B")
TEXT_SOFT = colors.HexColor("#243B53")
TEXT_MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#D8E1EF")
LIGHT_BG = colors.HexColor("#F4F8FF")
SOFT_WINE_BG = colors.HexColor("#FFF7FA")


class BookmarkFlowable(Flowable):
    """Crea un destino interno clicable dentro del PDF."""

    def __init__(self, key: str, title: str, level: int = 0) -> None:
        super().__init__()
        self.key = key
        self.title = title
        self.level = level

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        self.canv.bookmarkPage(self.key)
        try:
            self.canv.addOutlineEntry(
                title=self.title,
                key=self.key,
                level=self.level,
                closed=False,
            )
        except Exception:
            pass


class IndexLinkFlowable(Flowable):
    """Fila visual del índice con link interno."""

    def __init__(self, number: int, title: str, destination: str) -> None:
        super().__init__()
        self.number = number
        self.title = title
        self.destination = destination
        self.height = 30
        self.width = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        canvas = self.canv
        width = self.width
        height = self.height

        canvas.saveState()

        canvas.setFillColor(colors.white)
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.65)
        canvas.roundRect(0, 0, width, height, 7, stroke=1, fill=1)

        canvas.setFillColor(USTA_WINE)
        canvas.roundRect(7, 6, 30, height - 12, 6, stroke=0, fill=1)

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8.3)
        canvas.drawCentredString(22, 11, f"{self.number:02d}")

        canvas.setFillColor(TEXT_MAIN)
        canvas.setFont("Helvetica-Bold", 9.2)
        canvas.drawString(46, 10.5, self.title[:85])

        canvas.setFillColor(USTA_BLUE)
        canvas.setFont("Helvetica", 7.2)
        canvas.drawRightString(width - 10, 10.5, "Ir a sección")

        canvas.linkRect(
            contents="",
            destinationname=self.destination,
            Rect=(0, 0, width, height),
            relative=1,
            thickness=0,
        )

        canvas.restoreState()


def _find_logo_path() -> Path | None:
    candidates = [
        Path("frontend/assets/escudo_santo_tomas.png"),
        Path("../frontend/assets/escudo_santo_tomas.png"),
        Path("/app/frontend/assets/escudo_santo_tomas.png"),
        Path("/app/backend/frontend/assets/escudo_santo_tomas.png"),
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def _safe_text(value: Any) -> str:
    if value is None:
        return "N/D"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "N/D"
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items()) if value else "N/D"
    return str(value)


def _paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_safe_text(value)), style)


def _html_paragraph(value: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(value, style)


def _section_header(number: int, title: str, title_style: ParagraphStyle) -> Table:
    table = Table(
        [
            [
                _html_paragraph(
                    f"<b>{number:02d}</b>",
                    title_style,
                ),
                _paragraph(title, title_style),
            ]
        ],
        colWidths=[0.48 * inch, 6.07 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), USTA_WINE),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("BACKGROUND", (1, 0), (1, 0), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _body_card(body: str, body_style: ParagraphStyle) -> Table:
    card = Table(
        [[_paragraph(body, body_style)]],
        colWidths=[6.55 * inch],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3, USTA_WINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return card


def _key_value_table(
    items: dict[str, Any],
    label_style: ParagraphStyle,
    body_style: ParagraphStyle,
) -> Table:
    rows = []

    for key, value in items.items():
        label = str(key).replace("_", " ").title()
        rows.append(
            [
                _html_paragraph(f"<b>{escape(label)}</b>", label_style),
                _paragraph(value, body_style),
            ]
        )

    if not rows:
        rows = [[_paragraph("Sin datos", label_style), _paragraph("N/D", body_style)]]

    table = Table(rows, colWidths=[2.05 * inch, 4.50 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _two_column_table(
    rows_payload: list[dict[str, Any]],
    left_key: str,
    right_key: str,
    left_title: str,
    right_title: str,
    header_style: ParagraphStyle,
    body_style: ParagraphStyle,
) -> Table:
    rows = [
        [
            _html_paragraph(f"<b>{escape(left_title)}</b>", header_style),
            _html_paragraph(f"<b>{escape(right_title)}</b>", header_style),
        ]
    ]

    for item in rows_payload:
        rows.append(
            [
                _paragraph(item.get(left_key, "N/D"), body_style),
                _paragraph(item.get(right_key, "N/D"), body_style),
            ]
        )

    table = Table(rows, colWidths=[1.70 * inch, 4.85 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _bullet_list_table(items: list[str], body_style: ParagraphStyle) -> Table:
    rows = [[_paragraph(f"• {item}", body_style)] for item in items]

    if not rows:
        rows = [[_paragraph("Sin conclusiones registradas.", body_style)]]

    table = Table(rows, colWidths=[6.55 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_WINE_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _add_optional_charts(
    elements: list,
    charts: list[dict[str, Any]],
    title_style: ParagraphStyle,
    body_style: ParagraphStyle,
) -> None:
    """
    Soporte preparado para gráficas futuras.

    Cada gráfico podrá llegar como:
    {"title": "...", "path": "ruta/imagen.png", "caption": "..."}
    """
    if not charts:
        return

    elements.append(Spacer(1, 8))
    elements.append(_paragraph("Gráficas principales", title_style))

    for chart in charts:
        chart_path = Path(str(chart.get("path", "")))
        if not chart_path.exists():
            continue

        elements.append(_paragraph(chart.get("title", "Gráfica"), body_style))
        elements.append(Image(str(chart_path), width=6.15 * inch, height=3.05 * inch))

        caption = chart.get("caption")
        if caption:
            elements.append(_paragraph(caption, body_style))

        elements.append(Spacer(1, 8))


def build_executive_pdf(report_data: dict) -> bytes:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=34,
        bottomMargin=32,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InstitutionalTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=21,
        textColor=TEXT_MAIN,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        fontSize=8.6,
        leading=11.5,
        textColor=TEXT_SOFT,
    )

    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=10.6,
        leading=13,
        textColor=USTA_WINE,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8.45,
        leading=11.2,
        textColor=TEXT_SOFT,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=7.6,
        leading=9.6,
        textColor=TEXT_MUTED,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["BodyText"],
        fontSize=8.2,
        leading=10.5,
        textColor=TEXT_MAIN,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["BodyText"],
        fontSize=7.4,
        leading=9.4,
        textColor=TEXT_MUTED,
        alignment=1,
    )

    elements = []

    logo_path = _find_logo_path()
    logo = Image(str(logo_path), width=0.62 * inch, height=0.62 * inch) if logo_path else ""

    title = _paragraph(report_data.get("report_title", "Reporte Ejecutivo"), title_style)
    meta = _html_paragraph(
        f"<b>Institución:</b> {escape(_safe_text(report_data.get('institution', '')))}<br/>"
        f"<b>Proyecto:</b> {escape(_safe_text(report_data.get('project', '')))}<br/>"
        f"<b>Fecha:</b> {escape(_safe_text(report_data.get('generated_at', '')))}",
        subtitle_style,
    )

    header_table = Table(
        [[logo, title], ["", meta]],
        colWidths=[0.78 * inch, 6.12 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("SPAN", (0, 0), (0, 1)),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 2, USTA_BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    summary_table = Table(
        [
            [
                _html_paragraph("<b>Estado</b><br/>PDF ejecutivo", body_style),
                _html_paragraph("<b>Moneda base</b><br/>USD", body_style),
                _html_paragraph("<b>Alcance</b><br/>Riesgo · ML · Perri", body_style),
            ]
        ],
        colWidths=[2.15 * inch, 2.15 * inch, 2.15 * inch],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    sections = report_data.get("sections", [])
    toc_items = []

    for index, section in enumerate(sections, start=1):
        title_text = str(section.get("title", f"Sección {index}"))
        clean_title = title_text.split(".", 1)[-1].strip() if "." in title_text[:4] else title_text
        toc_items.append(
            {
                "number": index,
                "title": clean_title,
                "destination": f"section_{index}",
            }
        )

    elements.append(_paragraph("Índice ejecutivo", section_title_style))
    elements.append(
        _paragraph(
            "Haz clic en cualquier fila para ir directamente a la sección correspondiente dentro del PDF.",
            small_style,
        )
    )
    elements.append(Spacer(1, 6))

    for item in toc_items:
        elements.append(
            IndexLinkFlowable(
                number=item["number"],
                title=item["title"],
                destination=item["destination"],
            )
        )
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 8))
    elements.append(_paragraph("Configuración del portafolio", section_title_style))
    elements.append(
        _key_value_table(
            report_data.get("portfolio_context", {}),
            table_header_style,
            body_style,
        )
    )

    elements.append(PageBreak())

    for index, section in enumerate(sections, start=1):
        title_text = str(section.get("title", f"Sección {index}"))
        clean_title = title_text.split(".", 1)[-1].strip() if "." in title_text[:4] else title_text
        body_text = str(section.get("description", ""))

        block = [
            BookmarkFlowable(f"section_{index}", clean_title),
            _section_header(index, clean_title, section_title_style),
            Spacer(1, 5),
            _body_card(body_text, body_style),
        ]

        if index == 2:
            block.extend(
                [
                    Spacer(1, 8),
                    _two_column_table(
                        report_data.get("methodology_decisions", []),
                        left_key="decision",
                        right_key="detail",
                        left_title="Decisión",
                        right_title="Justificación",
                        header_style=table_header_style,
                        body_style=body_style,
                    ),
                ]
            )

        if index == 3:
            block.extend(
                [
                    Spacer(1, 8),
                    _two_column_table(
                        report_data.get("architecture_layers", []),
                        left_key="layer",
                        right_key="detail",
                        left_title="Capa",
                        right_title="Descripción",
                        header_style=table_header_style,
                        body_style=body_style,
                    ),
                ]
            )

        if index == 4:
            block.extend(
                [
                    Spacer(1, 8),
                    _key_value_table(
                        report_data.get("key_results", {}),
                        table_header_style,
                        body_style,
                    ),
                ]
            )

        if index == 5:
            block.extend(
                [
                    Spacer(1, 8),
                    _bullet_list_table(
                        report_data.get("conclusions", []),
                        body_style,
                    ),
                ]
            )

        elements.append(KeepTogether(block))
        elements.append(Spacer(1, 12))

        if index == 4:
            _add_optional_charts(
                elements=elements,
                charts=report_data.get("charts", []),
                title_style=section_title_style,
                body_style=body_style,
            )

    elements.append(Spacer(1, 8))
    elements.append(_paragraph("Stack técnico", section_title_style))
    elements.append(_paragraph(" · ".join(report_data.get("technical_stack", [])), body_style))
    elements.append(Spacer(1, 12))

    elements.append(
        _paragraph(
            "Portafolio Riesgo USTA · Reporte generado automáticamente desde backend FastAPI",
            footer_style,
        )
    )

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
