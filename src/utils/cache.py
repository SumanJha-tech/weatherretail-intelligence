import json
import os

def save_json(data: dict, filepath: str) -> None:
    """Saves a dictionary as a JSON file, creating folders if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f)

def load_json(filepath: str) -> dict | None:
    """Loads a JSON file if it exists, otherwise returns None."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        return json.load(f)