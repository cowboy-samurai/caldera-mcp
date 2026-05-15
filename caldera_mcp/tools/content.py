#!/usr/bin/env python3
"""
Content authoring tools for the Caldera MCP server.

Covers abilities and adversary profiles — the building blocks for
constructing attack scenarios from natural language or STIX bundles.
"""

import json
import re

from caldera_mcp.caldera_client import CalderaClient

_VALID_PLATFORMS = {"windows", "linux", "darwin"}
_VALID_EXECUTORS = {"psh", "cmd", "sh", "python"}
_TECHNIQUE_ID_RE = re.compile(r"^T\d{4}(\.\d{3})?$", re.IGNORECASE)


def _validate_platform(platform: str) -> None:
    if platform and platform.lower() not in _VALID_PLATFORMS:
        raise ValueError(f"Invalid platform '{platform}'. Must be one of: {', '.join(sorted(_VALID_PLATFORMS))}")


def _validate_technique_id(technique_id: str) -> None:
    if technique_id and not _TECHNIQUE_ID_RE.match(technique_id):
        raise ValueError(f"Invalid ATT&CK technique ID '{technique_id}'. Expected format: T1234 or T1234.001")


# ─────────────────────────────────────────────────────────────────────────────
# Abilities
# ─────────────────────────────────────────────────────────────────────────────

def list_abilities(
    technique_id: str = "",
    tactic: str = "",
    platform: str = "",
) -> str:
    """
    List available abilities in Caldera, with optional filters.

    Args:
        technique_id: Filter by ATT&CK technique ID (e.g. 'T1059.001').
                      Leave empty to return all techniques.
        tactic:       Filter by ATT&CK tactic (e.g. 'execution', 'discovery').
                      Leave empty to return all tactics.
        platform:     Filter by executor platform — 'windows', 'linux', or 'darwin'.
                      Leave empty to return all platforms.

    Returns:
        JSON string with a compact list of matching abilities
        (id, name, tactic, technique_id, platforms).
    """
    _validate_technique_id(technique_id)
    _validate_platform(platform)

    client = CalderaClient()
    abilities = client.get("/api/v2/abilities")

    results = []
    for ab in abilities:
        if technique_id and ab.get("technique_id", "").upper() != technique_id.upper():
            continue
        if tactic and ab.get("tactic", "").lower() != tactic.lower():
            continue

        platforms = list({ex.get("platform", "") for ex in ab.get("executors", [])})

        if platform and platform.lower() not in [p.lower() for p in platforms]:
            continue

        results.append({
            "ability_id": ab.get("ability_id"),
            "name": ab.get("name"),
            "tactic": ab.get("tactic"),
            "technique_id": ab.get("technique_id"),
            "technique_name": ab.get("technique_name"),
            "platforms": platforms,
            "description": ab.get("description", ""),
        })

    return json.dumps(results, indent=2)


def get_ability(ability_id: str) -> str:
    """
    Get full details for a single ability including all executors and commands.

    Args:
        ability_id: The Caldera ability UUID.

    Returns:
        JSON string with the full ability object.
    """
    client = CalderaClient()
    ability = client.get(f"/api/v2/abilities/{ability_id}")
    return json.dumps(ability, indent=2)


def create_ability(
    name: str,
    tactic: str,
    technique_id: str,
    technique_name: str,
    platform: str,
    executor: str,
    command: str,
    description: str = "",
    timeout: int = 60,
) -> str:
    """
    Create a new ability in Caldera.

    Args:
        name:           Human-readable ability name (e.g. 'Dump LSASS memory').
        tactic:         ATT&CK tactic (e.g. 'credential-access', 'discovery').
        technique_id:   ATT&CK technique ID (e.g. 'T1003.001').
        technique_name: ATT&CK technique name (e.g. 'OS Credential Dumping: LSASS Memory').
        platform:       Target platform — 'windows', 'linux', or 'darwin'.
        executor:       Executor name — 'psh' (PowerShell), 'cmd', 'sh', or 'python'.
        command:        The command to execute. Use #{variable} for Caldera facts.
        description:    Optional description of what the ability does.
        timeout:        Execution timeout in seconds (default 60).

    Returns:
        JSON string with the created ability including its generated ability_id.
    """
    _validate_technique_id(technique_id)
    _validate_platform(platform)
    if executor.lower() not in _VALID_EXECUTORS:
        raise ValueError(f"Invalid executor '{executor}'. Must be one of: {', '.join(sorted(_VALID_EXECUTORS))}")

    client = CalderaClient()
    body = {
        "name": name,
        "tactic": tactic,
        "technique_id": technique_id,
        "technique_name": technique_name,
        "description": description,
        "executors": [
            {
                "name": executor,
                "platform": platform,
                "command": command,
                "timeout": timeout,
                "payloads": [],
                "uploads": [],
                "cleanup": [],
                "parsers": [],
            }
        ],
    }
    result = client.post("/api/v2/abilities", body)
    return json.dumps(result, indent=2)


def delete_ability(ability_id: str) -> str:
    """
    Delete an ability from Caldera by its ID.

    Args:
        ability_id: The Caldera ability UUID to delete.

    Returns:
        Confirmation string.
    """
    client = CalderaClient()
    client.delete(f"/api/v2/abilities/{ability_id}")
    return json.dumps({"deleted": ability_id})


# ─────────────────────────────────────────────────────────────────────────────
# Adversaries
# ─────────────────────────────────────────────────────────────────────────────

def list_adversaries() -> str:
    """
    List all adversary profiles in Caldera.

    Returns:
        JSON string with a compact list of adversaries
        (id, name, description, ability count).
    """
    client = CalderaClient()
    adversaries = client.get("/api/v2/adversaries")

    results = [
        {
            "adversary_id": a.get("adversary_id"),
            "name": a.get("name"),
            "description": a.get("description", ""),
            "ability_count": len(a.get("atomic_ordering", [])),
        }
        for a in adversaries
    ]
    return json.dumps(results, indent=2)


def get_adversary(adversary_id: str) -> str:
    """
    Get full details for a single adversary profile including ability ordering.

    Args:
        adversary_id: The Caldera adversary UUID.

    Returns:
        JSON string with the full adversary object.
    """
    client = CalderaClient()
    adversary = client.get(f"/api/v2/adversaries/{adversary_id}")
    return json.dumps(adversary, indent=2)


def create_adversary(
    name: str,
    ability_ids: list[str],
    description: str = "",
) -> str:
    """
    Create a new adversary profile from an ordered list of ability IDs.

    Args:
        name:        Human-readable adversary name (e.g. 'APT29 Credential Access').
        ability_ids: Ordered list of Caldera ability UUIDs.
        description: Optional description of the adversary's TTPs or scenario context.

    Returns:
        JSON string with the created adversary including its generated adversary_id.
    """
    client = CalderaClient()
    body = {
        "name": name,
        "description": description,
        "atomic_ordering": ability_ids,
    }
    result = client.post("/api/v2/adversaries", body)
    return json.dumps(result, indent=2)


def update_adversary(
    adversary_id: str,
    name: str = "",
    ability_ids: list[str] = None,
    description: str = "",
) -> str:
    """
    Update an existing adversary profile.

    Args:
        adversary_id: The Caldera adversary UUID to update.
        name:         New name (leave empty to keep existing).
        ability_ids:  New ordered ability list (leave empty to keep existing).
        description:  New description (leave empty to keep existing).

    Returns:
        JSON string with the updated adversary.
    """
    client = CalderaClient()
    body = {}
    if name:
        body["name"] = name
    if ability_ids is not None:
        body["atomic_ordering"] = ability_ids
    if description:
        body["description"] = description

    result = client.patch(f"/api/v2/adversaries/{adversary_id}", body)
    return json.dumps(result, indent=2)


def delete_adversary(adversary_id: str) -> str:
    """
    Delete an adversary profile from Caldera.

    Args:
        adversary_id: The Caldera adversary UUID to delete.

    Returns:
        Confirmation string.
    """
    client = CalderaClient()
    client.delete(f"/api/v2/adversaries/{adversary_id}")
    return json.dumps({"deleted": adversary_id})
