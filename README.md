# caldera-mcp

MCP server for [MITRE Caldera](https://caldera.mitre.org/) adversary emulation platform.

Connects any MCP-compatible AI client (Claude, Cursor, VS Code, etc.) to a running Caldera instance. Build attack scenarios from natural language, inspect connected agents, and manage operations — all through conversation.

> **Important:** This tool connects an AI to a live adversary emulation platform. Only point it at Caldera instances you own and are authorized to operate. Always review scope before executing any operation.

---

## Tools (17)

| Group | Tools |
|---|---|
| Health | `caldera_health_check` |
| Agents | `caldera_list_agents`, `caldera_get_agent` |
| Abilities | `caldera_list_abilities`, `caldera_get_ability`, `caldera_create_ability`, `caldera_delete_ability` |
| Adversaries | `caldera_list_adversaries`, `caldera_get_adversary`, `caldera_create_adversary`, `caldera_update_adversary`, `caldera_delete_adversary` |
| Operations | `caldera_list_operations`, `caldera_get_operation`, `caldera_create_operation`, `caldera_set_operation_state`, `caldera_get_operation_results`, `caldera_delete_operation` |

Key behaviors:
- `caldera_list_abilities` supports filters: `technique_id`, `tactic`, `platform`
- `caldera_create_operation` defaults to `state="paused"` — operations never start automatically
- Input validation enforced on technique IDs (ATT&CK format), platforms, and executors

---

## Requirements

- Python 3.12+ **or** Docker
- A running [MITRE Caldera](https://github.com/mitre/caldera) instance (v5.x)
- The Caldera red team API key

---

## Installation

### uvx — zero install (recommended)

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

```bash
CALDERA_URL=http://my-caldera:8888 \
CALDERA_API_KEY=your-red-api-key \
uvx caldera-mcp
```

### pip

```bash
pip install caldera-mcp
CALDERA_URL=http://my-caldera:8888 CALDERA_API_KEY=your-red-api-key caldera-mcp
```

### Docker (SSE / server mode)

```bash
docker run --rm \
  -e CALDERA_URL=http://my-caldera:8888 \
  -e CALDERA_API_KEY=your-red-api-key \
  -p 8081:8081 \
  ghcr.io/cowboy-samurai/caldera-mcp \
  --transport sse
```

---

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `CALDERA_API_KEY` | Yes | — | Caldera red team API key |
| `CALDERA_URL` | No | `http://localhost:8888` | Caldera server base URL |

The red team API key can be found in your Caldera config (`conf/local.yml` → `api_key_red`), or in the container logs if auto-generated.

---

## MCP client setup

### Claude Code

Add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "caldera": {
      "command": "uvx",
      "args": ["caldera-mcp"],
      "env": {
        "CALDERA_URL": "http://my-caldera:8888",
        "CALDERA_API_KEY": "your-red-api-key"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "caldera": {
      "command": "uvx",
      "args": ["caldera-mcp"],
      "env": {
        "CALDERA_URL": "http://my-caldera:8888",
        "CALDERA_API_KEY": "your-red-api-key"
      }
    }
  }
}
```

### SSE mode (remote Caldera)

If your Caldera instance is remote and you want the MCP server to run as a persistent process:

```bash
caldera-mcp --transport sse --host 127.0.0.1 --port 8081
```

Then configure your client to connect via SSE:

```json
{
  "mcpServers": {
    "caldera": {
      "type": "sse",
      "url": "http://localhost:8081/sse"
    }
  }
}
```

---

## Usage examples

Once connected, talk to your AI client naturally:

```
List all alive agents
```
```
Find abilities for T1059.001 on Windows
```
```
Create an adversary from these techniques: T1566.001, T1059.001, T1003.001
```
```
What operations are currently running?
```

> Operations created through this server default to `paused` state. Always review scope — techniques, commands, and targeted hosts — before resuming any operation.

---

## License

[Apache 2.0](LICENSE)
