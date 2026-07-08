from __future__ import annotations

#import matplotlib.pyplot as plt

import os
from datetime import datetime
from io import BytesIO
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import time

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None

PROGRAM_NAME = "تقرير العصعص لتحليل المبيعات"
PROGRAM_SUBTITLE = "Al-osos Professional Sales Analyzer 2026"
DEVELOPER_NAME = "المهندس المالي : عزت العصعص | أتمتة الأعمال بلغة البايثون والذكاء الاصطناعي"
CONTACT_LINE = "للتواصل : 777884468"

PAGE_SIZE = landscape(A4)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

NAVY = "#1e3a8a"
BLUE = "#2563eb"
LIGHT_BLUE = "#60a5fa"
PALE_BLUE = "#dbeafe"
WHITE = "#ffffff"

LOGO_PATH = "logo.png"


def _register_arabic_font() -> str:
    """تسجيل خط عربي - البحث في مجلد المشروع أولاً"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ============================================================
    # 1. البحث في مجلد المشروع الرئيسي (بجانب app.py)
    # ============================================================
    font_files = ["arial.ttf", "tahoma.ttf", "times.ttf", "ARIAL.TTF", "Tahoma.ttf", "Times.ttf"]
    
    for font_file in font_files:
        font_path = os.path.join(current_dir, font_file)
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
                print(f"✅ تم تحميل الخط: {font_path}")
                return "ArabicFont"
            except Exception as e:
                print(f"⚠️ فشل تحميل {font_file}: {e}")
                continue
    
    # ============================================================
    # 2. البحث في نظام Windows (احتياطي)
    # ============================================================
    system_fonts = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\times.ttf",
    ]
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
                print(f"✅ تم تحميل الخط من النظام: {font_path}")
                return "ArabicFont"
            except Exception as e:
                continue
    
    print("❌ لم يتم العثور على خط عربي!")
    print("💡 يرجى وضع ملف arial.ttf في مجلد المشروع")
    return "Helvetica"


FONT_NAME = _register_arabic_font()


def _rtl(value) -> str:
    """تحويل النص إلى RTL مع تشكيل مناسب."""
    text = "" if pd.isna(value) else str(value)
    if arabic_reshaper and get_display:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
    return text


def _money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value) -> str:
    try:
        return f"{float(value):,.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName=FONT_NAME,
            fontSize=30,
            leading=40,
            alignment=TA_CENTER,
            textColor=colors.HexColor(NAVY),
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=13,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor(BLUE),
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=15,
            leading=20,
            alignment=TA_RIGHT,
            textColor=colors.white,
        ),
        "normal": ParagraphStyle(
            "ArabicNormal",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=16,
            alignment=TA_RIGHT,
            textColor=colors.HexColor(NAVY),
        ),
        "small": ParagraphStyle(
            "ArabicSmall",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=8.5,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor(BLUE),
        ),
        "toc": ParagraphStyle(
            "ArabicTOC",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=12,
            leading=22,
            alignment=TA_RIGHT,
            textColor=colors.HexColor(NAVY),
        ),
        "card_label": ParagraphStyle(
            "CardLabel",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor(BLUE),
        ),
        "card_value": ParagraphStyle(
            "CardValue",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor(NAVY),
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
    }


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_rtl(text), style)


class ProfessionalCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_pages)
        for page in self._saved_pages:
            self.__dict__.update(page)
            _draw_page_template(self, self._pageNumber, page_count)
            super().showPage()
        super().save()


def _draw_logo(c: canvas.Canvas, x: float, y: float, size: float):
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(ImageReader(LOGO_PATH), x, y, width=size, height=size, preserveAspectRatio=True, mask="auto")
            return
        except Exception:
            pass
    
    c.setFillColor(colors.HexColor(PALE_BLUE))
    c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
    c.setFillColor(colors.HexColor(BLUE))
    c.circle(x + size / 2, y + size / 2, size * 0.33, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FONT_NAME, 8)
    c.drawCentredString(x + size / 2, y + size / 2 - 3, _rtl("العصعص"))


def _draw_header(c: canvas.Canvas):
    c.saveState()
    top = PAGE_HEIGHT - 1.0 * cm
    
    center_logo_path = "logo2.png"
    logo_size = 0.8 * cm
    
    if os.path.exists(center_logo_path):
        try:
            c.drawImage(ImageReader(center_logo_path), (PAGE_WIDTH / 2) - (logo_size / 2), top - 0.8 * cm, width=logo_size, height=logo_size, preserveAspectRatio=True, mask="auto")
        except Exception:
            c.setFont(FONT_NAME, 8)
            c.setFillColor(colors.HexColor(BLUE))
            c.drawCentredString(PAGE_WIDTH / 2, top - 0.4 * cm, _rtl("هنا سنضع شعار شركتك"))
    else:
        c.setFont(FONT_NAME, 8)
        c.setFillColor(colors.HexColor(BLUE))
        c.drawCentredString(PAGE_WIDTH / 2, top - 0.4 * cm, _rtl("هنا سنضع شعار شركتك"))
    
    _draw_logo(c, 1.15 * cm, top - 0.72 * cm, 0.62 * cm)
    
    c.setFont(FONT_NAME, 15)
    c.setFillColor(colors.HexColor(NAVY))
    c.drawRightString(PAGE_WIDTH - 1.15 * cm, top - 0.2 * cm, _rtl("العصعص"))
    
    c.setStrokeColor(colors.HexColor(BLUE))
    c.setLineWidth(1.1)
    c.line(1.15 * cm, top - 0.92 * cm, PAGE_WIDTH - 1.15 * cm, top - 0.92 * cm)
    c.setStrokeColor(colors.HexColor(PALE_BLUE))
    c.setLineWidth(2.0)
    c.line(1.15 * cm, top - 1.02 * cm, PAGE_WIDTH - 1.15 * cm, top - 1.02 * cm)
    c.restoreState()


def _draw_footer(c: canvas.Canvas, page_number: int, page_count: int):
    c.saveState()
    y = 1.0 * cm
    c.setStrokeColor(colors.HexColor(PALE_BLUE))
    c.setLineWidth(0.8)
    c.line(1.15 * cm, y + 0.56 * cm, PAGE_WIDTH - 1.15 * cm, y + 0.56 * cm)
    
    c.setFont(FONT_NAME, 7.5)
    c.setFillColor(colors.HexColor(LIGHT_BLUE))
    c.drawCentredString(PAGE_WIDTH / 2, y + 0.26 * cm, _rtl(DEVELOPER_NAME))
    c.drawCentredString(PAGE_WIDTH / 2, y - 0.04 * cm, _rtl(CONTACT_LINE))
    
    page_text = f"الصفحة {page_number} من {page_count}"
    c.setFont(FONT_NAME, 8)
    c.setFillColor(colors.HexColor(NAVY))
    c.drawRightString(PAGE_WIDTH - 1.15 * cm, y + 0.05 * cm, _rtl(page_text))
    c.restoreState()


def _draw_page_template(c: canvas.Canvas, page_number: int, page_count: int):
    _draw_header(c)
    _draw_footer(c, page_number, page_count)


def _section_header(title: str, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [[_paragraph(title, styles["section_title"])]],
        colWidths=[PAGE_WIDTH - 2.8 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY)),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(BLUE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _cover_logo() -> Image | Table:
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=3.0 * cm, height=3.0 * cm)
            logo.hAlign = "CENTER"
            return logo
        except Exception:
            pass
    
    table = Table([[_rtl("العصعص")]], colWidths=[3.0 * cm], rowHeights=[3.0 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PALE_BLUE)),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(NAVY)),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor(BLUE)),
            ]
        )
    )
    return table


def _metric_cards(metrics: dict, styles: dict[str, ParagraphStyle]) -> Table:
    cards = [
        ("إجمالي المبيعات", _money(metrics.get("current_total", 0))),
        ("نسبة النمو", _percent(metrics.get("growth", 0))),
        ("عدد العملاء", str(metrics.get("customers_count", 0))),
        ("عدد المنتجات", str(metrics.get("products_count", 0))),
        ("عدد المناديب", str(metrics.get("representatives_count", 0))),
        ("عدد الفروع", str(metrics.get("branches_count", 0))),
    ]
    row = []
    for label, value in cards:
        row.append([_paragraph(label, styles["card_label"]), _paragraph(value, styles["card_value"])])
    
    nested = []
    for card in row:
        card_table = Table([[card[0]], [card[1]]], colWidths=[4.05 * cm], rowHeights=[0.55 * cm, 0.75 * cm])
        card_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(LIGHT_BLUE)),
                    ("LINEABOVE", (0, 0), (-1, 0), 4, colors.HexColor(BLUE)),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        nested.append(card_table)
    
    table = Table([nested[:3], nested[3:]], colWidths=[4.25 * cm, 4.25 * cm, 4.25 * cm], hAlign="CENTER")
    table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return table


def _format_frame(frame: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    shown = frame.head(max_rows).copy()
    if shown.empty:
        return pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    for column in shown.columns:
        if column in ["الحالي", "السابق", "الفرق", "القيمة"]:
            shown[column] = shown[column].map(_money)
        elif column == "النسبة":
            shown[column] = shown[column].map(_percent)
    return shown


def _table_from_frame(frame: pd.DataFrame, max_rows: int = 16) -> Table:
    shown = _format_frame(frame, max_rows)
    data = [[_rtl(column) for column in shown.columns]]
    data.extend([[_rtl(value) for value in row] for row in shown.astype(str).values.tolist()])
    
    available_width = PAGE_WIDTH - 2.8 * cm
    col_count = max(len(shown.columns), 1)
    col_widths = [available_width / col_count] * col_count
    
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(LIGHT_BLUE)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(PALE_BLUE)]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


# ============================================================
# دوال المخططات
# ============================================================
def _chart_theme(fig: go.Figure, title: str, height: int = 280) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 16, "color": NAVY}},
        font={"family": "Arial", "size": 10, "color": NAVY},
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        margin={"l": 30, "r": 30, "t": 50, "b": 30},
        height=height,
        colorway=[NAVY, BLUE, LIGHT_BLUE, PALE_BLUE],
        legend={"orientation": "h", "y": -0.16, "x": 0.5, "xanchor": "center"},
    )
    fig.update_xaxes(gridcolor=PALE_BLUE, linecolor=LIGHT_BLUE, tickfont={"color": NAVY})
    fig.update_yaxes(gridcolor=PALE_BLUE, linecolor=LIGHT_BLUE, tickfont={"color": NAVY})
    return fig


def _plotly_image(fig: go.Figure, width: int = 700, height: int = 250) -> Image | Table:
    """تحويل المخطط إلى صورة باستخدام matplotlib (بدون kaleido)."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    from io import BytesIO
    
    try:
        # تحويل Plotly إلى matplotlib
        # نرسم المخطط مباشرة باستخدام matplotlib
        fig_bytes = _fig_to_matplotlib(fig, width, height)
        if fig_bytes:
            image = Image(fig_bytes, width=18.0 * cm, height=(18.0 * cm) * height / width)
            image.hAlign = "CENTER"
            return image
        else:
            # فشل التحويل
            return _create_fallback_table()
    except Exception as e:
        print(f"⚠️ خطأ في تحويل المخطط: {e}")
        return _create_fallback_table()


def _fig_to_matplotlib(fig: go.Figure, width: int = 700, height: int = 250) -> BytesIO | None:
    """تحويل Plotly Figure إلى صورة matplotlib."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    try:
        # استخدام plotly's to_image مع engine='auto' أولاً
        try:
            png = fig.to_image(format="png", width=width, height=height, scale=1, engine='auto')
            if png:
                return BytesIO(png)
        except:
            pass
        
        # إذا فشل، نستخدم matplotlib
        import plotly.tools as tls
        fig_matplotlib = tls.mpl_to_matplotlib(fig)
        fig_matplotlib.set_size_inches(width/100, height/100)
        
        img_buffer = BytesIO()
        fig_matplotlib.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        img_buffer.seek(0)
        plt.close(fig_matplotlib)
        return img_buffer
        
    except Exception as e:
        print(f"⚠️ فشل تحويل المخطط إلى صورة: {e}")
        return None


def _create_fallback_table() -> Table:
    """إنشاء جدول بديل في حالة فشل الصورة."""
    fallback = Table(
        [[ar("⚠️ تعذر تحويل الرسم إلى صورة")]],
        colWidths=[PAGE_WIDTH - 2.8 * cm],
        rowHeights=[1.2 * cm],
    )
    fallback.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PALE_BLUE)),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(NAVY)),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(LIGHT_BLUE)),
            ]
        )
    )
    return fallback


def _bar_chart(frame: pd.DataFrame, title: str) -> Image | Table:
    data = frame.head(8).copy()
    fig = go.Figure(go.Bar(x=data.get("الاسم", []), y=data.get("الحالي", []), marker_color=BLUE, text=data.get("الحالي", []), textposition="outside"))
    fig = _chart_theme(fig, title)
    return _plotly_image(fig)


def _pie_chart(frame: pd.DataFrame, title: str) -> Image | Table:
    data = frame.head(8).copy()
    fig = go.Figure(go.Pie(labels=data.get("الاسم", []), values=data.get("الحالي", []), hole=0.42, marker={"colors": [NAVY, BLUE, LIGHT_BLUE, PALE_BLUE]}))
    fig = _chart_theme(fig, title)
    return _plotly_image(fig)


def _pareto_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["الاسم", "الحالي", "النسبة", "النسبة_التراكمية"])
    result = frame[["الاسم", "الحالي"]].copy().sort_values("الحالي", ascending=False)
    total = result["الحالي"].sum()
    result["النسبة"] = 0 if total == 0 else result["الحالي"] / total * 100
    result["النسبة_التراكمية"] = result["النسبة"].cumsum()
    return result


def _pareto_chart(frame: pd.DataFrame, title: str) -> Image | Table:
    data = _pareto_frame(frame).head(10)
    fig = go.Figure()
    fig.add_bar(x=data.get("الاسم", []), y=data.get("الحالي", []), name="المبيعات", marker_color=BLUE)
    fig.add_scatter(x=data.get("الاسم", []), y=data.get("النسبة_التراكمية", []), name="النسبة التراكمية", yaxis="y2", mode="lines+markers", line={"color": NAVY, "width": 3})
    fig.update_layout(yaxis2={"title": "النسبة التراكمية", "overlaying": "y", "side": "right", "range": [0, 100]})
    fig = _chart_theme(fig, title)
    return _plotly_image(fig)


def _trend_chart(metrics: dict) -> Image | Table:
    labels = ["السابق", "الحالي"]
    values = [metrics.get("previous_total", 0), metrics.get("current_total", 0)]
    fig = go.Figure()
    fig.add_scatter(x=labels, y=values, mode="lines+markers", line={"color": NAVY, "width": 3}, marker={"size": 10, "color": BLUE})
    fig.add_bar(x=labels, y=values, marker_color=[LIGHT_BLUE, BLUE], opacity=0.55)
    fig = _chart_theme(fig, "تحليل الاتجاه بين الفترة السابقة والحالية")
    return _plotly_image(fig)


def _metrics_frame(metrics: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"المؤشر": "إجمالي المبيعات الحالية", "القيمة": _money(metrics.get("current_total", 0))},
            {"المؤشر": "إجمالي المبيعات السابقة", "القيمة": _money(metrics.get("previous_total", 0))},
            {"المؤشر": "إجمالي الفرق", "القيمة": _money(metrics.get("difference", 0))},
            {"المؤشر": "نسبة النمو", "القيمة": _percent(metrics.get("growth", 0))},
            {"المؤشر": "عدد العملاء", "القيمة": metrics.get("customers_count", 0)},
            {"المؤشر": "عدد المنتجات", "القيمة": metrics.get("products_count", 0)},
            {"المؤشر": "عدد المناديب", "القيمة": metrics.get("representatives_count", 0)},
            {"المؤشر": "عدد الفروع", "القيمة": metrics.get("branches_count", 0)},
        ]
    )


def _add_section(story: list, title: str, styles: dict[str, ParagraphStyle]):
    story.append(_section_header(title, styles))
    story.append(Spacer(1, 0.28 * cm))


def _add_table_section(story: list, title: str, frame: pd.DataFrame, styles: dict[str, ParagraphStyle], max_rows: int = 14):
    _add_section(story, title, styles)
    story.append(_table_from_frame(frame, max_rows=max_rows))
    story.append(Spacer(1, 0.45 * cm))


def _add_chart_block(story: list, chart_flowables: Iterable[Image | Table]):
    for chart in chart_flowables:
        story.append(chart)
        story.append(Spacer(1, 0.3 * cm))


def _add_dimension_section(story: list, title: str, frame: pd.DataFrame, styles: dict[str, ParagraphStyle]):
    _add_table_section(story, title, frame, styles, max_rows=12)
    _add_chart_block(
        story,
        [
            _bar_chart(frame, f"{title} - Bar Chart"),
            _pie_chart(frame, f"{title} - Pie Chart"),
        ],
    )


def _add_toc(story: list, styles: dict[str, ParagraphStyle]):
    _add_section(story, "فهرس التقرير", styles)
    items = [
        "الملخص التنفيذي",
        "مؤشرات الأداء",
        "مركز ذكاء الأعمال",
        "تحليل العملاء",
        "تحليل المنتجات",
        "تحليل المناديب",
        "تحليل الفروع",
        "تحليل الاتجاهات",
        "تحليل باريتو",
    ]
    rows = [[_paragraph(item, styles["toc"]), _paragraph(str(index), styles["toc"])] for index, item in enumerate(items, start=1)]
    table = Table(rows, colWidths=[19 * cm, 2 * cm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor(PALE_BLUE)]),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(LIGHT_BLUE)),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor(PALE_BLUE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)


def _cover_info_table(
    report_type,
    report_period,
    report_date,
    records_count,
    report_description,
    styles,
):
    data = [
        [
            _paragraph("القيمة", styles["table_header"]),
            _paragraph("البيان", styles["table_header"]),
        ],
        [
            _paragraph(report_type, styles["normal"]),
            _paragraph("نوع التقرير", styles["normal"]),
        ],
        [
            _paragraph(report_period, styles["normal"]),
            _paragraph("الفترة محل التحليل", styles["normal"]),
        ],
        [
            _paragraph(f"{records_count:,} سجل", styles["normal"]),
            _paragraph("عدد السجلات المحللة", styles["normal"]),
        ],
    ]
    table = Table(
        data,
        colWidths=[10 * cm, 6 * cm],
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("BACKGROUND", (1,1), (1,-1), colors.HexColor("#EEF4FF")),
                ("BACKGROUND", (0,1), (0,-1), colors.white),
                ("GRID", (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 10),
                ("BOTTOMPADDING", (0,0), (-1,-1), 10),
                ("FONTNAME", (0,0), (-1,-1), FONT_NAME),
            ]
        )
    )
    return [
        table,
        Spacer(1, 0.5 * cm),
        _paragraph(report_description, styles["normal"]),
    ]


def export_to_pdf(
    metrics: dict,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    representatives: pd.DataFrame,
    branches: pd.DataFrame,
    insights: pd.DataFrame,
    report_description,
    report_type,
    report_period,
    records_count,
) -> BytesIO:
    """إنشاء تقرير PDF تنفيذي."""
    start = time.time()
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=PAGE_SIZE,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=2.35 * cm,
        bottomMargin=1.85 * cm,
    )
    styles = _styles()
    story = []

    story.append(Spacer(1, 0.8 * cm))
    story.append(_cover_logo())
    story.append(Spacer(1, 0.45 * cm))
    story.append(_paragraph(PROGRAM_NAME, styles["cover_title"]))
    story.append(_paragraph(PROGRAM_SUBTITLE, styles["cover_subtitle"]))
    story.append(Spacer(1, 0.45 * cm))
    story.append(_paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["cover_subtitle"]))
    story.append(Spacer(1, 0.65 * cm))

    story.extend(
        _cover_info_table(
            report_type=report_type,
            report_period=report_period,
            report_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            records_count=records_count,
            report_description=report_description,
            styles=styles,
        )
    )

    story.append(PageBreak())

    _add_toc(story, styles)
    story.append(PageBreak())

    _add_section(story, "الملخص التنفيذي", styles)
    story.append(
        _paragraph(
            "يعرض هذا التقرير مؤشرات الأداء الرئيسية وتحليل العملاء والمنتجات والمناديب والفروع، مع رسوم بيانية تنفيذية تساعد على قراءة النمو والانخفاض وتحديد أولويات المتابعة.",
            styles["normal"],
        )
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(_metric_cards(metrics, styles))
    story.append(Spacer(1, 0.4 * cm))

    _add_table_section(story, "مؤشرات الأداء", _metrics_frame(metrics), styles, max_rows=10)
    _add_table_section(story, "مركز ذكاء الأعمال", insights, styles, max_rows=10)
    story.append(PageBreak())

    _add_dimension_section(story, "تحليل العملاء", customers, styles)
    story.append(PageBreak())
    _add_dimension_section(story, "تحليل المنتجات", products, styles)
    story.append(PageBreak())
    _add_dimension_section(story, "تحليل المناديب", representatives, styles)
    story.append(PageBreak())
    _add_dimension_section(story, "تحليل الفروع", branches, styles)
    story.append(PageBreak())

    _add_section(story, "تحليل الاتجاهات", styles)
    _add_chart_block(story, [_trend_chart(metrics)])
    story.append(PageBreak())

    _add_section(story, "تحليل باريتو", styles)
    story.append(KeepTogether([_pareto_chart(customers, "مخطط باريتو للعملاء"), Spacer(1, 0.3 * cm)]))
    story.append(_pareto_chart(products, "مخطط باريتو للمنتجات"))
    story.append(Spacer(1, 0.35 * cm))

    _add_section(story, "الاستنتاجات", styles)
    story.append(
        _paragraph(
            "توضح المقارنات العناصر الأعلى أثراً في المبيعات، وتساعد رسوم باريتو على تحديد المساهمين الرئيسيين في الأداء، بينما تكشف مؤشرات النمو والانخفاض فرص المتابعة والتحسين.",
            styles["normal"],
        )
    )

    document.build(story, canvasmaker=ProfessionalCanvas)
    output.seek(0)
    print(f"⏱️ [pdf_export] إجمالي وقت التصدير: {time.time() - start:.2f} ثانية")
    return output