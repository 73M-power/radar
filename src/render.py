"""④ 渲染层：把信号渲染成飞书"雷达卡片"。

核心是行动导向：每条信号都带「为什么对你重要 + 下一步做什么 + 判决」，
并按判决分组，让你一眼看出"今天该深究什么、什么先观望"。
"""
import datetime as dt

_TYPE_EMOJI = {"工具": "🛠", "机会": "💡", "认知": "📚", "风险": "⚠️", "趋势": "📈"}

_VERDICT = {
    "深究": ("🔥 值得深究", 1),
    "试试": ("✅ 抽空试试", 2),
    "观望": ("👀 先观望", 3),
}

_STARS = {5: "🎯🎯🎯", 4: "🎯🎯", 3: "🎯", 2: "·", 1: "·"}


def _urgency_tail(s) -> str:
    if s.get("urgency") == "高":
        return "　⏰ 有时效，别拖"
    return ""


def _signal_md(s) -> str:
    te = _TYPE_EMOJI.get(s.get("type"), "📡")
    lines = [f"**{te} {s['title']}**　{_STARS.get(s.get('relevance', 3), '·')}"]
    if s.get("what"):
        lines.append(f"　{s['what']}")
    lines.append(f"🎯 对你：{s['why_you']}")
    if s.get("action"):
        lines.append(f"👉 下一步：**{s['action']}**{_urgency_tail(s)}")
    if s.get("basis") == "联网取证" and s.get("sources"):
        links = " · ".join(f"[{x['title'][:16]}]({x['url']})" for x in s["sources"])
        lines.append(f"🔎 出处：{links}")
    return "\n".join(lines)


def build_card(signals):
    stamp = dt.datetime.now().strftime("%Y-%m-%d")

    elements = []
    if not signals:
        elements.append({
            "tag": "markdown",
            "content": "今天广撒网没捞到对你目标够格的信号，省下你的注意力 🍵",
        })
    else:
        elements.append({
            "tag": "markdown",
            "content": "> 替你站岗的雷达：今天值得你花时间的，就这几件。",
        })
        # 按判决分组：深究 → 试试 → 观望
        groups = {}
        for s in signals:
            groups.setdefault(s.get("verdict", "观望"), []).append(s)
        for verdict, (label, _) in sorted(_VERDICT.items(), key=lambda kv: kv[1][1]):
            grp = groups.get(verdict)
            if not grp:
                continue
            elements.append({"tag": "hr"})
            elements.append({"tag": "markdown", "content": f"**{label}**"})
            for s in grp:
                elements.append({"tag": "markdown", "content": _signal_md(s)})

    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"信号雷达 · 共 {len(signals)} 条 · 🎯越多越相关 · 判断仅供参考",
        }],
    })

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📡 信号雷达 · {stamp}"},
                "template": "carmine",
            },
            "elements": elements,
        },
    }
