"""② 采集层：广撒网，把各类源拉下来作为"信号原料"。

和 antibubble 抓"主流共识"不同，雷达要的是「可能藏着机会/新工具/认知/风险」的
广谱信息——新产品、热门讨论、行业动态、你三根支柱里的专业内容。撒得越宽，
雷达能筛出的有效信号越多。

统一 item 结构：
    {"title", "summary", "link", "source", "heat", "ts"}
"""
import os
import re
import time

import feedparser
import requests
import yaml

from .config import RSSHUB_BASE

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def load_config(path: str = "sources.yaml"):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("settings", {}) or {}, data.get("sources", []) or []


def load_profile(path: str = "profile.yaml"):
    """读目标画像；文件不存在或为空则返回空 dict（退化为通用模式）。"""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _within_window(ts, lookback_hours) -> bool:
    if not ts:
        return True
    return (time.time() - ts) <= lookback_hours * 3600


def _collect_rss(src, lookback_hours):
    url = src["url"].replace("{RSSHUB}", RSSHUB_BASE)
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", 0) and not feed.entries:
        raise RuntimeError(f"RSS 解析失败: {getattr(feed, 'bozo_exception', '未知错误')}")
    items = []
    for e in feed.entries:
        ts = None
        for attr in ("published_parsed", "updated_parsed"):
            if getattr(e, attr, None):
                ts = time.mktime(getattr(e, attr))
                break
        if not _within_window(ts, lookback_hours):
            continue
        title = (e.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "title": title,
            "summary": _strip_html(e.get("summary") or e.get("description") or "")[:600],
            "link": e.get("link") or "",
            "source": src["name"],
            "heat": "",
            "ts": ts,
        })
    return items


def _collect_hackernews(src, lookback_hours):
    """Algolia HN 接口。tags 可选 story / show_hn 等，分数即热度。"""
    since = int(time.time() - lookback_hours * 3600)
    min_points = int(src.get("min_points", 50))
    params = {
        "tags": src.get("tags", "story"),
        "numericFilters": f"created_at_i>{since},points>={min_points}",
        "hitsPerPage": 40,
    }
    if src.get("query"):
        params["query"] = src["query"]
    r = requests.get("https://hn.algolia.com/api/v1/search", params=params, timeout=20)
    r.raise_for_status()
    items = []
    for h in r.json().get("hits", []):
        title = (h.get("title") or "").strip()
        if not title:
            continue
        link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        items.append({
            "title": title,
            "summary": _strip_html(h.get("story_text") or "")[:400],
            "link": link,
            "source": src["name"],
            "heat": f"{h.get('points', 0)}分 · {h.get('num_comments', 0)}评论",
            "ts": float(h.get("created_at_i")) if h.get("created_at_i") else None,
        })
    return items


_COLLECTORS = {
    "rss": _collect_rss,
    "hackernews": _collect_hackernews,
}


def collect_all(sources, lookback_hours):
    """遍历所有源，单个源失败不影响其它源。返回 (items, errors)。"""
    items, errors = [], []
    for src in sources:
        fn = _COLLECTORS.get(src.get("type"))
        if not fn:
            errors.append(f"{src.get('name', '?')}: 未知类型 {src.get('type')}")
            continue
        try:
            got = fn(src, lookback_hours)
            items.extend(got)
            print(f"  ✓ {src['name']}: {len(got)} 条")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{src.get('name', '?')}: {e}")
            print(f"  ✗ {src['name']}: {e}")
    return items, errors
