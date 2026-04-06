import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

st.set_page_config(page_title="Nassau Candy - Profitability Dashboard", layout="wide")

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "nassau_candy.csv")
    df = pd.read_csv(csv_path)
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  dayfirst=True, errors="coerce")
    df = df[df["Sales"] > 0].copy()
    df["Product Name"]   = df["Product Name"].str.strip().str.replace(r"\s+", " ", regex=True)
    df["Gross Margin (%)"] = (df["Gross Profit"] / df["Sales"] * 100).round(2)
    df["Profit per Unit"]  = (df["Gross Profit"] / df["Units"]).round(4)
    df["Month"] = df["Order Date"].dt.to_period("M")
    return df

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🍬 Nassau Candy Distributor")
st.subheader("Product Line Profitability & Margin Performance Dashboard")

df_raw = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.title("Filters")
min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()
date_range     = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
all_divs       = sorted(df_raw["Division"].dropna().unique())
sel_divs       = st.sidebar.multiselect("Division", all_divs, default=all_divs)
margin_thresh  = st.sidebar.slider("Margin Threshold (%)", 0, 100, 50)
product_search = st.sidebar.text_input("Product Search", placeholder="e.g. Gummy Bear")

df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df["Order Date"].dt.date >= date_range[0]) & (df["Order Date"].dt.date <= date_range[1])]
if sel_divs:
    df = df[df["Division"].isin(sel_divs)]
if product_search.strip():
    df = df[df["Product Name"].str.contains(product_search.strip(), case=False, na=False)]

if df.empty:
    st.warning("No data matches the current filters. Adjust the sidebar.")
    st.stop()

# ── Helper Functions ──────────────────────────────────────────────────────────
def build_product_df(data):
    p = data.groupby(["Division", "Product Name"]).agg(
        Total_Sales=("Sales","sum"), Total_Profit=("Gross Profit","sum"),
        Total_Cost=("Cost","sum"),   Total_Units=("Units","sum")
    ).reset_index()
    ts, tp = p["Total_Sales"].sum(), p["Total_Profit"].sum()
    p["Gross Margin (%)"]         = (p["Total_Profit"] / p["Total_Sales"] * 100).round(2)
    p["Profit per Unit"]          = (p["Total_Profit"] / p["Total_Units"]).round(4)
    p["Cost Ratio (%)"]           = (p["Total_Cost"]   / p["Total_Sales"] * 100).round(2)
    p["Revenue Contribution (%)"] = (p["Total_Sales"]  / ts * 100).round(2)
    p["Profit Contribution (%)"]  = (p["Total_Profit"] / tp * 100).round(2)
    vol = data.groupby(["Product Name","Month"])["Gross Margin (%)"].mean().reset_index()
    vol = vol.groupby("Product Name")["Gross Margin (%)"].agg(
        Margin_Volatility=lambda x: x.max() - x.min()
    ).reset_index()
    vol.columns = ["Product Name", "Margin Volatility"]
    p = p.merge(vol, on="Product Name", how="left")
    p["Margin Volatility"] = p["Margin Volatility"].round(2).fillna(0)
    return p

def build_division_df(data):
    d = data.groupby("Division").agg(
        Total_Sales=("Sales","sum"), Total_Profit=("Gross Profit","sum"),
        Total_Cost=("Cost","sum"),   Total_Units=("Units","sum")
    ).reset_index()
    d["Gross Margin (%)"]  = (d["Total_Profit"] / d["Total_Sales"] * 100).round(2)
    d["Revenue Share (%)"] = (d["Total_Sales"]  / d["Total_Sales"].sum()  * 100).round(2)
    d["Profit Share (%)"]  = (d["Total_Profit"] / d["Total_Profit"].sum() * 100).round(2)
    return d

product_df  = build_product_df(df)
division_df = build_division_df(df)
total_sales    = df["Sales"].sum()
total_profit   = df["Gross Profit"].sum()
overall_margin = total_profit / total_sales * 100 if total_sales > 0 else 0

# ── Sidebar Product List ──────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {len(product_df)} Products in NASSAU CANDY")
for p in sorted(product_df["Product Name"].unique()):
    st.sidebar.markdown(f"- {p}")

# ── Header ────────────────────────────────────────────────────────────────────
if product_search.strip():
    st.info(f'Filtering by: "{product_search.strip()}" — {product_df["Product Name"].nunique()} product(s) matched')
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Gross Margin (%)", f"{overall_margin:.1f}%")
k2.metric("Profit per Unit",  f"${total_profit/df['Units'].sum():.4f}" if df["Units"].sum() > 0 else "N/A")
k3.metric("Revenue",          f"${total_sales:,.0f}")
k4.metric("Profit",           f"${total_profit:,.0f}")
k5.metric("Units Sold",       f"{int(df['Units'].sum()):,}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Product Profitability", "Division Performance",
    "Cost & Margin Diagnostics", "Pareto Concentration", "Findings"
])

# ── Tab 1: Product Profitability ──────────────────────────────────────────────
with tab1:
    st.subheader("Product-Level Margin Leaderboard")
    sort_by = st.selectbox("Sort by", ["Total_Profit","Gross Margin (%)","Total_Sales","Profit per Unit","Revenue Contribution (%)","Profit Contribution (%)"])
    n_products = len(product_df)
    top_n = st.slider("Show top N", 1, n_products, min(10, n_products), key="t1") if n_products > 1 else 1
    sp = product_df.sort_values(sort_by, ascending=False).head(top_n)
    fig_h = max(4, top_n * 0.55)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(8, fig_h))
        colors = ["#2ecc71" if m >= margin_thresh else "#e74c3c" for m in sp["Gross Margin (%)"]]
        ax.barh(sp["Product Name"], sp["Total_Profit"], color=colors)
        ax.set_xlabel("Total Gross Profit ($)")
        ax.set_title("Gross Profit by Product")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        for i, v in enumerate(sp["Total_Profit"]):
            ax.text(v, i, f" ${v:,.0f}", va="center", fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        fig, ax = plt.subplots(figsize=(8, fig_h))
        avg = sp["Profit Contribution (%)"].mean()
        bar_colors = ["#3498db" if v >= avg else "#bdc3c7" for v in sp["Profit Contribution (%)"]]
        ax.barh(sp["Product Name"], sp["Profit Contribution (%)"], color=bar_colors)
        ax.set_xlabel("Profit Contribution (%)")
        ax.set_title("Profit Contribution %")
        for i, v in enumerate(sp["Profit Contribution (%)"]):
            ax.text(v, i, f" {v:.1f}%", va="center", fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    st.dataframe(
        sp[["Product Name","Division","Total_Sales","Total_Profit","Gross Margin (%)","Profit per Unit","Revenue Contribution (%)","Profit Contribution (%)","Margin Volatility"]]
        .style.format({"Total_Sales":"${:,.2f}","Total_Profit":"${:,.2f}","Gross Margin (%)":"{:.1f}%","Profit per Unit":"${:.4f}","Revenue Contribution (%)":"{:.1f}%","Profit Contribution (%)":"{:.1f}%","Margin Volatility":"{:.2f}"})
        .background_gradient(subset="Gross Margin (%)", cmap="RdYlGn"),
        use_container_width=True
    )

# ── Tab 2: Division Performance ───────────────────────────────────────────────
with tab2:
    st.subheader("Revenue vs Profit Comparison")
    ds = division_df.sort_values("Gross Margin (%)", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(8, 5))
        x = np.arange(len(ds)); w = 0.35
        ax.bar(x-w/2, ds["Total_Sales"],  w, label="Revenue",      color="#3498db", alpha=0.85)
        ax.bar(x+w/2, ds["Total_Profit"], w, label="Gross Profit", color="#2ecc71", alpha=0.85)
        ax.set_xticks(x); ax.set_xticklabels(ds["Division"], rotation=15)
        ax.set_ylabel("Amount ($)"); ax.set_title("Revenue vs Gross Profit")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.legend(); plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["#e74c3c" if m < overall_margin else "#3498db" for m in ds["Gross Margin (%)"]]
        ax.bar(ds["Division"], ds["Gross Margin (%)"], color=colors)
        ax.axhline(overall_margin, color="black", linestyle="--", linewidth=1.5, label=f"Overall {overall_margin:.1f}%")
        ax.set_title("Gross Margin % by Division"); ax.set_ylabel("Gross Margin (%)")
        ax.set_xticklabels(ds["Division"], rotation=15); ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()
    st.subheader("Margin Distribution by Division")
    if df["Division"].nunique() > 1:
        fig, ax = plt.subplots(figsize=(12, 4))
        div_order = df.groupby("Division")["Gross Margin (%)"].median().sort_values(ascending=False).index
        sns.boxplot(data=df, x="Division", y="Gross Margin (%)", order=div_order, palette="Set2", ax=ax,
                    flierprops=dict(marker="o", markersize=3, alpha=0.4))
        ax.axhline(overall_margin, color="red", linestyle="--", linewidth=1.5, label=f"Avg {overall_margin:.1f}%")
        ax.legend(); plt.tight_layout(); st.pyplot(fig); plt.close()
    else:
        st.info("Select multiple divisions to see the distribution.")
    st.dataframe(
        ds[["Division","Total_Sales","Total_Profit","Gross Margin (%)","Revenue Share (%)","Profit Share (%)"]]
        .style.format({"Total_Sales":"${:,.2f}","Total_Profit":"${:,.2f}","Gross Margin (%)":"{:.1f}%","Revenue Share (%)":"{:.1f}%","Profit Share (%)":"{:.1f}%"})
        .background_gradient(subset="Gross Margin (%)", cmap="RdYlGn"),
        use_container_width=True
    )

# ── Tab 3: Cost & Margin Diagnostics ─────────────────────────────────────────
with tab3:
    st.subheader("Cost-Sales Scatter Plots")
    dp = {d: c for d, c in zip(df["Division"].unique(), ["#3498db","#e74c3c","#2ecc71","#f39c12","#9b59b6"])}
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(df["Cost"], df["Sales"], c=df["Division"].map(dp), alpha=0.35, s=15, edgecolors="none")
        mv = max(df["Cost"].max(), df["Sales"].max())
        ax.plot([0, mv], [0, mv], "k--", linewidth=1, alpha=0.5, label="Break-even")
        for div, col in dp.items(): ax.scatter([], [], c=col, label=div, s=40)
        ax.set_xlabel("Cost ($)"); ax.set_ylabel("Sales ($)"); ax.set_title("Cost vs Sales")
        ax.legend(fontsize=7); plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(product_df["Cost Ratio (%)"], product_df["Total_Profit"],
                   c=[dp.get(d, "grey") for d in product_df["Division"]],
                   s=product_df["Total_Units"]/product_df["Total_Units"].max()*600+60,
                   alpha=0.8, edgecolors="grey", linewidth=0.5)
        for _, row in product_df.iterrows():
            ax.annotate(row["Product Name"].split(" - ")[-1],
                        xy=(row["Cost Ratio (%)"], row["Total_Profit"]),
                        xytext=(3, 3), textcoords="offset points", fontsize=7)
        ax.set_xlabel("Cost Ratio (%)"); ax.set_ylabel("Total Gross Profit ($)"); ax.set_title("Cost Ratio vs Gross Profit")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        plt.tight_layout(); st.pyplot(fig); plt.close()
    st.subheader("Monthly Margin Volatility Trend")
    m = df.groupby(["Month","Division"]).agg(S=("Sales","sum"), P=("Gross Profit","sum")).reset_index()
    m["Margin"] = m["P"] / m["S"] * 100
    m["Month_DT"] = m["Month"].dt.to_timestamp()
    fig, ax = plt.subplots(figsize=(12, 4))
    for div in m["Division"].unique():
        sub = m[m["Division"]==div].sort_values("Month_DT")
        ax.plot(sub["Month_DT"], sub["Margin"], marker="o", markersize=3, label=div, linewidth=1.8)
    ax.axhline(overall_margin, color="black", linestyle="--", linewidth=1.2, label=f"Overall {overall_margin:.1f}%")
    ax.set_ylabel("Gross Margin (%)"); ax.legend(fontsize=8); plt.xticks(rotation=30)
    plt.tight_layout(); st.pyplot(fig); plt.close()
    st.subheader("Margin Risk Flags")
    risk = product_df[product_df["Gross Margin (%)"] < overall_margin-10].sort_values("Gross Margin (%)")
    if len(risk):
        st.dataframe(
            risk[["Product Name","Division","Total_Sales","Total_Profit","Gross Margin (%)","Cost Ratio (%)","Margin Volatility"]]
            .style.format({"Total_Sales":"${:,.2f}","Total_Profit":"${:,.2f}","Gross Margin (%)":"{:.1f}%","Cost Ratio (%)":"{:.1f}%","Margin Volatility":"{:.2f}"})
            .applymap(lambda _: "background-color:#ffe0e0"),
            use_container_width=True
        )
    else:
        st.success("No products below the low-margin threshold!")

# ── Tab 4: Pareto Concentration ───────────────────────────────────────────────
with tab4:
    st.subheader("Profit Concentration - Pareto Charts & Dependency Indicators")
    pareto = product_df.sort_values("Total_Profit", ascending=False).copy()
    pareto["Cum Profit (%)"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum() * 100
    t80  = (pareto["Cum Profit (%)"] <= 80).sum() + 1
    top5 = pareto.head(5)["Profit Contribution (%)"].sum()
    ca, cb, cc = st.columns(3)
    ca.metric("Products to 80% Profit", f"{t80} of {len(pareto)}")
    cb.metric("Top 5 Profit Share",     f"{top5:.1f}%")
    cc.metric("Portfolio Dependency",   "High" if top5 > 60 else ("Moderate" if top5 > 40 else "Low"))
    fig, ax1 = plt.subplots(figsize=(14, 5)); ax2 = ax1.twinx()
    cp = ["#3498db" if i < t80 else "#e74c3c" for i in range(len(pareto))]
    ax1.bar(range(len(pareto)), pareto["Total_Profit"], color=cp, alpha=0.8)
    ax2.plot(range(len(pareto)), pareto["Cum Profit (%)"], color="#e67e22", linewidth=2.5, marker="o", markersize=4, label="Cumulative Profit %")
    ax2.axhline(80, color="grey", linestyle="--", linewidth=1.2)
    ax2.axvline(t80-0.5, color="red", linestyle=":", linewidth=1.5)
    ax1.set_xticks(range(len(pareto)))
    ax1.set_xticklabels([n.split(" - ")[-1] for n in pareto["Product Name"]], rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Total Gross Profit ($)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.set_ylabel("Cumulative Profit (%)"); ax2.set_ylim(0, 110); ax2.legend(loc="center right")
    plt.title("Pareto Chart - Profit Concentration", fontweight="bold")
    plt.tight_layout(); st.pyplot(fig); plt.close()
    reg = df.groupby("Region").agg(S=("Sales","sum"), P=("Gross Profit","sum")).reset_index()
    reg["Margin"] = reg["P"] / reg["S"] * 100
    reg = reg.sort_values("P", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(reg["Region"], reg["P"], color=sns.color_palette("Blues_d", len(reg)))
        ax.set_title("Gross Profit by Region"); ax.set_ylabel("Gross Profit ($)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.tick_params(axis="x", rotation=20); plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(reg["Region"], reg["Margin"], color=sns.color_palette("Greens_d", len(reg)))
        ax.axhline(overall_margin, color="red", linestyle="--", linewidth=1.5, label=f"Avg {overall_margin:.1f}%")
        ax.set_title("Gross Margin % by Region"); ax.tick_params(axis="x", rotation=20); ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ── Tab 5: Findings ───────────────────────────────────────────────────────────
with tab5:
    st.subheader("Key Findings & Recommendations")
    st.markdown("### Overall Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Gross Margin (%)", f"{overall_margin:.1f}%")
    col2.metric("Total Revenue",    f"${total_sales:,.0f}")
    col3.metric("Total Profit",     f"${total_profit:,.0f}")
    st.markdown("### Product Findings")
    top_profit   = product_df.sort_values("Total_Profit", ascending=False).iloc[0]
    top_margin   = product_df.sort_values("Gross Margin (%)", ascending=False).iloc[0]
    worst_margin = product_df.sort_values("Gross Margin (%)").iloc[0]
    low_thresh   = overall_margin - 10
    risk_count   = len(product_df[product_df["Gross Margin (%)"] < low_thresh])
    st.markdown(f"""
| Finding | Value |
|---------|-------|
| Highest Profit Product | {top_profit["Product Name"]} (${top_profit["Total_Profit"]:,.2f}) |
| Highest Margin Product | {top_margin["Product Name"]} ({top_margin["Gross Margin (%)"]:.1f}%) |
| Lowest Margin Product  | {worst_margin["Product Name"]} ({worst_margin["Gross Margin (%)"]:.1f}%) |
| Low-Margin Risk Count  | {risk_count} products flagged for review |
    """)
    st.markdown("### Division Findings")
    top_div   = division_df.sort_values("Gross Margin (%)", ascending=False).iloc[0]
    worst_div = division_df.sort_values("Gross Margin (%)").iloc[0]
    st.markdown(f"""
| Finding | Value |
|---------|-------|
| Best Margin Division | {top_div["Division"]} ({top_div["Gross Margin (%)"]:.1f}%) |
| Weakest Division     | {worst_div["Division"]} ({worst_div["Gross Margin (%)"]:.1f}%) |
    """)
    st.markdown("### Pareto Findings")
    pareto_f = product_df.sort_values("Total_Profit", ascending=False).copy()
    pareto_f["Cum Profit (%)"] = pareto_f["Total_Profit"].cumsum() / pareto_f["Total_Profit"].sum() * 100
    t80_f  = (pareto_f["Cum Profit (%)"] <= 80).sum() + 1
    top5_f = pareto_f.head(5)["Profit Contribution (%)"].sum()
    dep = "HIGH concentration risk" if top5_f > 60 else ("MODERATE concentration" if top5_f > 40 else "Healthy diversification")
    st.markdown(f"""
| Finding | Value |
|---------|-------|
| Products driving 80% profit | {t80_f} of {len(pareto_f)} ({t80_f/len(pareto_f)*100:.0f}% of portfolio) |
| Top 5 profit share          | {top5_f:.1f}% |
| Portfolio dependency        | {dep} |
    """)
    st.markdown("### Margin Volatility Note")
    vol_avg = product_df["Margin Volatility"].mean()
    if vol_avg == 0:
        st.warning(f"All products show 0% margin volatility — prices and costs are fixed with no month-to-month variation. Set the Margin Threshold slider to ~{overall_margin:.0f}% for meaningful product comparison.")
    else:
        st.info(f"Average margin volatility across products: {vol_avg:.2f}%")
    st.markdown("### Strategic Recommendations")
    st.success(f"""
1. PROMOTE high-margin products via targeted marketing
2. INVESTIGATE low-margin products: reprice or renegotiate COGS
3. AUDIT cost structure of {worst_div["Division"]} — margin lags overall average
4. PROTECT top {t80_f} profit-driving products from supply disruptions
5. SET margin threshold to ~{overall_margin:.0f}% in dashboard for meaningful flags
6. REVIEW products below {low_thresh:.1f}% margin for discontinuation
7. DIVERSIFY portfolio — reduce dependency on top 5 products
    """)

st.divider()
st.caption("Nassau Candy Distributor - Profitability Dashboard | Streamlit Community Cloud")
