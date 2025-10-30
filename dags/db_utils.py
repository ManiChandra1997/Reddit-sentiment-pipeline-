import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ─── Logging setup ───
log = logging.getLogger("db_utils")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

# ─── Global engine cache ───
_engine: Optional[Engine] = None

def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        # Use the Airflow DB connection
        db_url = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
        if not db_url:
            raise RuntimeError("Database URL not set in environment")
        _engine = create_engine(db_url, future=True, pool_pre_ping=True)
        log.info("Connected to database: %s", _engine.url.database)
    return _engine

def _ensure_table_exists(engine: Engine):
    ddl = text("""
        CREATE TABLE IF NOT EXISTS reddit_comments (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            comment_clean TEXT,
            sentiment TEXT,
            confidence FLOAT,
            created_utc TIMESTAMP,
            url TEXT
        );
    """)
    with engine.begin() as conn:
        conn.execute(ddl)
    log.info("Verified reddit_comments table exists")

def upsert_comments(rows: List[Dict[str, Any]]) -> int:
    """
    Upsert Reddit comments into the table.
    """
    if not rows:
        log.info("No rows to upsert")
        return 0

    for r in rows:
        # Normalize timestamp
        try:
            r["created_utc"] = int(float(r.get("created_utc", 0)))
        except Exception:
            r["created_utc"] = 0

        # Ensure sentiment is a string
        r["sentiment"] = str(r.get("sentiment", "neutral"))

        # Ensure confidence is a float
        try:
            r["confidence"] = float(r.get("confidence", 0))
        except (TypeError, ValueError):
            log.warning("Invalid confidence for id=%s, defaulting to 0.0", r.get("id"))
            r["confidence"] = 0.0

    sql = text("""
        INSERT INTO reddit_comments
            (id, subreddit, comment_clean, sentiment, confidence, created_utc, url)
        VALUES
            (:id, :subreddit, :comment_clean, :sentiment, :confidence, to_timestamp(:created_utc), :url)
        ON CONFLICT (id) DO UPDATE
        SET
            sentiment = EXCLUDED.sentiment,
            confidence = EXCLUDED.confidence
    """)

    engine = _get_engine()
    _ensure_table_exists(engine)

    try:
        with engine.begin() as conn:
            result = conn.execute(sql, rows)
            log.info("Upserted %d rows", result.rowcount)
            return result.rowcount
    except Exception as e:
        log.exception("Failed to upsert comments: %s", e)
        raise