"""Intelligence layer — pipes data through claude -p for chief-of-staff reasoning."""

import json
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

CHIEF_OF_STAFF_PROMPT = """You are a Virtual Chief of Staff.

Your role is to prioritize, connect dots across services, and suggest actions. You are strategic, not tactical.

Rules:
1. ALWAYS lead with "The One Thing" — a single sentence about the most important item right now.
2. Prioritize by: client relationships > revenue-impacting items > deadlines > commitments > everything else.
3. Connect signals across services (email + calendar + drive + notion = actionable insight).
4. Suggest specific next actions with the exact `g` CLI command to execute them.
5. Be concise. No filler. Every sentence earns its place.
6. Flag stale follow-ups and unmet commitments.
7. When in doubt, surface it — better to over-inform than to miss something important.

Output format: Clean text, use emoji headers sparingly (📅 📧 ✅ 📁 📤), bullet points for items.
"""


def _build_system_prompt(config: dict) -> str:
    """Build system prompt, personalizing with config if available."""
    prompt = CHIEF_OF_STAFF_PROMPT
    owner = config.get("owner_name")
    if owner:
        prompt = prompt.replace("You are a Virtual Chief of Staff.",
                                f"You are a Virtual Chief of Staff for {owner}.")
    return prompt


def call_claude(prompt: str, context: str, model: str = "default", timeout: int = 120, config: dict = None) -> str:
    """Call claude -p with the chief-of-staff system prompt and context.

    Args:
        prompt: The specific instruction (e.g., "Generate morning briefing").
        context: Pre-fetched data from Google Workspace and Notion.
        model: Model to use ("haiku", "sonnet", "default").
        timeout: Subprocess timeout in seconds.

    Returns:
        Claude's response text.
    """
    system_prompt = _build_system_prompt(config or {})
    full_prompt = f"{system_prompt}\n\n---\n\nDATA:\n{context}\n\n---\n\nINSTRUCTION: {prompt}"

    cmd = ["claude", "-p"]
    if model != "default":
        cmd.extend(["--model", model])

    # Must unset CLAUDECODE to avoid nested session guard
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"claude -p timed out after {timeout}s")

    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr.strip()}")

    return result.stdout.strip()
