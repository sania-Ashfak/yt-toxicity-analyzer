# --- Put these imports at the TOP of transform.py (they were missing: this is the
# --- cause of the 4 Pylance errors on transform.py in your VS Code screenshot) ---
import re

try:
    import config
except ImportError:  # keeps the function usable on its own
    config = None

DEFAULT_TOPIC_KEYWORDS = {
    "challenge": ["challenge", "vs", "survive", "last to", "$1", "$1,000", "million", "give away", "giveaway"],
    "tech":      ["iphone", "android", "review", "unboxing", "tesla", "ev", "phone", "laptop", "camera", "ai", "tech", "pixel", "galaxy", "macbook"],
    "music":     ["official video", "music video", "lyrics", "song", "album", "live", "concert", "never gonna give you up", "remix", "audio"],
    "gaming":    ["minecraft", "fortnite", "gameplay", "gaming", "playthrough", "roblox"],
    "education": ["how to", "explained", "tutorial", "learn", "science", "history"],
    "vlog":      ["vlog", "day in", "behind the scenes", "q&a", "my life"],
    "news":      ["news", "election", "breaking", "update", "announcement"],
}
# config.TOPIC_KEYWORDS (if you defined one) wins; otherwise use the defaults above.
TOPIC_KEYWORDS = getattr(config, "TOPIC_KEYWORDS", None) or DEFAULT_TOPIC_KEYWORDS


def infer_topic(title: str) -> str:
    """Assign a broad topic from whole words / phrases in a video title."""
    title = str(title or "").lower().strip()
    if not title:
        return "general"
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            keyword = keyword.strip().lower()
            if not keyword:
                continue
            if re.fullmatch(r"[^a-z0-9]+", keyword):
                if keyword in title:
                    return topic
                continue
            # \b-style guard that also works next to symbols such as "$1"
            if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", title):
                return topic
    return "general"