"""caldera-mcp: MCP server for MITRE Caldera adversary emulation platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("caldera-mcp")
except PackageNotFoundError:
    __version__ = "unknown"
