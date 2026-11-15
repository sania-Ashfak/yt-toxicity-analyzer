"""EXTRACT: pull comments + video metadata from the YouTube Data API v3.

Output: data/raw_comments.jsonl  (one JSON object per comment, video stats joined in)
Rate limits: API quota ~10,000 units/day; comments.list costs 1 unit/page.
"""
import json, os, time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config


def get_youtube():
    if config.API_KEY in ("", "YOUR_API_KEY_HERE"):
        raise RuntimeError("Set YOUTUBE_API_KEY env var or edit config.API_KEY")
    return build("youtube", "v3", developerKey=config.API_KEY)


def channel_uploads_playlist(youtube, channel):
    """Resolve a channel handle/ID to its uploads playlist ID."""
    if channel.startswith("UC") and len(channel) == 24:
        cid = channel
    else:
        resp = youtube.search().list(part="snippet", q=channel, type="channel",
                                     maxResults=1).execute()
        cid = resp["items"][0]["snippet"]["channelId"]
    ch = youtube.channels().list(part="contentDetails", id=cid).execute()
    return ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def videos_from_channel(youtube, playlist_id):
    """Most recent MAX_VIDEOS_PER_CHANNEL video IDs from an uploads playlist."""
    ids, token = [], None
    while len(ids) < config.MAX_VIDEOS_PER_CHANNEL:
        req = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id,
                                           maxResults=50, pageToken=token)
        resp = req.execute()
        ids += [i["contentDetails"]["videoId"] for i in resp["items"]]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids[:config.MAX_VIDEOS_PER_CHANNEL]


def video_stats(youtube, video_ids):
    """Map video_id -> {title, channel, views, likes, topic keywords}."""
    stats = {}
    for i in range(0, len(video_ids), 50):
        resp = youtube.videos().list(
            part="snippet,statistics", id=",".join(video_ids[i:i+50])).execute()
        for v in resp["items"]:
            vid = v["id"]
            stats[vid] = {
                "video_id": vid,
                "video_title": v["snippet"].get("title", ""),
                "channel": v["snippet"].get("channelTitle", ""),
                "published_at": v["snippet"].get("publishedAt", ""),
                "view_count": int(v["statistics"].get("viewCount", 0)),
                "like_count": int(v["statistics"].get("likeCount", 0)),
                "comment_count": int(v["statistics"].get("commentCount", 0)),
            }
    return stats


def fetch_comments(youtube, video_id, cap):
    """All top-level comments for one video (paged), up to `cap`."""
    comments, token = [], None
    while len(comments) < cap:
        req = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100,
            textFormat="plainText", pageToken=token)
        try:
            resp = req.execute()
        except HttpError as e:                       # comments disabled etc.
            print(f"  [skip] {video_id}: {e.resp.status}")
            break
        for item in resp.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "video_id": video_id,
                "author": s.get("authorDisplayName", ""),
                "text": s.get("textDisplay", ""),
                "like_count": int(s.get("likeCount", 0)),
                "published_at": s.get("publishedAt", ""),
                "reply_count": int(item["snippet"].get("totalReplyCount", 0)),
            })
        token = resp.get("nextPageToken")
        if not token:
            break
        time.sleep(0.2)                              # be polite with quota
    return comments[:cap]


def run():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    yt = get_youtube()
    video_ids = list(config.VIDEO_IDS)

    for ch in config.CHANNELS:
        pl = channel_uploads_playlist(yt, ch)
        video_ids += videos_from_channel(yt, pl)
    video_ids = list(dict.fromkeys(video_ids))       # dedupe, keep order
    print(f"Target videos: {len(video_ids)}")

    stats = video_stats(yt, video_ids)
    n = 0
    with open(config.RAW_PATH, "w", encoding="utf-8") as out:
        for vid in video_ids:
            for c in fetch_comments(yt, vid, config.MAX_COMMENTS_PER_VIDEO):
                out.write(json.dumps({**stats.get(vid, {}), **c},
                                     ensure_ascii=False) + "\n")
                n += 1
            print(f"  {vid}: total comments so far = {n}")
    print(f"EXTRACT done -> {config.RAW_PATH} ({n} comments)")


if __name__ == "__main__":
    run()
