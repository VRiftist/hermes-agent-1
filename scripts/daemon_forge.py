#!/Users/lumenhubai/.hermes/hermes-agent/venv/bin/python3
"""
HERMES DAEMON FORGING — Create temporary sub-agents for specific tasks
"""

import json
import os
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Optional

DAEMON_DIR = os.path.expanduser("~/.hermes/daemon-templates")
ACTIVE_DAEMONS_DIR = os.path.expanduser("~/.hermes/daemons")


class DaemonForge:
    def __init__(self):
        os.makedirs(DAEMON_DIR, exist_ok=True)
        os.makedirs(ACTIVE_DAEMONS_DIR, exist_ok=True)

    def create_daemon(self, name: str, constitution: str,
                      model_preference: str = "mac-ollama:qwen3:14b",
                      max_turns: int = 20,
                      tool_access: list = None,
                      auto_terminate: bool = True) -> str:
        """
        Create a new daemon with a defined constitution.

        Args:
            name: Daemon identifier
            constitution: Defines the daemon's purpose, behavior, and constraints
            model_preference: Which model to use
            max_turns: Maximum conversation turns before auto-terminate
            tool_access: List of allowed tools (subset of master toolset)
            auto_terminate: Whether to auto-terminate after task completion

        Returns:
            daemon_id: Unique identifier for the daemon
        """
        daemon_id = f"{name}_{uuid.uuid4().hex[:8]}"
        daemon = {
            "id": daemon_id,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "constitution": constitution,
            "model_preference": model_preference,
            "max_turns": max_turns,
            "tool_access": tool_access or ["read", "memory"],
            "auto_terminate": auto_terminate,
            "status": "active",
            "turns_used": 0,
            "output_log": [],
        }

        daemon_path = os.path.join(ACTIVE_DAEMONS_DIR, f"{daemon_id}.json")
        with open(daemon_path, "w") as f:
            json.dump(daemon, f, indent=2)

        return daemon_id

    def execute_daemon(self, daemon_id: str, task: str,
                       context: str = "") -> Dict:
        """Execute a daemon's task and return structured output."""
        daemon_path = os.path.join(ACTIVE_DAEMONS_DIR, f"{daemon_id}.json")

        if not os.path.exists(daemon_path):
            return {"error": f"Daemon {daemon_id} not found"}

        with open(daemon_path, "r") as f:
            daemon = json.load(f)

        if daemon["status"] != "active":
            return {"error": f"Daemon {daemon_id} is {daemon['status']}"}

        if daemon["turns_used"] >= daemon["max_turns"]:
            daemon["status"] = "terminated_max_turns"
            self._save_daemon(daemon)
            return {"error": f"Daemon exceeded max turns ({daemon['max_turns']})",
                    "outputs": daemon["output_log"]}

        # Build the daemon prompt from constitution + task + context
        prompt = f"""{daemon['constitution']}

TASK: {task}

CONTEXT: {context}

Respond strictly within your constitutional boundaries."""

        # Log the execution
        daemon["turns_used"] += 1
        daemon["output_log"].append({
            "turn": daemon["turns_used"],
            "task": task[:100],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if daemon["auto_terminate"]:
            daemon["status"] = "completed"

        self._save_daemon(daemon)

        return {
            "daemon_id": daemon_id,
            "name": daemon["name"],
            "prompt_generated": True,
            "constitution": daemon["constitution"],
            "turns_remaining": daemon["max_turns"] - daemon["turns_used"],
            "status": daemon["status"],
            "prompt": prompt,  # Return for execution by Hermes
        }

    def list_active_daemons(self) -> list:
        """List all active daemons."""
        daemons = []
        for f in os.listdir(ACTIVE_DAEMONS_DIR):
            if f.endswith(".json"):
                with open(os.path.join(ACTIVE_DAEMONS_DIR, f)) as fp:
                    daemons.append(json.load(fp))
        return daemons

    def terminate_daemon(self, daemon_id: str):
        """Terminate a daemon and archive its output."""
        daemon_path = os.path.join(ACTIVE_DAEMONS_DIR, f"{daemon_id}.json")
        if os.path.exists(daemon_path):
            with open(daemon_path, "r") as f:
                daemon = json.load(f)
            daemon["status"] = "terminated"
            daemon["terminated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_daemon(daemon)
            os.remove(daemon_path)
            return {"status": "terminated", "daemon_id": daemon_id}
        return {"error": f"Daemon {daemon_id} not found"}

    def _save_daemon(self, daemon: Dict):
        daemon_path = os.path.join(ACTIVE_DAEMONS_DIR, f"{daemon['id']}.json")
        with open(daemon_path, "w") as f:
            json.dump(daemon, f, indent=2)


# Pre-built daemon templates
DAEMON_TEMPLATES = {
    "code_reviewer": {
        "constitution": """You are a meticulous code reviewer. Your job is to:
1. Find bugs, edge cases, and performance issues
2. Check for security vulnerabilities
3. Ensure code follows best practices
4. Be specific — reference exact lines and suggest fixes
5. Rate severity of issues: CRITICAL / HIGH / MEDIUM / LOW
Do NOT write new code unless asked. Focus on analysis.""",
        "model": "deepseek:deepseek-v4-pro",
        "tool_access": ["read", "memory"],
    },
    "security_auditor": {
        "constitution": """You are a security auditor. Your job is to:
1. Identify security vulnerabilities in code, configs, and architecture
2. Check for PII exposure, key leaks, and auth issues
3. Assess threat vectors and attack surfaces
4. Prioritize findings by exploitability and impact
Be paranoid. When in doubt, flag it.""",
        "model": "deepseek:deepseek-v4-pro",
        "tool_access": ["read", "memory"],
    },
    "architect": {
        "constitution": """You are a system architect. Your job is to:
1. Design scalable, maintainable system architectures
2. Identify coupling, bottlenecks, and single points of failure
3. Propose alternatives with tradeoff analysis
4. Think 3 moves ahead — what breaks when X changes?
5. Always provide a concrete implementation plan
Focus on long-term sustainability over quick fixes.""",
        "model": "x-ai:grok-4.20-reasoning",
        "tool_access": ["read", "memory", "web"],
    },
    "research_assistant": {
        "constitution": """"You are a research assistant. Your job is to:
1. Gather comprehensive information from web and memory
2. Synthesize findings into clear, structured summaries
3. Identify gaps in available information
4. Cross-reference multiple sources
5. Distinguish facts from opinions/speculation
Be thorough. Depth over speed.""",
        "model": "linux-ollama:qwen3-14b-128k",
        "tool_access": ["read", "memory", "web", "terminal"],
    },
}


def forge_from_template(template_name: str, custom_constitution: str = "") -> str:
    """Create a daemon from a pre-built template."""
    forge = DaemonForge()
    template = DAEMON_TEMPLATES.get(template_name)

    if not template:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(DAEMON_TEMPLATES.keys())}")

    constitution = custom_constitution if custom_constitution else template["constitution"]

    return forge.create_daemon(
        name=template_name,
        constitution=constitution,
        model_preference=template["model"],
        tool_access=template["tool_access"],
    )


if __name__ == "__main__":
    print("Daemon Forging self-test...")
    forge = DaemonForge()

    # Create a code reviewer daemon
    daemon_id = forge.create_daemon(
        name="test_reviewer",
        constitution="You are a code reviewer. Find bugs.",
        model_preference="mac-ollama:qwen3:14b",
        max_turns=5,
    )
    print(f"  Created daemon: {daemon_id}")

    # Execute it
    result = forge.execute_daemon(daemon_id, "Review this code: def foo(): pass", "")
    print(f"  Execution: turns_used={forge.ACTIVE_DAEMONS_DIR}")
    print(f"  Status: {result.get('status')}")

    # List active
    active = forge.list_active_daemons()
    print(f"  Active daemons: {len(active)}")

    # Test template forge
    template_id = forge_from_template("code_reviewer")
    print(f"  Template daemon: {template_id}")

    print("Daemon Forging ready. ✅")