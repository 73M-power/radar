# 📡 radar · 个人信号雷达

> 你不缺信息，你缺的是「替你站岗的人」。

每天广撒网抓取一大堆信息，然后用 AI 当你的**私人信号侦察兵**——
按**你的目标**狠狠过滤噪音，筛出真正值得你花时间的信号，并对每条给出判决:
**该深究 / 试试 / 观望**，外加一个**今天就能做的下一步动作**。

把你从「被动刷信息」变成「有人主动替你求取」。零服务器，跑在 GitHub Actions 上。

> 🫧 它和 [antibubble](https://github.com/73M-power/antibubble) 是一对：
> **雷达帮你发现「该关心什么」，antibubble 帮你想清楚「已经信的对不对」**——一个探路，一个对症。

---

## 它长什么样

```
📡 信号雷达 · 2026-06-15
> 替你站岗的雷达：今天值得你花时间的，就这几件。
────────────────────────────
🔥 值得深究
🛠 某开源 Agent 框架  🎯🎯🎯
  一个能本地跑、带记忆的多智能体框架，今天冲上 HN 第一
🎯 对你：正好是你"做小而美 AI 产品"能直接复用的轮子
👉 下一步：花 30 分钟 clone 跑通 demo　⏰ 有时效，别拖
────────────────────────────
👀 先观望
📈 美联储官员放鹰  🎯
  …
🎯 对你：影响你关注的美股，但短期别据此操作
👉 下一步：设个提醒，等下周 CPI 再看
```

## 为什么不一样

普通资讯工具给你**更多信息**，让你更焦虑。雷达给你**更少但更准**——
它的核心不是"告诉你发生了什么"，而是**替你判断"这对你值不值得"**，
并把信息变成**行动**。每条信号都钉死在你的某个具体目标上，配一个判决和动作。

## 工作原理

```
广撒网采集  →  侦察兵筛选判决        →  去重  →  飞书雷达卡片
(新品/热点/   按你的目标过滤噪音、      (同信号    (按 深究/试试/观望
 你的领域)    打相关度、给判决+动作      不重复)     分组 + 下一步)
```

| 文件 | 职责 |
|------|------|
| `src/collect.py` | 广撒网（Product Hunt / Show HN / 各领域 RSS） |
| `src/llm.py`     | **核心**：按你目标筛信号、判决、给动作 |
| `src/search.py`  | 可选联网取证 |
| `src/render.py`  | 渲染成"雷达卡片"（按判决分组） |
| `src/push.py` / `dedup.py` / `main.py` | 推送 / 去重 / 编排 |
| `profile.yaml`   | **你的目标画像**：relevance 的唯一标准 |

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env                   # 填 FEISHU_WEBHOOK 和 DEEPSEEK_API_KEY
cp profile.example.yaml profile.yaml   # 填你的目标（最关键！）

python -m src.main --collect-only      # 测采集
python -m src.main --dry-run           # 看卡片
python -m src.main                     # 正式推
```

需要：**飞书机器人 Webhook** + **DeepSeek API Key**（[platform.deepseek.com](https://platform.deepseek.com)）。
可选：**Tavily Key**（[tavily.com](https://tavily.com)）开启联网取证。

## 让它每天自动跑

1. Fork → 仓库 Settings → Secrets 加 `FEISHU_WEBHOOK`、`DEEPSEEK_API_KEY`（可选 `TAVILY_API_KEY`）
2. 改 `.github/workflows/daily.yml` 的 cron（默认北京时间 06:30）
3. 收工。

## 核心：填好 `profile.yaml`

雷达准不准，全看你的 `goals` 写得够不够具体。把你真正想达成的事写进去，
它就只为这些目标站岗。`ignore` 里写明你不想被打扰的噪音，命中一律过滤。

## License

MIT
