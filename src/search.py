"""可选的联网检索层：给"另一面"找真实出处（grounding）。

只有配置了 TAVILY_API_KEY 才启用；没配或任何报错都静默跳过，
退化为模型纯推理（counter_basis 会如实标注 "模型推理"），不影响主流程。

为什么用 Tavily：它是专为 LLM 取证设计的搜索 API，直接返回正文片段，
免去自己抓网页解析的麻烦，免费额度足够每天跑。换成 Brave / SerpAPI 同理，
只需改这一个文件。
"""
import requests

from .config import TAVILY_API_KEY

_ENDPOINT = "https://api.tavily.com/search"


def enabled() -> bool:
    return bool(TAVILY_API_KEY)


def search(query: str, max_results: int = 3):
    """搜一个查询，返回 [{"title","url","snippet"}]；未配置或失败返回 []。"""
    if not TAVILY_API_KEY or not query:
        return []
    try:
        r = requests.post(
            _ENDPOINT,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("results", []) or []
        out = []
        for it in results:
            title = (it.get("title") or "").strip()
            url = it.get("url") or ""
            snippet = (it.get("content") or "").strip()[:500]
            if title and url:
                out.append({"title": title, "url": url, "snippet": snippet})
        return out
    except Exception as e:  # noqa: BLE001 — 取证失败不能拖垮主流程
        print(f"  ✗ 检索失败（已忽略，退化为纯推理）: {e}")
        return []
