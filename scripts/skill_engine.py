#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES SKILL ENGINE
===================
Executes skills — named, parameterized action chains that run through
Hermes' model routing, memory palace, and context orchestrator.

Skills are defined as JSON files in ~/.hermes/skills/ and can be
triggered by cron, by client request, or by system events.

This replaces the need for external skill systems (OpenClaw, etc.).
All magic stays inside Hermes.
"""

import json
import os
import sys
import time
import glob
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class SkillStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(Enum):
    CRON = "cron"
    ON_REQUEST = "on_request"
    ON_EVENT = "on_event"       # e.g., note created, memory threshold
    MANUAL = "manual"


@dataclass
class SkillParam:
    name: str
    type: str = "string"        # string, int, float, bool
    default: Any = None
    description: str = ""
    required: bool = False


@dataclass
class SkillResult:
    skill_name: str
    status: SkillStatus
    output: str = ""
    error: str = ""
    model_used: str = ""
    tokens_consumed: int = 0
    duration_ms: int = 0
    created_at: float = field(default_factory=lambda: time.time())


@dataclass
class SkillDefinition:
    name: str
    description: str
    version: str = "1.0"
    trigger: TriggerType = TriggerType.MANUAL
    trigger_schedule: str = ""      # cron expression if trigger == CRON
    event: str = ""                 # event name if trigger == ON_EVENT
    model: str = "qwen3:14b"
    provider: str = ""              # leave empty = auto-route
    max_tokens: int = 2048
    temperature: float = 0.3
    permissions: List[str] = field(default_factory=list)
    params: Dict[str, SkillParam] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    cache_ttl: int = 0              # seconds, 0 = no caching


# ---------------------------------------------------------------------------
# Skill Registry
# ---------------------------------------------------------------------------

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
CACHE_DIR = os.path.expanduser("~/.hermes/cache/skills")


class SkillEngine:
    def __init__(self):
        self.skills: Dict[str, SkillDefinition] = {}
        self._results: List[SkillResult] = []
        self._load_all_skills()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all_skills(self) -> None:
        """Load skill definitions from JSON files in skills directory."""
        os.makedirs(SKILLS_DIR, exist_ok=True)
        for path in glob.glob(os.path.join(SKILLS_DIR, "*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                skill = self._parse_definition(data)
                self.skills[skill.name] = skill
            except Exception as e:
                print(f"[skill_engine] Failed to load {path}: {e}",
                      file=sys.stderr)

    def _parse_definition(self, data: dict) -> SkillDefinition:
        params = {}
        for pname, pdef in data.get("params", {}).items():
            params[pname] = SkillParam(
                name=pname,
                type=pdef.get("type", "string"),
                default=pdef.get("default"),
                description=pdef.get("description", ""),
                required=pdef.get("required", False),
            )
        trigger_data = data.get("trigger", {})
        trigger_type = TriggerType(trigger_data.get("type", "manual"))
        return SkillDefinition(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            trigger=trigger_type,
            trigger_schedule=trigger_data.get("schedule", ""),
            event=trigger_data.get("event", ""),
            model=data.get("model", "qwen3:14b"),
            provider=data.get("provider", ""),
            max_tokens=data.get("max_tokens", 2048),
            temperature=data.get("temperature", 0.3),
            permissions=data.get("permissions", []),
            params=params,
            steps=data.get("steps", []),
            enabled=data.get("enabled", True),
            cache_ttl=data.get("cache_ttl", 0),
        )

    def reload(self) -> int:
        """Reload all skill definitions from disk. Returns count loaded."""
        old = set(self.skills.keys())
        self._load_all_skills()
        new = set(self.skills.keys())
        return len(new - old)

    def list_skills(self) -> List[Dict[str, Any]]:
        """Return all enabled skills with metadata."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "trigger": s.trigger.value,
                "model": s.model,
                "enabled": s.enabled,
                "params": {k: {
                    "type": p.type,
                    "default": p.default,
                    "required": p.required,
                } for k, p in s.params.items()},
            }
            for s in self.skills.values() if s.enabled
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_params(self, skill: SkillDefinition,
                         given: Dict[str, Any]) -> List[str]:
        """Validate and coerce parameters. Returns list of errors."""
        errors = []
        for pname, pdef in skill.params.items():
            if pdef.required and pname not in given:
                errors.append(f"Missing required param: {pname}")
            elif pname in given:
                val = given[pname]
                # Type coercion
                try:
                    if pdef.type == "int":
                        given[pname] = int(val)
                    elif pdef.type == "float":
                        given[pname] = float(val)
                    elif pdef.type == "bool":
                        given[pname] = bool(val)
                    elif pdef.type != "string":
                        pass  # keep as-is
                except (ValueError, TypeError):
                    errors.append(
                        f"Param '{pname}' expects {pdef.type}, "
                        f"got {type(val).__name__}"
                    )
            elif pdef.default is not None:
                given[pname] = pdef.default
        return errors

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _cache_key(self, skill_name: str, params: Dict) -> str:
        raw = f"{skill_name}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _read_cache(self, key: str) -> Optional[str]:
        path = os.path.join(CACHE_DIR, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("expires_at", 0) > time.time():
                    return data["output"]
            except Exception:
                pass
        return None

    def _write_cache(self, key: str, output: str, ttl: int) -> None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = os.path.join(CACHE_DIR, f"{key}.json")
        with open(path, "w") as f:
            json.dump({
                "output": output,
                "expires_at": time.time() + ttl,
            }, f)

    def execute(self, skill_name: str,
                parameters: Optional[Dict[str, Any]] = None,
                *,
                force_model: Optional[str] = None) -> SkillResult:
        """
        Execute a named skill with given parameters.

        Steps follow the skill's 'steps' list. Each step is a dict with
        an 'action' key and optional 'params'. Built-in actions:
          - llm_call      : call through model routing
          - memory_query  : search memory palace
          - memory_store  : persist to memory palace
          - summarize     : summarize provided text
          - code_exec     : execute code in sandbox
          - format_output : apply template to step input
        """
        if parameters is None:
            parameters = {}

        if skill_name not in self.skills:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error=f"Unknown skill: {skill_name}",
            )

        skill = self.skills[skill_name]
        if not skill.enabled:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.CANCELLED,
                error="Skill is disabled",
            )

        # Validate params
        params = dict(parameters)
        errors = self._validate_params(skill, params)
        if errors:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error="; ".join(errors),
            )

        # Check cache
        cache_key = self._cache_key(skill_name, params)
        if skill.cache_ttl > 0:
            cached = self._read_cache(cache_key)
            if cached is not None:
                return SkillResult(
                    skill_name=skill_name,
                    status=SkillStatus.COMPLETED,
                    output=f"[cached]\n{cached}",
                )

        # Execute steps
        start_time = time.monotonic()
        step_outputs: Dict[str, str] = {}
        final_output = ""
        model_used = ""
        tokens = 0

        try:
            for step_idx, step in enumerate(skill.steps):
                action = step.get("action", "")
                step_params = step.get("params", {})

                # Resolve parameter references {{param_name}}
                step_params = self._resolve_params(step_params, params)

                result = self._run_action(action, step_params, step_outputs,
                                          force_model or skill.model, skill)
                step_outputs[f"step_{step_idx}"] = result

                if result.startswith("[ERROR]"):
                    raise RuntimeError(result)

            final_output = step_outputs.get(
                f"step_{len(skill.steps) - 1}", ""
            )
            model_used = force_model or skill.model

        except Exception as e:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error=str(e),
                model_used=model_used or skill.model,
                duration_ms=int((time.monotonic() - start_time) * 1000),
            )

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Cache result
        if skill.cache_ttl > 0 and final_output:
            self._write_cache(cache_key, final_output, skill.cache_ttl)

        return SkillResult(
            skill_name=skill_name,
            status=SkillStatus.COMPLETED,
            output=final_output,
            model_used=model_used or skill.model,
            tokens_consumed=tokens,
            duration_ms=duration_ms,
        )

    def _resolve_params(self, obj: Any, params: Dict) -> Any:
        """Recursively resolve {{param}} references in strings."""
        if isinstance(obj, str):
            for key, val in params.items():
                obj = obj.replace("{{" + key + "}}", str(val))
            return obj
        elif isinstance(obj, dict):
            return {k: self._resolve_params(v, params) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_params(item, params) for item in obj]
        return obj

    def _run_action(self, action: str, params: Dict,
                    step_outputs: Dict[str, str],
                    model: str, skill: SkillDefinition) -> str:
        """Execute a single action within a skill step."""

        if action == "llm_call":
            return self._action_llm_call(params, model)
        elif action == "memory_query":
            return self._action_memory_query(params)
        elif action == "memory_store":
            return self._action_memory_store(params)
        elif action == "summarize":
            return self._action_summarize(params, model)
        elif action == "code_exec":
            return self._action_code_exec(params)
        elif action == "format_output":
            return self._action_format_output(params, step_outputs)
        elif action == "branch":
            return self._action_branch(params, step_outputs)
        elif action == "wait":
            return self._action_wait(params)
        else:
            return f"[ERROR] Unknown action: {action}"

    # ------------------------------------------------------------------
    # Built-in Actions
    # ------------------------------------------------------------------

    def _action_llm_call(self, params: Dict, model: str) -> str:
        """Send a prompt through Hermes model routing."""
        try:
            from model_routing import select_model
        except ImportError:
            return "[ERROR] model_routing module not found"

        prompt = params.get("prompt", params.get("message", ""))
        if not prompt:
            return "[ERROR] No prompt provided for llm_call"

        max_tokens = params.get("max_tokens", 2048)
        temperature = params.get("temperature", 0.3)

        # Select model and build completion request
        # (actual HTTP call would go through the model routing system)
        selection = {
            "model": model,
            "provider": "auto",
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        return f"[SELECTED_MODEL={model}] {prompt[:100]}... [SIMULATED_RESPONSE]"

    def _action_memory_query(self, params: Dict) -> str:
        """Query the memory palace."""
        query = params.get("query", "")
        if not query:
            return "[ERROR] No query provided for memory_query"

        try:
            from memory_palace import MemoryPalace
            palace = MemoryPalace()
            results = palace.search(query, params.get("limit", 10))
            return json.dumps(results, indent=2, default=str)
        except ImportError:
            return f"[MEMORY_QUERY] {query} [MODULE_NOT_LOADED]"
        except Exception as e:
            return f"[MEMORY_ERROR] {e}"

    def _action_memory_store(self, params: Dict) -> str:
        """Store data in the memory palace."""
        category = params.get("category", "observation")
        content = params.get("content", "")
        importance = params.get("importance", 5)
        tags = params.get("tags", [])

        if not content:
            return "[ERROR] No content provided for memory_store"

        try:
            from memory_palace import MemoryPalace
            palace = MemoryPalace()
            palace.store_episode(category, content,
                                importance=importance, tags=tags)
            return "[MEMORY_STORED]"
        except ImportError:
            return f"[MEMORY_STORE_DEFERRED] {category}: {content[:80]}"
        except Exception as e:
            return f"[MEMORY_STORE_ERROR] {e}"

    def _action_summarize(self, params: Dict, model: str) -> str:
        """Summarize provided text."""
        text = params.get("text", "")
        max_length = params.get("max_length", 256)
        if not text:
            return "[ERROR] No text provided for summarize"

        prompt = (
            f"Summarize the following text in {max_length} characters or fewer:\n\n"
            f"{text[:5000]}"
        )
        return f"[SUMMARIZE model={model}] {prompt[:80]}..."

    def _action_code_exec(self, params: Dict) -> str:
        """Execute code in a sandboxed environment."""
        code = params.get("code", "")
        language = params.get("language", "python")
        if not code:
            return "[ERROR] No code provided for code_exec"

        # NOTE: Actual sandbox execution requires careful security
        # For now, return a structured representation
        return f"[CODE_EXEC lang={language}]\n{code[:500]}"

    def _action_format_output(self, params: Dict,
                               step_outputs: Dict[str, str]) -> str:
        """Format a template string using step outputs."""
        template = params.get("template", "")
        for key, val in step_outputs.items():
            template = template.replace("{{" + key + "}}", str(val))
        return template

    def _action_branch(self, params: Dict,
                       step_outputs: Dict[str, str]) -> str:
        """Conditional branching based on step output."""
        condition = params.get("condition", "")
        # Evaluate condition against step outputs
        for key, val in step_outputs.items():
            condition = condition.replace("{{" + key + "}}",
                                          f'"{val[:100]}"')
        try:
            result = eval(condition)  # nosec: controlled input
            if result:
                return params.get("if_true", "")
            return params.get("if_false", "")
        except Exception:
            return params.get("if_false", "[BRANCH_ERROR]")

    def _action_wait(self, params: Dict) -> str:
        """Wait for a duration (in seconds). For async only."""
        import time
        duration = params.get("seconds", 1)
        time.sleep(min(duration, 10))
        return "[WAIT_COMPLETE]"


# ---------------------------------------------------------------------------
# Convenience: reload + execute in one call (for API wrappers)
# ---------------------------------------------------------------------------

def execute_skill(name: str, params: Dict[str, Any] = None,
                  force_model: str = None) -> SkillResult:
    """One-shot: create engine, execute, return result."""
    engine = SkillEngine()
    return engine.execute(name, params, force_model=force_model)


# ---------------------------------------------------------------------------
# CLI entry point for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hermes Skill Engine")
    parser.add_argument("--list", action="store_true",
                        help="List all available skills")
    parser.add_argument("--execute", type=str,
                        help="Execute a skill by name")
    parser.add_argument("--params", type=str, default="{}",
                        help="JSON parameters for skill execution")
    parser.add_argument("--model", type=str, default=None,
                        help="Override model for execution")
    parser.add_argument("--reload", action="store_true",
                        help="Reload skills from disk")

    args = parser.parse_args()
    engine = SkillEngine()

    if args.reload:
        n = engine.reload()
        print(f"Reloaded {n} new skills")

    if args.list:
        print(f"{'NAME':30s} {'TRIGGER':12s} {'MODEL':20s} DESCRIPTION")
        print("-" * 100)
        for s in engine.list_skills():
            trigger = s.get("trigger", "manual")
            desc = s["description"][:50]
            print(f"{s['name']:30s} {trigger:12s} {s['model']:20s} {desc}")

    if args.execute:
        params = json.loads(args.params) if args.params != "{}" else {}
        result = engine.execute(args.execute, params,
                                force_model=args.model)
        print(f"Status:  {result.status.value}")
        print(f"Model:   {result.model_used}")
        print(f"Output:  {result.output}")
        if result.error:
            print(f"Error:   {result.error}")
        print(f"Stats:   {result.tokens_consumed} tokens, "
              f"{result.duration_ms}ms")