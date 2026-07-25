"""Geração do relatório PDF de exames finalizados."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Polygon, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DARK_GREEN = colors.HexColor("#0f5132")
PRIMARY_GREEN = colors.HexColor("#198754")
LIGHT_GREEN = colors.HexColor("#d1e7dd")
BORDER_GREEN = colors.HexColor("#75b798")
SOFT_GREEN = colors.HexColor("#f1f8f4")
TEXT_COLOR = colors.HexColor("#212529")
SECONDARY_TEXT = colors.HexColor("#6c757d")
LIGHT_BORDER = colors.HexColor("#d8e4dc")

MODEL_DISPLAY_NAMES = {
    "ensemble_stacking": "ClinicAI ES Gastrointestinal",
    "clinicai_stacking": "ClinicAI ES Gastrointestinal",
}

EXAM_TYPE_LABELS = {
    "colonoscopy": "Colonoscopia",
    "endoscopy": "Endoscopia digestiva alta",
}

STATUS_LABELS = {
    "completed": "Concluído",
    "completed_with_divergence": "Concluído com divergência",
}

PREDICTION_LABELS = {
    "normal": "Normal",
    "abnormal": "Anormal",
}


def _safe(value) -> str:
    if value is None or value == "":
        return "-"
    return escape(str(value))


def _format_date(value: date | datetime | None) -> str:
    if value is None:
        return "-"

    if isinstance(value, datetime):
        value = value.date()

    return value.strftime("%d/%m/%Y")


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"

    return value.strftime("%d/%m/%Y às %H:%M")


def _format_cpf(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")

    if len(digits) != 11:
        return value or "-"

    return (
        f"{digits[:3]}.{digits[3:6]}."
        f"{digits[6:9]}-{digits[9:]}"
    )


def _format_confidence(value: float | None) -> str:
    if value is None:
        return "-"

    return f"{round(float(value) * 100)}%"


def _model_display_name(model_name: str | None) -> str:
    return MODEL_DISPLAY_NAMES.get(
        model_name,
        model_name or "-",
    )


def _slugify(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value)
    return slug.strip("-").lower() or "paciente"


def build_exam_report_filename(exam) -> str:
    patient_name = (
        exam.patient.name
        if getattr(exam, "patient", None)
        else None
    )

    return (
        f"relatorio-exame-{exam.id}-"
        f"{_slugify(patient_name)}.pdf"
    )




def _build_logo() -> Drawing:
    """Desenha o símbolo vetorial do ClinicAI."""

    drawing = Drawing(30, 30)

    drawing.add(
        Rect(
            0.75,
            0.75,
            28.5,
            28.5,
            rx=7.1,
            ry=7.1,
            fillColor=DARK_GREEN,
            strokeColor=colors.HexColor("#5dd39e"),
            strokeWidth=1.1,
        )
    )

    drawing.add(
        Polygon(
            [
                11.625, 24.75,
                18.375, 24.75,
                18.375, 18.375,
                24.75, 18.375,
                24.75, 11.625,
                18.375, 11.625,
                18.375, 5.25,
                11.625, 5.25,
                11.625, 11.625,
                5.25, 11.625,
                5.25, 18.375,
                11.625, 18.375,
            ],
            fillColor=LIGHT_GREEN,
            strokeColor=None,
        )
    )

    drawing.add(
        PolyLine(
            [
                6.75, 14.25,
                10.125, 14.25,
                11.625, 17.25,
                13.875, 10.5,
                16.5, 19.875,
                18.75, 14.25,
                22.5, 14.25,
            ],
            strokeColor=PRIMARY_GREEN,
            strokeWidth=1.65,
            strokeLineCap=1,
            strokeLineJoin=1,
        )
    )

    return drawing


def _build_styles():
    sample = getSampleStyleSheet()

    return {
        "brand": ParagraphStyle(
            "ClinicAIBrand",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=16,
            textColor=DARK_GREEN,
        ),
        "brand_subtitle": ParagraphStyle(
            "ClinicAIBrandSubtitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=9,
            textColor=SECONDARY_TEXT,
        ),
        "title": ParagraphStyle(
            "ClinicAITitle",
            parent=sample["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=TEXT_COLOR,
            spaceAfter=0,
            leftIndent=-1.5 * mm,
            firstLineIndent=0,
        ),
        "subtitle": ParagraphStyle(
            "ClinicAISubtitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=SECONDARY_TEXT,
        ),
        "section": ParagraphStyle(
            "ClinicAISection",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=11,
            textColor=DARK_GREEN,
        ),
        "section_right": ParagraphStyle(
            "ClinicAISectionRight",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=2,
            textColor=DARK_GREEN,
        ),
        "field": ParagraphStyle(
            "ClinicAIField",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=TEXT_COLOR,
        ),
        "image_title": ParagraphStyle(
            "ClinicAIImageTitle",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=1,
            textColor=TEXT_COLOR,
        ),
        "placeholder": ParagraphStyle(
            "ClinicAIPlaceholder",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            alignment=1,
            textColor=SECONDARY_TEXT,
        ),
        "notice": ParagraphStyle(
            "ClinicAINotice",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8,
            textColor=SECONDARY_TEXT,
        ),
    }


def _field(label: str, value, styles) -> Paragraph:
    return Paragraph(
        (
            f'<font color="#6c757d" size="7">'
            f"{escape(label)}</font><br/>"
            f"<b>{_safe(value)}</b>"
        ),
        styles["field"],
    )



def _card(
    title: str,
    body,
    content_width,
    styles,
    *,
    title_right: str | None = None,
) -> Table:
    if title_right:
        header = Table(
            [
                [
                    Paragraph(title, styles["section"]),
                    Paragraph(
                        title_right,
                        styles["section_right"],
                    ),
                ]
            ],
            colWidths=[
                content_width * 0.57,
                content_width * 0.43,
            ],
        )
    else:
        header = Table(
            [[Paragraph(title, styles["section"])]],
            colWidths=[content_width],
        )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_GREEN,
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    card = Table(
        [
            [header],
            [body],
        ],
        colWidths=[content_width],
        splitByRow=1,
    )

    card.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    BORDER_GREEN,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    0.8,
                    BORDER_GREEN,
                ),
                ("LEFTPADDING", (0, 0), (-1, 0), 0),
                ("RIGHTPADDING", (0, 0), (-1, 0), 0),
                ("TOPPADDING", (0, 0), (-1, 0), 0),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                ("LEFTPADDING", (0, 1), (-1, -1), 8),
                ("RIGHTPADDING", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.white,
                ),
            ]
        )
    )

    return card


def _scaled_image(
    path: Path | None,
    *,
    max_width: float,
    max_height: float,
):
    if path is None or not path.exists() or not path.is_file():
        return None

    try:
        image = Image(str(path))

        width_scale = max_width / image.imageWidth
        height_scale = max_height / image.imageHeight
        scale = min(width_scale, height_scale, 1)

        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        image.hAlign = "CENTER"

        return image
    except Exception:
        return None




def _build_activation_scale(
    max_width: float,
) -> Drawing:
    """Desenha a escala qualitativa do mapa de atribuição."""

    drawing_height = 8 * mm
    drawing = Drawing(
        max_width,
        drawing_height,
    )

    bar_width = max_width * 0.78
    bar_height = 5
    bar_x = (max_width - bar_width) / 2
    bar_y = 11

    color_stops = [
        (0.00, (0.05, 0.18, 0.72)),
        (0.30, (0.00, 0.78, 0.95)),
        (0.65, (1.00, 0.88, 0.00)),
        (1.00, (0.88, 0.02, 0.02)),
    ]

    def interpolate(position):
        for index in range(
            len(color_stops) - 1
        ):
            start_position, start_color = (
                color_stops[index]
            )
            end_position, end_color = (
                color_stops[index + 1]
            )

            if (
                start_position
                <= position
                <= end_position
            ):
                interval = (
                    end_position - start_position
                )

                ratio = (
                    (
                        position
                        - start_position
                    )
                    / interval
                    if interval
                    else 0
                )

                return colors.Color(
                    start_color[0]
                    + (
                        end_color[0]
                        - start_color[0]
                    )
                    * ratio,
                    start_color[1]
                    + (
                        end_color[1]
                        - start_color[1]
                    )
                    * ratio,
                    start_color[2]
                    + (
                        end_color[2]
                        - start_color[2]
                    )
                    * ratio,
                )

        return colors.Color(
            *color_stops[-1][1]
        )

    segments = 96
    segment_width = bar_width / segments

    for index in range(segments):
        position = index / (segments - 1)

        drawing.add(
            Rect(
                bar_x
                + index * segment_width,
                bar_y,
                segment_width + 0.25,
                bar_height,
                fillColor=interpolate(
                    position
                ),
                strokeColor=None,
            )
        )

    drawing.add(
        Rect(
            bar_x,
            bar_y,
            bar_width,
            bar_height,
            fillColor=None,
            strokeColor=LIGHT_BORDER,
            strokeWidth=0.4,
        )
    )

    drawing.add(
        String(
            bar_x,
            1.5,
            "Baixa Ativação",
            fontName="Helvetica",
            fontSize=6.2,
            fillColor=SECONDARY_TEXT,
        )
    )

    drawing.add(
        String(
            bar_x + bar_width,
            1.5,
            "Alta Ativação",
            fontName="Helvetica",
            fontSize=6.2,
            fillColor=SECONDARY_TEXT,
            textAnchor="end",
        )
    )

    return drawing


def _image_cell(
    title: str,
    path: Path | None,
    *,
    max_width: float,
    max_height: float,
    styles,
    show_activation_scale: bool = False,
):
    image = _scaled_image(
        path,
        max_width=max_width,
        max_height=max_height,
    )

    visual = (
        image
        if image is not None
        else Paragraph(
            "Imagem não disponível.",
            styles["placeholder"],
        )
    )

    rows = [
        [
            Paragraph(
                title,
                styles["image_title"],
            )
        ],
        [visual],
    ]

    if (
        show_activation_scale
        and image is not None
    ):
        rows.append(
            [
                _build_activation_scale(
                    max_width
                )
            ]
        )

    cell = Table(
        rows,
        colWidths=[max_width],
    )

    style_commands = [
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER",
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, 0),
            4,
        ),
    ]

    if (
        show_activation_scale
        and image is not None
    ):
        style_commands.append(
            (
                "TOPPADDING",
                (0, 2),
                (0, 2),
                3,
            )
        )

    cell.setStyle(
        TableStyle(style_commands)
    )

    return cell


def _draw_footer(canvas, document):
    canvas.saveState()

    page_width, _ = A4
    footer_y = 6 * mm

    canvas.setStrokeColor(LIGHT_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(
        13 * mm,
        footer_y + 3 * mm,
        page_width - 13 * mm,
        footer_y + 3 * mm,
    )

    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(SECONDARY_TEXT)

    canvas.drawString(
        13 * mm,
        footer_y,
        "ClinicAI - Relatório de Suporte à Análise Médica",
    )

    canvas.drawRightString(
        page_width - 13 * mm,
        footer_y,
        f"Página {document.page}",
    )

    canvas.restoreState()


def generate_exam_report_pdf(
    exam,
    *,
    original_image_path: Path | None = None,
    gradcam_path: Path | None = None,
) -> bytes:
    """Gera um relatório compacto em uma página A4."""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=13 * mm,
        title=f"Relatório do exame {exam.id}",
        author="ClinicAI",
        subject="Relatório de exame finalizado",
    )

    styles = _build_styles()
    content_width = (
        A4[0]
        - document.leftMargin
        - document.rightMargin
    )

    patient = getattr(exam, "patient", None)
    clinic = getattr(exam, "clinic", None)
    doctor = getattr(exam, "doctor", None)
    analysis = getattr(exam, "ai_analysis", None)

    story = []

    header = Table(
        [
            [
                _build_logo(),
                [
                    Paragraph(
                        "ClinicAI",
                        styles["brand"],
                    ),
                    Spacer(1, 0.8 * mm),
                    Paragraph(
                        (
                            "Sistema de Suporte à Análise "
                            "de Exames"
                        ),
                        styles["brand_subtitle"],
                    ),
                ],
            ]
        ],
        colWidths=[
            12 * mm,
            content_width - 12 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 1.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 2.5 * mm))
    story.append(
        Paragraph(
            "Relatório do Exame",
            styles["title"],
        )
    )
    story.append(Spacer(1, 2.5 * mm))

    compact_table_style = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )

    patient_table = Table(
        [
            [
                _field(
                    "Clínica",
                    getattr(clinic, "name", None),
                    styles,
                ),
                _field(
                    "Médico Responsável",
                    getattr(doctor, "name", None),
                    styles,
                ),
            ],
            [
                _field(
                    "Paciente",
                    getattr(patient, "name", None),
                    styles,
                ),
                _field(
                    "CPF",
                    _format_cpf(
                        getattr(patient, "cpf", None)
                    ),
                    styles,
                ),
            ],
            [
                _field(
                    "Tipo de Exame",
                    EXAM_TYPE_LABELS.get(
                        getattr(exam, "exam_type", None),
                        getattr(exam, "exam_type", None),
                    ),
                    styles,
                ),
                _field(
                    "Data de Nascimento",
                    _format_date(
                        getattr(
                            patient,
                            "birth_date",
                            None,
                        )
                    ),
                    styles,
                ),
            ],
        ],
        colWidths=[
            (content_width - 16) * 0.58,
            (content_width - 16) * 0.42,
        ],
    )

    patient_table.setStyle(compact_table_style)

    story.append(
        _card(
            "Paciente e Exame",
            patient_table,
            content_width,
            styles,
            title_right=(
                "Data do Exame: "
                f"<b>{_format_date(getattr(exam, 'exam_date', None))}</b>"
            ),
        )
    )
    story.append(Spacer(1, 2.4 * mm))

    review_table = Table(
        [
            [
                _field(
                    "Achados",
                    getattr(exam, "findings", None),
                    styles,
                )
            ],
            [
                _field(
                    "Conclusão",
                    getattr(exam, "conclusion", None),
                    styles,
                )
            ],
        ],
        colWidths=[content_width - 16],
    )

    review_table.setStyle(compact_table_style)

    story.append(
        _card(
            "Revisão Médica",
            review_table,
            content_width,
            styles,
            title_right=(
                "Data da Revisão: "
                f"<b>{_format_date(getattr(exam, 'reviewed_at', None))}</b>"
            ),
        )
    )
    story.append(Spacer(1, 2.4 * mm))

    analysis_table = Table(
        [
            [
                _field(
                    "Resultado",
                    PREDICTION_LABELS.get(
                        getattr(
                            analysis,
                            "prediction_label",
                            None,
                        ),
                        getattr(
                            analysis,
                            "prediction_label",
                            None,
                        ),
                    ),
                    styles,
                ),
                _field(
                    "Confiança",
                    _format_confidence(
                        getattr(
                            analysis,
                            "confidence",
                            None,
                        )
                    ),
                    styles,
                ),
                _field(
                    "Modelo",
                    _model_display_name(
                        getattr(
                            analysis,
                            "model_name",
                            None,
                        )
                    ),
                    styles,
                ),
            ]
        ],
        colWidths=[
            (content_width - 16) * 0.20,
            (content_width - 16) * 0.16,
            (content_width - 16) * 0.64,
        ],
    )

    analysis_table.setStyle(compact_table_style)

    story.append(
        _card(
            "Análise Automatizada",
            analysis_table,
            content_width,
            styles,
        )
    )
    story.append(Spacer(1, 2.4 * mm))

    image_width = (content_width - 16) / 2

    images_table = Table(
        [
            [
                _image_cell(
                    "Imagem Original",
                    original_image_path,
                    max_width=image_width - 6,
                    max_height=63 * mm,
                    styles=styles,
                ),
                _image_cell(
                    "Mapa de Atribuição",
                    gradcam_path,
                    max_width=image_width - 6,
                    max_height=63 * mm,
                    styles=styles,
                    show_activation_scale=True,
                ),
            ]
        ],
        colWidths=[image_width, image_width],
    )

    images_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LINEAFTER",
                    (0, 0),
                    (0, -1),
                    0.5,
                    LIGHT_BORDER,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(
        _card(
            "Imagens do Exame",
            images_table,
            content_width,
            styles,
        )
    )
    story.append(Spacer(1, 2 * mm))

    notice = Table(
        [
            [
                Paragraph(
                    (
                        "<b>Aviso:</b> o resultado automatizado "
                        "é um recurso de suporte e não substitui "
                        "a avaliação do profissional responsável."
                    ),
                    styles["notice"],
                )
            ]
        ],
        colWidths=[content_width],
    )

    notice.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    SOFT_GREEN,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER_GREEN,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(notice)

    document.build(
        story,
        onFirstPage=_draw_footer,
        onLaterPages=_draw_footer,
    )

    return buffer.getvalue()
