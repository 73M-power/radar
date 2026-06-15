"""去重：用 state/seen.json 记录已处理过的话题指纹，避免天天推同一个争论。

注意：茧房粉碎机的去重粒度是"话题"而非"单条新闻"——同一个话题里换几条新闻
来源仍算同一件事，所以指纹由 LLM 归纳出的话题标题生成（见 main.py）。
"""
import hashlib
import json
import os

STATE_PATH = "state/seen.json"
MAX_KEEP = 2000  # 状态库上限，超出丢弃最旧的


def topic_id(title: str) -> str:
    """把话题标题归一化后做指纹：去空白、转小写，让措辞微调仍判为同一话题。"""
    key = "".join((title or "").split()).lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def load_seen() -> set:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def mark_seen(ids, seen):
    """把 ids 标记为已见并落盘，维持插入顺序，超限截掉头部。"""
    new_ids = [i for i in ids if i not in seen]
    if not new_ids:
        return
    existing = _load_ordered()
    existing.extend(new_ids)
    trimmed = existing[-MAX_KEEP:]
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False)
    seen.update(new_ids)


def _load_ordered() -> list:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return list(json.load(f))
        except (json.JSONDecodeError, OSError):
            return []
    return []
