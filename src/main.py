"""编排入口：广撒网采集 → 侦察兵筛选判决 → 去重 → 渲染 → 推送。

用法：
    python -m src.main                # 完整跑一遍并推送到飞书
    python -m src.main --dry-run      # 跑全链路但不推送，打印卡片 JSON
    python -m src.main --collect-only # 只测采集（不调 LLM、不推送）
"""
import argparse
import json
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from . import collect, dedup, llm, render, push, search


def run(dry_run=False, collect_only=False):
    settings, sources = collect.load_config()
    profile = collect.load_profile()
    lookback = settings.get("lookback_hours", 48)
    max_signals = settings.get("max_signals", 6)

    print("① 广撒网采集中…")
    items, errors = collect.collect_all(sources, lookback)
    print(f"   采集到 {len(items)} 条原料，失败源 {len(errors)} 个")

    if collect_only:
        for it in items[:50]:
            heat = f" [{it['heat']}]" if it.get("heat") else ""
            print(f"   {it['title']}{heat}  <{it['source']}>")
        return 0

    if not items:
        print("   没采到任何原料，跳过（不推送）。")
        return 0

    mode = "对症（已读目标）" if (profile.get("goals") or profile.get("interests")) else "通用"
    grounding = "联网取证" if search.enabled() else "模型推理"
    print(f"② 侦察兵筛选判决中（模式: {mode} · 依据: {grounding}）…")
    signals = llm.scout(items, max_signals, profile)
    print(f"   筛出 {len(signals)} 条值得你看的信号")

    print("③ 去重中（同一信号不重复打扰）…")
    seen = dedup.load_seen()
    fresh = [s for s in signals if dedup.topic_id(s["title"]) not in seen]
    print(f"   新信号 {len(fresh)} 条（已过滤 {len(signals) - len(fresh)} 条近期已推）")

    if not fresh:
        print("   今日信号都近期推过，静默退出。")
        return 0

    print("④ 渲染雷达卡片…")
    card = render.build_card(fresh)

    if dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        print("\n(--dry-run：未推送，未更新状态库)")
        return 0

    print("⑤ 推送到飞书…")
    push.push(card)
    dedup.mark_seen([dedup.topic_id(s["title"]) for s in fresh], seen)
    print("   ✓ 推送完成，状态库已更新")
    return 0


def main():
    p = argparse.ArgumentParser(description="信号雷达 · 每日主动信号侦察")
    p.add_argument("--dry-run", action="store_true", help="跑全链路但不推送")
    p.add_argument("--collect-only", action="store_true", help="只测采集层")
    args = p.parse_args()
    try:
        return run(dry_run=args.dry_run, collect_only=args.collect_only)
    except Exception as e:  # noqa: BLE001
        print(f"运行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
