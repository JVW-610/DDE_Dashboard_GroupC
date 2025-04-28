import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import altair as alt
import groq  # Groq client

# --- Load environment variables ---
load_dotenv("API_KEY.env")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in environment. Please set it in API_KEY.env without extra spaces or comments.")
    st.stop()
os.environ['GROQ_API_KEY'] = GROQ_API_KEY  # Provide to Groq client

# Page config must be the first Streamlit command
st.set_page_config(page_title="Denmark Companies Dashboard", layout="wide")

st.markdown(
    """
    <style>
    button[data-baseweb="tab"] {
        font-size: 20px !important;
        padding: 10px 20px !important;
    }
    body {
        background-color: #f5f5f5;
    }
    .stApp {
        background-color: #f5f5f5;
    }
    </style>

    <div style='text-align: center; margin-top: 20px;'>
        <h1>Denmark Companies Dashboard</h1>
        <p style='font-size:18px;'>Explore sector distributions, company growth, and performance metrics.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"] > div:first-child {
                background:white;
                border-radius:20px;
                box-shadow:0 4px 8px rgba(0,0,0,0.05);
                margin-bottom:3px;
                padding:20px;
                display:flex;                 /*  flex‑box  */
                flex-direction:column;        /*  stack children  */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

# Define a muted color scale manually
muted_colors = [
    "#D3D7DD",  # very light gray-blue
    "#5A6272",  # dark gray-blue
    "#A6783D",  # muted brown-gold
    "#A0ABB8",  # light gray-blue
    "#7D8A9C",  # medium gray-blue
    "#6A8E61",  # muted green (optional highlight)
]

# Load data
@st.cache_data
def load_data():
    return pd.read_excel('V5_denmark_companies_with_merged_topics.xlsx')

DF = load_data()

# Calculate Company Age for ALL companies
date_col = next((c for c in DF.columns if "date of incorporation" in c.lower()), None)

if date_col and date_col in DF.columns:
    today = pd.to_datetime("today")
    DF['Company Age'] = (today - pd.to_datetime(DF[date_col])).dt.days // 365
    age_col = 'Company Age'
else:
    age_col = None

# Your tabs
tabs = st.tabs(["Company description", "Sectors", "Regions", "Regions deep-dive", "Age"])

# Identify key columns
tab_company_col = "Company name Latin alphabet"
desc_cols = [col for col in DF.columns if "description" in col.lower()]
description_col = desc_cols[0] if desc_cols else None
topic_col = "Topic - Umbrella (Merged)"
bvd_cols = [col for col in DF.columns if "bvd" in col.lower() and "sector" in col.lower()]
bvd_sector_col = bvd_cols[0] if bvd_cols else None
emp_col = next((c for c in DF.columns if "employee" in c.lower() and "2023" in c), None)
growth_col = next((c for c in DF.columns if "growth" in c.lower() and "2023" in c), None)
aagr_col = next((c for c in DF.columns if "aagr" in c.lower() and "2023" in c), None)

# Tab 1: Company description, topics, and metrics
with tabs[0]:
    st.header("Company Analysis")
    with st.container():
        company = st.selectbox(
        "Select a Company",
        sorted(DF[tab_company_col].dropna().unique())
    )
    if description_col and description_col in DF.columns:
        st.write(DF.loc[DF[tab_company_col] == company, description_col].iloc[0])
    else:
        st.write("No description available.")

    # Date of Incorporation and Company Age side by side
    date_col = next((c for c in DF.columns if "date of incorporation" in c.lower()), None)
    if date_col and date_col in DF.columns:
        doj = pd.to_datetime(DF.loc[DF[tab_company_col] == company, date_col].iloc[0])
        today = pd.to_datetime("today")
        age_years = (today - doj).days // 365
        cd, ca = st.columns(2)
        with cd:
            st.subheader("Sectors")
            if topic_col in DF.columns:
                st.write(DF.loc[DF[tab_company_col] == company, topic_col].iloc[0])
            else:                
                st.write("No topics available.")
        with ca:
            st.subheader("Date of Incorporation")
            st.markdown(f"<h6 style='margin:0; font-weight:normal'>{doj.date()}</h6>", unsafe_allow_html=True)
    else:
        st.write("No date of incorporation available.")
        st.subheader("Key Metrics (2023)")    
    # Extract values
    emp_val = DF.loc[DF[tab_company_col] == company, emp_col].iloc[0] if emp_col in DF.columns else None
    growth_val = DF.loc[DF[tab_company_col] == company, growth_col].iloc[0] if growth_col in DF.columns else None
    aagr_val = DF.loc[DF[tab_company_col] == company, aagr_col].iloc[0] if aagr_col in DF.columns else None
    # Compute overall stats and percentiles
    stats = {}
    if emp_col in DF.columns:
        stats['emp_avg'] = DF[emp_col].mean()
        stats['emp_med'] = DF[emp_col].median()
        stats['emp_pct'] = DF[emp_col].rank(pct=True).loc[DF[tab_company_col] == company].iloc[0] * 100

    if growth_col in DF.columns: 
        stats['growth_avg'] = DF[growth_col].mean()
        stats['growth_med'] = DF[growth_col].median()
        stats['growth_pct'] = DF[growth_col].rank(pct=True).loc[DF[tab_company_col] == company].iloc[0] * 100

    if aagr_col in DF.columns:
        stats['aagr_avg'] = DF[aagr_col].mean()
        stats['aagr_med'] = DF[aagr_col].median()
        stats['aagr_pct'] = DF[aagr_col].rank(pct=True).loc[DF[tab_company_col] == company].iloc[0] * 100

    # Calculate Age Statistics
    if 'Company Age' in DF.columns:
        stats['age_avg'] = DF['Company Age'].mean()
        stats['age_med'] = DF['Company Age'].median()
        stats['age_pct'] = DF['Company Age'].rank(pct=True).loc[DF[tab_company_col] == company].iloc[0] * 100
    
    with st.container():
        st.subheader(f"Peer Analysis: *{company}* vs Sector Peers")

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.subheader("Employees")
        st.markdown(f"**Employees at Company in 2023:** {emp_val}")
        st.markdown(f"**Sector Average:** {stats['emp_avg']:.1f}")  
        st.markdown(f"**Sector Median:** {stats['emp_med']:.1f}")
        st.markdown(f"**Percentile in Sector:** {stats['emp_pct']:.1f}th")

    with col2:
        st.subheader("Growth")
        st.markdown(f"**Company Growth in 2023:** {growth_val * 100:.2f}%")
        st.markdown(f"**Sector Average:** {stats['growth_avg']:.1f}%")
        st.markdown(f"**Sector Median:** {stats['growth_med']:.1f}%")
        st.markdown(f"**Percentile in Sector:** {stats['growth_pct']:.1f}th")

    with col3:
        st.subheader("AAGR")
        st.markdown(f"**AAGR in 2023:** {aagr_val * 100:.2f}%")
        st.markdown(f"**Sector Average:** {stats['aagr_avg']:.1f}%")
        st.markdown(f"**Sector Median::** {stats['aagr_med']:.1f}%")
        st.markdown(f"**Percentile in Sector:** {stats['aagr_pct']:.1f}th")

    with col4:
        st.subheader("Company Age")
        st.markdown(f"**Company Age:** {age_years} years")
        st.markdown(f"**Sector Average Age:** {stats['age_avg']:.1f} years")
        st.markdown(f"**Sector Median Age:** {stats['age_med']:.1f} years")
        st.markdown(f"**Percentile in Sector:** {stats['age_pct']:.1f}th")

    # Add traffic light indicators
    with st.container():
        st.subheader("Traffic Light Performance Indicators")

    perf1, perf2, perf3, perf4 = st.columns(4)

    def traffic_light(percentile, reverse=False):
        if not reverse:
            # Standard logic: higher percentile = better
            if percentile < 40:
                return "#C0392B"
            elif percentile <= 70:
                return "#F1C40F"
            else:
                return "#1E8449"    
        else:
            # Reversed logic: lower percentile (younger) = better
            if percentile < 40:
                return "#1E8449"
            elif percentile <= 70:
                return "#F1C40F"
            else:
                return "#C0392B"

    with perf1:
        color = traffic_light(stats['emp_pct'])
        st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center;'>
                <div style='background-color:{color}; width:70px; height:70px; border-radius:50%; margin:10px;'></div>
                <p style='text-align:center; margin:0;'>Employees</p>
            </div>
        """, unsafe_allow_html=True)

    with perf2:
        color = traffic_light(stats['growth_pct'])
        st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center;'>
                <div style='background-color:{color}; width:70px; height:70px; border-radius:50%; margin:10px;'></div>
                <p style='text-align:center; margin:0;'>Growth</p>
            </div>
        """, unsafe_allow_html=True)

    with perf3:
        color = traffic_light(stats['aagr_pct'])
        st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center;'>
                <div style='background-color:{color}; width:70px; height:70px; border-radius:50%; margin:10px;'></div>
                <p style='text-align:center; margin:0;'>AAGR</p>
            </div>
        """, unsafe_allow_html=True)

    with perf4:
        # Reverse traffic light logic for Company Age (younger is green)
        color = traffic_light(stats['age_pct'], reverse=True)
        st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center;'>
                <div style='background-color:{color}; width:70px; height:70px; border-radius:50%; margin:10px;'></div>
                <p style='text-align:center; margin:0;'>Company Age</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Automated Insight for Company
    st.markdown("---")
    with st.container():
        st.subheader("AI-generated Insights on Individual Company Performance")
        if st.button("Generate Company Insights"):
            with st.spinner("Generating company insights..."):
                # Prepare company stats payload
                comp_stats = {
                    'Employees': emp_val,
                    'Sector Average Employees': stats['emp_avg'],
                    'Employees Percentile': stats['emp_pct'],
                    'Growth Rate (%)': growth_val * 100 if growth_val is not None else None,
                    'Sector Avg Growth (%)': stats['growth_avg'] * 100 if 'growth_avg' in stats else None,
                    'Growth Percentile': stats['growth_pct'] if 'growth_pct' in stats else None,
                    'AAGR (%)': aagr_val * 100 if aagr_val is not None else None,
                    'Sector Avg AAGR (%)': stats['aagr_avg'] * 100 if 'aagr_avg' in stats else None,
                    'AAGR Percentile': stats['aagr_pct'] if 'aagr_pct' in stats else None,
                    'Company Age (years)': age_years,
                    'Sector Avg Age': stats['age_avg'],
                    'Age Percentile': stats['age_pct']
                }
                prompt1 = (
                    f"You are an expert business analyst. Provide a concise summary of {company}'s performance in 2023 compared to its sector peers. "
                    f"Here are the metrics: {comp_stats}."
                )
                client1 = groq.Groq(api_key=GROQ_API_KEY)
                response1 = client1.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt1}],
                    temperature=0.5,
                    max_tokens=600
                )
                company_insight = response1.choices[0].message.content.strip()
                st.markdown(company_insight)

    st.markdown("""
        <div style='text-align: center; margin-top: 20px;'>
            <h4>Legend</h4>
            <p style='font-size:16px; margin:4px;'>
                <span style='color:#1E8449; font-weight:bold;'>Green</span> (>70th percentile) — Excellent performance<br>
                <span style='color:#F1C40F; font-weight:bold;'>Yellow</span> (40th–70th percentile) — Average performance<br>
                <span style='color:#C0392B; font-weight:bold;'>Red</span> (<40th percentile) — Below average performance<br>
                <em>Note: Reverse logic applies for Company Age—lower percentiles (younger companies) are considered better.</em>
            </p>
        </div>
        """, unsafe_allow_html=True)


# --- Tab 2: Sectors with LLM summary ---
with tabs[1]:
    st.header("Sectors")

    # Prepare data sources for charts
    if bvd_sector_col and bvd_sector_col in DF.columns:
        bvd_df = DF[bvd_sector_col].value_counts().sort_values(ascending=False).reset_index()
        bvd_df.columns = [bvd_sector_col, 'count']
    else:
        bvd_df = pd.DataFrame(columns=[bvd_sector_col, 'count'])

    if topic_col in DF.columns:
        topic_df = DF[topic_col].value_counts().sort_values(ascending=False).reset_index()
        topic_df.columns = [topic_col, 'count']
    else:
        topic_df = pd.DataFrame(columns=[topic_col, 'count'])

    # Chart layout
    c1, c2 = st.columns(2)
    with c1:
        with st.container():
            st.subheader("Sector Distribution")
            chart1 = alt.Chart(bvd_df).mark_bar(color='#5A6272').encode(
                x=alt.X('count:Q', title='No. of Companies'),
                y=alt.Y(f"{bvd_sector_col}:N", title="Sector", sort='-x')
            ).properties(height=400)
            st.altair_chart(chart1, use_container_width=True)
    with c2:
        with st.container():
            st.subheader("Average Growth Rate by Sector")
            if growth_col and bvd_sector_col in DF.columns:
                avg_growth = DF.groupby(bvd_sector_col)[growth_col].mean().reset_index()
                avg_growth.columns = [bvd_sector_col, 'avg']
                cg = alt.Chart(avg_growth).mark_bar(color='#A6783D').encode(
                    x=alt.X('avg:Q', title='Avg. growth rate', axis=alt.Axis(format='.2%')),
                    y=alt.Y(f"{bvd_sector_col}:N", title="Sector", sort='-x')
                ).properties(height=400)
                st.altair_chart(cg, use_container_width=True)
            else:
                st.write("No growth data available.")

    c3, c4 = st.columns(2)
    with c3:
        with st.container():
            st.subheader("Topic Distribution")
            chart2 = alt.Chart(topic_df).mark_bar(color='#7D8A9C').encode(
                x=alt.X('count:Q', title='No. of Companies'),
                y=alt.Y(f"{topic_col}:N", title="Topic", sort='-x')
            ).properties(height=400)
            st.altair_chart(chart2, use_container_width=True)
    with c4:
        with st.container():
            st.subheader("Average Company Size by Sector")
            if emp_col and bvd_sector_col in DF.columns:
                avg_emp = DF.groupby(bvd_sector_col)[emp_col].mean().reset_index()
                avg_emp.columns = [bvd_sector_col, 'avg']
                avg_emp['avg'] = avg_emp['avg'].round(2)
                ce = alt.Chart(avg_emp).mark_bar(color='#6A8E61').encode(
                    x=alt.X('avg:Q', title='Avg. no. of Employees'),
                    y=alt.Y(f"{bvd_sector_col}:N", title="Sector", sort='-x')
                ).properties(height=400)
                st.altair_chart(ce, use_container_width=True)
            else:
                st.write("No employee data available.")

    # Automated Insight via Groq
    st.markdown("---")
    with st.container():
        st.subheader("AI-generated Insights on Sector Graphs")
        if st.button("Generate Sector Insights"):
            with st.spinner("Generating insights..."):
                # Construct LLM input
                payload = {
                    'top_sectors': bvd_df.head(5).to_dict(orient='records'),
                    'avg_growth': avg_growth.to_dict(orient='records') if 'avg_growth' in locals() else [],
                    'top_topics': topic_df.head(5).to_dict(orient='records'),
                    'avg_employees': avg_emp.to_dict(orient='records') if 'avg_emp' in locals() else []
                }
                prompt_content = (
                    "You are an expert data analyst. "
                    "Given these summaries of Danish companies, write a concise paragraph highlighting key trends and noteworthy observations.\n"
                    f"Top 5 sectors by company count: {payload['top_sectors']}\n"
                    f"Average growth rate by sector: {payload['avg_growth']}\n"
                    f"Top 5 topics by company count: {payload['top_topics']}\n"
                    f"Average employees by sector: {payload['avg_employees']}"
                )
                client = groq.Groq(api_key=GROQ_API_KEY)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt_content}],
                    temperature=0.5,
                    max_tokens=600
                )
                insight = response.choices[0].message.content.strip()
                st.markdown(insight)
    st.markdown("---")
    with st.container():
        st.subheader("Filter by Sector for Sector Metrics")
        if bvd_sector_col and bvd_sector_col in DF.columns:
            with st.container():
                sel = st.selectbox("Select a Sector", sorted(DF[bvd_sector_col].dropna().unique()))
            df_sel = DF[DF[bvd_sector_col] == sel]

            sec_cols = ['Employees', 'Growth Rate', 'AAGR']
            sec_keys = [emp_col, growth_col, aagr_col]
            s1, s2, s3 = st.columns(3)

            for mcol, label, key in zip([s1, s2, s3], sec_cols, sec_keys):
                with mcol:
                    st.subheader(f"**{label}**")
                    if key and key in df_sel:
                        series = df_sel[key].dropna()
                        avg = series.mean()
                        med = series.median()
                        p10 = series.quantile(0.1)
                        p90 = series.quantile(0.9)
                        suffix = '%' if 'growth' in key.lower() or 'aagr' in key.lower() else ''
                        st.markdown(f"**Sector Average:** {avg:.2f}{suffix}")
                        st.markdown(f"**Sector Median:** {med:.2f}{suffix}")
                        st.markdown(f"**10th percentile in Sector:** {p10:.2f}{suffix}")
                        st.markdown(f"**90th percentile in Sector:** {p90:.2f}{suffix}")
                    else:
                        st.write("N/A")

    # Automated Insight for Selected Sector
    st.markdown("---")
    with st.container():
        st.subheader("AI-generated Insights on different Sectors")
        if st.button("Generate Selected Sector Insights"):
            with st.spinner("Generating sector-specific insights..."):
                # Prepare selected sector stats
                sel_name = sel
                stats_series = {}
                for key, label in zip([emp_col, growth_col, aagr_col], ['Employees', 'Growth Rate', 'AAGR']):
                    if key and key in df_sel:
                        series = df_sel[key].dropna()
                        stats_series[label] = {
                            'average': series.mean(),
                            'median': series.median(),
                            '10th_percentile': series.quantile(0.1),
                            '90th_percentile': series.quantile(0.9)
                        }
                # Build prompt for sector insight
                prompt2 = (
                    f"You are an expert industry analyst. Provide a concise paragraph summarizing the performance of the '{sel_name}' sector in Denmark in 2023. "
                    "Include key metrics such as average, median, 10th and 90th percentiles for Employees, Growth Rate, and AAGR as provided below:"
                    f"{stats_series}"
                )
                client2 = groq.Groq(api_key=GROQ_API_KEY)
                response2 = client2.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt2}],
                    temperature=0.5,
                    max_tokens=600
                )
                sector_insight = response2.choices[0].message.content.strip()
                st.markdown(sector_insight)

# Tab 3: Regions
with tabs[2]:
    st.header("Regions")

    region_col = next((c for c in DF.columns if "region" in c.lower()), None)

    if region_col and region_col in DF.columns:
        # Create top two graphs
        r1, r2 = st.columns(2)

        with r1:
            with st.container():
                st.subheader("Number of Businesses per Region")
                region_count = DF[region_col].value_counts().reset_index()
                region_count.columns = [region_col, 'count']
                chart_r1 = alt.Chart(region_count).mark_bar(color='#5A6272').encode(
                    x=alt.X('count:Q', title='No. of Companies in Region'),
                    y=alt.Y(f'{region_col}:N', sort='-x')
                ).properties(height=600)
                st.altair_chart(chart_r1, use_container_width=True)

        with r2:
            with st.container():
                st.subheader("Average Growth Rate per Region")
                if growth_col:
                    avg_growth_region = DF.groupby(region_col)[growth_col].mean().reset_index()
                    avg_growth_region.columns = [region_col, 'avg_growth']
                    chart_r2 = alt.Chart(avg_growth_region).mark_bar(color='#A6783D').encode(
                       x=alt.X('avg_growth:Q',
                            title='Avg. Growth in Region',
                            axis=alt.Axis(format='.2%')),
                        y=alt.Y(f'{region_col}:N', sort='-x')
                    ).properties(height=600)
                    st.altair_chart(chart_r2, use_container_width=True)
                else:
                    st.write("No growth data available.")

        r3, r4 = st.columns(2)

        with r3:
            with st.container():
                st.subheader("Percentage of Businesses per Region")
                region_count = DF[region_col].value_counts().reset_index()
                region_count.columns = [region_col, 'count']
                total_companies = region_count['count'].sum()
                region_count['percentage'] = (region_count['count'] / total_companies) * 100

                chart_r3 = alt.Chart(region_count).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="percentage", type="quantitative"),
                    color=alt.Color(
                        f"{region_col}:N",
                        scale=alt.Scale(range=muted_colors),  
                        legend=alt.Legend(title="Region")
                    ),
                    tooltip=[
                        f"{region_col}:N",
                        alt.Tooltip("percentage:Q", format=".2f")
                    ]
                ).properties(width=600, height=600)

                st.altair_chart(chart_r3, use_container_width=True)


        with r4:
            with st.container():
                st.subheader("Percentage of Employees per Region")
                if emp_col:
                    emp_region = DF.groupby(region_col)[emp_col].sum().reset_index()
                    emp_region.columns = [region_col, 'total_employees']
                    total_employees = emp_region['total_employees'].sum()
                    emp_region['percentage'] = (emp_region['total_employees'] / total_employees) * 100

                    chart_r4 = alt.Chart(emp_region).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="percentage", type="quantitative"),
                        color=alt.Color(
                            f"{region_col}:N",
                            scale=alt.Scale(range=muted_colors),  
                            legend=alt.Legend(title="Region")
                        ),
                        tooltip=[
                            f"{region_col}:N",
                            alt.Tooltip("percentage:Q", format=".2f")
                        ]
                    ).properties(width=600, height=600)

                    st.altair_chart(chart_r4, use_container_width=True)
                else:
                    st.write("No employee data available.")

# Automated Insight for Regions Overview
    st.markdown("---")
    with st.container():
        st.subheader("AI-generated Insights on different Regions")
        if st.button("Generate Regions Insights"):
            with st.spinner("Generating regions overview insights..."):
                # Compute summary data
                # Count distinct regions and identify top region by company count
                total_regions = region_count[region_col].nunique()
                top_region = region_count.iloc[0][region_col] if not region_count.empty else None
                top_count = region_count.iloc[0]['count'] if not region_count.empty else None
                avg_growth_overall = DF[growth_col].mean() if growth_col in DF.columns else None
                # Build prompt for regions insight
                prompt3 = (
                    "You are a data analyst. Provide a brief summary of the Danish regions overview for 2023. "
                    f"There are {total_regions} regions. The region with the most companies is {top_region} ({top_count} companies). "
                    f"The overall average growth across regions is {avg_growth_overall:.2%}."
                )
                client3 = groq.Groq(api_key=GROQ_API_KEY)
                response3 = client3.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt3}],
                    temperature=0.5,
                    max_tokens=600
                )
                insight3 = response3.choices[0].message.content.strip()
                st.markdown(insight3)

# Tab 4: Sectors with charts and filters
with tabs[3]:
    st.header("Regions deep-dive")

    region_col = next((c for c in DF.columns if "region" in c.lower()), None)
    if region_col and region_col in DF.columns:

        with st.container():
            selected_region = st.selectbox("Select a Region", sorted(DF[region_col].dropna().unique()))

        df_region = DF[DF[region_col] == selected_region]

        b1, b2 = st.columns(2)

        with b1:
            with st.container():
                st.subheader(f"Businesses by Sector in {selected_region}")
                if bvd_sector_col:
                    sector_count = df_region[bvd_sector_col].value_counts().reset_index()
                    sector_count.columns = [bvd_sector_col, 'count']
                    total_companies = sector_count['count'].sum()
                    sector_count['percentage'] = (sector_count['count'] / total_companies) * 100

                    chart_b1 = alt.Chart(sector_count).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="percentage", type="quantitative"),
                        color=alt.Color(
                            f"{bvd_sector_col}:N",
                            scale=alt.Scale(range=muted_colors),  # << Here!
                            legend=alt.Legend(title="Sector")
                        ),
                        tooltip=[
                            alt.Tooltip(f"{bvd_sector_col}:N", title="Sector"),
                            alt.Tooltip('percentage:Q', title="Percentage", format=".2f")
                        ]
                    ).properties(width=600, height=600)

                    st.altair_chart(chart_b1, use_container_width=True)
                else:
                    st.write("No sector data available.")


        with b2:
            with st.container():
                st.subheader(f"Employees by Sector in {selected_region}")
                if emp_col and bvd_sector_col:
                    emp_sector = df_region.groupby(bvd_sector_col)[emp_col].sum().reset_index()
                    emp_sector.columns = [bvd_sector_col, 'total_employees']
                    total_employees = emp_sector['total_employees'].sum()
                    emp_sector['percentage'] = (emp_sector['total_employees'] / total_employees) * 100

                    chart_b2 = alt.Chart(emp_sector).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="percentage", type="quantitative"),
                        color=alt.Color(
                            f"{bvd_sector_col}:N",
                            scale=alt.Scale(range=muted_colors),  # << Here too!
                            legend=alt.Legend(title="Sector")
                        ),
                        tooltip=[
                            alt.Tooltip(f"{bvd_sector_col}:N", title="Sector"),
                            alt.Tooltip('percentage:Q', title="Percentage", format=".2f")
                        ]
                    ).properties(width=600, height=600)

                    st.altair_chart(chart_b2, use_container_width=True)
                else:
                    st.write("No employee data available.")
        
        b3, b4 = st.columns(2)

        with b3:
            with st.container():
                st.subheader(f"Growth Rates by Sector in {selected_region}")
                if growth_col and bvd_sector_col:
                    growth_sector = df_region.groupby(bvd_sector_col)[growth_col].mean().reset_index()
                    growth_sector.columns = [bvd_sector_col, 'avg_growth']
                    chart_b3 = alt.Chart(growth_sector).mark_bar(color='#A6783D').encode(
                        x=alt.X('avg_growth:Q', title=f'Average Growth Rate in Sector in {selected_region}', axis=alt.Axis(format='.2%')),
                        y=alt.Y(f'{bvd_sector_col}:N', title = "Sector", sort='-x')
                    ).properties(height=600)
                    st.altair_chart(chart_b3, use_container_width=True)
                else:
                    st.write("No growth data available.")

        with b4:
            with st.container():
                st.subheader(f"AAGR by Sector in {selected_region}")
                if 'aagr 2023' in df_region.columns and bvd_sector_col:
                    aagr_sector = df_region.groupby(bvd_sector_col)['aagr 2023'].mean().reset_index()
                    aagr_sector.columns = [bvd_sector_col, 'avg_aagr']
                    chart_b4 = alt.Chart(aagr_sector).mark_bar(color='#6A8E61').encode(
                        x=alt.X('avg_aagr:Q', title=f'Average AAGR in Sector in {selected_region}', axis=alt.Axis(format='.2%')),
                        y=alt.Y(f'{bvd_sector_col}:N', title="Sector", sort='-x')
                    ).properties(height=600)
                    st.altair_chart(chart_b4, use_container_width=True)
                else:
                    st.write("No AAGR data available.")

    else:
        st.write("No region data available.")

    # Automated Insight for Region Deep-Dive
    st.markdown("---")
    with st.container():
        st.subheader(f"AI-generated Insights for {selected_region}")
        if st.button(f"Generate Deep-Dive Insights for {selected_region}"):
            with st.spinner("Generating deep-dive insights..."):
                # Summarize region deep-dive metrics
                # Top sector by number of businesses
                top_sector = sector_count.iloc[0][bvd_sector_col] if not sector_count.empty else None
                top_sector_count = sector_count.iloc[0]['count'] if not sector_count.empty else None
                # Sector employing most employees
                top_emp_sector = emp_sector.sort_values('total_employees', ascending=False).iloc[0][bvd_sector_col] if not emp_sector.empty else None
                top_emp_count = emp_sector.sort_values('total_employees', ascending=False).iloc[0]['total_employees'] if not emp_sector.empty else None
                # Sector with highest average growth
                top_growth_sector = growth_sector.sort_values('avg_growth', ascending=False).iloc[0][bvd_sector_col] if not growth_sector.empty else None
                top_growth_rate = growth_sector.sort_values('avg_growth', ascending=False).iloc[0]['avg_growth'] if not growth_sector.empty else None
                # Sector with highest AAGR
                top_aagr_sector = aagr_sector.sort_values('avg_aagr', ascending=False).iloc[0][bvd_sector_col] if not 'aagr_sector' in locals() or not aagr_sector.empty else None
                top_aagr_rate = aagr_sector.sort_values('avg_aagr', ascending=False).iloc[0]['avg_aagr'] if not 'aagr_sector' in locals() or not aagr_sector.empty else None
                # Build prompt
                prompt4 = (
                    f"You are an expert data analyst. Provide a concise summary of the business landscape in {selected_region} based on the deep-dive analysis. "
                    f"The top sector by company count is {top_sector} ({top_sector_count} companies). "
                    f"The sector employing the most employees is {top_emp_sector} ({top_emp_count} employees). "
                    f"The sector with the highest average growth is {top_growth_sector} ({top_growth_rate:.2%}). "
                    f"The sector with the highest average AAGR is {top_aagr_sector} ({top_aagr_rate:.2%})."
                )
                client4 = groq.Groq(api_key=GROQ_API_KEY)
                response4 = client4.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt4}],
                    temperature=0.5,
                    max_tokens=600
                )
                deep_insight = response4.choices[0].message.content.strip()
                st.markdown(deep_insight)

# Tab 5: Company Age
with tabs[4]:
    st.header("Company Age")

    if age_col:
        b5, b6 = st.columns(2)

        with b5:
            with st.container():
                st.subheader("Average Company Age by Region")
                avg_age_region = DF.groupby(region_col)[age_col].mean().reset_index()
                avg_age_region.columns = [region_col, 'avg_age']

                chart_age_region = alt.Chart(avg_age_region).mark_bar(color='#3E5C76').encode(
                    x=alt.X('avg_age:Q', title='Average Age (years)'),
                    y=alt.Y(f'{region_col}:N', title='Region', sort='-x'),
                    tooltip=[
                        alt.Tooltip(f'{region_col}:N', title='Region'),
                        alt.Tooltip('avg_age:Q', title='Average Age', format='.2f')
                    ]
                ).properties(height=600)

                st.altair_chart(chart_age_region, use_container_width=True)

        with b6:
            with st.container():
                st.subheader("Average Company Age by Sector")
                avg_age_sector = DF.groupby(bvd_sector_col)[age_col].mean().reset_index()
                avg_age_sector.columns = [bvd_sector_col, 'avg_age']

                chart_age_sector = alt.Chart(avg_age_sector).mark_bar(color='#665D1E').encode(
                    x=alt.X('avg_age:Q', title='Average Age (years)'),
                    y=alt.Y(f'{bvd_sector_col}:N', title='Sector', sort='-x'),
                    tooltip=[
                        alt.Tooltip(f'{bvd_sector_col}:N', title='Sector'),
                        alt.Tooltip('avg_age:Q', title='Average Age', format='.2f')
                    ]
                ).properties(height=600)

                st.altair_chart(chart_age_sector, use_container_width=True)

    else:
        st.write("No age data available.")

    # Automated Insight for Company Age Overview
    st.markdown("---")
    with st.container():
        st.subheader("AI-generated Insights on Company Ages")
        if st.button("Generate Company Age Insights"):
            with st.spinner("Generating company age insights..."):
                # Summarize age metrics
                overall_avg_age = DF['Company Age'].mean() if 'Company Age' in DF else None
                min_age = DF['Company Age'].min() if 'Company Age' in DF else None
                max_age = DF['Company Age'].max() if 'Company Age' in DF else None
                # Build prompt
                prompt5 = (
                    "You are an experienced business analyst. Provide a brief summary of company age statistics in Denmark. "
                    f"In 2023, the average company age is {overall_avg_age:.1f} years, with the youngest company at {min_age} years and the oldest at {max_age} years."
                )
                client5 = groq.Groq(api_key=GROQ_API_KEY)
                response5 = client5.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt5}],
                    temperature=0.5,
                    max_tokens=600
                )
                age_insight = response5.choices[0].message.content.strip()
                st.markdown(age_insight)
