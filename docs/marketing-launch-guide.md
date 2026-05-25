# LumenHub Marketing Launch — Complete Guide

> **Purpose**: All marketing materials, announcement copy, and messaging frameworks for the KIMI-powered product launch and ongoing campaigns.
> **Strategy**: Lead with the "local-first AI" differentiator. Personal privacy + AI power = irresistible for power users.

---

## 1. Brand Positioning Statement

**LumenHub** — Your knowledge, your AI, your rules.

> LumenHub is the first local-first AI-powered personal knowledge management system. Your notes, your memory, your intelligence — never in someone else's cloud. Powered by Hermes Agent, a multi-model AI engine that runs locally on your machine and falls back to the cloud only when you need it.

**Taglines:**
- "Think locally. Remember everything."
- "Your second brain, running on your hardware."
- "AI that stays on your side of the desk."

---

## 2. Target Audiences

| Segment | Pain Point | LumenHub Value Proposition |
|---------|-----------|---------------------------|
| **Power Users** (Obsidian/Roam/Logseq) | Tools are powerful but dumb — no real AI | Full AI integrated into existing PKM workflows |
| **Enterprise Teams** | Notion/Airtable expensive, data leaves company | Self-hosted, local-first, data sovereignty |
| **Privacy-First Users** | Paranoia about AI reading their notes | Everything local by default, cloud opt-in |
| **Developers** | Want to build on top of PKM APIs | Open-source core, plugin architecture, managed memory |
| **Students/Researchers** | Overwhelmed by information | AI synthesis + spaced repetition + memory palace |
| **Creative Professionals** | Need inspiration + structured output | AI creative partner with memory of all your work |

---

## 3. Product Launch Phases

### Phase 1: "The Reveal" (Pre-Launch Hype)
- **Duration**: 2 weeks before launch
- **Content**: Teaser posts showing "local AI in action"
- **Channels**: X/Twitter, Hacker News, Product Hunt, Reddit (r/productivity, r/ObsidianMD, r/logseq)
- **Goal**: Build waitlist, collect emails

### Phase 2: "Early Access" (Closed Beta)
- **Duration**: 2 weeks
- **Content**: Behind-the-scenes architecture posts, "how we built Hermes"
- **Channels**: Developer communities, Discord, Newsletter
- **Goal**: Get 500 beta testers, collect testimonials

### Phase 3: "Launch Day"
- **Duration**: 1 week
- **Content**: Full product reveal, demo videos, comparison posts
- **Channels**: Product Hunt (day 1), Hacker News, all social
- **Goal**: Diggity, Product Hunt #1

### Phase 4: "The Story" (Post-Launch)
- **Duration**: Ongoing
- **Content**: User stories, case studies, feature deep-dives
- **Channels**: Blog, newsletter, podcast appearances
- **Goal**: Sustained momentum, enterprise inquiries

---

## 4. Launch Announcement Templates

### 4a. X/Twitter Thread (Launch Day)

> **T1**: We just shipped something we've been building in secret for months.
>
> LumenHub: A local-first AI knowledge management system.
>
> Your notes. Your AI. Your hardware.
>
> Here's why this matters 🧵👇

> **T2**: The problem: Every PKM tool treats AI as an afterthought — a bolted-on feature that sends your private notes to some server you don't control.
>
> What if your AI could work entirely on your machine?

> **T3**: Introducing Hermes Agent — our multi-model AI engine that runs locally on your Mac/PC.
>
> Uses qwen3:14b (general reasoning) + qwen3:8b (fast tool use) + qwen3-coder:30b (code reasoning) on your hardware.

> **T4**: When you need more power, it seamlessly falls back to cloud models (DeepSeek, Grok, Ring) — but only if you choose to.
>
> Your data never leaves your machine unless you explicitly opt in.

> **T5**: Features at launch:
> ✅ AI-powered note composition
> ✅ Automatic semantic tagging
> ✅ Memory Palace — spatial AI memory that persists across sessions
> ✅ 6-tier context trimming for efficient token usage
> ✅ Multi-model fallback chain with 262K context

> **T6**: Built with:
> 🔹 Flutter 3.44 + Riverpod
> 🔹 SQLite + drift for local storage
> 🔹 Multi-model routing with quality gates
> 🔹 Resource guard that prevents your laptop from melting 🔥

> **T7**: Pricing:
> 🆓 Free tier — local-only, no limits on notes
> 🚀 Starter $8/mo — AI features included
> 🏆 Pro $20/mo — Everything, unlimited
> 🏢 Enterprise $50/user/mo — Teams + admin
>
> Launch discount: 40% off Pro for first 3 months.

> **T8**: Available today for macOS. Windows, iOS, and Android coming soon.
>
> Try it free → [link]
>
> This is just the beginning. Our AI remembers everything you tell it, across sessions, across devices.
>
> The future of knowledge management is local. 🧠

### 4b. Hacker News Launch Post

```
LumenHub (YC W26) — Local-first AI Knowledge Management
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

### 4c. Product Hunt Launch Copy

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

### 4d. Blog Post: "Why We Built LumenHub"

```markdown
# Why Your PKM Should Run AI Locally

The AI revolution happened. But your notes are still in someone else's 
cloud, feeding someone else's model, serving someone else's interests.

We started LumenHub with one question: **What if your AI worked entirely 
on your hardware?**

## The Problem with Cloud-AI PKM

Notion AI sends your notes to OpenAI. Roam's AI runs on their servers. 
Even Obsidian's plugins often route through external APIs. Every keystroke, 
every private thought, every half-formed idea — transmitted to a server 
you've never seen, governed by a ToS you've never read.

For knowledge workers, researchers, and anyone who takes their intellectual 
life seriously — this is unacceptable.

## The Solution: Hermes Agent

We built **Hermes Agent** — a multi-model AI engine that lives on your 
machine. It's not one model. It's a carefully orchestrated team:

- **qwen3:8b** — Fast tool execution (filesystem, git, terminal)
- **qwen3:14b** — General reasoning and note composition  
- **qwen3-coder:30b** — Code generation and complex analysis
- **Cloud fallback** — DeepSeek/Grok/Ring when local isn't enough

The system decides which model to use based on what you're doing. You don't 
configure anything — it just works.

## Memory Palace

Unlike ChatGPT which forgets everything between conversations, LumenHub 
remembers. Our memory palace stores patterns, preferences, and 
relationships in a local SQLite database that persists across every 
session.

Over time, your AI doesn't just process your notes — it understands the 
connections between them.

## Launch Details

- **macOS**: Available now (M2+ recommended)
- **Windows**: Coming Q3 2026
- **Mobile**: Coming Q4 2026
- **Free tier**: Full local experience with note limits
- **Pro**: $20/mo (launch discount 40% off for early adopters)

Your knowledge deserves better than someone else's server.

→ [Download LumenHub](https://lumenhub.ai)
```

---

## 5. Content Calendar (Pre-Launch)

| Week | Content Type | Platform | Topic |
|------|-------------|----------|-------|
| -4 | Teaser | X | "Something is coming. Your AI is about to get local." |
| -3 | Thread | X | "Why cloud AI in PKM is broken" (thread) |
| -2 | Dev Post | HN | "We're building a local-first AI PKM" |
| -1 | Preview | Blog | "How Hermes Agent routes between models" |
| 0 | Launch | All | Full reveal + Product Hunt |
| +1 | Deep Dive | Blog | "Inside the Memory Palace" |
| +2 | Case Study | Blog | "How I migrated from Notion to LumenHub" |
| +3 | Comparison | Video | "LumenHub vs Notion AI vs Logseq" |

---

## 6. KIMI Integration Plan

When KIMI becomes available:

1. **Role Assignment**: KIMI handles "Creative/UX" tasks alongside "Analysis" — filling the most human-like role in the stack
2. **Quality Gate**: KIMI becomes the final aesthetic/review layer for generated content
3. **Pricing Lever**: KIMI access unlocks "Creative Mode" — a feature that could justify Pro tier
4. **Marketing Angle**: "Powered by 5 AI models including Moonshot's KIMI" — premium positioning

### KIMI-Specific Marketing Angles
- "Designed with aesthetic intelligence" — KIMI's design sensibility for UI/UX
- "Your AI that gets design" — for creative professionals
- "From notes to beauty" — automatic formatting and visual design suggestions

---

## 7. Competitive Messaging Matrix

| Feature | LumenHub | Notion AI | Obsidian | Logseq |
|---------|----------|-----------|----------|--------|
| Local AI processing | ✅ | ❌ | ❌ | ❌ |
| Multi-model routing | ✅ | ❌ | ❌ | ❌ |
| Memory palace | ✅ | ❌ | ❌ | ❌ |
| Context trimming | ✅ | ❌ | ❌ | ❌ |
| Privacy by default | ✅ | ❌ | ⚠️ | ⚠️ |
| Free tier | ✅ | ✅(limited) | ✅ | ✅ |
| Cross-platform | ✅ | ✅ | ✅ | ✅ |
| AI pricing | $8-$20/mo | $10/mo add-on | N/A | Usage-based |
| Cloud fallback | ✅ | N/A | N/A | N/A |

---

## 8. Launch Metrics to Track

| Metric | Target | Measurement |
|--------|--------|-------------|
| Waitlist signups (pre-launch) | 2,000+ | Landing page |
| Day 1 Product Upvotes | 300+ | Product Hunt |
| Week 1 downloads | 500+ | Direct + Store |
| Activation rate | >60% | Added first note within 24h |
| Free→Paid conversion | 5-8% | Monthly |
| NPS (day 30) | >40 | In-app survey |
| AI usage per user | >5 AI actions/week | Backend telemetry |
| Churn rate | <5% monthly | Subscription cohort |