#!/usr/bin/env python3
"""
AKASHIC ENGINE — Structured Memory Upgrade
Replaces flat 2200-char limit with multi-layer memory system.

Layers:
1. Surface Palace (2200 char): Compressed symbolic state
2. Episodic Layer: Timestamped events with importance scores
3. Semantic Layer: Concept relationships and facts
4. Working Layer: Active session state
5. Mythic Substrate: Narrative structures (quarterly update)
"""

from memory_palace import (
    store_episode, recall_episodes,
    store_fact, recall_facts,
    set_working, get_working,
    get_stats, prune_expired
)


class AkashicEngine:
    def __init__(self):
        self.surface_palace_limit = 2200
        self._surface_cache = None

    def get_surface_palace(self) -> str:
        """Get the compressed symbolic state (top-of-context)."""
        # This is what gets prepended to every session
        working = get_working("active_task") or {}
        stats = get_stats()

        palace = f"""# ACTIVE CONTEXT — SURFACE PALACE
## Who You Are
- Agent: Hermes Operating Mind
- Task: {working.get('task', 'Idle')}
- Phase: {working.get('phase', 'None')}
- Since: {working.get('since', 'Unknown')}

## Powers Available
- 5-model chain (all verified 2026-05-25)
- Consult/merge protocol: active
- Memory palace: {stats['episodic_count']} episodes, {stats['semantic_count']} facts
- Security model: tiered (safe/approved/restricted/forbidden)

## Current Constraints
- Memory budget: {stats['db_size_bytes']} bytes used
- Top priority: coherence over speed
- Operating agreement: foreground=foreground
"""
        return palace[:self.surface_palace_limit]

    def ingest(self, content: str, category: str = "observation",
               session_id: str = None, importance: int = 0,
               tags: list = None):
        """Ingest new information into the memory system."""
        session = session_id or self._current_session()

        # Store as episode
        store_episode(session, category, content,
                      importance=importance, tags=tags or [])

        # Extract facts and store in semantic layer
        facts = self._extract_facts(content)
        for fact in facts:
            store_fact(fact["concept"], fact["description"],
                       confidence=fact.get("confidence", 0.5),
                       source_ids=[session])

    def recall(self, query: str, hours: int = 24,
               category: str = None, limit: int = 20) -> dict:
        """Search across all memory layers."""
        episodes = recall_episodes(hours=hours, category=category,
                                   limit=limit)
        facts = recall_facts(query, limit=limit)

        return {
            "episodes": episodes,
            "facts": facts,
            "surface_palace": self.get_surface_palace(),
        }

    def activate_for_session(self, session_context: dict):
        """Prepare memory for a fresh session."""
        # Set working memory for this session
        set_working("active_task", session_context)

        # Recall recent context
        recent = recall_episodes(hours=24, min_importance=5, limit=10)
        facts = recall_facts("current project", limit=10)

        return {
            "status": "activated",
            "recent_highlights": len(recent),
            "relevant_facts": len(facts),
            "surface_palace": self.get_surface_palace(),
        }

    def _extract_facts(self, text: str) -> list:
        """Extract structured facts from unstructured text."""
        facts = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Skip empty lines and markdown headers
            if not line or line.startswith("#"):
                continue
            # Look for key-value patterns
            if " - " in line or ": " in line:
                facts.append({
                    "concept": line[:80],
                    "description": line[:200],
                    "confidence": 0.6,
                })

        return facts

    def _current_session(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def maintenance(self):
        """Run periodic maintenance: prune expired, compact."""
        deleted = prune_expired()
        stats = get_stats()
        return {
            "deleted_entries": deleted,
            "current_stats": stats,
        }


if __name__ == "__main__":
    print("AKASHIC ENGINE self-test...")
    print("=" * 50)

    engine = AkashicEngine()

    # Ingest test data
    engine.ingest("Project: Build consult/merge protocol. Status: P0 tasks identified.",
                  category="state_change", importance=8, tags=["protocol", "architecture"])

    engine.ingest("Decision: Use SQLite for memory persistence instead of flat files.",
                  category="decision", importance=7, tags=["memory", "persistence"])

    engine.ingest("Observation: All 4 cloud keys verified live. Kimi still dead at 401.",
                  category="observation", importance=5, tags=["keys", "status"])

    # Test surface palace
    palace = engine.get_surface_palace()
    print(f"Surface Palace ({len(palace)} chars):")
    print(palace)
    print()

    # Test recall
    results = engine.recall("protocol architecture")
    print(f"Recall results: {len(results['episodes'])} episodes, {len(results['facts'])} facts")

    # Test session activation
    activation = engine.activate_for_session({"task": "full dev push", "phase": "infrastructure"})
    print(f"Activation: {activation['status']}, {activation['recent_highlights']} highlights")

    # Maintenance
    maint = engine.maintenance()
    print(f"Maintenance: {maint['current_stats']}")

    print("\nAkashic Engine ready. ✅")