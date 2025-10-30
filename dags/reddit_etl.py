import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
import praw

# ──────────────────────────────────────────────
# Add DAG folder to Python path
# ──────────────────────────────────────────────
sys.path.append(os.path.dirname(__file__))

from db_utils import upsert_comments  # lightweight import

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
log = logging.getLogger("reddit_sentiment_etl")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

# ──────────────────────────────────────────────
# Defaults & Constants
# ──────────────────────────────────────────────
DEFAULT_SUBREDDITS = [
    "India", "AskIndia", "IndiaSpeaks", "IndianSocial",
    "TamilNadu", "Karnataka", "Maharashtra", "WestBengal", "Kerala",
    "Telangana", "Gujarat", "Rajasthan", "Punjab", "Bihar", "Odisha",
    "UttarPradesh", "MadhyaPradesh", "Haryana", "Jharkhand", "Assam",
    "Chhattisgarh", "AndhraPradesh", "HimachalPradesh", "Uttarakhand",
    "Goa", "Tripura", "Meghalaya", "Manipur", "Nagaland", "ArunachalPradesh",
    "Mizoram", "Sikkim", "AndamanAndNicobar", "Puducherry"
]

STATE_NAMES = [
    "Tamil Nadu", "Karnataka", "Maharashtra", "West Bengal", "Kerala",
    "Telangana", "Gujarat", "Rajasthan", "Punjab", "Bihar", "Odisha",
    "Uttar Pradesh", "Madhya Pradesh", "Haryana", "Jharkhand", "Assam",
    "Chhattisgarh", "Andhra Pradesh", "Himachal Pradesh", "Uttarakhand",
    "Goa", "Tripura", "Meghalaya", "Manipur", "Nagaland", "Arunachal Pradesh",
    "Mizoram", "Sikkim", "Andaman", "Nicobar", "Puducherry"
]

DEFAULT_KEYWORDS = [
    "government", "policy", "scheme", "minister", "cm", "chief minister",
    "budget", "tax", "healthcare", "education", "infrastructure", "railway",
    "election", "privatization", "subsidy", "reservation", "gst", "fdi",
    "niti aayog", "ayushman bharat", "pm kisan", "startup india", "digital india",
    "amma canteen", "kalia scheme", "shakti scheme"
] + [s.lower() for s in STATE_NAMES]

default_args = {
    "owner": "mani",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ──────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────
def _get_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch Airflow variable with fallback."""
    try:
        return Variable.get(name) if default is None else Variable.get(name, default_var=default)
    except Exception:
        return default

def _parse_csv_var(name: str, default_list: List[str]) -> List[str]:
    """Convert a comma-separated Variable into a list."""
    raw = _get_var(name, ",".join(default_list))
    return [p.strip() for p in raw.split(",") if p.strip()] if raw else default_list

def _get_reddit_client() -> praw.Reddit:
    """Initialize and return a Reddit API client."""
    return praw.Reddit(
        client_id=Variable.get("REDDIT_CLIENT_ID"),
        client_secret=Variable.get("REDDIT_CLIENT_SECRET"),
        user_agent=Variable.get("REDDIT_USER_AGENT", "reddit_sentiment_bot/0.1")
    )

# ──────────────────────────────────────────────
# DAG Definition
# ──────────────────────────────────────────────
with DAG(
    dag_id="reddit_sentiment_etl",
    default_args=default_args,
    start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
    schedule_interval="@daily",
    catchup=False,
    tags=["reddit", "etl", "sentiment"],
) as dag:

    # ─── Extract Task ───
    @task()
    def extract_comments() -> List[Dict[str, Any]]:
        reddit = _get_reddit_client()
        subreddits = _parse_csv_var("SUBREDDITS", DEFAULT_SUBREDDITS)
        keywords = _parse_csv_var("KEYWORDS", DEFAULT_KEYWORDS)
        max_comments = int(_get_var("MAX_COMMENTS", "1000"))
        sleep_time = float(_get_var("SLEEP_TIME_SECONDS", "2"))

        today_ts = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        rows: List[Dict[str, Any]] = []

        for sub in subreddits:
            try:
                log.info("🔍 Fetching comments from r/%s", sub)
                subreddit = reddit.subreddit(sub)

                if getattr(subreddit, "subreddit_type", "public") != "public":
                    log.info("Skipping non-public subreddit %s", sub)
                    continue

                for comment in subreddit.comments(limit=max_comments):
                    created = int(getattr(comment, "created_utc", 0))
                    if created < today_ts:
                        continue

                    body = (getattr(comment, "body", "") or "").strip()
                    if not body:
                        continue

                    text = body.lower()
                    if any(kw in text for kw in keywords):
                        rows.append({
                            "id": getattr(comment, "id", ""),
                            "subreddit": sub,
                            "body": body.replace("\n", " "),
                            "created_utc": created,
                            "permalink": f"https://reddit.com{getattr(comment, 'permalink', '')}"
                        })

                log.info("✅ r/%s: collected %d comments", sub, len(rows))
                time.sleep(sleep_time)

            except Exception as e:
                log.warning("⚠️ Skipping r/%s due to error: %s", sub, e)

        log.info("📦 Extracted total %d comments", len(rows))
        return rows

    # ─── Transform Task ───
    @task()
    def transform_comments(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw:
            log.info("No comments to transform")
            return []

        from sentiment_model import score_sentiment  # Safe local import

        transformed = []
        for item in raw:
            try:
                sentiment, confidence = score_sentiment(item["body"])
                transformed.append({
                    "id": item["id"],
                    "subreddit": item["subreddit"],
                    "comment_clean": item["body"],
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "created_utc": int(item["created_utc"]),
                    "url": item["permalink"]
                })
            except Exception as e:
                log.warning("Failed to process comment %s: %s", item.get("id"), e)

        log.info("✨ Transformed %d comments", len(transformed))
        return transformed

    # ─── Load Task ───
    @task()
    def load_comments(records: List[Dict[str, Any]]) -> int:
        if not records:
            log.info("No records to load into DB")
            return 0

        try:
            inserted = upsert_comments(records)
            latest_ts = max(int(r["created_utc"]) for r in records)
            Variable.set("last_extracted_timestamp", str(latest_ts))
            log.info("💾 Loaded %d records, last_extracted_timestamp=%s", inserted, latest_ts)
            return inserted
        except Exception as e:
            log.error("❌ Failed to load comments: %s", e)
            return 0

    # ─── Task Chain ───
    raw_comments = extract_comments()
    processed_comments = transform_comments(raw_comments)
    load_comments(processed_comments)