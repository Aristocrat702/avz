import json
import os
from typing import Any, Optional

def load_json(path: str, default: Optional[Any] = None) -> Any:
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: str, data: Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
