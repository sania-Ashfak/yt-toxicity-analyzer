"""Toxicity classifier with two swappable backends.

1. lexicon     - zero-dependency, offline: weighted category lexicons + text signals.
2. transformer - unitary/toxic-bert via detoxify (pip install detoxify torch).

Both expose: predict(text) -> {"toxicity": float in [0,1], "is_toxic": bool,
                               "categories": {cat: float}}
"""
import re, html
import config

# ----------------------------- lexicon backend ------------------------------
LEXICONS = {
    "profanity": ["fuck","shit","bitch","asshole","dick","cunt","piss","bastard"],
    "insult":    ["idiot","stupid","dumb","moron","loser","retard","trash","pathetic",
                  "clown","useless","worthless","ugly","hate you","shut up","cry"],
    "threat":    ["kill yourself","kys","die","death","hurt you","beat you","attack",
                  "burn","destroy you","come find"],
    "hate":      ["nigger","faggot","retarded","slur","racist","nazi","kkk","genocide"],
    "spam":      ["subscribe to my channel","check my channel","free money","click the link",
                  "crypto giveaway","www.","http://","buy now","promo code"],
}

_WORD = re.compile(r"[a-z0-9']+")

def _lexicon_score(text: str) -> dict:
    t = html.unescape(text).lower()
    words = set(_WORD.findall(t))
    cats, hits = {}, 0
    for cat, terms in LEXICONS.items():
        h = sum(1 for term in terms if term in t or term in words)
        cats[cat] = min(h / 3.0, 1.0)                 # normalize ~3 hits = max
        hits += h
    base = min(hits / 4.0, 1.0)
    # text-level signals: CAPS ratio, exclamation spam, emoji-free repetition
    alpha = [c for c in t if c.isalpha()]
    caps_ratio = (sum(c.isupper() for c in alpha) / len(alpha)) if alpha else 0
    if caps_ratio > 0.6 and len(alpha) > 10:
        base = min(base + 0.15, 1.0)
    if t.count("!") > 4:
        base = min(base + 0.1, 1.0)
    return {"toxicity": round(min(base + 0.15 * cats.get("hate", 0) +
                                  0.10 * cats.get("threat", 0), 1.0), 4), "categories": cats}

# --------------------------- transformer backend ----------------------------
class TransformerBackend:
    def __init__(self):
        from detoxify import Detoxify           # lazy import: only if selected
        self._model = Detoxify("original")

    def predict(self, text: str) -> dict:
        scores = self._model.predict(text)
        cats = {k.replace("_", " "): round(float(v), 4)
                for k, v in scores.items() if k != "toxicity"}
        tox = float(scores["toxicity"])
        return {"toxicity": round(tox, 4), "categories": cats}

# ------------------------------- dispatcher ---------------------------------
_backend = None

def get_backend():
    global _backend
    if _backend is None:
        if config.TOXICITY_BACKEND == "transformer":
            _backend = TransformerBackend()
        else:
            _backend = type("Lexicon", (), {"predict": staticmethod(_lexicon_score)})()
    return _backend

def predict(text: str) -> dict:
    r = get_backend().predict(text or "")
    r["is_toxic"] = bool(r["toxicity"] >= config.TOXIC_THRESHOLD)
    return r
