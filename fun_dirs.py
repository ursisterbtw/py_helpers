import os
from pathlib import Path

emoji_map = {
    "krabby": "📁",
    "secret": "🔒",
    "venv": "🧪",
    "assets": "🖼️",
    "docs": "📚",
    "sandooo": "🏖️",
    "src": "🛠️",
    "submodules": "🧩",
    "target": "🎯",
    "utils": "🛠️",
    ".cursorignore": "📜",
    ".cursorrules": "📜",
    ".env": "📜",
    ".gitignore": "🙈",
    "Cargo.lock": "🔒",
    "Cargo.toml": "📦",
    "krabby.code-workspace": "🧠",
    "README.md": "📄",
    "requirements.txt": "📋",
    "TODO.md": "✅",
    "world-chain-contract-address": "🌐",
}


def get_emoji(name):
    return emoji_map.get(name, "📄")  # Default to 📄 for unknown files/folders


def print_directory_structure(startpath, level=0):
    for root, dirs, files in os.walk(startpath):
        if ".git" in dirs:
            dirs.remove(".git")  # Don't show git directory
        path = Path(root)
        print("   " * level + f"{get_emoji(path.name)} {path.name}")
        level += 1
        for file in files:
            print("   " * level + f"{get_emoji(file)} {file}")
        level -= 1
        if level == 0:
            break  # Only process the top-level directory


# Usage
print_directory_structure(".")
