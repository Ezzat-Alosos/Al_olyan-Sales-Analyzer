import streamlit as st
st.set_page_config(
    page_title="العليان لتحليل المبيعات",
    page_icon="📊",
    layout="wide"
)

import plotly.express as px
import plotly.graph_objects as go
import time

# ============================================================
# دوال الرسم (بدون Treemap)
# ============================================================
@st.cache_data(ttl=3600)
def chart_bar(df, title):
    start = time.time()
    result = px.bar(df.head(8), x="الاسم", y="الحالي", title=title, text_auto=".2s")
    print(f"⏱️ [ui] chart_bar: {time.time() - start:.2f} ثانية")
    return result

@st.cache_data(ttl=3600)
def chart_pie(df, title):
    start = time.time()
    result = px.pie(df.head(8), names="الاسم", values="الحالي", title=title, hole=0.35)
    print(f"⏱️ [ui] chart_pie: {time.time() - start:.2f} ثانية")
    return result

@st.cache_data(ttl=3600)
def chart_line(monthly_df):
    start = time.time()
    result = px.line(monthly_df, x="شهر_نصي", y="المبيعات", markers=True, title="اتجاه المبيعات الشهري")
    print(f"⏱️ [ui] chart_line: {time.time() - start:.2f} ثانية")
    return result

def chart_pareto(pareto_df, title):
    start = time.time()
    fig = go.Figure()
    fig.add_bar(x=pareto_df["الاسم"], y=pareto_df["الحالي"], name="المبيعات")
    fig.add_scatter(x=pareto_df["الاسم"], y=pareto_df["النسبة_التراكمية"], name="النسبة التراكمية", yaxis="y2")
    fig.update_layout(
        title=title,
        yaxis=dict(title="المبيعات"),
        yaxis2=dict(title="النسبة التراكمية", overlaying="y", side="right", range=[0, 100]),
    )
    print(f"⏱️ [ui] chart_pareto: {time.time() - start:.2f} ثانية")
    return fig

# ============================================================
# دوال الواجهة
# ============================================================
def setup_page():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
    }
    section[data-testid="stSidebar"] {
        background: #0f172a;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,.05);
        text-align: center;
    }
    .main-header {
        text-align: center;
        background: #1e3a8a;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .main-header h1 {
        margin: 0;
        color: white;
        font-size: 36px;
    }
    .info-bar {
        text-align: center;
        padding: 10px;
        font-size: 18px;
        color: #1e3a8a;
    }
    .modules-title {
        text-align: center;
        margin: 20px 0 10px 0;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
    }
    .js-plotly-plot {
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>📊 نظام العليان لتحليل المبيعات</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="info-bar">
            منصة ذكاء أعمال لتحليل المبيعات والعملاء والمنتجات والفروع
        </div>
        """,
        unsafe_allow_html=True
    )


def render_modules():
    st.markdown("<h3 class='modules-title'>الوحدات التحليلية</h3>", unsafe_allow_html=True)
    modules = [
        "👥 العملاء",
        "📦 المنتجات",
        "🧑‍💼 المناديب",
        "🏢 الفروع",
        "📈 تحليل باريتو",
        "📉 الاتجاهات",
    ]
    cols = st.columns(3, gap="small")
    for i, page in enumerate(modules):
        with cols[i % 3]:
            if st.button(
                page,
                use_container_width=True,
                type="primary" if st.session_state.page == page else "secondary",
                key=f"btn_{page}",
            ):
                st.session_state.page = page
                st.rerun()


def render_filters(years):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_year = st.selectbox("السنة الحالية", years, index=0)
    with col2:
        previous_default = 1 if len(years) > 1 else 0
        previous_year = st.selectbox("السنة السابقة", years, index=previous_default)
    with col3:
        comparison_type = st.selectbox("نوع المقارنة", ["شهر", "ربع سنوي", "نصف سنوي", "سنة كاملة"], index=3)
    with col4:
        period_value = None
        if comparison_type == "شهر":
            period_value = st.selectbox("الشهر", list(range(1, 13)))
        elif comparison_type == "ربع سنوي":
            period_value = st.selectbox("الربع", [1, 2, 3, 4])
        elif comparison_type == "نصف سنوي":
            period_value = st.selectbox("النصف", [1, 2])
        else:
            st.info("سنة كاملة")
    return current_year, previous_year, comparison_type, period_value


def render_dashboard(metrics):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي المبيعات الحالية", f"{metrics['current_total']:,.2f}")
    col2.metric("إجمالي المبيعات السابقة", f"{metrics['previous_total']:,.2f}")
    col3.metric("إجمالي الفرق", f"{metrics['difference']:,.2f}")
    col4.metric("نسبة النمو", f"{metrics['growth']:,.2f}%")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("عدد العملاء", metrics["customers_count"])
    col2.metric("عدد المنتجات", metrics["products_count"])
    col3.metric("عدد المناديب", metrics["representatives_count"])
    col4.metric("عدد الفروع", metrics["branches_count"])


def render_analysis_table(df, key):
    search = st.text_input("بحث", key=f"search_{key}")
    shown = df.copy()
    if search:
        shown = shown[shown["الاسم"].astype(str).str.contains(search, case=False, na=False)]
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.download_button(
        "تنزيل CSV",
        shown.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"download_{key}",
    )


def render_alerts(alerts_df):
    st.subheader("مركز التنبيهات")
    if alerts_df.empty:
        st.success("لا توجد تنبيهات حرجة أو فرص نمو كبيرة حالياً.")
        return
    for _, row in alerts_df.iterrows():
        if row["النوع"] == "خطر":
            st.error(f"{row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")
        else:
            st.success(f"{row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")


def render_insights(insights_df):
    st.subheader("Executive Insights")
    if insights_df.empty:
        st.info("لا توجد مؤشرات كافية.")
        return
    cols = st.columns(4)
    for idx, (_, row) in enumerate(insights_df.iterrows()):
        with cols[idx % 4]:
            st.metric(row["المؤشر"], row["الاسم"], f"{row['النسبة']:.2f}%")