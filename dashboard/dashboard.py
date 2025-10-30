import os
import logging
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.express as px

# Setup logging
log = logging.getLogger(__name__)
if not log.handlers:
    logging.basicConfig(level=logging.INFO)

# --- Fallback DB loader ---
def _read_from_db_via_sqlalchemy(limit: int = 10000) -> pd.DataFrame:
    try:
        from sqlalchemy import create_engine, text
    except Exception as e:
        log.exception("SQLAlchemy not available: %s", e)
        return pd.DataFrame()

    db_url = os.getenv("DATABASE_URL")
    log.info(f"Using DATABASE_URL: {db_url}")
    if not db_url:
        log.warning("DATABASE_URL not set")
        return pd.DataFrame()

    try:
        engine = create_engine(db_url)
        sql = text("""
            SELECT id, subreddit, comment_clean, sentiment, confidence, created_utc, url
            FROM reddit_comments
            ORDER BY created_utc DESC
            LIMIT :limit
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"limit": limit})
            log.info(f"Loaded {len(df)} records from reddit_comments")
            return df
    except Exception as e:
        log.exception("DB query failed: %s", e)
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_data(limit: int = 10000) -> pd.DataFrame:
    try:
        return _read_from_db_via_sqlalchemy(limit=limit)
    except Exception as e:
        log.exception("Failed to load data: %s", e)
        return pd.DataFrame()

# --- Visual helpers ---
def _subreddit_bar(df: pd.DataFrame):
    counts = df["subreddit"].value_counts().reset_index()
    counts.columns = ["subreddit", "count"]
    return px.bar(counts, x="subreddit", y="count", title="Comments by Subreddit", color="count")

def _sentiment_pie(df: pd.DataFrame):
    pie = df["sentiment"].value_counts().reset_index()
    pie.columns = ["sentiment", "count"]
    return px.pie(pie, names="sentiment", values="count", title="Sentiment Distribution")

def _confidence_histogram(df: pd.DataFrame):
    return px.histogram(df, x="confidence", nbins=20, title="Confidence Distribution")

def _daily_trend(df: pd.DataFrame):
    df = df.copy()
    df["date"] = pd.to_datetime(df["created_utc"], errors="coerce").dt.date
    trend = df.groupby(["date", "sentiment"]).size().reset_index(name="count")
    return px.line(trend, x="date", y="count", color="sentiment", title="Daily Trend by Sentiment")

# --- Page layout ---
st.set_page_config(page_title="Reddit Sentiment Dashboard", layout="wide")
st.title("📈 Reddit Sentiment Dashboard")

df = get_data()
if df.empty:
    st.error(f"No data available. Check DATABASE_URL and table existence. Current URL: {os.getenv('DATABASE_URL')}")
    st.stop()

# Normalize columns
df.columns = df.columns.str.lower().str.strip()
col_map = {
    "pred_label": "sentiment",
    "pred_score": "confidence",
    "comment_clean": "comment",
    "body": "comment",
    "text": "comment",
    "selftext": "comment",
}
for src, dst in col_map.items():
    if src in df.columns and dst not in df.columns:
        df[dst] = df[src]

required_cols = ["subreddit", "sentiment", "confidence", "created_utc"]
for c in required_cols:
    if c not in df.columns:
        df[c] = None

df["created_utc"] = pd.to_datetime(df["created_utc"], errors="coerce")
if df["created_utc"].dt.tz is None:
    try:
        df["created_utc"] = df["created_utc"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    except Exception:
        df["created_utc"] = pd.to_datetime(df["created_utc"], errors="coerce")

# Sidebar filters
st.sidebar.header("Filters")
subreddits = sorted(df["subreddit"].dropna().unique().tolist())
selected_subreddit = st.sidebar.selectbox("Select Subreddit", ["All"] + subreddits)

filtered_df = df.copy()
if selected_subreddit != "All":
    filtered_df = filtered_df[filtered_df["subreddit"] == selected_subreddit]

sentiments = sorted(filtered_df["sentiment"].dropna().unique().tolist())
selected_sentiment = st.sidebar.multiselect("Select Sentiment", sentiments, default=sentiments or None)
if selected_sentiment:
    filtered_df = filtered_df[filtered_df["sentiment"].isin(selected_sentiment)]

if filtered_df.empty:
    st.info("No comments match the selected filters.")
    st.stop()

# Top metrics
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Comments", f"{len(df):,}")
col2.metric("Filtered Comments", f"{len(filtered_df):,}")
# Score table
st.subheader("Sentiment Score Table (Top 10 Rows)")
comment_col = next((c for c in ["comment", "comment_clean", "body", "text", "selftext"] if c in filtered_df.columns), None)
table_cols = ["subreddit", "sentiment", "confidence", "created_utc"] + ([comment_col] if comment_col else [])
table = filtered_df[table_cols].head(10).copy()
if comment_col:
    table = table.rename(columns={comment_col: "comment"})
    table["comment"] = table["comment"].astype(str).str.slice(0, 300)
st.dataframe(table, use_container_width=True)

# CSV export
csv = filtered_df.to_csv(index=False)
st.download_button("Download Filtered Data", csv, "filtered_data.csv", mime="text/csv")

# Plotting
def safe_plot(func, df_, title, color_override: Optional[str] = None):
    if df_.empty:
        st.warning(f"No data for {title}")
        return
    try:
        st.subheader(title)
        fig = func(df_)
        if color_override and hasattr(fig, "update_traces"):
            fig.update_traces(marker_color=color_override)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        log.exception("Plot failed %s: %s", title, e)
        st.warning(f"Failed to render {title}")

safe_plot(_subreddit_bar, filtered_df, "Comments by Subreddit", color_override="blue")
safe_plot(_sentiment_pie, filtered_df, "Sentiment Distribution")
safe_plot(_confidence_histogram, filtered_df, "Confidence Histogram")
safe_plot(_daily_trend, filtered_df, "Daily Trend by Sentiment")

st.markdown("Built with Streamlit. Data refreshed every 5 minutes.")