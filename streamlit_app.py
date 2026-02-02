"""
Greenwashing Litigation Dashboard

A Streamlit dashboard with two main sections:
1. Market Overview - Analytics and trends across all greenwashing litigation
2. Case Explorer - Browse and search individual cases

Features:
- Market statistics and trends
- Interactive charts and filters
- Case search and detailed views
- Settlement analysis

Usage:
    pip install streamlit pandas plotly
    streamlit run greenwashing_dashboard.py

Author: AI Agent
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CSV = "140_greenwashing_cases.csv"

st.set_page_config(
    page_title="Greenwashing Litigation Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Big metric cards */
    .big-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .big-metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .big-metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Colored metric cards */
    .metric-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .metric-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .metric-blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .metric-yellow {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    
    /* Case card */
    .case-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    
    .case-card:hover {
        transform: translateX(5px);
    }
    
    /* Status badges */
    .status-settled { background-color: #28a745; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500; }
    .status-pending { background-color: #ffc107; color: black; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500; }
    .status-dismissed { background-color: #dc3545; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500; }
    .status-other { background-color: #6c757d; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500; }
    
    /* Quote box */
    .quote-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        font-style: italic;
        margin: 1rem 0;
    }
    
    /* Detail section */
    .detail-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .detail-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E3A5F;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    /* Section divider */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A5F;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Chart container */
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    /* Navigation tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: #f0f2f6;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Load and preprocess the CSV data."""
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    
    # Fill NaN with empty strings for text columns
    text_cols = ['case_name', 'quote', 'claim_type', 'sub_category', 'jurisdiction', 
                 'current_status', 'summary', 'ruling_description', 'sources',
                 'plaintiff_law_firm', 'court', 'docket_number', 'settlement_amount',
                 'channel', 'industry_sector', 'state_law_cited', 'relief_sought',
                 'Product/Company', 'Environmental Claims/Allegations']
    
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
    
    # Create display name
    df['display_name'] = df.apply(
        lambda x: x['case_name'] if x['case_name'] and x['case_name'] != '' else x['Product/Company'],
        axis=1
    )
    
    # Parse settlement amounts to numeric
    df['settlement_numeric'] = df['settlement_amount'].apply(parse_settlement_amount)
    
    # Normalize status for grouping
    df['status_group'] = df['current_status'].apply(normalize_status)
    
    return df


def parse_settlement_amount(amount_str: str) -> float:
    """Parse settlement amount string to numeric value."""
    if not amount_str or amount_str == '' or amount_str == 'nan':
        return 0
    
    amount_str = str(amount_str).lower().replace(',', '').replace('$', '')
    
    # Handle "X million" or "X billion"
    if 'billion' in amount_str:
        match = re.search(r'([\d.]+)', amount_str)
        if match:
            return float(match.group(1)) * 1_000_000_000
    elif 'million' in amount_str:
        match = re.search(r'([\d.]+)', amount_str)
        if match:
            return float(match.group(1)) * 1_000_000
    else:
        # Try to extract number directly
        match = re.search(r'([\d.]+)', amount_str)
        if match:
            return float(match.group(1))
    
    return 0


def normalize_status(status: str) -> str:
    """Normalize status for grouping."""
    status_lower = str(status).lower()
    if 'settled' in status_lower:
        return 'Settled'
    elif 'pending' in status_lower:
        return 'Pending'
    elif 'dismissed' in status_lower and 'without' in status_lower:
        return 'Dismissed (without prejudice)'
    elif 'dismissed' in status_lower:
        return 'Dismissed'
    elif 'voluntarily' in status_lower:
        return 'Voluntarily Dismissed'
    elif 'motion' in status_lower and 'denied' in status_lower:
        return 'MTD Denied'
    elif 'motion' in status_lower and 'granted' in status_lower:
        return 'MTD Granted'
    elif 'appeal' in status_lower:
        return 'On Appeal'
    elif 'class' in status_lower and 'certified' in status_lower:
        return 'Class Certified'
    elif status_lower == '' or status_lower == 'nan' or 'unknown' in status_lower:
        return 'Unknown'
    else:
        return 'Other'


def get_status_badge(status: str) -> str:
    """Return HTML for status badge."""
    status_lower = str(status).lower()
    if 'settled' in status_lower:
        return f'<span class="status-settled">💰 {status}</span>'
    elif 'pending' in status_lower:
        return f'<span class="status-pending">⏳ {status}</span>'
    elif 'dismissed' in status_lower:
        return f'<span class="status-dismissed">❌ {status}</span>'
    else:
        return f'<span class="status-other">📋 {status}</span>'


def highlight_keywords(text: str, keywords: str) -> str:
    """Highlight keywords in text."""
    if not keywords or not text:
        return text
    for word in keywords.split():
        if len(word) > 2:
            pattern = re.compile(f'({re.escape(word)})', re.IGNORECASE)
            text = pattern.sub(r'<mark style="background-color: #ffeb3b; padding: 0 2px;">\1</mark>', text)
    return text


# ============================================================================
# MARKET OVERVIEW DASHBOARD
# ============================================================================

def render_market_overview(df: pd.DataFrame):
    """Render the market overview dashboard."""
    
    st.markdown('<p class="section-header">📊 Market Overview</p>', unsafe_allow_html=True)
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'''
        <div class="big-metric">
            <div class="big-metric-value">{len(df)}</div>
            <div class="big-metric-label">Total Cases</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        settled = len(df[df['status_group'] == 'Settled'])
        st.markdown(f'''
        <div class="big-metric metric-green">
            <div class="big-metric-value">{settled}</div>
            <div class="big-metric-label">Settled</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        pending = len(df[df['status_group'] == 'Pending'])
        st.markdown(f'''
        <div class="big-metric metric-yellow">
            <div class="big-metric-value">{pending}</div>
            <div class="big-metric-label">Pending</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        dismissed = len(df[df['status_group'].str.contains('Dismissed', na=False)])
        st.markdown(f'''
        <div class="big-metric metric-orange">
            <div class="big-metric-value">{dismissed}</div>
            <div class="big-metric-label">Dismissed</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        total_settlements = df['settlement_numeric'].sum()
        if total_settlements >= 1_000_000_000:
            settlement_str = f"${total_settlements/1_000_000_000:.1f}B"
        elif total_settlements >= 1_000_000:
            settlement_str = f"${total_settlements/1_000_000:.1f}M"
        else:
            settlement_str = f"${total_settlements:,.0f}"
        st.markdown(f'''
        <div class="big-metric metric-blue">
            <div class="big-metric-value">{settlement_str}</div>
            <div class="big-metric-label">Total Settlements</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter row for market overview
    st.markdown("#### 🎛️ Filter Data")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        years = sorted([x for x in df['Year'].dropna().unique() if x])
        if years:
            year_range = st.slider(
                "Year Range",
                min_value=int(min(years)),
                max_value=int(max(years)),
                value=(int(min(years)), int(max(years))),
                key="market_year"
            )
        else:
            year_range = None
    
    with filter_col2:
        claim_types = ['All'] + sorted([x for x in df['claim_type'].unique() if x and x != ''])
        selected_claim = st.selectbox("Claim Type", claim_types, key="market_claim")
    
    with filter_col3:
        industries = ['All'] + sorted([x for x in df['industry_sector'].unique() if x and x != ''])
        selected_industry = st.selectbox("Industry Sector", industries, key="market_industry")
    
    # Apply filters
    filtered_df = df.copy()
    if year_range:
        filtered_df = filtered_df[(filtered_df['Year'] >= year_range[0]) & (filtered_df['Year'] <= year_range[1])]
    if selected_claim != 'All':
        filtered_df = filtered_df[filtered_df['claim_type'] == selected_claim]
    if selected_industry != 'All':
        filtered_df = filtered_df[filtered_df['industry_sector'] == selected_industry]
    
    st.markdown(f"*Showing {len(filtered_df)} cases based on filters*")
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Cases by Year")
        year_data = filtered_df.groupby('Year').size().reset_index(name='count')
        year_data = year_data.sort_values('Year')
        
        fig = px.bar(
            year_data, 
            x='Year', 
            y='count',
            color='count',
            color_continuous_scale='Viridis',
            labels={'count': 'Number of Cases', 'Year': 'Year'}
        )
        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🥧 Cases by Status")
        status_data = filtered_df['status_group'].value_counts().reset_index()
        status_data.columns = ['Status', 'Count']
        
        fig = px.pie(
            status_data, 
            values='Count', 
            names='Status',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📂 Cases by Claim Type")
        claim_data = filtered_df['claim_type'].value_counts().reset_index()
        claim_data.columns = ['Claim Type', 'Count']
        
        fig = px.bar(
            claim_data,
            x='Count',
            y='Claim Type',
            orientation='h',
            color='Count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🏭 Cases by Industry")
        industry_data = filtered_df['industry_sector'].value_counts().head(10).reset_index()
        industry_data.columns = ['Industry', 'Count']
        
        fig = px.bar(
            industry_data,
            x='Count',
            y='Industry',
            orientation='h',
            color='Count',
            color_continuous_scale='Greens'
        )
        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts Row 3
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏛️ Top Jurisdictions")
        jurisdiction_data = filtered_df['jurisdiction'].value_counts().head(8).reset_index()
        jurisdiction_data.columns = ['Jurisdiction', 'Count']
        
        fig = px.bar(
            jurisdiction_data,
            x='Count',
            y='Jurisdiction',
            orientation='h',
            color='Count',
            color_continuous_scale='Purples'
        )
        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Top Settlements")
        settlements_df = filtered_df[filtered_df['settlement_numeric'] > 0].nlargest(10, 'settlement_numeric')
        
        if len(settlements_df) > 0:
            settlements_df['settlement_display'] = settlements_df['settlement_numeric'].apply(
                lambda x: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x:,.0f}"
            )
            
            fig = px.bar(
                settlements_df,
                x='settlement_numeric',
                y='display_name',
                orientation='h',
                color='settlement_numeric',
                color_continuous_scale='Oranges',
                labels={'settlement_numeric': 'Settlement Amount', 'display_name': 'Case'}
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                coloraxis_showscale=False,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_tickformat='$,.0f'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No settlement data available for selected filters")
    
    # Trends analysis
    st.markdown("---")
    st.markdown("#### 📊 Trends Over Time")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Cases by year and claim type
        trend_data = filtered_df.groupby(['Year', 'claim_type']).size().reset_index(name='count')
        
        fig = px.line(
            trend_data,
            x='Year',
            y='count',
            color='claim_type',
            markers=True,
            labels={'count': 'Number of Cases', 'claim_type': 'Claim Type'}
        )
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title="Cases by Claim Type Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Settlements by year
        settlement_trend = filtered_df[filtered_df['settlement_numeric'] > 0].groupby('Year')['settlement_numeric'].sum().reset_index()
        
        fig = px.bar(
            settlement_trend,
            x='Year',
            y='settlement_numeric',
            labels={'settlement_numeric': 'Total Settlements ($)'},
            color='settlement_numeric',
            color_continuous_scale='Greens'
        )
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            title="Settlement Amounts by Year",
            coloraxis_showscale=False,
            yaxis_tickformat='$,.0f'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics table
    st.markdown("---")
    st.markdown("#### 📋 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**By Claim Type**")
        claim_summary = filtered_df.groupby('claim_type').agg({
            'display_name': 'count',
            'settlement_numeric': 'sum'
        }).reset_index()
        claim_summary.columns = ['Claim Type', 'Cases', 'Total Settlements']
        claim_summary['Total Settlements'] = claim_summary['Total Settlements'].apply(
            lambda x: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x:,.0f}" if x > 0 else "-"
        )
        st.dataframe(claim_summary, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("**By Status**")
        status_summary = filtered_df['status_group'].value_counts().reset_index()
        status_summary.columns = ['Status', 'Count']
        status_summary['Percentage'] = (status_summary['Count'] / status_summary['Count'].sum() * 100).round(1).astype(str) + '%'
        st.dataframe(status_summary, hide_index=True, use_container_width=True)
    
    with col3:
        st.markdown("**By Channel**")
        channel_summary = filtered_df['channel'].value_counts().reset_index()
        channel_summary.columns = ['Channel', 'Count']
        st.dataframe(channel_summary, hide_index=True, use_container_width=True)


# ============================================================================
# CASE EXPLORER DASHBOARD
# ============================================================================

def render_case_explorer(df: pd.DataFrame):
    """Render the case explorer dashboard."""
    
    st.markdown('<p class="section-header">🔍 Case Explorer</p>', unsafe_allow_html=True)
    
    # Sidebar-style filters in columns
    st.markdown("#### 🎛️ Search & Filter")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        keyword = st.text_input(
            "🔎 Search in quotes",
            placeholder="e.g., recyclable, sustainable",
            key="case_keyword"
        )
    
    with col2:
        claim_types = ['All'] + sorted([x for x in df['claim_type'].unique() if x and x != ''])
        selected_claim = st.selectbox("📁 Claim Type", claim_types, key="case_claim")
    
    with col3:
        if selected_claim != 'All':
            sub_cats = df[df['claim_type'] == selected_claim]['sub_category'].unique()
            sub_categories = ['All'] + sorted([x for x in sub_cats if x and x != ''])
        else:
            sub_categories = ['All'] + sorted([x for x in df['sub_category'].unique() if x and x != ''])
        selected_sub = st.selectbox("📂 Sub-Category", sub_categories, key="case_sub")
    
    with col4:
        statuses = ['All'] + sorted([x for x in df['status_group'].unique() if x and x != ''])
        selected_status = st.selectbox("📊 Status", statuses, key="case_status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        jurisdictions = ['All'] + sorted([x for x in df['jurisdiction'].unique() if x and x != ''])
        selected_jurisdiction = st.selectbox("🏛️ Jurisdiction", jurisdictions, key="case_jurisdiction")
    
    with col2:
        sort_options = ["Year (newest)", "Year (oldest)", "Case Name (A-Z)", "Settlement (highest)"]
        sort_by = st.selectbox("📋 Sort by", sort_options, key="case_sort")
    
    # Apply filters
    filtered_df = df.copy()
    
    if keyword:
        filtered_df = filtered_df[filtered_df['quote'].str.lower().str.contains(keyword.lower(), na=False)]
    if selected_claim != 'All':
        filtered_df = filtered_df[filtered_df['claim_type'] == selected_claim]
    if selected_sub != 'All':
        filtered_df = filtered_df[filtered_df['sub_category'] == selected_sub]
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['status_group'] == selected_status]
    if selected_jurisdiction != 'All':
        filtered_df = filtered_df[filtered_df['jurisdiction'] == selected_jurisdiction]
    
    # Sort
    if sort_by == "Year (newest)":
        filtered_df = filtered_df.sort_values('Year', ascending=False)
    elif sort_by == "Year (oldest)":
        filtered_df = filtered_df.sort_values('Year', ascending=True)
    elif sort_by == "Case Name (A-Z)":
        filtered_df = filtered_df.sort_values('display_name')
    elif sort_by == "Settlement (highest)":
        filtered_df = filtered_df.sort_values('settlement_numeric', ascending=False)
    
    st.markdown("---")
    st.markdown(f"**Found {len(filtered_df)} cases**")
    
    # Check if viewing detail
    if 'selected_case_idx' in st.session_state and st.session_state['selected_case_idx'] is not None:
        render_case_detail(df, st.session_state['selected_case_idx'], keyword)
    else:
        # Display case list
        for idx, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([5, 2, 1, 1])
                
                with col1:
                    case_name = row['display_name'] if row['display_name'] else f"Case #{idx}"
                    if st.button(f"📁 {case_name[:60]}{'...' if len(case_name) > 60 else ''}", key=f"btn_{idx}", use_container_width=True):
                        st.session_state['selected_case_idx'] = idx
                        st.rerun()
                
                with col2:
                    st.markdown(get_status_badge(row['current_status']), unsafe_allow_html=True)
                
                with col3:
                    year = row['Year'] if pd.notna(row['Year']) else 'N/A'
                    st.markdown(f"**{int(year) if isinstance(year, float) else year}**")
                
                with col4:
                    claim = row['claim_type'][:15] if row['claim_type'] else ''
                    st.markdown(f"*{claim}*")
                
                # Show quote preview if keyword search
                if keyword and row['quote']:
                    quote_preview = row['quote'][:150] + '...' if len(row['quote']) > 150 else row['quote']
                    highlighted = highlight_keywords(quote_preview, keyword)
                    st.markdown(f'<div class="quote-box">{highlighted}</div>', unsafe_allow_html=True)
                
                st.markdown("---")


def render_case_detail(df: pd.DataFrame, case_idx: int, keyword: str = ''):
    """Render detailed view of a single case."""
    
    row = df.loc[case_idx]
    
    # Back button
    if st.button("← Back to Case List", key="back_btn"):
        st.session_state['selected_case_idx'] = None
        st.rerun()
    
    # Header
    case_name = row['display_name'] if row['display_name'] else f"Case #{case_idx}"
    st.markdown(f"## 📁 {case_name}")
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"**Status**")
        st.markdown(get_status_badge(row['current_status']), unsafe_allow_html=True)
    
    with col2:
        year = row['Year'] if pd.notna(row['Year']) else 'N/A'
        st.metric("Year", int(year) if isinstance(year, float) else year)
    
    with col3:
        st.metric("Claim Type", row['claim_type'] or 'N/A')
    
    with col4:
        st.metric("Confidence", row['confidence'] or 'N/A')
    
    with col5:
        settlement = row['settlement_amount'] if row['settlement_amount'] and row['settlement_amount'] != '' else 'N/A'
        st.metric("Settlement", settlement)
    
    st.markdown("---")
    
    # Tabs for detailed info
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "⚖️ Legal Details", "📝 Ruling & Summary", "🔗 Sources"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏢 Parties")
            st.markdown(f"**Product/Company:** {row['Product/Company']}")
            st.markdown(f"**Defendant Type:** {row['defendant_type']}")
            st.markdown(f"**Plaintiff Law Firm:** {row['plaintiff_law_firm']}")
            st.markdown(f"**Industry Sector:** {row['industry_sector']}")
        
        with col2:
            st.markdown("##### 📁 Classification")
            st.markdown(f"**Claim Type:** {row['claim_type']}")
            st.markdown(f"**Sub-Category:** {row['sub_category']}")
            st.markdown(f"**Channel:** {row['channel']}")
            st.markdown(f"**Claim Location:** {row['claim_location']}")
        
        if row['quote']:
            st.markdown("##### 💬 Misleading Quote")
            quote_text = highlight_keywords(row['quote'], keyword) if keyword else row['quote']
            st.markdown(f'<div class="quote-box">"{quote_text}"</div>', unsafe_allow_html=True)
        
        if row['Environmental Claims/Allegations']:
            st.markdown("##### 🌿 Environmental Claims/Allegations")
            st.info(row['Environmental Claims/Allegations'])
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏛️ Court Information")
            st.markdown(f"**Court:** {row['court']}")
            st.markdown(f"**Jurisdiction:** {row['jurisdiction']}")
            st.markdown(f"**Docket Number:** {row['docket_number']}")
        
        with col2:
            st.markdown("##### 📜 Legal Basis")
            st.markdown(f"**State Law Cited:** {row['state_law_cited']}")
            st.markdown(f"**Relief Sought:** {row['relief_sought']}")
            st.markdown(f"**Class Size:** {row['class_size']}")
            st.markdown(f"**Certification Misuse:** {row['certification_misuse']}")
        
        if row['key_dates']:
            st.markdown("##### 📅 Key Dates")
            st.info(row['key_dates'])
    
    with tab3:
        if row['summary']:
            st.markdown("##### 📝 Case Summary")
            st.markdown(row['summary'])
        
        if row['ruling_description']:
            st.markdown("##### ⚖️ Ruling Description")
            st.warning(row['ruling_description'])
        
        if row['ruling_pdf_url'] and row['ruling_pdf_url'] != '':
            st.markdown("##### 📄 Ruling Document")
            st.markdown(f"[📥 View Ruling PDF]({row['ruling_pdf_url']})")
        
        if row['Outcome']:
            st.markdown("##### 🎯 Outcome")
            st.success(row['Outcome'])
    
    with tab4:
        if row['Product/Company URL']:
            st.markdown("##### 📎 Complaint Source")
            st.markdown(f"[🔗 View Original Complaint]({row['Product/Company URL']})")
        
        if row['sources']:
            st.markdown("##### 🔍 Research Sources")
            sources = row['sources'].split(' | ')
            for i, source in enumerate(sources, 1):
                if source.startswith('http'):
                    domain = source.split('/')[2] if len(source.split('/')) > 2 else source
                    st.markdown(f"{i}. [{domain}]({source})")
        
        st.markdown("##### ✅ Verification")
        verified = row['verified_independently']
        if verified == True or str(verified).upper() == 'TRUE':
            st.success("✅ **Independently Verified** - Information confirmed from multiple sources")
        else:
            st.warning("⚠️ **Not Independently Verified** - Based on limited sources")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application."""
    
    # Initialize session state
    if 'selected_case_idx' not in st.session_state:
        st.session_state['selected_case_idx'] = None
    
    # Header
    st.markdown('<h1 class="main-header">⚖️ Greenwashing Litigation Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive analysis of greenwashing lawsuits and market trends</p>', unsafe_allow_html=True)
    
    # Load data
    try:
        if Path(DEFAULT_CSV).exists():
            df = load_data(DEFAULT_CSV)
        else:
            st.error(f"Could not find {DEFAULT_CSV}. Please ensure the file is in the same directory.")
            st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    # Main navigation tabs
    tab1, tab2 = st.tabs(["📊 Market Overview", "🔍 Case Explorer"])
    
    with tab1:
        render_market_overview(df)
    
    with tab2:
        render_case_explorer(df)


if __name__ == "__main__":
    main()
