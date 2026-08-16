#!/usr/bin/env python3
"""Verify working-excerpt trust metadata (offline hash; optional --write to stamp)."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from cite_resolve import (  # noqa: E402
    parse_source_meta,
    split_source_frontmatter,
    verify_excerpt_hash,
)


def find_excerpt_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            if "sources" not in p.parts:
                continue
            out.append(p)
    return out


def stamp_frontmatter(path: Path, *, retrieved: str) -> None:
    text = path.read_text(encoding="utf-8")
    meta = parse_source_meta(text)
    _, body = split_source_frontmatter(text)
    body_norm = body.rstrip() + "\n"
    h = hashlib.sha256(body_norm.encode("utf-8")).hexdigest()
    rid = (meta.get("id") or path.parent.parent.name).strip()
    instrument = (meta.get("instrument") or "").strip()
    url = (meta.get("source_url") or "").strip()
    parts = [f"id={rid}"]
    if instrument:
        parts.append(f'instrument="{instrument}"')
    if url:
        parts.append(f'source_url="{url}"')
    parts.append(f'retrieved="{retrieved}"')
    parts.append(f'sha256="{h}"')
    fm = "<!-- tundra-source: " + " ".join(parts) + " -->\n"
    path.write_text(fm + body_norm, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify / stamp excerpt sha256 metadata (offline)"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories (default: examples/regulations + skill sources)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite front-matter sha256 (and retrieved) from current body",
    )
    parser.add_argument(
        "--retrieved",
        default="2026-08-16",
        help="ISO date for --write",
    )
    args = parser.parse_args(argv)

    if args.paths:
        files: list[Path] = []
        for p in args.paths:
            if p.is_file():
                files.append(p)
            else:
                files.extend(find_excerpt_files([p]))
    else:
        files = find_excerpt_files(
            [
                ROOT / "examples" / "regulations",
                ROOT / ".grok" / "skills" / "tundra" / "references" / "sources",
            ]
        )

    if not files:
        print("No excerpt files found", file=sys.stderr)
        return 2

    if args.write:
        for p in files:
            stamp_frontmatter(p, retrieved=args.retrieved)
            print(f"stamped {p}")
        return 0

    any_err = False
    for p in files:
        text = p.read_text(encoding="utf-8")
        meta = parse_source_meta(text)
        try:
            rel: object = p.resolve().relative_to(ROOT)
        except ValueError:
            rel = p
        if not (meta.get("id") or "").strip():
            print(f"WARN {rel}: missing id= in tundra-source")
        ok, declared, actual = verify_excerpt_hash(text)
        if declared is None:
            print(f"WARN {rel}: missing sha256= (actual {actual[:12]}…)")
            continue
        if not ok:
            any_err = True
            print(
                f"FAIL {rel}: sha256 mismatch "
                f"declared={declared[:12]}… actual={actual[:12]}…"
            )
        else:
            print(f"OK   {rel}")
    return 1 if any_err else 0


if __name__ == "__main__":
    sys.exit(main())
