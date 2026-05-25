# LumenHub Sprint Plan

## Sprint Structure
- **Sprint duration:** 2 weeks
- **Sprint goal:** Ship functional MVP with core memory management features
- **Review cadence:** End of each sprint with working demo

## Sprint 1: Foundation (Current → Week 2)
### Goals:
1. ✅ Set up dev environment (Win11 VM + Flutter Windows desktop enabled)
2. ✅ Implement SQLite storage with drift (ADR-001)
3. ✅ Port existing MemoryPalette to use new storage backend
4. ✅ CRUD operations for memory items
5. ✅ Zone management (hot/warm/cold/archive)
6. ✅ Tag system

### Deliverables:
- Working app with persistent storage
- All existing UI functional with real database
- Basic import/export

### Success Criteria:
- [ ] App launches on macOS and Windows
- [ ] Can create, read, update, delete memory items
- [ ] Items persist across restarts
- [ ] Search returns correct results
- [ ] Zones visually distinct in MemoryPalette

## Sprint 2: Intelligence (Week 3-4)
### Goals:
1. ✅ Integrate Hermes context orchestrator into app
2. ✅ Relevance scoring via background AI analysis
3. ✅ Auto-tagging using Hermes model routing
4. ✅ Natural language search prototype
5. ✅ Aging/decay algorithm tuned

### Deliverables:
- AI-powered memory scoring
- Auto-generated tags
- Semantic search capability

### Success Criteria:
- [ ] Memory items auto-tagged on creation
- [ ] Relevance scores update based on access patterns
- [ ] NL search returns relevant results
- [ ] Hermes stack fully integrated (not just standalone)

## Sprint 3: Features (Week 5-6)
### Goals:
1. ✅ Memory relationships (graph edges)
2. ✅ Graph visualization component
3. ✅ Settings & preferences
4. ✅ Markdown/HTML export
5. ✅ Cross-platform sync (if Supabase decided in ADR)

### Deliverables:
- Visual knowledge graph
- Configurable preferences
- Shareable exports

### Success Criteria:
- [ ] Can link memory items with typed relationships
- [ ] Graph view renders and is navigable
- [ ] Export generates clean Markdown
- [ ] Settings persist across sessions

## Sprint 4: Polish (Week 7-8)
### Goals:
1. ✅ Spaced repetition system
2. ✅ Performance optimization
3. ✅ Mobile-responsive layouts
4. ✅ Browser extension for web clipping (stretch)
5. ✅ Comprehensive tests

### Deliverables:
- Production-ready V1
- Test suite covering core functionality
- Documentation for users and contributors

## Risk Register
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Win11 VM setup issues | Medium | Medium | Use UTM with ARM64; fallback to Android-only |
| Drift/SQLite complexity | Medium | Low | Start pure SQLite, migrate to drift if needed |
| Hermes integration delays | High | Medium | Integration points defined before sprint start |
| Solo dev burnout | High | Medium | 2-week sprints, clear deliverables, no overcommitment |

## Definition of Done
- Code compiles and runs on target platform(s)
- Feature has automated test or manual test documented
- UI follows existing dark theme design system
- Changes committed and pushed to GitHub
- Memory palace updated with new knowledge