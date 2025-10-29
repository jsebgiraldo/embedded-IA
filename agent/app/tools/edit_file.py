from pathlib import Path

def read_file(path: str):
    """Read a file from workspace"""
    fp = Path("/workspace") / path
    return fp.read_text(encoding="utf-8")

def write_file(path: str, content: str):
    """Write content to a file in workspace"""
    fp = Path("/workspace") / path
    fp.write_text(content, encoding="utf-8")
    return f"File written: {path} ({len(content)} bytes)"
