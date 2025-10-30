import logging
from typing import Tuple
import re
from langdetect import detect
from transformers import pipeline

# ─── Logging Setup ───
log = logging.getLogger("sentiment_model")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

# ─── Load Transformer Models ───
try:
    en_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    multi_model = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
except Exception as e:
    log.exception("Failed to load sentiment models: %s", e)
    en_model = None
    multi_model = None

# ─── Lexicons for Indian Languages ───
_POSITIVE_WORDS = {
    "good", "great", "excellent", "awesome", "positive", "happy", "love", "like",
    "best", "fantastic", "support", "achha", "shandar", "badiya", "sahi", "nalla", "sirappu"
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "worst", "negative", "hate", "dislike",
    "problem", "fail", "angry", "issue", "bura", "galat", "ghatak", "kharaab", "mosamana", "ketta"
}

def lexicon_sentiment(text: str) -> Tuple[str, float]:
    tokens = re.findall(r'\w+', text.lower())
    pos_hits = sum(1 for t in tokens if t in _POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in _NEGATIVE_WORDS)
    total_hits = pos_hits + neg_hits

    if total_hits == 0:
        return "neutral", 0.0

    score = (pos_hits - neg_hits) / total_hits
    confidence = round(min(abs(score), 1.0), 2)

    if score > 0:
        return "positive", confidence
    elif score < 0:
        return "negative", confidence
    else:
        return "neutral", confidence

def score_sentiment(text: str) -> Tuple[str, float]:
    if not text or not text.strip():
        return "neutral", 0.0

    try:
        lang = detect(text)
    except Exception:
        lang = "unknown"

    try:
        if lang == "en" and en_model:
            result = en_model(text[:512])[0]
            label = result["label"].lower()
            score = round(float(result["score"]), 2)
            return label, score if score >= 0.6 else ("neutral", score)

        elif multi_model and lang in ["hi", "ta", "mr", "bn", "gu", "kn", "ml", "ur"]:
            result = multi_model(text[:512])[0]
            label = result["label"].lower()
            score = round(float(result["score"]), 2)
            return label, score if score >= 0.6 else ("neutral", score)

        else:
            return lexicon_sentiment(text)

    except Exception as e:
        log.exception("Sentiment scoring failed: %s", e)
        return "neutral", 0.0