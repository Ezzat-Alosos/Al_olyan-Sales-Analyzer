import os
from typing import BinaryIO

import pandas as pd
import streamlit as st  # تمت الإضافة


REQUIRED_COLUMNS = ["التاريخ", "الاسم", "المندوب", "الصنف", "الفرع", "المبيعات"]

COLUMN_ALIASES = {
    "date": "التاريخ",
    "customer": "الاسم",
    "representative": "المندوب",
    "product": "الصنف",
    "branch": "الفرع",
    "sales_amount": "المبيعات",
    "sales": "المبيعات",
    "amount": "المبيعات",
    "التاريخ": "التاريخ",
    "تاريخ": "التاريخ",
    "العميل": "الاسم",
    "عميل": "الاسم",
    "الاسم": "الاسم",
    "اسم_العميل": "الاسم",
    "اسم العميل": "الاسم",
    "المندوب": "المندوب",
    "مندوب": "المندوب",
    "المناديب": "المندوب",
    "الصنف": "الصنف",
    "المنتج": "الصنف",
    "منتج": "الصنف",
    "المنتجات": "الصنف",
    "الفرع": "الفرع",
    "فروع": "الفرع",
    "المبيعات": "المبيعات",
    "قيمة_المبيعات": "المبيعات",
    "قيمة المبيعات": "المبيعات",
    "قيمة_مبيعات": "المبيعات",
    "قيمة مبيعات": "المبيعات",
}


class DataValidationError(ValueError):
    """خطأ واضح يظهر للمستخدم عند وجود مشكلة في ملف البيانات."""
    pass


def _normalize_column_name(column: object) -> str:
    return str(column).strip().lower().replace(" ", "_")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in df.columns:
        raw = str(column).strip()
        normalized = _normalize_column_name(column)
        renamed[column] = COLUMN_ALIASES.get(normalized, COLUMN_ALIASES.get(raw, raw))
    return df.rename(columns=renamed)


def load_excel_file(file: BinaryIO) -> pd.DataFrame:
    """تحميل ملف Excel بصيغتي xlsx و xls ثم تنظيفه وتجهيزه للتحليل."""
    filename = getattr(file, "name", "")
    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".xlsx", ".xls"]:
        raise DataValidationError("صيغة الملف غير مدعومة. يرجى رفع ملف Excel بصيغة xlsx أو xls.")

    try:
        engine = "openpyxl" if extension == ".xlsx" else "xlrd"
        
        # ============================================================
        # محاولة قراءة الملف مع عرض أسماء الأوراق (للتصحيح)
        # ============================================================
        try:
            # قراءة الملف مع engine
            df = pd.read_excel(file, engine=engine)
        except Exception as e1:
            # إذا فشل، حاول قراءة الملف بدون تحديد engine
            try:
                file.seek(0)  # إعادة المؤشر إلى بداية الملف
                df = pd.read_excel(file)
            except Exception as e2:
                # إذا فشل مرة أخرى، حاول قراءة جميع الأوراق
                try:
                    file.seek(0)
                    xls = pd.ExcelFile(file)
                    sheet_names = xls.sheet_names
                    print(f"📋 أسماء الأوراق في الملف: {sheet_names}")
                    # قراءة أول ورقة
                    df = pd.read_excel(file, sheet_name=sheet_names[0])
                except Exception as e3:
                    raise DataValidationError(f"تعذر قراءة ملف Excel: {e3}") from e3
                    
    except Exception as exc:
        raise DataValidationError(f"تعذر قراءة ملف Excel: {exc}") from exc

    # طباعة أسماء الأعمدة للتصحيح
    print(f"📋 أسماء الأعمدة في الملف: {list(df.columns)}")
    
    return clean_sales_data(df, filename)


def clean_sales_data(df: pd.DataFrame, filename: str = "") -> pd.DataFrame:
    """تنظيف أسماء الأعمدة وتوحيد التاريخ وإنشاء أعمدة الفترة الزمنية."""
    if df.empty:
        raise DataValidationError("ملف Excel فارغ ولا يحتوي على بيانات.")

    df = df.copy()
    df.columns = [str(column).strip() for column in df.columns]
    
    # محاولة إعادة تسمية الأعمدة
    df = _rename_columns(df)
    
    # طباعة الأعمدة بعد إعادة التسمية
    print(f"📋 الأعمدة بعد إعادة التسمية: {list(df.columns)}")

    # التحقق من الأعمدة المطلوبة
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise DataValidationError(
            f"الأعمدة المطلوبة غير موجودة: {', '.join(missing)}\n"
            f"الأعمدة الموجودة في ملفك: {', '.join(df.columns)}\n"
            f"تأكد من أن لديك الأعمدة: {', '.join(REQUIRED_COLUMNS)}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    for column in ["الاسم", "المندوب", "الصنف", "الفرع"]:
        df[column] = df[column].astype(str).str.strip()
        df[column] = df[column].replace({"": "غير محدد", "nan": "غير محدد", "None": "غير محدد"})

    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")    
    invalid_dates = int(df["التاريخ"].isna().sum())
    if invalid_dates:
        raise DataValidationError(f"يوجد {invalid_dates} صف يحتوي على تاريخ غير صالح.")

    df["المبيعات"] = pd.to_numeric(df["المبيعات"], errors="coerce")
    invalid_sales = int(df["المبيعات"].isna().sum())
    if invalid_sales:
        raise DataValidationError(f"يوجد {invalid_sales} صف يحتوي على قيمة مبيعات غير صالحة.")

    df = df.dropna(subset=["التاريخ", "المبيعات"])
    df = df[df["المبيعات"] >= 0]
    if df.empty:
        raise DataValidationError("لا توجد بيانات صالحة بعد التنظيف.")

    df["السنة"] = df["التاريخ"].dt.year.astype(int)
    df["الشهر"] = df["التاريخ"].dt.month.astype(int)
    df["الربع"] = df["التاريخ"].dt.quarter.astype(int)
    df["النصف"] = ((df["الشهر"] - 1) // 6 + 1).astype(int)
    df["شهر_نصي"] = df["التاريخ"].dt.strftime("%Y-%m")

    return df


def get_available_years(df: pd.DataFrame) -> list[int]:
    return sorted(df["السنة"].dropna().astype(int).unique().tolist(), reverse=True)


# ============================================================
# التعديل 2: إضافة دالة التخزين المؤقت لتحميل الملف (تحسين الأداء)
# ============================================================
@st.cache_data(ttl=3600)
def load_and_clean_excel(file) -> pd.DataFrame:
    """تحميل وتنظيف ملف Excel مع التخزين المؤقت لمنع إعادة التحميل."""
    return load_excel_file(file)