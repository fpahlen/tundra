"""Repo paths (web/ is one level under repo root)."""

from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEB_ROOT.parent
TUNDRA_MD = REPO_ROOT / "tundra.md"
EXTRACT_PROMPT = REPO_ROOT / "prompts" / "extract-tundra.md"
FORMAT_MD = REPO_ROOT / ".grok" / "skills" / "tundra" / "references" / "format.md"
SCHEMA = REPO_ROOT / "schema" / "tundra.schema.json"
