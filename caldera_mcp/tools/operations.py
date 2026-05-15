#!/usr/bin/env python3
"""
Operation management tools for the Caldera MCP server.

Operations are intentionally kept separate from the safety gate — the
execute-operation Claude skill owns scope review and user confirmation.
These tools are a direct, thin wrapper around the Caldera operations API.
"""

import json

from caldera_mcp.caldera_client import CalderaClient


def list_operations() -> str:
    """
    List all operations in Caldera with their current state and progress.

    Returns:
        JSON string with a compact list of operations
        (id, name, state, adversary, progress).
    """
    client = CalderaClient()
    operations = client.get("/api/v2/operations")

    results = [
        {
            "operation_id": op.get("id"),
            "name": op.get("name"),
            "state": op.get("state"),
            "adversary": op.get("adversary", {}).get("name"),
            "adversary_id": op.get("adversary", {}).get("adversary_id"),
            "abilities_executed": len(op.get("chain", [])),
            "start": op.get("start"),
            "finish": op.get("finish"),
        }
        for op in operations
    ]
    return json.dumps(results, indent=2)


def get_operation(operation_id: str) -> str:
    """
    Get full details for an operation including its execution chain.

    Args:
        operation_id: The Caldera operation ID.

    Returns:
        JSON string with the full operation object including chain results.
    """
    client = CalderaClient()
    op = client.get(f"/api/v2/operations/{operation_id}")
    return json.dumps(op, indent=2)


def create_operation(
    name: str,
    adversary_id: str,
    group: str = "",
    state: str = "paused",
) -> str:
    """
    Create a new operation in Caldera.

    Operations are created in 'paused' state by default so the execute-operation
    skill can perform scope review and get user confirmation before execution
    begins. Pass state='running' only if you have already completed that review.

    Args:
        name:         Human-readable operation name.
        adversary_id: UUID of the adversary profile to run.
        group:        Agent group to target (leave empty to target all connected agents).
        state:        Initial state — 'paused' (default) or 'running'.

    Returns:
        JSON string with the created operation including its operation ID.
    """
    client = CalderaClient()
    body: dict = {
        "name": name,
        "adversary": {"adversary_id": adversary_id},
        "state": state,
    }
    if group:
        body["group"] = group

    result = client.post("/api/v2/operations", body)
    return json.dumps(result, indent=2)


def set_operation_state(operation_id: str, state: str) -> str:
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
    client = CalderaClient()
    result = client.patch(f"/api/v2/operations/{operation_id}", {"state": state})
    return json.dumps({"operation_id": operation_id, "state": result.get("state", state)})


def get_operation_results(operation_id: str) -> str:
    """
    Get a structured summary of operation execution results.

    Returns per-ability success/failure breakdown, exit codes, and output
    from each executed ability in the operation chain.

    Args:
        operation_id: The Caldera operation ID.

    Returns:
        JSON string with execution summary and per-ability results.
    """
    client = CalderaClient()
    op = client.get(f"/api/v2/operations/{operation_id}")

    chain = op.get("chain", [])
    total = len(op.get("adversary", {}).get("atomic_ordering", []))

    abilities = []
    success = timeout = failure = pending = 0

    for link in chain:
        raw_status = link.get("status", -3)

        if raw_status == 0:
            success += 1
            outcome = "success"
        elif raw_status == 124:
            timeout += 1
            outcome = "timeout"
        elif raw_status == -3:
            pending += 1
            outcome = "pending"
        else:
            failure += 1
            outcome = "failure"

        abilities.append({
            "ability_id": link.get("ability", {}).get("ability_id"),
            "name": link.get("ability", {}).get("name"),
            "technique_id": link.get("ability", {}).get("technique_id"),
            "tactic": link.get("ability", {}).get("tactic"),
            "status": raw_status,
            "outcome": outcome,
            "output": link.get("output", ""),
            "collected": link.get("collect"),
            "finished": link.get("finish"),
        })

    summary = {
        "operation_id": operation_id,
        "name": op.get("name"),
        "state": op.get("state"),
        "adversary": op.get("adversary", {}).get("name"),
        "progress": f"{len(chain)}/{total}",
        "results": {
            "success": success,
            "failure": failure,
            "timeout": timeout,
            "pending": pending,
        },
        "abilities": abilities,
    }
    return json.dumps(summary, indent=2)


def delete_operation(operation_id: str) -> str:
    """
    Delete an operation from Caldera.

    Args:
        operation_id: The Caldera operation ID to delete.

    Returns:
        Confirmation string.
    """
    client = CalderaClient()
    client.delete(f"/api/v2/operations/{operation_id}")
    return json.dumps({"deleted": operation_id})
