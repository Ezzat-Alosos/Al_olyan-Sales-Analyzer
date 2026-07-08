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


def _create_chart_image(df: pd.DataFrame, chart_type: str, title: str, x_col: str = "الاسم", y_col: str = "الحالي") -> BytesIO:
    """إنشاء صورة للشارت باستخدام Plotly."""
    data = df.head(8).copy()
    
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
    elif chart_type == "treemap":
        fig = go.Figure(go.Treemap(
            labels=data[x_col].astype(str),
            values=data[y_col],
            parents=[""] * len(data),
            marker=dict(colorscale=[[0, "#bfdbfe"], [0.5, "#60a5fa"], [1, "#1e3a8a"]])
        ))
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
    
    if chart_type in ["bar", "treemap"]:
        fig.update_xaxes(gridcolor="#bfdbfe", linecolor="#93c5fd")
        fig.update_yaxes(gridcolor="#bfdbfe", linecolor="#93c5fd")
    
    try:
        img_bytes = pio.to_image(fig, format="png", scale=0.8)
        return BytesIO(img_bytes)
    except Exception as e:
        print(f"خطأ في إنشاء الصورة: {e}")
        return None


def _add_image_to_sheet(worksheet, img_bytes: BytesIO, cell_position: str, width: int = 250, height: int = 160):
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
                ("treemap", "🌳 مخطط شجري")
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
                        if _add_image_to_sheet(worksheet, img_bytes, cell_pos, width=250, height=160):
                            current_row += 12
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


def _write_pareto_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل باريتو"):
    """كتابة ورقة تحليل باريتو مع مخطط."""
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
            
            try:
                # استخدام بيانات باريتو مباشرة
                data = frame.head(10).copy()
                if not data.empty:
                    x = data["الاسم"].astype(str).tolist()
                    y = data["الحالي"].tolist()
                    
                    # إنشاء مخطط باريتو
                    fig = go.Figure()
                    fig.add_bar(x=x, y=y, name="المبيعات", marker_color="#2563eb")
                    
                    # حساب النسبة التراكمية
                    total = sum(y)
                    cumsum = 0
                    cum_percentages = []
                    for val in y:
                        cumsum += val
                        cum_percentages.append((cumsum / total) * 100 if total > 0 else 0)
                    
                    fig.add_scatter(x=x, y=cum_percentages, name="النسبة التراكمية", 
                                   yaxis="y2", mode="lines+markers", 
                                   line=dict(color="#dc2626", width=2))
                    
                    fig.update_layout(
                        title={"text": chart_title, "x": 0.5, "xanchor": "center", 
                               "font": {"size": 10, "color": "#1e3a8a"}},
                        font={"size": 8, "color": "#1e3a8a"},
                        paper_bgcolor="white",
                        plot_bgcolor="white",
                        margin={"l": 20, "r": 20, "t": 30, "b": 20},
                        height=200,
                        width=300,
                        yaxis2=dict(
                            title="النسبة التراكمية %",
                            overlaying="y",
                            side="right",
                            range=[0, 110]
                        )
                    )
                    
                    img_bytes = pio.to_image(fig, format="png", scale=0.8)
                    
                    if img_bytes:
                        img = XLImage(BytesIO(img_bytes))
                        img.width = 300
                        img.height = 200
                        
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
                        worksheet.add_image(img, cell_pos)
                        current_row += 14
                    
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
            error_cell.value = f"⚠️ تعذر إضافة المخطط: {str(e)[:50]}"
            error_cell.font = Font(color="EF4444", size=10)


def _write_trend_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل الاتجاهات"):
    """كتابة ورقة تحليل الاتجاهات مع مخطط."""
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
            
            try:
                x_col = frame.columns[0]
                y_col = frame.columns[1] if len(frame.columns) > 1 else frame.columns[0]
                
                data = frame.head(10).copy()
                if not data.empty:
                    x = data[x_col].astype(str).tolist()
                    y = data[y_col].tolist()
                    
                    fig = go.Figure()
                    fig.add_bar(x=x, y=y, name="المبيعات", marker_color="#2563eb")
                    fig.add_scatter(x=x, y=y, name="خط الاتجاه", 
                                   mode="lines+markers",
                                   line=dict(color="#dc2626", width=2))
                    
                    fig.update_layout(
                        title={"text": chart_title, "x": 0.5, "xanchor": "center", 
                               "font": {"size": 10, "color": "#1e3a8a"}},
                        font={"size": 8, "color": "#1e3a8a"},
                        paper_bgcolor="white",
                        plot_bgcolor="white",
                        margin={"l": 20, "r": 20, "t": 30, "b": 20},
                        height=200,
                        width=300,
                        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
                    )
                    
                    img_bytes = pio.to_image(fig, format="png", scale=0.8)
                    
                    if img_bytes:
                        img = XLImage(BytesIO(img_bytes))
                        img.width = 300
                        img.height = 200
                        
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
                        worksheet.add_image(img, cell_pos)
                        current_row += 14
                    
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
            error_cell.value = f"⚠️ تعذر إضافة المخطط: {str(e)[:50]}"
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
        _write_sheet(writer, "Dashboard", dashboard)
        _write_sheet_with_charts(writer, "العملاء", customers, "تحليل العملاء")
        _write_sheet_with_charts(writer, "المنتجات", products, "تحليل المنتجات")
        _write_sheet_with_charts(writer, "المناديب", representatives, "تحليل المناديب")
        _write_sheet_with_charts(writer, "الفروع", branches, "تحليل الفروع")
        
        if pareto_customers is not None and not pareto_customers.empty:
            _write_pareto_sheet(writer, "باريتو العملاء", pareto_customers, "تحليل باريتو للعملاء")
        
        if pareto_products is not None and not pareto_products.empty:
            _write_pareto_sheet(writer, "باريتو المنتجات", pareto_products, "تحليل باريتو للمنتجات")
        
        if trend_data is not None and not trend_data.empty:
            _write_trend_sheet(writer, "تحليل الاتجاهات", trend_data, "تحليل اتجاهات المبيعات")
        
        _write_sheet(writer, "Insights", insights)

        for worksheet in writer.book.worksheets:
            worksheet.sheet_properties.pageSetUpPr.fitToPage = True
            worksheet.page_setup.fitToWidth = 1

    output.seek(0)
    print(f"⏱️ [excel_export] إجمالي التصدير: {time.time() - start:.2f} ثانية")
    return output