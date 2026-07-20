import streamlit as st

st.set_page_config(
    page_title="العليان لتحليل المبيعات",
    page_icon="📊",
    layout="wide"
)

import plotly.express as px
import plotly.graph_objects as go


def setup_page():
    st.markdown("""
    <style>
    /* تنسيق عام */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
    }
    
    /* تنسيق الشريط الجانبي */
    section[data-testid="stSidebar"] {
        background: #0f172a;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* تنسيق رأس الصفحة */
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #1e3a8a, #2563eb);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
    }
    .main-header h1 {
        margin: 0;
        color: white;
        font-size: 36px;
        font-weight: 700;
    }
    
    /* تنسيق النص التعريفي */
    .info-bar {
        text-align: center;
        padding: 12px;
        font-size: 18px;
        color: #1e3a8a;
        background: rgba(255,255,255,0.7);
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #dbeafe;
    }
    
    /* ============================================================
    تنسيق الكروت
    ============================================================ */
    .cards-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
        margin: 20px 0;
        direction: rtl;
    }
    
    .card {
        background: white;
        border-radius: 16px;
        padding: 20px 18px;
        width: 160px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
        position: relative;
        overflow: hidden;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(30, 58, 138, 0.15);
        border-color: #2563eb;
    }
    
    .card.active {
        border-color: #2563eb;
        box-shadow: 0 8px 30px rgba(30, 58, 138, 0.2);
        background: linear-gradient(135deg, #ffffff, #eff6ff);
    }
    
    .card.active::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #1e3a8a, #2563eb);
        border-radius: 16px 16px 0 0;
    }
    
    .card .icon {
        font-size: 32px;
        margin-bottom: 8px;
        display: block;
    }
    
    .card .title {
        font-size: 13px;
        font-weight: 600;
        color: #1e293b;
        margin: 0;
    }
    
    .card .badge {
        font-size: 10px;
        color: #2563eb;
        background: #dbeafe;
        padding: 2px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 6px;
    }
    
    /* ألوان مختلفة لكل كارت */
    .card-1 .icon { color: #1e3a8a; }
    .card-2 .icon { color: #2563eb; }
    .card-3 .icon { color: #7c3aed; }
    .card-4 .icon { color: #0891b2; }
    .card-5 .icon { color: #059669; }
    .card-6 .icon { color: #dc2626; }
    
    /* ============================================================
    تنسيق بطاقات المؤشرات (Metrics) - محسّن
    ============================================================ */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 10px 0 20px 0;
        direction: rtl;
    }
    
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-color: #2563eb;
    }
    
    .metric-card .metric-icon {
        font-size: 22px;
        display: block;
        margin-bottom: 4px;
    }
    
    .metric-card .metric-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 4px;
    }
    
    .metric-card .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
    }
    
    .metric-card .metric-change {
        font-size: 11px;
        font-weight: 500;
        margin-top: 4px;
    }
    
    .metric-card .metric-change.positive {
        color: #059669;
    }
    
    .metric-card .metric-change.negative {
        color: #dc2626;
    }
    
    /* ألوان مختلفة للمؤشرات */
    .metric-blue .metric-value { color: #1e3a8a; }
    .metric-blue .metric-icon { color: #1e3a8a; }
    .metric-green .metric-value { color: #059669; }
    .metric-green .metric-icon { color: #059669; }
    .metric-purple .metric-value { color: #7c3aed; }
    .metric-purple .metric-icon { color: #7c3aed; }
    .metric-orange .metric-value { color: #d97706; }
    .metric-orange .metric-icon { color: #d97706; }
    .metric-red .metric-value { color: #dc2626; }
    .metric-red .metric-icon { color: #dc2626; }
    .metric-teal .metric-value { color: #0891b2; }
    .metric-teal .metric-icon { color: #0891b2; }
    .metric-pink .metric-value { color: #db2777; }
    .metric-pink .metric-icon { color: #db2777; }
    
    /* ============================================================
    تنسيق باقي العناصر
    ============================================================ */
    .stButton button {
        width: 100%;
        border-radius: 10px;
        font-weight: 500;
    }
    
    .js-plotly-plot {
        margin: 0 auto;
    }
    
    .upload-area {
        border: 2px dashed #93c5fd;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        background: rgba(219, 234, 254, 0.3);
        margin: 15px 0;
    }
                
    #===============
    /* تنسيق بطاقات المؤشرات - تحسين وضوح النصوص */
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-color: #2563eb;
    }

    .metric-card .metric-icon {
        font-size: 24px;
        display: block;
        margin-bottom: 6px;
    }

    .metric-card .metric-label {
        font-size: 13px;
        color: #1e293b;  /* 🔥 تغيير من #64748b إلى لون داكن */
        font-weight: 600;  /* 🔥 زيادة الوزن */
        margin-bottom: 6px;
        letter-spacing: 0.3px;  /* 🔥 تحسين القراءة */
    }

    .metric-card .metric-value {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;  /* 🔥 لون داكن جداً */
    }

    /* ألوان مختلفة للمؤشرات (للأرقام فقط) */
    .metric-blue .metric-value { color: #1e3a8a; }
    .metric-green .metric-value { color: #059669; }
    .metric-purple .metric-value { color: #7c3aed; }
    .metric-orange .metric-value { color: #d97706; }
    .metric-red .metric-value { color: #dc2626; }
    .metric-teal .metric-value { color: #0891b2; }
    .metric-pink .metric-value { color: #db2777; }

    /* 🔥 الأيقونات بألوان واضحة */
    .metric-blue .metric-icon { color: #1e3a8a; }
    .metric-green .metric-icon { color: #059669; }
    .metric-purple .metric-icon { color: #7c3aed; }
    .metric-orange .metric-icon { color: #d97706; }
    .metric-red .metric-icon { color: #dc2626; }
    .metric-teal .metric-icon { color: #0891b2; }
    .metric-pink .metric-icon { color: #db2777; }
        #================================




    </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>📊 العليان لتحليل المبيعات</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="info-bar">
            🚀 منصة ذكاء أعمال لتحليل المبيعات والعملاء والمنتجات والفروع
        </div>
        """,
        unsafe_allow_html=True
    )


def render_modules():
    """عرض الوحدات التحليلية على شكل أزرار"""
    
    modules = [
        {"id": "👥 العملاء", "icon": "👥", "title": "العملاء"},
        {"id": "📦 المنتجات", "icon": "📦", "title": "المنتجات"},
        {"id": "🧑‍💼 المناديب", "icon": "🧑‍💼", "title": "المناديب"},
        {"id": "🏢 الفروع", "icon": "🏢", "title": "الفروع"},
        {"id": "📈 تحليل باريتو", "icon": "📈", "title": "باريتو 80/20"},
        {"id": "📉 الاتجاهات", "icon": "📉", "title": "الاتجاهات"},
    ]
    
    cols = st.columns(3, gap="small")
    
    for i, module in enumerate(modules):
        with cols[i % 3]:
            is_active = st.session_state.page == module["id"]
            btn_type = "primary" if is_active else "secondary"
            
            # عرض الزر مع "تحليل" مرة واحدة فقط
            if st.button(
                f"{module['icon']}\nتحليل {module['title']}",
                key=f"btn_{module['id']}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.page = module["id"]
                st.rerun()


def render_filters(years):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_year = st.selectbox("📅 السنة الحالية", years, index=0)
    with col2:
        previous_default = 1 if len(years) > 1 else 0
        previous_year = st.selectbox("📅 السنة السابقة", years, index=previous_default)
    with col3:
        comparison_type = st.selectbox("📊 نوع المقارنة", ["شهر", "ربع سنوي", "نصف سنوي", "سنة كاملة"], index=3)
    with col4:
        period_value = None
        if comparison_type == "شهر":
            period_value = st.selectbox("📆 الشهر", list(range(1, 13)))
        elif comparison_type == "ربع سنوي":
            period_value = st.selectbox("📆 الربع", [1, 2, 3, 4])
        elif comparison_type == "نصف سنوي":
            period_value = st.selectbox("📆 النصف", [1, 2])
        else:
            st.info("📅 سنة كاملة")
    return current_year, previous_year, comparison_type, period_value


def render_dashboard(metrics):
    """عرض المؤشرات على شكل كروت منظمة"""
    
    # الصف الأول - مؤشرات المبيعات
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card metric-blue">
            <span class="metric-icon">💰</span>
            <div class="metric-label">إجمالي المبيعات الحالية</div>
            <div class="metric-value">{metrics['current_total']:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card metric-purple">
            <span class="metric-icon">📊</span>
            <div class="metric-label">إجمالي المبيعات السابقة</div>
            <div class="metric-value">{metrics['previous_total']:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        # تغيير اللون حسب الفرق (إيجابي أو سلبي)
        diff_class = "metric-green" if metrics['difference'] >= 0 else "metric-red"
        diff_icon = "📈" if metrics['difference'] >= 0 else "📉"
        st.markdown(f'''
        <div class="metric-card {diff_class}">
            <span class="metric-icon">{diff_icon}</span>
            <div class="metric-label">إجمالي الفرق</div>
            <div class="metric-value">{metrics['difference']:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        # تغيير اللون حسب نسبة النمو
        growth_class = "metric-green" if metrics['growth'] >= 0 else "metric-red"
        st.markdown(f'''
        <div class="metric-card {growth_class}">
            <span class="metric-icon">📈</span>
            <div class="metric-label">نسبة النمو</div>
            <div class="metric-value">{metrics['growth']:.2%}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # الصف الثاني - مؤشرات العد
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card metric-teal">
            <span class="metric-icon">👥</span>
            <div class="metric-label">عدد العملاء</div>
            <div class="metric-value">{metrics['customers_count']:,}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card metric-orange">
            <span class="metric-icon">📦</span>
            <div class="metric-label">عدد المنتجات</div>
            <div class="metric-value">{metrics['products_count']:,}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card metric-pink">
            <span class="metric-icon">🧑‍💼</span>
            <div class="metric-label">عدد المناديب</div>
            <div class="metric-value">{metrics['representatives_count']:,}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card metric-purple">
            <span class="metric-icon">🏢</span>
            <div class="metric-label">عدد الفروع</div>
            <div class="metric-value">{metrics['branches_count']:,}</div>
        </div>
        ''', unsafe_allow_html=True)


def render_analysis_table(df, key):
    search = st.text_input("🔍 بحث", key=f"search_{key}")
    shown = df.copy()
    if search:
        shown = shown[shown["الاسم"].astype(str).str.contains(search, case=False, na=False)]
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 تنزيل CSV",
        shown.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"download_{key}",
    )


# ============================================================
# دوال الرسوم البيانية
# ============================================================
@st.cache_data(ttl=3600)
def chart_bar(df, title):
    data = df.head(15)
    return px.bar(data, x="الاسم", y="الحالي", title=title, text_auto=".2s")


@st.cache_data(ttl=3600)
def chart_pie(df, title):
    return px.pie(df.head(10), names="الاسم", values="الحالي", title=title, hole=0.35)


@st.cache_data(ttl=3600)
def chart_line(monthly_df):
    return px.line(monthly_df, x="شهر_نصي", y="المبيعات", markers=True, title="اتجاه المبيعات الشهري")


def chart_pareto(pareto_df, title):
    fig = go.Figure()
    fig.add_bar(x=pareto_df["الاسم"], y=pareto_df["الحالي"], name="المبيعات")
    fig.add_scatter(x=pareto_df["الاسم"], y=pareto_df["النسبة_التراكمية"], name="النسبة التراكمية", yaxis="y2")
    fig.update_layout(
        title=title,
        yaxis=dict(title="المبيعات"),
        yaxis2=dict(title="النسبة التراكمية", overlaying="y", side="right", range=[0, 100]),
    )
    return fig


def render_alerts(alerts_df):
    st.subheader("🔔 مركز التنبيهات")
    if alerts_df.empty:
        st.success("✅ لا توجد تنبيهات حرجة أو فرص نمو كبيرة حالياً.")
        return
    for _, row in alerts_df.iterrows():
        if row["النوع"] == "خطر":
            st.error(f"⚠️ {row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")
        else:
            st.success(f"✅ {row['الرسالة']}: {row['الاسم']} ({row['النسبة']:.2f}%)")


def render_insights(insights_df):
    st.subheader("💡 Executive Insights")
    if insights_df.empty:
        st.info("لا توجد مؤشرات كافية.")
        return
    cols = st.columns(4)
    for idx, (_, row) in enumerate(insights_df.iterrows()):
        with cols[idx % 4]:
            st.metric(row["المؤشر"], row["الاسم"], f"{row['النسبة']:.2f}%")