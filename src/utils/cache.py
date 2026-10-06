import json
import os

def save_json(data: dict, filepath: str) -> None:
    """Write JSON, creating parent directories when they do not exist."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f)

def load_json(filepath: str) -> dict | None:
    """Return parsed JSON, or None when the file is absent."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        return json.load(f)