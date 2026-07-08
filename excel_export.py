from io import BytesIO
import pandas as pd
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


def _create_chart_image(df: pd.DataFrame, chart_type: str, title: str, x_col: str = "الاسم", y_col: str = "الحالي", _y2_col: str = None) -> BytesIO:
    """إنشاء صورة للشارت باستخدام matplotlib."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    
    data = df.head(10).copy()
    if data.empty or len(data) < 2:
        return None
    
    data = data.dropna(subset=[x_col, y_col])
    if data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    if chart_type == "bar":
        x = data[x_col].astype(str).tolist()
        y = data[y_col].tolist()
        colors = ['#1e3a8a', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe']
        bars = ax.bar(x, y, color=colors[:len(x)])
        ax.set_ylabel('المبيعات')
        ax.set_title(title, fontsize=12)
        for bar, val in zip(bars, y):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(y)*0.01,
                   f'{val:,.0f}', ha='center', va='bottom', fontsize=8)
        plt.xticks(rotation=45, ha='right')
        
    elif chart_type == "pie":
        data = data.sort_values(y_col, ascending=False)
        labels = data[x_col].astype(str).tolist()
        values = data[y_col].tolist()
        total = sum(values)
        if total > 0:
            colors = ['#1e3a8a', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff']
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=labels, 
                autopct=lambda pct: f'{pct:.1f}%' if pct > 2 else '',
                colors=colors[:len(labels)],
                startangle=90,
                pctdistance=0.85
            )
            ax.set_title(title, fontsize=12)
            for text in texts:
                text.set_fontsize(8)
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_color('white')
        
    elif chart_type == "pareto":
        data = data.sort_values(y_col, ascending=False)
        x = data[x_col].astype(str).tolist()
        y = data[y_col].tolist()
        
        colors = ['#2563eb'] * len(x)
        bars = ax.bar(x, y, color=colors, alpha=0.7)
        ax.set_ylabel('المبيعات', color='blue')
        ax.tick_params(axis='y', labelcolor='blue')
        
        total = sum(y)
        cumsum = 0
        cum_percentages = []
        for val in y:
            cumsum += val
            cum_percentages.append((cumsum / total) * 100 if total > 0 else 0)
        
        ax2 = ax.twinx()
        ax2.plot(x, cum_percentages, color='red', marker='o', linewidth=2, markersize=6)
        ax2.axhline(y=80, color='red', linestyle='--', alpha=0.5)
        ax2.text(len(x)-1, 82, '80%', color='red', fontsize=9, ha='right')
        ax2.set_ylabel('النسبة التراكمية %', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_ylim(0, 105)
        ax.set_title(title, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
    elif chart_type == "trend":
        x = data[x_col].astype(str).tolist()
        y = data[y_col].tolist()
        ax.bar(x, y, color='#2563eb', alpha=0.6, label='المبيعات')
        ax.plot(x, y, color='red', marker='o', linewidth=2, markersize=8, label='خط الاتجاه')
        ax.set_ylabel('المبيعات')
        ax.set_title(title, fontsize=12)
        ax.legend()
        plt.xticks(rotation=45, ha='right')
    
    else:
        plt.close()
        return None
    
    plt.tight_layout()
    
    try:
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        img_buffer.seek(0)
        plt.close()
        return img_buffer
    except Exception as e:
        print(f"❌ خطأ في حفظ الصورة: {e}")
        plt.close()
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
        print(f"❌ خطأ في إضافة الصورة: {e}")
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
            error_cell.value = f"⚠️ تعذر إضافة المخططات: {str(e)[:50]}"
            error_cell.font = Font(color="EF4444", size=10)


def _write_pareto_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل باريتو"):
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
                img_bytes = _create_chart_image(
                    frame, "pareto", chart_title,
                    x_col="الاسم", y_col="الحالي"
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
            error_cell.value = f"⚠️ تعذر إضافة المخطط: {str(e)[:50]}"
            error_cell.font = Font(color="EF4444", size=10)


def _write_trend_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل الاتجاهات"):
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