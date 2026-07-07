from io import BytesIO
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import time

HEADER_FILL = PatternFill("solid", fgColor="1E3A5F")
HEADER_FONT = Font(color="FFFFFF", bold=True)
THIN_BORDER = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)


def _autosize_and_style(worksheet):
    worksheet.sheet_view.rightToLeft = True
    worksheet.freeze_panes = "A2"
    for cell in worksheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER
    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0.00'
    for column_cells in worksheet.columns:
        max_length = 12
        column_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            if cell.value is not None:
                max_length = max(max_length, min(len(str(cell.value)) + 2, 45))
        worksheet.column_dimensions[column_letter].width = max_length


def _write_sheet(writer, sheet_name: str, frame: pd.DataFrame):
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    _autosize_and_style(writer.book[sheet_name])


def _create_chart_image(df: pd.DataFrame, chart_type: str, title: str, x_col: str = "الاسم", y_col: str = "الحالي", y2_col: str = None) -> BytesIO:
    """إنشاء صورة للشارت - Bar, Pie, Pareto, Trend"""
    data = df.head(10).copy()
    if data.empty or len(data) < 2:
        return None
    
    fig = None
    
    if chart_type == "bar":
        fig = go.Figure(go.Bar(
            x=data[x_col].astype(str), 
            y=data[y_col],
            marker_color="#2563eb",
            text=data[y_col],
            textposition="outside"
        ))
    elif chart_type == "pie":
        fig = go.Figure(go.Pie(
            labels=data[x_col].astype(str),
            values=data[y_col],
            hole=0.35,
            marker=dict(colors=["#1e3a8a", "#2563eb", "#60a5fa", "#93c5fd", "#bfdbfe"])
        ))
    elif chart_type == "pareto":
        fig = go.Figure()
        fig.add_bar(
            x=data[x_col].astype(str),
            y=data[y_col],
            name="المبيعات",
            marker_color="#2563eb",
            text=data[y_col],
            textposition="outside"
        )
        if y2_col and y2_col in data.columns:
            fig.add_scatter(
                x=data[x_col].astype(str),
                y=data[y2_col],
                name="النسبة التراكمية",
                mode="lines+markers",
                line=dict(color="#dc2626", width=2),
                marker=dict(size=8, color="#dc2626"),
                yaxis="y2"
            )
            fig.add_hline(y=80, line_dash="dash", line_color="#dc2626", annotation_text="80%")
            fig.update_layout(
                yaxis2=dict(
                    title="النسبة التراكمية %",
                    overlaying="y",
                    side="right",
                    range=[0, 110]
                )
            )
    elif chart_type == "trend":
        fig = go.Figure()
        fig.add_bar(
            x=data[x_col].astype(str),
            y=data[y_col],
            name="المبيعات",
            marker_color="#2563eb",
            text=data[y_col],
            textposition="outside"
        )
        fig.add_scatter(
            x=data[x_col].astype(str),
            y=data[y_col],
            name="خط الاتجاه",
            mode="lines+markers",
            line=dict(color="#dc2626", width=3),
            marker=dict(size=10, color="#dc2626")
        )
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
    else:
        return None
    
    fig.update_layout(
        title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 10, "color": "#1e3a8a"}},
        font={"size": 8, "color": "#1e3a8a"},
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        height=200,
        width=300,
        colorway=["#1e3a8a", "#2563eb", "#60a5fa", "#93c5fd"]
    )
    
    if chart_type in ["bar", "trend"]:
        fig.update_xaxes(gridcolor="#bfdbfe", linecolor="#93c5fd")
        fig.update_yaxes(gridcolor="#bfdbfe", linecolor="#93c5fd")
    
    try:
        img_bytes = pio.to_image(fig, format="png", scale=0.8)
        return BytesIO(img_bytes)
    except Exception as e:
        print(f"خطأ في إنشاء الصورة: {e}")
        return None


def _add_image_to_sheet(worksheet, img_bytes: BytesIO, cell_position: str, width: int = 300, height: int = 200):
    try:
        img_bytes.seek(0)
        img = XLImage(img_bytes)
        img.width = width
        img.height = height
        worksheet.add_image(img, cell_position)
        return True
    except Exception as e:
        print(f"خطأ في إضافة الصورة: {e}")
        return False


def _write_sheet_with_charts(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = None):
    """كتابة ورقة مع Bar و Pie فقط (بدون Treemap)"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    if not frame.empty and len(frame) > 1 and chart_title:
        try:
            table_cols = len(frame.columns)
            chart_start_col = table_cols + 2
            empty_col_letter = get_column_letter(table_cols + 1)
            worksheet.column_dimensions[empty_col_letter].width = 3
            
            header_cell = worksheet.cell(row=1, column=chart_start_col)
            header_cell.value = "📊 المخططات البيانية"
            header_cell.font = Font(color="1E3A5F", bold=True, size=14)
            header_cell.alignment = Alignment(horizontal="center")
            worksheet.merge_cells(
                start_row=1,
                start_column=chart_start_col,
                end_row=1,
                end_column=chart_start_col + 2
            )
            
            chart_types = [
                ("bar", "📊 مخطط شريطي"),
                ("pie", "🧩 مخطط دائري"),
            ]
            
            current_row = 2
            
            for chart_type, chart_label in chart_types:
                try:
                    img_bytes = _create_chart_image(frame, chart_type, f"{chart_title} - {chart_label}")
                    
                    if img_bytes:
                        title_cell = worksheet.cell(row=current_row, column=chart_start_col)
                        title_cell.value = chart_label
                        title_cell.font = Font(color="1E3A5F", bold=True, size=10)
                        title_cell.alignment = Alignment(horizontal="center")
                        worksheet.merge_cells(
                            start_row=current_row,
                            start_column=chart_start_col,
                            end_row=current_row,
                            end_column=chart_start_col + 2
                        )
                        current_row += 1
                        
                        cell_pos = f"{get_column_letter(chart_start_col)}{current_row}"
                        if _add_image_to_sheet(worksheet, img_bytes, cell_pos, width=300, height=200):
                            current_row += 14
                        else:
                            error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                            error_cell.value = f"⚠️ فشل إدراج الصورة"
                            error_cell.font = Font(color="EF4444", size=9)
                            current_row += 2
                    else:
                        error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                        error_cell.value = f"⚠️ لا توجد بيانات كافية"
                        error_cell.font = Font(color="EF4444", size=9)
                        current_row += 2
                        
                except Exception as e:
                    error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                    error_cell.value = f"⚠️ خطأ: {str(e)[:30]}"
                    error_cell.font = Font(color="EF4444", size=9)
                    current_row += 2
            
            for col in range(chart_start_col, chart_start_col + 3):
                col_letter = get_column_letter(col)
                worksheet.column_dimensions[col_letter].width = 30
                
        except Exception as e:
            error_cell = worksheet.cell(row=1, column=5)
            error_cell.value = f"⚠️ تعذر إضافة المخططات"
            error_cell.font = Font(color="EF4444", size=10)


# ============================================================
# دوال جديدة لإضافة باريتو والاتجاهات
# ============================================================
def _write_pareto_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل باريتو"):
    """كتابة ورقة تحليل باريتو مع مخطط"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    if not frame.empty and len(frame) > 1:
        try:
            table_cols = len(frame.columns)
            chart_start_col = table_cols + 2
            empty_col_letter = get_column_letter(table_cols + 1)
            worksheet.column_dimensions[empty_col_letter].width = 3
            
            header_cell = worksheet.cell(row=1, column=chart_start_col)
            header_cell.value = "📊 مخطط باريتو"
            header_cell.font = Font(color="1E3A5F", bold=True, size=14)
            header_cell.alignment = Alignment(horizontal="center")
            worksheet.merge_cells(
                start_row=1,
                start_column=chart_start_col,
                end_row=1,
                end_column=chart_start_col + 2
            )
            
            current_row = 2
            
            # مخطط باريتو
            try:
                img_bytes = _create_chart_image(
                    frame, "pareto", chart_title,
                    x_col="الاسم", y_col="الحالي", y2_col="النسبة_التراكمية"
                )
                
                if img_bytes:
                    title_cell = worksheet.cell(row=current_row, column=chart_start_col)
                    title_cell.value = "📊 مخطط باريتو (قاعدة 80/20)"
                    title_cell.font = Font(color="1E3A5F", bold=True, size=10)
                    title_cell.alignment = Alignment(horizontal="center")
                    worksheet.merge_cells(
                        start_row=current_row,
                        start_column=chart_start_col,
                        end_row=current_row,
                        end_column=chart_start_col + 2
                    )
                    current_row += 1
                    
                    cell_pos = f"{get_column_letter(chart_start_col)}{current_row}"
                    if _add_image_to_sheet(worksheet, img_bytes, cell_pos, width=350, height=230):
                        current_row += 16
                    else:
                        error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                        error_cell.value = f"⚠️ فشل إدراج الصورة"
                        error_cell.font = Font(color="EF4444", size=9)
                        current_row += 2
                else:
                    error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                    error_cell.value = f"⚠️ لا توجد بيانات كافية"
                    error_cell.font = Font(color="EF4444", size=9)
                    current_row += 2
                    
            except Exception as e:
                error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                error_cell.value = f"⚠️ خطأ: {str(e)[:30]}"
                error_cell.font = Font(color="EF4444", size=9)
                current_row += 2
            
            for col in range(chart_start_col, chart_start_col + 3):
                col_letter = get_column_letter(col)
                worksheet.column_dimensions[col_letter].width = 30
                
        except Exception as e:
            error_cell = worksheet.cell(row=1, column=5)
            error_cell.value = f"⚠️ تعذر إضافة المخطط"
            error_cell.font = Font(color="EF4444", size=10)


def _write_trend_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل الاتجاهات"):
    """كتابة ورقة تحليل الاتجاهات مع مخطط"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    if not frame.empty and len(frame) > 1:
        try:
            table_cols = len(frame.columns)
            chart_start_col = table_cols + 2
            empty_col_letter = get_column_letter(table_cols + 1)
            worksheet.column_dimensions[empty_col_letter].width = 3
            
            header_cell = worksheet.cell(row=1, column=chart_start_col)
            header_cell.value = "📊 مخطط الاتجاهات"
            header_cell.font = Font(color="1E3A5F", bold=True, size=14)
            header_cell.alignment = Alignment(horizontal="center")
            worksheet.merge_cells(
                start_row=1,
                start_column=chart_start_col,
                end_row=1,
                end_column=chart_start_col + 2
            )
            
            current_row = 2
            
            # مخطط الاتجاهات
            try:
                # استخدام أول عمودين من البيانات
                x_col = frame.columns[0]
                y_col = frame.columns[1] if len(frame.columns) > 1 else frame.columns[0]
                
                img_bytes = _create_chart_image(
                    frame, "trend", chart_title,
                    x_col=x_col, y_col=y_col
                )
                
                if img_bytes:
                    title_cell = worksheet.cell(row=current_row, column=chart_start_col)
                    title_cell.value = "📈 مخطط اتجاه المبيعات"
                    title_cell.font = Font(color="1E3A5F", bold=True, size=10)
                    title_cell.alignment = Alignment(horizontal="center")
                    worksheet.merge_cells(
                        start_row=current_row,
                        start_column=chart_start_col,
                        end_row=current_row,
                        end_column=chart_start_col + 2
                    )
                    current_row += 1
                    
                    cell_pos = f"{get_column_letter(chart_start_col)}{current_row}"
                    if _add_image_to_sheet(worksheet, img_bytes, cell_pos, width=350, height=230):
                        current_row += 16
                    else:
                        error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                        error_cell.value = f"⚠️ فشل إدراج الصورة"
                        error_cell.font = Font(color="EF4444", size=9)
                        current_row += 2
                else:
                    error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                    error_cell.value = f"⚠️ لا توجد بيانات كافية"
                    error_cell.font = Font(color="EF4444", size=9)
                    current_row += 2
                    
            except Exception as e:
                error_cell = worksheet.cell(row=current_row, column=chart_start_col)
                error_cell.value = f"⚠️ خطأ: {str(e)[:30]}"
                error_cell.font = Font(color="EF4444", size=9)
                current_row += 2
            
            for col in range(chart_start_col, chart_start_col + 3):
                col_letter = get_column_letter(col)
                worksheet.column_dimensions[col_letter].width = 30
                
        except Exception as e:
            error_cell = worksheet.cell(row=1, column=5)
            error_cell.value = f"⚠️ تعذر إضافة المخطط"
            error_cell.font = Font(color="EF4444", size=10)


def export_to_excel(
    metrics: dict,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    representatives: pd.DataFrame,
    branches: pd.DataFrame,
    insights: pd.DataFrame,
    pareto_customers: pd.DataFrame = None,
    pareto_products: pd.DataFrame = None,
    trend_data: pd.DataFrame = None,
) -> BytesIO:
    """
    إنشاء ملف Excel مع:
    - Dashboard (المؤشرات)
    - العملاء (جدول + مخططات)
    - المنتجات (جدول + مخططات)
    - المناديب (جدول + مخططات)
    - الفروع (جدول + مخططات)
    - تحليل باريتو (جدول + مخطط)
    - تحليل الاتجاهات (جدول + مخطط)
    - Insights (الرؤى)
    """
    start = time.time()
    output = BytesIO()

    dashboard = pd.DataFrame(
        [
            {"المؤشر": "إجمالي المبيعات الحالية", "القيمة": metrics["current_total"]},
            {"المؤشر": "إجمالي المبيعات السابقة", "القيمة": metrics["previous_total"]},
            {"المؤشر": "إجمالي الفرق", "القيمة": metrics["difference"]},
            {"المؤشر": "نسبة النمو", "القيمة": metrics["growth"]},
            {"المؤشر": "عدد العملاء", "القيمة": metrics["customers_count"]},
            {"المؤشر": "عدد المنتجات", "القيمة": metrics["products_count"]},
            {"المؤشر": "عدد المناديب", "القيمة": metrics["representatives_count"]},
            {"المؤشر": "عدد الفروع", "القيمة": metrics["branches_count"]},
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # الأوراق الأساسية
        _write_sheet(writer, "Dashboard", dashboard)
        _write_sheet_with_charts(writer, "العملاء", customers, "تحليل العملاء")
        _write_sheet_with_charts(writer, "المنتجات", products, "تحليل المنتجات")
        _write_sheet_with_charts(writer, "المناديب", representatives, "تحليل المناديب")
        _write_sheet_with_charts(writer, "الفروع", branches, "تحليل الفروع")
        
        # ============================================================
        # إضافة تحليل باريتو (إذا توفرت البيانات)
        # ============================================================
        if pareto_customers is not None and not pareto_customers.empty:
            _write_pareto_sheet(writer, "باريتو - العملاء", pareto_customers, "تحليل باريتو للعملاء")
        
        if pareto_products is not None and not pareto_products.empty:
            _write_pareto_sheet(writer, "باريتو - المنتجات", pareto_products, "تحليل باريتو للمنتجات")
        
        # ============================================================
        # إضافة تحليل الاتجاهات (إذا توفرت البيانات)
        # ============================================================
        if trend_data is not None and not trend_data.empty:
            _write_trend_sheet(writer, "تحليل الاتجاهات", trend_data, "تحليل اتجاهات المبيعات")
        
        # Insights
        _write_sheet(writer, "Insights", insights)

        for worksheet in writer.book.worksheets:
            worksheet.sheet_properties.pageSetUpPr.fitToPage = True
            worksheet.page_setup.fitToWidth = 1

    output.seek(0)
    print(f"⏱️ [excel_export] إجمالي التصدير: {time.time() - start:.2f} ثانية")
    return output