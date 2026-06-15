"""③ 智能处理层（核心价值层）：用 DeepSeek 当你的「私人信号侦察兵」。

不是帮你总结新闻，而是替你站岗：从今天广撒网捞来的一大堆信息里，
按【你的目标】筛出真正值得你花时间的信号，过滤噪音，并对每条给出判决——
该深究 / 试试 / 观望 / 忽略，以及一个具体的下一步动作。

这把你从"被动摄入"变成"有人替你主动求取"。
"""
import json

from openai import OpenAI

from . import search
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

MAX_FEED = 120  # 雷达要广撒网，喂得比 antibubble 多

_VALID_TYPE = {"工具", "机会", "认知", "风险", "趋势"}
_VALID_URGENCY = {"高", "中", "低"}
_VALID_VERDICT = {"深究", "试试", "观望", "忽略"}


def _client():
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，请在 .env 或 GitHub Secrets 中配置")
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def _profile_block(profile) -> str:
    profile = profile or {}
    goals = [str(x).strip() for x in (profile.get("goals") or []) if str(x).strip()]
    interests = [str(x).strip() for x in (profile.get("interests") or []) if str(x).strip()]
    ignore = [str(x).strip() for x in (profile.get("ignore") or []) if str(x).strip()]

    if not goals and not interests:
        return ("【服务对象】未提供目标，按通用模式：挑对一个'想搞钱、想成长、想用好 AI'"
                "的年轻人最有行动价值的信号。")

    lines = ["【服务对象画像】你在专门为这一个人站岗，一切判断都围绕他："]
    if goals:
        lines.append("· 他正在追求的目标（relevance 的唯一标准——离这些越近分越高）：")
        for i, g in enumerate(goals, 1):
            lines.append(f"    {i}. {g}")
    if interests:
        lines.append("· 关注领域：" + "、".join(interests))
    if ignore:
        lines.append("· 明确的噪音（命中这些一律 verdict=忽略，不要浪费他注意力）：" + "、".join(ignore))
    return "\n".join(lines)


def _system_prompt(profile) -> str:
    return f"""你是一个为特定个人服务的「私人信号侦察兵 / 机会雷达」。他每天信息过载、
被动摄入，不知道哪些值得花有限的时间。你的职责不是总结，而是替他筛选与判决。

{_profile_block(profile)}

我会给你今天广撒网捞来的一批信息（标题+来源+摘要）。请你：

第一步：狠狠过滤。绝大多数都是噪音，跳过。只留下对他的目标真正有"行动价值"的信号
        ——能让他用上的新工具、抓得住的机会、该补的关键认知、要警惕的风险、值得跟的趋势。
        宁缺毋滥，挑出最值钱的若干条。

第二步：对每条信号严格输出：
- title:     信号标题（≤20字）
- what:      到底发生了什么 / 是什么（≤50字，客观）
- why_you:   为什么这对【他】重要——必须紧扣他上面的某个具体目标，不能泛泛（≤60字）
- type:      从["工具","机会","认知","风险","趋势"]里选一个
- urgency:   时效性，高(有限时窗口/先到先得)/中/低(长期有效，不急)
- relevance: 对他目标的相关度 1-5（5=直接推进他的目标，别滥用高分）
- action:    一个具体、今天就能做的小动作（≤40字，例：花20分钟试用X / 读这篇 / 设个提醒先观望）
- verdict:   从["深究","试试","观望","忽略"]里选一个；噪音填"忽略"

只输出 JSON 对象：{{"signals": [ ... ]}}，按 relevance 从高到低排序，不要任何额外文字。"""


def _identify(client, items, profile):
    feed = [
        {"i": idx, "source": it["source"], "title": it["title"],
         "summary": (it.get("summary") or "")[:200], "heat": it.get("heat", "")}
        for idx, it in enumerate(items[:MAX_FEED])
    ]
    user = ("下面是今天广撒网捞到的信息，请按系统指令筛选并判决：\n"
            + json.dumps(feed, ensure_ascii=False))
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": _system_prompt(profile)},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,  # 要的是靠谱判断，不是发散
    )
    data = json.loads(resp.choices[0].message.content)
    raw = data.get("signals", []) if isinstance(data, dict) else []

    signals = []
    for s in raw:
        title = (s.get("title") or "").strip()
        why = (s.get("why_you") or "").strip()
        verdict = (s.get("verdict") or "观望").strip()
        if not title or not why or verdict == "忽略":  # 噪音不上墙
            continue
        try:
            rel = int(s.get("relevance", 3))
        except (TypeError, ValueError):
            rel = 3
        signals.append({
            "title": title,
            "what": (s.get("what") or "").strip(),
            "why_you": why,
            "type": (s.get("type") or "趋势").strip() if (s.get("type") or "").strip() in _VALID_TYPE else "趋势",
            "urgency": (s.get("urgency") or "中").strip() if (s.get("urgency") or "").strip() in _VALID_URGENCY else "中",
            "relevance": max(1, min(5, rel)),
            "action": (s.get("action") or "").strip(),
            "verdict": verdict if verdict in _VALID_VERDICT else "观望",
            "search_query": (s.get("title") or title).strip(),
            "basis": "模型推理",
            "sources": [],
        })
    signals.sort(key=lambda x: x["relevance"], reverse=True)
    return signals


def _ground(client, signals):
    """可选取证：给「认知/趋势/风险」类信号找真实出处，让 why_you 更可信。"""
    payload, pool = [], {}
    for si, s in enumerate(signals):
        if s["type"] not in ("认知", "趋势", "风险"):
            continue
        hits = search.search(s["search_query"], max_results=2)
        if not hits:
            continue
        pool[si] = hits
        payload.append({"index": si, "claim": s["why_you"],
                        "evidence": [{"index": ei, "title": h["title"], "snippet": h["snippet"]}
                                     for ei, h in enumerate(hits)]})
    if not payload:
        return
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content":
                "给每个 claim 用 evidence 核验：若有材料支撑，grounded=true 并回填最多2条"
                ' evidence 的 index。只输出 JSON：{"items":[{"index":int,"grounded":bool,"sources":[int]}]}'},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(resp.choices[0].message.content)
    for item in (data.get("items", []) if isinstance(data, dict) else []):
        si = item.get("index")
        if not isinstance(si, int) or si not in pool or not item.get("grounded"):
            continue
        hits = pool[si]
        srcs = [{"title": hits[ei]["title"], "url": hits[ei]["url"]}
                for ei in (item.get("sources") or [])[:2]
                if isinstance(ei, int) and 0 <= ei < len(hits)]
        signals[si]["basis"] = "联网取证"
        signals[si]["sources"] = srcs


def scout(items, max_signals=6, profile=None):
    """从原料里筛出信号并判决。返回 signals（已清洗、按相关度排序、截断）。"""
    if not items:
        return []
    client = _client()
    signals = _identify(client, items, profile)
    if signals and search.enabled():
        try:
            _ground(client, signals)
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ 取证环节失败（已忽略）: {e}")
    return signals[:max_signals]
