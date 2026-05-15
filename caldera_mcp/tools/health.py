#!/usr/bin/env python3
"""
Health and connectivity tools for the Caldera MCP server.
"""

import json

from caldera_mcp.caldera_client import CalderaClient


def health_check() -> str:
    """
    Verify that the Caldera server is reachable and return version information.

    Returns:
        JSON string with server health status and version details.
    """
    client = CalderaClient()
    try:
        data = client.get("/api/v2/health")
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "unreachable"})
