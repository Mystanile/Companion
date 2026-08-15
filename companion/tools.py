from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from companion.paths import expand_path, guard_path, load_allowed_roots

ALLOWED_ROOTS = load_allowed_roots([os.path.expanduser("~")])


def set_allowed_roots(raw_roots: list[str]) -> None:
    global ALLOWED_ROOTS
    ALLOWED_ROOTS = load_allowed_roots(raw_roots)


def _ok(message: str, **extra: Any) -> str:
    payload = {"ok": True, "message": message, **extra}
    return json.dumps(payload)


def _err(message: str) -> str:
    return json.dumps({"ok": False, "message": message})


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    webbrowser.open(url, new=2)
    return _ok(f"Opened {url}")


def open_path(path: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    if not target.exists():
        return _err(f"Path does not exist: {target}")
    os.startfile(target)  # type: ignore[attr-defined]
    return _ok(f"Opened {target}")


def open_in_editor(path: str, editor: str = "default") -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    if editor == "default":
        os.startfile(target if target.exists() else target.parent)  # type: ignore[attr-defined]
        return _ok(f"Opened {target} with default app")

    commands = {
        "cursor": ["cursor"],
        "vscode": ["code"],
        "code": ["code"],
    }
    cmd = commands.get(editor.lower())
    if not cmd:
        return _err(f"Unknown editor: {editor}")

    open_target = target if target.exists() else target.parent
    subprocess.Popen([*cmd, str(open_target)], shell=False)
    return _ok(f"Opened {open_target} in {editor}")


def create_folder(path: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    target.mkdir(parents=True, exist_ok=True)
    return _ok(f"Created folder {target}", path=str(target))


def list_directory(path: str = "~") -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    if not target.is_dir():
        return _err(f"Not a directory: {target}")
    entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    lines = [f"{'[dir]' if item.is_dir() else '[file]'} {item.name}" for item in entries[:200]]
    return _ok(f"Listed {target}", entries=lines)


def read_file(path: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    if not target.is_file():
        return _err(f"Not a file: {target}")
    if target.stat().st_size > 500_000:
        return _err("File too large to read (500KB limit)")
    content = target.read_text(encoding="utf-8", errors="replace")
    return _ok(f"Read {target}", content=content)


def write_file(path: str, content: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _ok(f"Wrote {target}", path=str(target))


def append_file(path: str, content: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return _ok(f"Appended to {target}", path=str(target))


def rename_path(old_path: str, new_path: str) -> str:
    source = guard_path(old_path, ALLOWED_ROOTS)
    destination = guard_path(new_path, ALLOWED_ROOTS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.rename(destination)
    return _ok(f"Renamed to {destination}", path=str(destination))


def move_path(source_path: str, destination_path: str) -> str:
    source = guard_path(source_path, ALLOWED_ROOTS)
    destination = guard_path(destination_path, ALLOWED_ROOTS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return _ok(f"Moved to {destination}", path=str(destination))


def copy_path(source_path: str, destination_path: str) -> str:
    source = guard_path(source_path, ALLOWED_ROOTS)
    destination = guard_path(destination_path, ALLOWED_ROOTS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    return _ok(f"Copied to {destination}", path=str(destination))


def delete_path(path: str) -> str:
    target = guard_path(path, ALLOWED_ROOTS)
    if not target.exists():
        return _err(f"Path does not exist: {target}")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return _ok(f"Deleted {target}")


def get_special_folder(name: str) -> str:
    mapping = {
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "downloads": Path.home() / "Downloads",
        "home": Path.home(),
    }
    folder = mapping.get(name.lower())
    if not folder:
        return _err(f"Unknown folder name: {name}. Use desktop, documents, downloads, or home.")
    return _ok(f"Resolved {name}", path=str(folder))


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default browser, usually in a new tab.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_path",
            "description": "Open a file or folder with its default Windows application.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_in_editor",
            "description": "Open a file or folder in Cursor, VS Code, or the default app.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "editor": {
                        "type": "string",
                        "enum": ["default", "cursor", "vscode", "code"],
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a folder and any missing parent folders.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append text to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_path",
            "description": "Rename or move a file/folder within allowed paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_path": {"type": "string"},
                    "new_path": {"type": "string"},
                },
                "required": ["old_path", "new_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_path",
            "description": "Move a file or folder to a new location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {"type": "string"},
                    "destination_path": {"type": "string"},
                },
                "required": ["source_path", "destination_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_path",
            "description": "Copy a file or folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {"type": "string"},
                    "destination_path": {"type": "string"},
                },
                "required": ["source_path", "destination_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_path",
            "description": "Delete a file or folder.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_special_folder",
            "description": "Resolve common folders: desktop, documents, downloads, home.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": ["desktop", "documents", "downloads", "home"],
                    }
                },
                "required": ["name"],
            },
        },
    },
]

TOOL_HANDLERS = {
    "open_url": open_url,
    "open_path": open_path,
    "open_in_editor": open_in_editor,
    "create_folder": create_folder,
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "rename_path": rename_path,
    "move_path": move_path,
    "copy_path": copy_path,
    "delete_path": delete_path,
    "get_special_folder": get_special_folder,
}


def run_tool(name: str, arguments: dict[str, Any]) -> str:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return _err(f"Unknown tool: {name}")
    try:
        return handler(**arguments)
    except TypeError as exc:
        return _err(f"Bad arguments for {name}: {exc}")
    except PermissionError as exc:
        return _err(str(exc))
    except Exception as exc:  # noqa: BLE001 - surface tool failures to the model
        return _err(f"{name} failed: {exc}")
