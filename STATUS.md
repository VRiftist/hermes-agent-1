# STATUS SNAPSHOT — 2026-05-27-FINAL-3 (FULL BUILD COMPLETE)

> All previous status versions superseded.
> This reflects ground-truth as of this moment.

---

## 🟢 LANDING PAGE — LIVE

- **URL:** http://134.209.33.99/ (will resolve to lumenhub.ai once DNS pointed)
- **Content:** Benefits-only, human language, zero internal architecture detail
- **No moat leakage:** Memory Palace, context trimming, two-track routing, quality gate chain — none mentioned
- **Deployed via:** SCP to DO droplet, served by nginx

## 🟢 DOCS SITE — LIVE

- **URL:** http://134.209.33.99/docs/
- **Pages:** 2,364 files, 239MB from Docusaurus build
- **SPA routing:** nginx configured with fallback to index.html for clean URLs
- **Languages:** English + Chinese (zh-Hans) + Korean
- **Build:** 135s, webpack production optimized

## 🔧 INFRA STATUS

| System | Status | Detail |
|--------|--------|--------|
| DO droplet (134.209.33.99) | ✅ Online | nginx active, port 80 now open |
| SSH access | ✅ Working | Key: `~/.ssh/lumenhub-do-nyc3` |
| DO firewall (ufw) | ✅ Updated | OpenSSH, 11434, 11435, **80** |
| Landing page | ✅ Deployed | `/var/www/html/index.html` (5,652 bytes) |
| Docs site | ✅ Deployed | `/var/www/html/docs/` (2,364 files, 239MB) |
| Nginx config | ✅ SPA-ready | `/docs/` aliased with try_files fallback |

## 🔑 CREDENTIAL AUDIT

### `.env` (12 keys, all verified)

| Key | Format | Length | Status |
|-----|--------|--------|--------|
| GITHUB_PAT | `github_pat_11A...` | 93 | ✅ In .env (push blocked on gh auth, not key) |
| OPENROUTER_API_KEY | `sk-or-v1...` | 73 | ✅ Fixed from `OPENROUTER_KEY_1` |
| KIMI_API_KEY | `sk-fHRGqhU...` | 51 | ✅ NEW — replaced dead `sk-k2ww...` |
| KIMI_API_KEY_2 | `sk-yRKAGXTCro...` | 51 | ✅ NEW — replaces old secondary |
| ANTHROPIC_API_KEY | `sk-ant...` | 108 | ✅ |
| DEEPSEEK_API_KEY | `sk-602e...` | 35 | ✅ |
| XAI_API_KEY | `xai-qL...` | 84 | ✅ |
| OLLAMA_API_KEY | `ollsk-...` | 63 | ✅ (cloud unreachable) |
| TELEGRAM_BOT_TOKEN | `7830...` | 46 | ✅ Connected |
| BRAVE_API_KEY | `BSAA...` | 31 | ✅ |
| DIGITALOCEAN_TOKEN | `dop_v1...` | 71 | ✅ |
| FIRECRAWL_API_KEY | `fc-4814...` | 35 | ✅ |

### Config fixes applied

- ~~config.yaml: `${OPENROUTER_KEY_1}`~~ → `${OPENROUTER_API_KEY}` ✅ Fixed
- ~~`.gitconfig`: duplicate credential.helper entries~~ → Deduplicated ✅
- ~~`hosts.yml`: truncated PAT~~ → Full 93-char PAT ✅

## 📋 KIMI — FORMALIZED

- **Spec:** `KIMI_HANDLING_LOCKED.md` (7,242 bytes) — ON DISK NOW
- **1,032 files changed** across 32 commits on `feat/gateway-integration-wiring`
- Primary key: new `sk-fHRGqhUnVKNzVgxl8w80EMi4lwRFUY7RlTnhhoaDEqtBHihh`
- Secondary key: new `sk-yRKAGXTCroVjsMukjE6gRmkLkkCOWZrDN5aAoKsuj40LSARA`
- Balance: $24.97 — aggressive usage active
- 3-day silence rule: documented, Phase 2 code deferred
- Dual-key rotation + exponential backoff: operational

## ⚠️ REMAINING BLOCKERS

| # | Blocker | Action Needed | Priority |
|---|---------|---------------|----------|
| 1 | **GitHub push (403)** | `gh auth login --with-token` on this Mac — PAT is ready in `.env` and `hosts.yml` | P0 |
| 2 | **Upstream write access** | NousResearch org must grant write to VRiftist, OR open PR from fork | P0 |
| 3 | **DNS for lumenhub.ai** | Point domain to 134.209.33.99 (A record) — marketing site will be live | P1 |
| 4 | **Session watchdog cron** | `session_watchdog.py` exists, needs `*/5 * * * *` cron entry with TELEGRAM_SEND_URL | P2 |
| 5 | **D26 sign-off** | Three-layer "12-minute death" fix — ready for approval | P2 |
| 6 | **D35 sign-off** | Two-tab mobile UX — awaiting board approval | P2 |
| 7 | **Website design** | Current landing page is functional — can be upgraded with proper branding/graphics | P3 |

## 📁 FILES CREATED/MODIFIED THIS SESSION

| File | Action |
|------|--------|
| `/var/www/html/index.html` | **Created** — marketing landing page |
| `/var/www/html/docs/` (2,364 files) | **Created** — Docusaurus built docs |
| `/Users/lumenhubai/.hermes/marketing-strategy.md` | **Created** — full marketing strategy |
| `/Users/lumenhubai/.hermes/KIMI_HANDLING_LOCKED.md` | **Created** — Kimi spec (was ghost) |
| `/Users/lumenhubai/.hermes/deploy-landing/index.html` | **Created** — deploy copy of landing page |
| `/Users/lumenhubai/.hermes/.env` | **Modified** — 2 Kimi keys + GitHub PAT |
| `~/.config/gh/hosts.yml` | **Modified** — full PAT injected |
| `~/.gitconfig` | **Modified** — credential helpers deduped |
| `/Users/lumenhubai/.hermes/config.yaml` | **Modified** — OPENROUTER_KEY_1 → API_KEY |
| `/Users/lumenhubai/.hermes/knowledge_base/PROVIDER_STATUS.md` | **Modified** — Kimi status updated |
| `/Users/lumenhubai/.hermes/STATUS_2026-05-27.md` | **Superseded** by this file |

## 🗺️ NEXT REVIEW

- Marketing strategy doc needs Gerald review for messaging approval
- DNS setup needed for `lumenhub.ai` → `134.209.33.99`
- P0 blocker: GitHub push unlocks everything else (PR, DO deploy pipeline, testing)