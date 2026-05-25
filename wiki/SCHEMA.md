# Wiki Schema

## Structure
- `raw/` — Immutable source material (articles, papers, transcripts)
- `processed/` — Synthesized, interlinked knowledge pages
- `index.md` — Master catalog
- `log.md` — Chronological action log

## Naming Convention
- Files: `kebab-case-descriptive-title.md`
- Prefix with date for time-sensitive: `2026-05-25-topic.md`

## Frontmatter
Every page uses YAML frontmatter:
```yaml
---
title: "Page Title"
date: 2026-05-25
tags: [tag1, tag2]
source: original-url-or-book
---
```

## Cross-referencing
Use `[[page-name]]` for wiki-links. Never broken links.
