## X/Twitter Thread (8 tweets, ready to post)

**T1**: We just shipped something we've been building in secret for months.
LumenHub: A local-first AI knowledge management system.
Your notes. Your AI. Your hardware.
Here's why this matters 🧵👇

**T2**: The problem: Every PKM tool treats AI as an afterthought — a bolted-on feature that sends your private notes to some server you don't control.
What if your AI could work entirely on your machine?

**T3**: Introducing Hermes Agent — our multi-model AI engine that runs locally on your Mac/PC.
Uses qwen3:14b (general reasoning) + qwen3:8b (fast tool use) + qwen3-coder:30b (code reasoning) on your hardware.

**T4**: When you need more power, it seamlessly falls back to cloud models (DeepSeek, Grok, Ring) — but only if you choose to.
Your data never leaves your machine unless you explicitly opt in.

**T5**: Features at launch:
✅ AI-powered note composition
✅ Automatic semantic tagging
✅ Memory Palace — spatial AI memory that persists across sessions
✅ 6-tier context trimming for efficient token usage
✅ Multi-model fallback chain with 262K context

**T6**: Built with:
🔹 Flutter 3.44 + Riverpod
🔹 SQLite + drift for local storage
🔹 Multi-model routing with quality gates
🔹 Resource guard that prevents your laptop from melting 🔥

**T7**: Pricing:
🆓 Free tier — local-only, no limits on notes
🚀 Starter $8/mo — AI features included
🏆 Pro $20/mo — Everything, unlimited
🏢 Enterprise $50/user/mo — Teams + admin
Launch discount: 40% off Pro for first 3 months.

**T8**: Available today for macOS. Windows, iOS, and Android coming soon.
Try it free → [link]
This is just the beginning. Our AI remembers everything you tell it, across sessions, across devices.
The future of knowledge management is local. 🧠

---

## Hacker News Launch Post

```
LumenHub — Local-first AI Knowledge Management
https://lumenhub.ai

We built LumenHub because existing PKM tools (Obsidian, Notion, Logseq)
treat AI as an afterthought. Your private notes get sent to APIs you
don't control, with no guarantee of privacy.

What makes LumenHub different:

1. **Local-first AI**: Hermes Agent runs qwen3 models on your machine.
   No data leaves your hardware by default.

2. **Multi-model routing**: Smart task classification routes queries to
   the right model — 8B for tool use, 14B for general, 30B for code,
   cloud models when needed.

3. **Memory Palace**: SQLite-backed persistent memory that remembers
   context across sessions. Not just search — actual understanding
   of your knowledge graph.

4. **Context trimming**: 6-tier priority system keeps your context
   window efficient without losing important information.

Tech: Flutter 3.44, Riverpod, SQLite+drift, Rust for perf-critical paths.

We're hiring: backend@lumenhub.ai
```

---

## Product Hunt Launch Copy

```
🔥 LumenHub — AI that stays on your side of the desk

The first local-first AI-powered PKM. Hermes Agent runs 3 local
models on your machine with cloud fallback only when you choose it.

✨ AI note composition
✨ Semantic auto-tagging
✨ Persistent memory palace
✨ Multi-model routing with quality gates

Free tier available. Launch discount: 40% off Pro.

#productivity #ai #privacy #notes
```