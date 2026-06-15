"""集中读取环境变量。本地从 .env 读，线上从 GitHub Secrets 注入。"""
import os

from dotenv import load_dotenv

load_dotenv()


def _env(key, default=""):
    """读取环境变量并清掉首尾空白与 BOM(﻿)——记事本/PowerShell 管道常会带上。"""
    return os.getenv(key, default).strip().strip("﻿").strip()


# 飞书自定义机器人 Webhook
FEISHU_WEBHOOK = _env("FEISHU_WEBHOOK")

# DeepSeek（OpenAI 兼容接口）
DEEPSEEK_API_KEY = _env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODEL = _env("DEEPSEEK_MODEL", "deepseek-chat")

# RSSHub 实例（{RSSHUB} 占位符会被替换成这个）
RSSHUB_BASE = _env("RSSHUB_BASE", "https://rsshub.app").rstrip("/")

# Tavily 联网检索（可选）：填了就给"另一面"找真实出处（grounding），
# 不填则反方退化为模型纯推理，并在卡片上如实标注。https://tavily.com
TAVILY_API_KEY = _env("TAVILY_API_KEY")
