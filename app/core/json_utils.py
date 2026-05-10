import json
from typing import Any


def safe_json_loads(value: Any, default: Any = None) -> Any:
    """Parse a JSON string, returning `default` on any failure or empty input."""
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default
