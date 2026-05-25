# Endpoint Validation — 2026-05-25

## Summary: 4/7 endpoints live

| Provider | Status | Detail | Latency |
|----------|--------|--------|---------|
| OpenRouter (Ring 256K) | ✅ | Found 357 models, Ring models: ['inclusionai/ring-2.6-1t', 'inclusionai/ling-2.6 | 0.17s |
| DeepSeek Pro | ✅ | Response: Hello! How can I | 1.24s |
| Anthropic (Claude) | ❌ | HTTP Error 404: Not Found | 0.51s |
| Kimi K2 | ❌ | HTTP Error 401: Unauthorized | 1.53s |
| xAI (Grok 4.20) | ✅ | Response: Hi


\confidence{90} | 2.82s |
| Firecrawl | ❌ | HTTP Error 404: Not Found | 0.16s |
| Brave Search | ✅ | Found 0 results for 'hello' | 0.7s |

## Failed Endpoints

- **Anthropic (Claude)**: HTTP Error 404: Not Found
- **Kimi K2**: HTTP Error 401: Unauthorized
- **Firecrawl**: HTTP Error 404: Not Found
