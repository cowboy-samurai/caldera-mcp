#!/usr/bin/env python3
"""
Agent management tools for the Caldera MCP server.
"""

import json
from datetime import datetime, timezone

from caldera_mcp.caldera_client import CalderaClient

_VALID_PLATFORMS = {"windows", "linux", "darwin"}


def _is_alive(agent: dict) -> bool:
    """Return True if the agent has checked in within 3x its sleep_max window."""
    last_seen_str = agent.get("last_seen", "")
    sleep_max = agent.get("sleep_max", 60)
    if not last_seen_str:
        return False
    try:
        last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - last_seen).total_seconds()
        return age <= sleep_max * 3
    except ValueError:
        return False


def _summarize(agent: dict) -> dict:
    return {
        "paw": agent.get("paw"),
        "host": agent.get("host"),
        "username": agent.get("username"),
        "platform": agent.get("platform"),
        "privilege": agent.get("privilege"),
        "last_seen": agent.get("last_seen"),
        "sleep_min": agent.get("sleep_min"),
        "sleep_max": agent.get("sleep_max"),
        "alive": _is_alive(agent),
        "exe_name": agent.get("exe_name"),
        "pid": agent.get("pid"),
    }


def list_agents(platform: str = "", alive_only: bool = False) -> str:
    """
    List all agents connected to Caldera.

    Args:
        platform:   Optional platform filter — 'windows', 'linux', or 'darwin'.
                    Leave empty to return all platforms.
        alive_only: If True, only return agents that have checked in recently
                    (within 3x their sleep_max interval). Default False.

    Returns:
        JSON string with a list of agents and their status.
    """
    if platform and platform.lower() not in _VALID_PLATFORMS:
        raise ValueError(f"Invalid platform '{platform}'. Must be one of: {', '.join(sorted(_VALID_PLATFORMS))}")
    client = CalderaClient()
    agents = client.get("/api/v2/agents")

    if platform:
        agents = [a for a in agents if a.get("platform", "").lower() == platform.lower()]

    if alive_only:
        agents = [a for a in agents if _is_alive(a)]

    return json.dumps([_summarize(a) for a in agents], indent=2)


def get_agent(paw: str) -> str:
    """
    Get full details for a specific agent by its PAW identifier.

    Args:
        paw: The agent's PAW (unique identifier assigned by Caldera).

    Returns:
        JSON string with full agent details including alive status.
    """
    client = CalderaClient()
    agent = client.get(f"/api/v2/agents/{paw}")
    result = _summarize(agent)
    result["group"] = agent.get("group", "")
    result["trusted"] = agent.get("trusted")
    result["architecture"] = agent.get("architecture")
    result["links"] = len(agent.get("links", []))
    return json.dumps(result, indent=2)
