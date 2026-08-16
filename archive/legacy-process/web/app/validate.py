"""Validate draft YAML using the repo checker."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.paths import REPO_ROOT


def validate_tundra_yaml(yaml_text: str) -> dict:
    """Return {ok, errors, warnings, display} for a draft model body."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from check_tundra import SCHEMA_PATH, check_file, load_deps  # type: ignore

    yaml, jsonschema = load_deps()
    schema = __import__("json").loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".tundra",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(yaml_text if yaml_text.endswith("\n") else yaml_text + "\n")
        path = Path(tmp.name)

    try:
        errors, warnings = check_file(path, schema, yaml, jsonschema)
    finally:
        path.unlink(missing_ok=True)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
