## KIMI Integration Plan

### Current Status
- KIMI (Moonshot AI) account exists but API key has returned 401
- Cold standby in fallack chain
- User has offered to send key — must resend

### When KIMI Arrives: Technical Integration

1. **Add to config.yaml:**
```yaml
kimi:
  api_key: ${KIMI_API_KEY}
  base_url: https://api.moonshot.cn/v1
  models:
    kimi-v1-8k:
      context_length: 8192
```

2. **Add to fallback chain (in model_routing.py):**
```python
PREFERENCE_ORDER = [
    "qwen3:8b", "qwen3:14b", "qwen3-coder:30b-a3b",
    "deepseek-v4-flash", "grok-4.20-reasoning",
    "kimi-v1-8k",  # New — between Grok and Ring
    "ring-2.6-1t"
]
```

3. **Define role in routing matrix:**
   - **Primary:** Creative/UX tasks, aesthetic review
   - **Secondary:** Analysis tasks (competing with Grok for position)
   - **Differentiator:** Best-in-class for Chinese language, long-form creative

4. **Add quality gate checks:**
   - Health check on startup and daily via Night Council
   - Auto-failover if 401 persists

### Marketing Integration

#### "Creative Mode" Feature Tier
- KIMI access unlocks "Creative Mode" in Pro tier
- Features: aesthetic review, design suggestions, tone matching
- Marketing: "Powered by 5 AI models including KIMI"

#### Website Launch Stories
- "Our 5th AI model just arrived from Moonshot"
- "Now the most AI-dense PKM in existence"

### Key Considerations
- KIMI's 8K context is smaller than competitors — use for creative tasks, not long research
- Chinese language capability is unique in our stack — market to bilingual users
- Keep cold standby if key issues recur — not blocking launch

### Activation Checklist
- [ ] Receive valid API key from user
- [ ] Add to .env vault and config.yaml
- [ ] Update model_routing.py PREFERENCE_ORDER + CATEGORY_BEST
- [ ] Validate with health check
- [ ] Update marketing materials
- [ ] Announce KIMI integration as feature update