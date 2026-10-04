"""
app.py — Karinderya Management System
Streamlit app for a small Filipino karinderya.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import db
import ai

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="🍲 Karinderya Management",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Import Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* ── Root vars ── */
    :root {
        --karin-orange: #E8751A;
        --karin-yellow: #F5A623;
        --karin-red: #C0392B;
        --karin-green: #27AE60;
        --karin-dark: #1A1A2E;
        --karin-card: #16213E;
        --karin-surface: #0F3460;
        --karin-text: #E8E8E8;
        --karin-accent: #F7B731;
        --karin-gradient: linear-gradient(135deg, #E8751A 0%, #F5A623 100%);
    }

    /* ── Global ── */
    .stApp {
        font-family: 'Outfit', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
        border-right: 2px solid rgba(232, 117, 26, 0.3);
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #F5A623 !important;
        font-weight: 600;
        font-size: 1.05rem;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(245,166,35,0.15);
        border-radius: 12px;
        padding: 10px 18px !important;
        margin-bottom: 6px;
        transition: all 0.25s ease;
        font-size: 1rem;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(232, 117, 26, 0.15);
        border-color: rgba(232, 117, 26, 0.5);
        transform: translateX(4px);
    }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(22,33,62,0.9) 0%, rgba(15,52,96,0.9) 100%);
        border: 1px solid rgba(245,166,35,0.25);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(232,117,26,0.15);
    }
    div[data-testid="stMetric"] label {
        color: #F5A623 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 1.8rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-weight: 500;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        font-family: 'Outfit', sans-serif;
        padding: 10px 28px;
        font-size: 1rem;
        transition: all 0.25s ease;
        border: none;
    }
    .stButton > button[kind="primary"],
    .stButton > button:first-child {
        background: linear-gradient(135deg, #E8751A 0%, #F5A623 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(232,117,26,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(232,117,26,0.4);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(22,33,62,0.5);
        border-radius: 14px;
        padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 500;
        color: #B0B0B0;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #E8751A 0%, #F5A623 100%) !important;
        color: white !important;
        font-weight: 600;
    }

    /* ── DataFrames / tables ── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Header banner ── */
    .karin-header {
        background: linear-gradient(135deg, #E8751A 0%, #F5A623 50%, #E8751A 100%);
        background-size: 200% 200%;
        animation: gradientShift 4s ease infinite;
        padding: 24px 32px;
        border-radius: 18px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(232,117,26,0.25);
        text-align: center;
    }
    .karin-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        letter-spacing: -0.5px;
    }
    .karin-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 4px 0 0;
        font-weight: 400;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ── Info box ── */
    .karin-info {
        background: linear-gradient(135deg, rgba(39,174,96,0.1) 0%, rgba(22,33,62,0.8) 100%);
        border: 1px solid rgba(39,174,96,0.3);
        border-radius: 14px;
        padding: 16px 20px;
        margin: 12px 0;
    }

    /* ── Section header ── */
    .section-hdr {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 20px 0 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(245,166,35,0.2);
    }
    .section-hdr h3 {
        color: #F5A623;
        font-weight: 700;
        font-size: 1.2rem;
        margin: 0;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1rem;
        border-radius: 12px;
    }

    /* ── Form elements ── */
    .stSelectbox > label, .stNumberInput > label, .stDateInput > label, .stTimeInput > label, .stTextInput > label {
        font-weight: 500;
        color: #F5A623 !important;
    }

    /* ── Divider ── */
    hr {
        border-color: rgba(245,166,35,0.15);
    }

    /* ── Hide Streamlit default ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Init DB ──────────────────────────────────────────────────────────────────

db.init_db()


# ── Plotly theme ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(22,33,62,0.4)",
    font=dict(family="Outfit, sans-serif", color="#E8E8E8"),
    margin=dict(l=40, r=20, t=50, b=40),
    xaxis=dict(gridcolor="rgba(245,166,35,0.08)"),
    yaxis=dict(gridcolor="rgba(245,166,35,0.08)"),
)

COLORS = ["#E8751A", "#F5A623", "#27AE60", "#3498DB", "#9B59B6",
          "#E74C3C", "#1ABC9C", "#F39C12", "#2ECC71", "#E67E22"]


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 12px 0 20px;'>
        <div style='font-size: 3rem; margin-bottom: 4px;'>🍲</div>
        <h2 style='color: #F5A623; margin: 0; font-weight: 800; font-size: 1.4rem;'>Karinderya Management</h2>
        <p style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin: 2px 0 0;'>Sales Tracking System</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "📍 Navigation",
        ["📊 Dashboard", "🧾 Record Sale", "📋 Menu", "🤖 AI Insights"],
        label_visibility="collapsed",
    )

    st.divider()

    # Generate sample data
    st.markdown("<p style='color:#F5A623; font-weight:600; font-size:0.85rem;'>⚡ QUICK ACTIONS</p>", unsafe_allow_html=True)
    if st.button("🎲 Generate Sample Data", use_container_width=True, help="Generate 60 days of random test data"):
        with st.spinner("Generating sample data..."):
            n = db.generate_sample_data(60)
        st.success(f"✅ Generated {n:,} sample sales records!")
        st.rerun()

    # Export CSV
    all_sales = db.get_all_sales()
    if not all_sales.empty:
        csv = all_sales.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export to CSV",
            data=csv,
            file_name=f"karinderya_sales_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    st.markdown(
        "<p style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.7rem;'>"
        "Karinderya Management v1.0<br>Made with ❤️ for Pinoy businesses</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.markdown("""
    <div class="karin-header">
        <h1>📊 Sales Dashboard</h1>
        <p>Monitor your karinderya's performance at a glance</p>
    </div>
    """, unsafe_allow_html=True)

    sales_df = db.get_all_sales()

    if sales_df.empty:
        st.info("📭 **No sales data yet.** Record a sale or click '🎲 Generate Sample Data' in the sidebar to get started.")
    else:
        sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])
        today = pd.Timestamp(datetime.now().date())
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        today_sales = sales_df[sales_df["sale_date"] == today]["total"].sum()
        week_sales = sales_df[sales_df["sale_date"] >= week_start]["total"].sum()
        month_sales = sales_df[sales_df["sale_date"] >= month_start]["total"].sum()

        # Yesterday comparison
        yesterday = today - timedelta(days=1)
        yesterday_sales = sales_df[sales_df["sale_date"] == yesterday]["total"].sum()
        today_delta = None
        if yesterday_sales > 0:
            pct = ((today_sales - yesterday_sales) / yesterday_sales) * 100
            today_delta = f"{pct:+.1f}% vs yesterday"

        # ── Metric Cards ──
        st.markdown("<div class='section-hdr'><h3>💰 Sales Overview</h3></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📅 Today", f"₱{today_sales:,.2f}", today_delta)
        c2.metric("📆 This Week", f"₱{week_sales:,.2f}")
        c3.metric("📆 This Month", f"₱{month_sales:,.2f}")
        c4.metric("📦 Total Transactions", f"{len(sales_df):,}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Charts Row 1: Sales Trend + Best/Worst dishes ──
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("<div class='section-hdr'><h3>📈 Sales Trend</h3></div>", unsafe_allow_html=True)
            trend_mode = st.radio("Grouping:", ["Daily", "Weekly", "Monthly"], horizontal=True, label_visibility="collapsed")

            trend_df = sales_df.copy()
            if trend_mode == "Daily":
                grouped = trend_df.groupby(trend_df["sale_date"].dt.date).agg(
                    revenue=("total", "sum"), orders=("quantity", "sum")
                ).reset_index()
                grouped.columns = ["Date", "Revenue", "Orders"]
            elif trend_mode == "Weekly":
                trend_df["week"] = trend_df["sale_date"].dt.to_period("W").apply(lambda x: x.start_time)
                grouped = trend_df.groupby("week").agg(
                    revenue=("total", "sum"), orders=("quantity", "sum")
                ).reset_index()
                grouped.columns = ["Date", "Revenue", "Orders"]
            else:
                trend_df["month"] = trend_df["sale_date"].dt.to_period("M").apply(lambda x: x.start_time)
                grouped = trend_df.groupby("month").agg(
                    revenue=("total", "sum"), orders=("quantity", "sum")
                ).reset_index()
                grouped.columns = ["Date", "Revenue", "Orders"]

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=grouped["Date"], y=grouped["Revenue"],
                mode="lines+markers",
                name="Revenue (₱)",
                line=dict(color="#F5A623", width=3, shape="spline"),
                marker=dict(size=6, color="#E8751A"),
                fill="tozeroy",
                fillcolor="rgba(245,166,35,0.1)",
            ))
            fig_trend.update_layout(
                **PLOTLY_LAYOUT,
                height=380,
                yaxis_title="Revenue (₱)",
                showlegend=False,
                hovermode="x unified",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_right:
            st.markdown("<div class='section-hdr'><h3>🏆 Top & Bottom Dishes</h3></div>", unsafe_allow_html=True)
            dish_sales = sales_df.groupby("dish_name").agg(
                revenue=("total", "sum"), qty=("quantity", "sum")
            ).sort_values("revenue", ascending=True).reset_index()

            fig_dishes = go.Figure()
            fig_dishes.add_trace(go.Bar(
                y=dish_sales["dish_name"],
                x=dish_sales["revenue"],
                orientation="h",
                marker=dict(
                    color=dish_sales["revenue"],
                    colorscale=[[0, "#C0392B"], [0.5, "#F5A623"], [1, "#27AE60"]],
                    cornerradius=6,
                ),
                text=[f"₱{v:,.0f}" for v in dish_sales["revenue"]],
                textposition="outside",
                textfont=dict(size=11, color="#E8E8E8"),
            ))
            fig_dishes.update_layout(
                **PLOTLY_LAYOUT,
                height=380,
                xaxis_title="Revenue (₱)",
                showlegend=False,
            )
            st.plotly_chart(fig_dishes, use_container_width=True)

        # ── Charts Row 2: Peak Hours + Pie chart ──
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("<div class='section-hdr'><h3>⏰ Peak Hours</h3></div>", unsafe_allow_html=True)
            sales_df["hour"] = sales_df["sale_time"].apply(lambda t: int(str(t).split(":")[0]))
            hourly = sales_df.groupby("hour").agg(
                revenue=("total", "sum"), orders=("quantity", "sum")
            ).reindex(range(5, 22), fill_value=0).reset_index()

            hourly["label"] = hourly["hour"].apply(lambda h: f"{h}:00")

            fig_hours = go.Figure()
            fig_hours.add_trace(go.Bar(
                x=hourly["label"],
                y=hourly["revenue"],
                marker=dict(
                    color=hourly["revenue"],
                    colorscale=[[0, "#16213E"], [0.4, "#E8751A"], [1, "#F5A623"]],
                    cornerradius=8,
                ),
                text=[f"₱{v:,.0f}" for v in hourly["revenue"]],
                textposition="outside",
                textfont=dict(size=10, color="#B0B0B0"),
            ))
            fig_hours.update_layout(
                **PLOTLY_LAYOUT,
                height=360,
                xaxis_title="Hour",
                yaxis_title="Revenue (₱)",
                showlegend=False,
            )
            st.plotly_chart(fig_hours, use_container_width=True)

        with col_b:
            st.markdown("<div class='section-hdr'><h3>🍽️ Customer Food Preferences</h3></div>", unsafe_allow_html=True)
            pie_data = sales_df.groupby("dish_name")["quantity"].sum().reset_index()
            pie_data.columns = ["Dish", "Quantity"]
            pie_data = pie_data.sort_values("Quantity", ascending=False)

            fig_pie = go.Figure()
            fig_pie.add_trace(go.Pie(
                labels=pie_data["Dish"],
                values=pie_data["Quantity"],
                hole=0.45,
                marker=dict(colors=COLORS[:len(pie_data)]),
                textinfo="label+percent",
                textfont=dict(size=11),
                hovertemplate="<b>%{label}</b><br>Quantity: %{value}<br>Share: %{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                **PLOTLY_LAYOUT,
                height=360,
                showlegend=False,
                annotations=[dict(
                    text="Sales",
                    x=0.5, y=0.5,
                    font=dict(size=16, color="#F5A623", family="Outfit"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_pie, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: RECORD SALE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🧾 Record Sale":
    st.markdown("""
    <div class="karin-header">
        <h1>🧾 Record a Sale</h1>
        <p>Add a new sales transaction</p>
    </div>
    """, unsafe_allow_html=True)

    menu_df = db.get_active_dishes()
    dish_list = menu_df["dish_name"].tolist() if not menu_df.empty else []

    # ── Add New Sale Form ──
    st.markdown("<div class='section-hdr'><h3>➕ New Sale</h3></div>", unsafe_allow_html=True)

    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sale_date = st.date_input("📅 Date", value=datetime.now().date())
            sale_time = st.time_input("🕐 Time", value=datetime.now().time())
        with col2:
            selected_dish = st.selectbox("🍲 Dish", options=dish_list, index=0 if dish_list else None)
            quantity = st.number_input("📦 Quantity", min_value=1, max_value=100, value=1, step=1)

        # Auto price
        if selected_dish and not menu_df.empty:
            price = float(menu_df[menu_df["dish_name"] == selected_dish]["price"].values[0])
        else:
            price = 0.0

        colp1, colp2 = st.columns(2)
        with colp1:
            price_input = st.number_input("💲 Price per serving (₱)", min_value=0.0, value=price, step=5.0, format="%.2f")
        with colp2:
            total = quantity * price_input
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(39,174,96,0.15), rgba(22,33,62,0.8));
                        border: 1px solid rgba(39,174,96,0.3); border-radius: 14px;
                        padding: 18px 20px; text-align: center; margin-top: 26px;'>
                <span style='color: rgba(255,255,255,0.6); font-size: 0.85rem;'>TOTAL</span><br>
                <span style='color: #27AE60; font-size: 1.8rem; font-weight: 800;'>₱{total:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)

        submitted = st.form_submit_button("✅  SAVE SALE", use_container_width=True)
        if submitted:
            if not selected_dish:
                st.error("❌ Please select a dish first!")
            else:
                db.add_sale(
                    sale_date.isoformat(),
                    sale_time.strftime("%H:%M"),
                    selected_dish,
                    quantity,
                    price_input,
                )
                st.success(f"✅ Saved! {selected_dish} × {quantity} = **₱{total:,.2f}**")
                st.rerun()

    # ── Recent Sales Table ──
    st.markdown("<div class='section-hdr'><h3>📋 Recent Sales</h3></div>", unsafe_allow_html=True)

    recent = db.get_all_sales().head(50)
    if recent.empty:
        st.info("No sales recorded yet.")
    else:
        display_df = recent[["id", "sale_date", "sale_time", "dish_name", "quantity", "price", "total"]].copy()
        display_df.columns = ["ID", "Date", "Time", "Dish", "Qty", "Price (₱)", "Total (₱)"]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price (₱)": st.column_config.NumberColumn(format="₱%.2f"),
                "Total (₱)": st.column_config.NumberColumn(format="₱%.2f"),
            },
        )

        # ── Edit / Delete ──
        with st.expander("✏️ Edit or delete an entry"):
            sale_id = st.number_input("Sale ID to edit/delete", min_value=1, step=1, key="edit_id")

            target_row = recent[recent["id"] == sale_id]
            if not target_row.empty:
                row = target_row.iloc[0]
                st.markdown(f"**Current:** {row['dish_name']} × {row['quantity']} = ₱{row['total']:,.2f} ({row['sale_date']} {row['sale_time']})")

                tab_edit, tab_delete = st.tabs(["✏️ Edit", "🗑️ Delete"])

                with tab_edit:
                    with st.form("edit_form"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_date = st.date_input("New date", value=pd.to_datetime(row["sale_date"]).date(), key="ed_date")
                            new_time = st.time_input("New time", value=datetime.strptime(row["sale_time"], "%H:%M").time(), key="ed_time")
                        with ec2:
                            dish_idx = dish_list.index(row["dish_name"]) if row["dish_name"] in dish_list else 0
                            new_dish = st.selectbox("New dish", dish_list, index=dish_idx, key="ed_dish")
                            new_qty = st.number_input("New quantity", min_value=1, value=int(row["quantity"]), key="ed_qty")

                        new_price_val = float(menu_df[menu_df["dish_name"] == new_dish]["price"].values[0]) if new_dish in dish_list else float(row["price"])
                        new_price = st.number_input("New price (₱)", min_value=0.0, value=new_price_val, key="ed_price", format="%.2f")

                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            db.update_sale(sale_id, new_date.isoformat(), new_time.strftime("%H:%M"), new_dish, new_qty, new_price)
                            st.success("✅ Updated successfully!")
                            st.rerun()

                with tab_delete:
                    st.warning(f"⚠️ Are you sure you want to delete Sale #{sale_id}?")
                    if st.button("🗑️ YES, DELETE", key="del_btn", type="primary"):
                        db.delete_sale(sale_id)
                        st.success("✅ Deleted successfully!")
                        st.rerun()
            else:
                st.caption("No entry selected or invalid ID.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: MENU
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📋 Menu":
    st.markdown("""
    <div class="karin-header">
        <h1>📋 Karinderya Menu</h1>
        <p>Manage your list of dishes and prices</p>
    </div>
    """, unsafe_allow_html=True)

    menu_df = db.get_menu()

    # ── Add new dish ──
    st.markdown("<div class='section-hdr'><h3>➕ Add a New Dish</h3></div>", unsafe_allow_html=True)

    with st.form("add_dish_form", clear_on_submit=True):
        ac1, ac2 = st.columns([2, 1])
        with ac1:
            new_name = st.text_input("🍲 Dish Name")
        with ac2:
            new_price = st.number_input("💲 Price (₱)", min_value=1.0, value=50.0, step=5.0, format="%.2f")
        if st.form_submit_button("➕ ADD DISH", use_container_width=True):
            if new_name.strip():
                db.add_dish(new_name, new_price)
                st.success(f"✅ Added **{new_name}** — ₱{new_price:,.2f}")
                st.rerun()
            else:
                st.error("❌ Please enter a dish name.")

    # ── Current menu ──
    st.markdown("<div class='section-hdr'><h3>📜 Current Menu</h3></div>", unsafe_allow_html=True)

    if menu_df.empty:
        st.info("No dishes in the menu.")
    else:
        active = menu_df[menu_df["is_active"] == 1].copy()
        inactive = menu_df[menu_df["is_active"] == 0].copy()

        if not active.empty:
            # Display as nice cards
            cols = st.columns(3)
            for i, (_, row) in enumerate(active.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, rgba(22,33,62,0.95), rgba(15,52,96,0.9));
                                border: 1px solid rgba(245,166,35,0.2); border-radius: 14px;
                                padding: 18px; margin-bottom: 12px; text-align: center;
                                box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                                transition: transform 0.2s;'>
                        <div style='font-size: 1.8rem; margin-bottom: 6px;'>🍽️</div>
                        <div style='color: white; font-weight: 700; font-size: 1.05rem;'>{row['dish_name']}</div>
                        <div style='color: #27AE60; font-weight: 800; font-size: 1.4rem; margin-top: 4px;'>₱{row['price']:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Edit/Delete section
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("✏️ Edit or remove a dish"):
                dish_options = active["dish_name"].tolist()
                sel_dish = st.selectbox("Select a dish", dish_options, key="menu_edit_sel")
                sel_row = active[active["dish_name"] == sel_dish].iloc[0]

                tab_e, tab_d = st.tabs(["✏️ Edit", "🗑️ Remove"])

                with tab_e:
                    with st.form("edit_dish_form"):
                        e1, e2 = st.columns([2, 1])
                        with e1:
                            upd_name = st.text_input("New name", value=sel_row["dish_name"], key="upd_dish_name")
                        with e2:
                            upd_price = st.number_input("New price (₱)", value=float(sel_row["price"]),
                                                        min_value=1.0, step=5.0, key="upd_dish_price", format="%.2f")
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            db.update_dish(int(sel_row["id"]), upd_name, upd_price)
                            st.success(f"✅ Updated: {upd_name} — ₱{upd_price:,.2f}")
                            st.rerun()

                with tab_d:
                    st.warning(f"⚠️ Remove **{sel_dish}** from the menu?")
                    if st.button("🗑️ YES, REMOVE", key="remove_dish_btn", type="primary"):
                        db.delete_dish(int(sel_row["id"]))
                        st.success(f"✅ Removed {sel_dish}")
                        st.rerun()

        if not inactive.empty:
            with st.expander(f"🔇 Hidden dishes ({len(inactive)})"):
                for _, row in inactive.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"~~{row['dish_name']}~~ — ₱{row['price']:,.2f}")
                    if c2.button("♻️ Restore", key=f"restore_{row['id']}"):
                        db.add_dish(row["dish_name"], row["price"])
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🤖 AI Insights":
    st.markdown("""
    <div class="karin-header">
        <h1>🤖 AI-Powered Insights</h1>
        <p>Smart analysis and recommendations for your karinderya</p>
    </div>
    """, unsafe_allow_html=True)

    sales_df = db.get_all_sales()

    if sales_df.empty:
        st.info("📭 **No data yet.** Record some sales or generate sample data first.")
    else:
        # Date range selector
        st.markdown("<div class='section-hdr'><h3>📅 Analysis Date Range</h3></div>", unsafe_allow_html=True)
        range_col1, range_col2 = st.columns(2)
        with range_col1:
            min_date = pd.to_datetime(sales_df["sale_date"]).min().date()
            start = st.date_input("From", value=min_date, key="ai_start")
        with range_col2:
            end = st.date_input("To", value=datetime.now().date(), key="ai_end")

        filtered = db.get_sales_range(start.isoformat(), end.isoformat())
        summary = db.sales_summary(filtered)

        # Quick stats
        qs1, qs2, qs3 = st.columns(3)
        qs1.metric("💰 Total Sales", f"₱{summary['total_sales']:,.2f}")
        qs2.metric("📦 Transactions", f"{summary['total_transactions']:,}")
        qs3.metric("📊 Daily Average", f"₱{summary['avg_daily_sales']:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Generate insights button
        if st.button("🧠  GENERATE AI INSIGHTS", use_container_width=True, type="primary"):
            with st.spinner("🔄 Analyzing your data... please wait..."):
                result = ai.get_ai_insights(summary)

            if result.get("error"):
                st.warning(result["error"])

            source_label = "🤖 Anthropic AI" if result["source"] == "ai" else "📐 Rule-Based Analysis"
            st.markdown(f"""
            <div style='background: rgba(245,166,35,0.08); border: 1px solid rgba(245,166,35,0.2);
                        border-radius: 12px; padding: 10px 16px; margin-bottom: 12px;
                        display: inline-block;'>
                <span style='color: #F5A623; font-weight: 600; font-size: 0.85rem;'>Source: {source_label}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(result["insights"])

        else:
            st.markdown("""
            <div class="karin-info">
                <p style='color: #E8E8E8; margin: 0;'>
                    👆 Click the button above to get AI-powered insights about your sales.<br><br>
                    <strong style='color: #F5A623;'>The analysis includes:</strong><br>
                    📊 Sales pattern summary<br>
                    🍳 Cooking recommendations — which dishes to prepare more or less<br>
                    📦 Inventory and food waste tips<br>
                    💰 Strategies to increase revenue
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Tip about API key
            with st.expander("🔑 How to set up an Anthropic API key"):
                st.markdown("""
                1. Create a `.env` file in the project folder
                2. Add this line inside:
                ```
                ANTHROPIC_API_KEY=sk-ant-xxxxxxxxx
                ```
                3. Get your API key at [console.anthropic.com](https://console.anthropic.com)
                4. Without a key, the system will use **rule-based analysis** — which still works great! 👍
                """)
