"""⑤ 推送层：把卡片发到飞书自定义机器人 Webhook。"""
import requests

from .config import FEISHU_WEBHOOK


def push(card: dict):
    if not FEISHU_WEBHOOK:
        raise RuntimeError("缺少 FEISHU_WEBHOOK，请在 .env 或 GitHub Secrets 中配置")
    r = requests.post(FEISHU_WEBHOOK, json=card, timeout=20)
    r.raise_for_status()
    data = r.json()
    # 飞书成功返回 StatusCode==0（旧）或 code==0（新）
    code = data.get("code", data.get("StatusCode", -1))
    if code not in (0, None):
        raise RuntimeError(f"飞书推送失败: {data}")
    return data
