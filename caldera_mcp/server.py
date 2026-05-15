#!/usr/bin/env python3
"""
Caldera MCP Server
──────────────────
Exposes MITRE Caldera platform tools via the Model Context Protocol (MCP).

Supports two transports:
  stdio  — default; for Claude Desktop, Claude Code, VS Code, and other local clients
  sse    — HTTP/SSE server mode; for remote or containerized deployments

Environment variables:
  CALDERA_URL        — Caldera server base URL (default: http://localhost:8888)
  CALDERA_API_KEY    — Caldera red team API key (required)

Usage:
  caldera-mcp                                          # stdio (default)
  caldera-mcp --transport sse --host 0.0.0.0 --port 8081  # SSE server mode
"""

import argparse
import os
import sys

from fastmcp import FastMCP

from caldera_mcp.tools.health import health_check
from caldera_mcp.tools.agents import list_agents, get_agent
from caldera_mcp.tools.content import (
    list_abilities,
    get_ability,
    create_ability,
    delete_ability,
    list_adversaries,
    get_adversary,
    create_adversary,
    update_adversary,
    delete_adversary,
)
from caldera_mcp.tools.operations import (
    list_operations,
    get_operation,
    create_operation,
    set_operation_state,
    get_operation_results,
    delete_operation,
)

# ─────────────────────────────────────────────────────────────────────────────
# MCP Server
# ─────────────────────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="Caldera",
    instructions=(
        "You are connected to a MITRE Caldera adversary emulation platform. "
        "Use these tools to build attack scenarios (abilities and adversaries), "
        "inspect connected agents, and manage operations. "
        "Operations should be created in 'paused' state by default — always perform "
        "a scope review and get explicit user confirmation before resuming. "
        "When building adversaries from STIX bundles or natural language descriptions, "
        "call list_abilities first to find existing abilities for the target techniques "
        "before creating new ones."
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def caldera_health_check() -> str:
    """
    Verify that the Caldera server is reachable and return version information.

    Returns:
        JSON string with server health status and version details.
    """
    return health_check()


# ─────────────────────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def caldera_list_agents(platform: str = "", alive_only: bool = False) -> str:
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
    return list_agents(platform, alive_only)


@mcp.tool()
def caldera_get_agent(paw: str) -> str:
    """
    Get full details for a specific agent by its PAW identifier.

    Args:
        paw: The agent's PAW (unique identifier assigned by Caldera).

    Returns:
        JSON string with full agent details including alive status.
    """
    return get_agent(paw)


# ─────────────────────────────────────────────────────────────────────────────
# Abilities
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def caldera_list_abilities(
    technique_id: str = "",
    tactic: str = "",
    platform: str = "",
) -> str:
    """
    List available abilities in Caldera, with optional filters.

    Useful for finding what abilities already exist before creating new ones,
    or for mapping ATT&CK technique IDs to Caldera ability IDs when building
    an adversary from a STIX bundle.

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
    return list_abilities(technique_id, tactic, platform)


@mcp.tool()
def caldera_get_ability(ability_id: str) -> str:
    """
    Get full details for a single ability including all executors and commands.

    Args:
        ability_id: The Caldera ability UUID.

    Returns:
        JSON string with the full ability object.
    """
    return get_ability(ability_id)


@mcp.tool()
def caldera_create_ability(
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
    return create_ability(
        name, tactic, technique_id, technique_name,
        platform, executor, command, description, timeout,
    )


@mcp.tool()
def caldera_delete_ability(ability_id: str) -> str:
    """
    Delete an ability from Caldera by its ID.

    Args:
        ability_id: The Caldera ability UUID to delete.

    Returns:
        Confirmation string.
    """
    return delete_ability(ability_id)


# ─────────────────────────────────────────────────────────────────────────────
# Adversaries
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def caldera_list_adversaries() -> str:
    """
    List all adversary profiles in Caldera.

    Returns:
        JSON string with a compact list of adversaries
        (id, name, description, ability count).
    """
    return list_adversaries()


@mcp.tool()
def caldera_get_adversary(adversary_id: str) -> str:
    """
    Get full details for a single adversary profile including ability ordering.

    Args:
        adversary_id: The Caldera adversary UUID.

    Returns:
        JSON string with the full adversary object.
    """
    return get_adversary(adversary_id)


@mcp.tool()
def caldera_create_adversary(
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
    return create_adversary(name, ability_ids, description)


@mcp.tool()
def caldera_update_adversary(
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
    return update_adversary(adversary_id, name, ability_ids, description)


@mcp.tool()
def caldera_delete_adversary(adversary_id: str) -> str:
    """
    Delete an adversary profile from Caldera.

    Args:
        adversary_id: The Caldera adversary UUID to delete.

    Returns:
        Confirmation string.
    """
    return delete_adversary(adversary_id)


# ─────────────────────────────────────────────────────────────────────────────
# Operations
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def caldera_list_operations() -> str:
    """
    List all operations in Caldera with their current state and progress.

    Returns:
        JSON string with a compact list of operations
        (id, name, state, adversary, progress).
    """
    return list_operations()


@mcp.tool()
def caldera_get_operation(operation_id: str) -> str:
    """
    Get full details for an operation including its execution chain.

    Args:
        operation_id: The Caldera operation ID.

    Returns:
        JSON string with the full operation object including chain results.
    """
    return get_operation(operation_id)


@mcp.tool()
def caldera_create_operation(
    name: str,
    adversary_id: str,
    group: str = "",
    state: str = "paused",
) -> str:
    """
    Create a new operation in Caldera.

    Operations are created in 'paused' state by default — always perform
    scope review and get explicit user confirmation before resuming execution.

    Args:
        name:         Human-readable operation name.
        adversary_id: UUID of the adversary profile to run.
        group:        Agent group to target (leave empty for all connected agents).
        state:        Initial state — 'paused' (default) or 'running'.

    Returns:
        JSON string with the created operation including its operation ID.
    """
    return create_operation(name, adversary_id, group, state)


@mcp.tool()
def caldera_set_operation_state(operation_id: str, state: str) -> str:
    """
    Change the state of an existing operation.

    Valid transitions:
      paused  → running   (resume execution)
      running → paused    (pause execution)
      running → stop      (terminate cleanly)

    Args:
        operation_id: The Caldera operation ID.
        state:        Target state — 'running', 'paused', or 'stop'.

    Returns:
        JSON string with the updated operation state.
    """
    return set_operation_state(operation_id, state)


@mcp.tool()
def caldera_get_operation_results(operation_id: str) -> str:
    """
    Get a structured summary of operation execution results.

    Args:
        operation_id: The Caldera operation ID.

    Returns:
        JSON string with execution summary and per-ability results.
    """
    return get_operation_results(operation_id)


@mcp.tool()
def caldera_delete_operation(operation_id: str) -> str:
    """
    Delete an operation from Caldera.

    Args:
        operation_id: The Caldera operation ID to delete.

    Returns:
        Confirmation string.
    """
    return delete_operation(operation_id)


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MCP server for MITRE Caldera adversary emulation platform",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (SSE mode only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8081,
        help="Bind port (SSE mode only)",
    )
    args = parser.parse_args()

    if not os.getenv("CALDERA_API_KEY"):
        print("ERROR: CALDERA_API_KEY environment variable must be set", file=sys.stderr)
        sys.exit(1)

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
