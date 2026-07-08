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


def _write_sheet_with_charts(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = None):
    """كتابة ورقة بدون مخططات (مؤقتاً) حتى يعمل التطبيق"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    # إضافة رسالة بدلاً من المخططات
    if not frame.empty and len(frame) > 1 and chart_title:
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
        
        info_cell = worksheet.cell(row=2, column=chart_start_col)
        info_cell.value = "⚠️ يتم إعداد المخططات..."
        info_cell.font = Font(color="EF4444", size=10)
        info_cell.alignment = Alignment(horizontal="center")


def _write_pareto_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل باريتو"):
    """كتابة ورقة تحليل باريتو بدون مخططات (مؤقتاً)"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    if not frame.empty and len(frame) > 1:
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
        
        info_cell = worksheet.cell(row=2, column=chart_start_col)
        info_cell.value = "⚠️ يتم إعداد المخططات..."
        info_cell.font = Font(color="EF4444", size=10)
        info_cell.alignment = Alignment(horizontal="center")


def _write_trend_sheet(writer, sheet_name: str, frame: pd.DataFrame, chart_title: str = "تحليل الاتجاهات"):
    """كتابة ورقة تحليل الاتجاهات بدون مخططات (مؤقتاً)"""
    safe_frame = frame.copy()
    if safe_frame.empty:
        safe_frame = pd.DataFrame({"البيان": ["لا توجد بيانات"]})
    
    safe_frame.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.book[sheet_name]
    _autosize_and_style(worksheet)
    
    if not frame.empty and len(frame) > 1:
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
        
        info_cell = worksheet.cell(row=2, column=chart_start_col)
        info_cell.value = "⚠️ يتم إعداد المخططات..."
        info_cell.font = Font(color="EF4444", size=10)
        info_cell.alignment = Alignment(horizontal="center")


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