# LumenHub Product Architecture

## Current State
- Seed/prototype: 3 source files, 368 lines
- MemoryPalette UI with relevance scoring
- Hermes agent infrastructure (9/13 layers)

## Architecture Decisions (ADRs)

| # | Decision | Status |
|---|----------|--------|
| ADR-001 | Storage: SQLite + drift (local-first, FTS5) | PROPOSED |
| ADR-002 | AI: Phased (passive → active → conversational) | PROPOSED |
| ADR-003 | Platform: macOS → Windows → Android → iOS → Web | PROPOSED |
| ADR-004 | MVP: CRUD + zones + tags + search + scoring | PROPOSED |

## MVP Feature Set
1. CRUD memory items
2. Zone mgmt (hot/warm/cold/archive)
3. Tag system
4. FTS search
5. Relevance scoring
6. Dark theme
7. SQLite persistence
8. Import/export JSON

## Open Questions
1. Naming: memory items vs notes vs cards vs contexts?
2. Relationship types?
3. Graph view priority?
4. AI opt-in or always-on?
5. Monetization model?
6. Encryption for cloud sync?
