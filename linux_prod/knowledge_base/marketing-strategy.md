# LumenHub Marketing Strategy

> Status: DRAFT — Loop in before publishing externally.
> Tone: Human-first. No AI jargon. Benefits over features.

---

## Positioning

**One line:** Your assistant that remembers everything and never makes you start over.

**Who it's for:** People who work in terminals and messengers, use multiple AI models, and are tired of re-explaining context to every new session.

**What it replaces:** The copy-paste between ChatGPT/Claude/Gemini windows. The lost context. The "who are you again?" feeling every time you open a new chat.

---

## Value Proposition

### For developers and power users:
- **It remembers.** Your preferences, project context, past decisions — all stored locally. Open a chat tomorrow and it knows exactly where you left off.
- **It picks the right brain.** You have DeepSeek for quick code, Grok for reasoning, Claude for polish. LumenHub routes each question to the best match — you don't manage that yourself.
- **It lives where you live.** Terminal your team already uses, the messaging app on your phone, or a desktop app. No separate dashboard to open.

### For teams and small companies:
- **No per-seat costs.** Run it on your own hardware. Your API keys, your cloud subscriptions, your data.
- **No vendor lock-in.** Open source. Fork it. Run it anywhere. If you stop using it, your data walks out in standard formats.
- **Shared memory.** Team members can contribute to a shared knowledge base that the assistant draws from — no onboarding docs needed.

---

## Key Messages (for website, social, launch)

| Audience | Message |
|----------|---------|
| Developers | "An AI assistant that remembers your project history and picks the best model automatically — runs on your machine." |
| Tech leads | "Self-hosted intelligence with no per-seat fees. Your data stays local, your models stay yours." |
| Curious users | "Imagine if ChatGPT remembered everything from your last conversation — and ran entirely on your computer." |
| Hacker/news crowd | "Open source AI assistant with persistent memory. No cloud dependency. Terminal-native." |

---

## Launch Plan

### Phase 1: Community Preview (NOW)
- Landing page live: benefits + "Coming Soon" signup
- GitHub repo public with docs site deployed
- Telegram channel active for early adopters
- Target: build waitlist, collect feedback on architecture

### Phase 2: Open Beta
- Terminal installer works end-to-end (curl | bash)
- Telegram bridge functional
- Desktop app available
- Blog series: "Building an AI that remembers"
- Target: 100 active self-hosters

### Phase 3: Public Launch
- Full documentation site
- Comparison page (vs ChatGPT, local-only alternatives)
- First-party blog: use cases, benchmarks, architecture deep-dives
- Target: production users, GitHub stars momentum

---

## Content Plan

### Blog topics (human-written, no AI-generated filler):
1. "Why AI assistants lose your context — and how we fixed it"
2. "Self-hosted AI: what you actually save and what it costs"
3. "One command to a smarter terminal: setting up your AI assistant"
4. "How model routing works — picking the right tool without reading a manual"
5. "Memory that doesn't expire: building a knowledge base that grows with you"

### Social content pillars:
- **Tips & tricks** — real workflows people use
- **Before/after** — "here's what you used to do, here's what happens now"
- **Under the hood** — architecture decisions, explained plainly
- **Community wins** — what people are building with it

---

## Competitive Framing (DO NOT publish specifics)

Keep comparisons high-level. Never name competitors' architectures or reveal our internal systems.

| What people use now | What we offer instead |
|---|---|
| Start from scratch every chat | Continuity across sessions |
| One model for everything | Automatic model selection |
| Cloud-only = data leaves your machine | Local-first, cloud-optional |
| Expensive per-token pricing | Use your existing subscriptions |
| Dashboard you never open | Works where you already are |

---

## Visual Direction

- Dark theme, gold accent (#FFD700)
- Terminal screenshots showing real conversations
- Architecture diagrams only if they explain user-facing behavior (never internal systems)
- Photography style: clean, minimal, terminal-focused

---

## Metrics to Track

| Metric | Target (Phase 1) |
|--------|-------------------|
| GitHub stars | 500+ before launch |
| Waitlist signups | 200+ |
| Telegram group members | 100+ |
| Self-hosted installs | 50+ before beta |
| Docs site traffic | 1K pageviews/week |

---

## DO NOT MENTION ON THE WEBSITE

These are our competitive advantages. Keep them internal:
- ❌ Memory Palace architecture
- ❌ Context compression/trimming system
- ❌ Two-track model routing
- ❌ Quality gate chain (Ring, Kimi, Flash, Grok)
- ❌ Shadow reviewer system
- ❌ Agent loop internals
- ❌ Fallback/provider failover logic
- ❌ Any specific model names in architecture context

What's OK: "uses multiple AI models," "runs locally," "remembers across conversations," "open source."

---

## Next Steps
- [ ] Gerald reviews and approves messaging
- [ ] Graphic designer for logo/banner (or use existing assets)
- [ ] Set up analytics on landing page (Plausible or similar)
- [ ] Create GitHub discussion templates for community feedback
- [ ] Draft launch day post for Hacker News / Reddit