import time
import streamlit as st
from calculations import (
    compare_all_dimensions,
    dashboard_metrics,
    pareto_analysis,
    trend_monthly,
    trend_yearly,
    executive_insights,
    customer_segments,
)
from data_manager import DataValidationError, get_available_years, load_and_clean_excel
from excel_export import export_to_excel
from pdf_export import export_to_pdf
from ui import (
    chart_bar,
    chart_line,
    chart_pareto,
    chart_pie,
    render_analysis_table,
    render_dashboard,
    render_filters,
    render_header,
    setup_page,
    render_modules,
)

# ============================================================
# تخزين مؤقت للبيانات
# ============================================================
@st.cache_resource(ttl=3600)
def load_and_process_data(file):
    start = time.time()
    df = load_and_clean_excel(file)
    years = get_available_years(df)
    print(f"⏱️ [cache] تحميل ومعالجة الملف: {time.time() - start:.2f} ثانية")
    return df, years


@st.cache_resource(ttl=3600)
def compute_all_results_cached(df, current_year, previous_year, comparison_type, period_value):
    start = time.time()
    all_results = compare_all_dimensions(df, current_year, previous_year, comparison_type, period_value)
    metrics = dashboard_metrics(df, current_year, previous_year, comparison_type, period_value)
    insights = executive_insights({
        "customers": all_results["customers"],
        "products": all_results["products"],
        "representatives": all_results["representatives"],
        "branches": all_results["branches"],
    })
    print(f"⏱️ [cache] حساب النتائج: {time.time() - start:.2f} ثانية")
    return all_results, metrics, insights


@st.cache_resource(ttl=3600)
def compute_pareto_cached(df, current_year, comparison_type, period_value):
    start = time.time()
    result = {
        "customers": pareto_analysis(df, "الاسم", current_year, comparison_type, period_value),
        "products": pareto_analysis(df, "الصنف", current_year, comparison_type, period_value),
    }
    print(f"⏱️ [cache] حساب باريتو: {time.time() - start:.2f} ثانية")
    return result


@st.cache_resource(ttl=3600)
def compute_trends_cached(df):
    start = time.time()
    monthly = trend_monthly(df)
    yearly = trend_yearly(df)
    print(f"⏱️ [cache] حساب الاتجاهات: {time.time() - start:.2f} ثانية")
    return monthly, yearly


@st.cache_resource(ttl=3600)
def get_export_data(df, current_year, comparison_type, period_value):
    """جلب بيانات باريتو والاتجاهات للتصدير"""
    start = time.time()
    pareto_customers = pareto_analysis(df, "الاسم", current_year, comparison_type, period_value)
    pareto_products = pareto_analysis(df, "الصنف", current_year, comparison_type, period_value)
    trend_data = trend_monthly(df)
    print(f"⏱️ [cache] بيانات التصدير: {time.time() - start:.2f} ثانية")
    return pareto_customers, pareto_products, trend_data


# ============================================================
# دوال العرض (بدون Treemap)
# ============================================================
def _render_tab(title: str, frame, chart_title: str, key: str):
    st.subheader(title)
    render_analysis_table(frame, key)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_bar(frame.head(10), f"{chart_title} - Bar Chart"), use_container_width=True)
    with col2:
        st.plotly_chart(chart_pie(frame.head(10), f"{chart_title} - Pie Chart"), use_container_width=True)


def _render_customer_analysis(customers):
    st.subheader("تحليل العملاء")
    segments = customer_segments(customers)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("العملاء الجدد", len(segments["new"]))
    col2.metric("العملاء المفقودون", len(segments["lost"]))
    col3.metric("العملاء المتنامون", len(segments["growing"]))
    col4.metric("العملاء المتراجعون", len(segments["declining"]))

    segment_tabs = st.tabs(["الجدد", "المفقودون", "المتنامون", "المتراجعون"])
    with segment_tabs[0]:
        st.dataframe(segments["new"], use_container_width=True, hide_index=True)
    with segment_tabs[1]:
        st.dataframe(segments["lost"], use_container_width=True, hide_index=True)
    with segment_tabs[2]:
        st.dataframe(segments["growing"], use_container_width=True, hide_index=True)
    with segment_tabs[3]:
        st.dataframe(segments["declining"], use_container_width=True, hide_index=True)


# ============================================================
# الرئيسية
# ============================================================
def main():
    setup_page()

    if "page" not in st.session_state:
        st.session_state.page = "👥 العملاء"

    render_header()

    uploaded_file = st.file_uploader("ارفع ملف Excel", type=["xlsx", "xls"])

    render_modules()

    with st.sidebar:
        st.image("logo.png", width=180)
        st.markdown("## القرار  السليم  في  التقرير  السليم")
        st.success("جاهز لتحليل بيانات المبيعات")
        st.markdown("---")
        st.markdown("""
        ### 🎯 هدفنا  من  إنشاء  أدوات  التحليل

        📊 تحويل  البيانات  إلى  قرارات  ذكية  وتقارير  دقيقة.

        📈 اكتشاف  فرص  النمو  وزيادة  الأرباح.

        ⚡ تقليل  التكاليف  وتوفير  الوقت  والجهد.

        🎯 قياس  الأداء  بدقة  ووضوح.

        📉 كشف  نقاط  الضعف  قبل  تفاقمها.

        💡 دعم  اتخاذ  القرار  بثقة.

        🚀 رفع  كفاءة  الأعمال  وتحقيق  النمو.
        """)
        st.markdown("---")
        st.caption(
            "المهندس المالي: عزت العليان\n\n"
            "أتمتة الأعمال بالذكاء الاصطناعي\n\n"
            "777884468"
        )

    if uploaded_file is None:
        st.info("يرجى رفع ملف Excel يحتوي على أعمدة المبيعات المطلوبة للبدء.")
        return

    # ============================================================
    # تحميل البيانات
    # ============================================================
    try:
        start_total = time.time()
        df, years = load_and_process_data(uploaded_file)
        print(f"⏱️ [main] إجمالي تحميل ومعالجة: {time.time() - start_total:.2f} ثانية")
    except DataValidationError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"حدث خطأ غير متوقع: {exc}")
        return

    if len(years) < 1:
        st.error("لا توجد سنوات صالحة.")
        return

    # ============================================================
    # الفلاتر
    # ============================================================
    current_year, previous_year, comparison_type, period_value = render_filters(years)

    # ============================================================
    # حساب النتائج
    # ============================================================
    with st.spinner("جاري تحليل البيانات..."):
        start_analysis = time.time()
        all_results, metrics, insights = compute_all_results_cached(
            df, current_year, previous_year, comparison_type, period_value
        )
        print(f"⏱️ [main] إجمالي التحليل: {time.time() - start_analysis:.2f} ثانية")

    customers = all_results["customers"]
    products = all_results["products"]
    representatives = all_results["representatives"]
    branches = all_results["branches"]

    # ============================================================
    # بطاقة تعريف التقرير
    # ============================================================
    months = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
              7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
    quarters = {1: "الربع الأول", 2: "الربع الثاني", 3: "الربع الثالث", 4: "الربع الرابع"}
    halves = {1: "النصف الأول", 2: "النصف الثاني"}

    if comparison_type == "سنة كاملة":
        report_type = "مقارنة سنوية"
        report_period = f"{previous_year} ↔ {current_year}"
    elif comparison_type == "شهر":
        report_type = "مقارنة شهرية"
        report_period = f"{months.get(period_value)} {previous_year} ↔ {months.get(period_value)} {current_year}"
    elif comparison_type == "ربع سنوي":
        report_type = "مقارنة ربع سنوية"
        report_period = f"{quarters.get(period_value)} {previous_year} ↔ {quarters.get(period_value)} {current_year}"
    elif comparison_type == "نصف سنوي":
        report_type = "مقارنة نصف سنوية"
        report_period = f"{halves.get(period_value)} {previous_year} ↔ {halves.get(period_value)} {current_year}"
    else:
        report_type = "تحليل مبيعات"
        report_period = "-"

    # ============================================================
    # أزرار التصدير
    # ============================================================
    export_col1, export_col2 = st.columns(2)

    # ============================================================
    # حساب بيانات باريتو والاتجاهات للتصدير
    # ============================================================
    pareto_customers, pareto_products, trend_data = get_export_data(df, current_year, comparison_type, period_value)

    # تصدير Excel
    excel_file = export_to_excel(
        metrics, 
        customers, 
        products, 
        representatives, 
        branches, 
        insights,
        pareto_customers=pareto_customers,
        pareto_products=pareto_products,
        trend_data=trend_data
    )
    export_col1.download_button(
        "📥 تصدير Excel",
        excel_file,
        file_name="al_asa_sales_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # تصدير PDF
    report_description = ""
    records_count = len(df)

    pdf_file = export_to_pdf(
        metrics,
        customers,
        products,
        representatives,
        branches,
        insights,
        report_description,
        report_type,
        report_period,
        records_count,
    )

    export_col2.download_button(
        "📄 تصدير PDF",
        pdf_file,
        file_name="al_asa_sales_analysis.pdf",
        mime="application/pdf",
    )

    # ============================================================
    # عرض لوحة المؤشرات والوحدات
    # ============================================================
    render_dashboard(metrics)

    analysis_page = st.session_state.page

    if analysis_page == "👥 العملاء":
        _render_tab("العملاء", customers, "تحليل العملاء", "customers")
        _render_customer_analysis(customers)

    elif analysis_page == "📦 المنتجات":
        _render_tab("المنتجات", products, "تحليل المنتجات", "products")

    elif analysis_page == "🧑‍💼 المناديب":
        _render_tab("المناديب", representatives, "تحليل المناديب", "representatives")

    elif analysis_page == "🏢 الفروع":
        _render_tab("الفروع", branches, "تحليل الفروع", "branches")

    elif analysis_page == "📈 تحليل باريتو":
        st.subheader("تحليل باريتو")
        pareto_data = compute_pareto_cached(df, current_year, comparison_type, period_value)
        pareto_customers = pareto_data["customers"]
        pareto_products = pareto_data["products"]

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_pareto(pareto_customers, "Pareto - العملاء"), use_container_width=True)
        with col2:
            st.plotly_chart(chart_pareto(pareto_products, "Pareto - المنتجات"), use_container_width=True)

        st.write("أفضل العملاء المساهمين في 80% من المبيعات")
        st.dataframe(pareto_customers[pareto_customers["ضمن_80"]], use_container_width=True, hide_index=True)

        st.write("أفضل المنتجات المساهمة في 80% من المبيعات")
        st.dataframe(pareto_products[pareto_products["ضمن_80"]], use_container_width=True, hide_index=True)

    elif analysis_page == "📉 الاتجاهات":
        st.subheader("تحليل الاتجاهات")
        monthly, yearly = compute_trends_cached(df)
        st.plotly_chart(chart_line(monthly), use_container_width=True)
        st.line_chart(yearly, x="السنة", y="المبيعات")


if __name__ == "__main__":
    main()