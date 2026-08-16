"""Resolve Contract/Process cites against instrument working excerpts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


def normalise_legal(s: str) -> str:
    """Collapse whitespace and normalise quotes/dashes/ellipsis for quote match."""
    if not s:
        return ""
    t = unicodedata.normalize("NFKC", s)
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2026", "...").replace("…", "...")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def find_sources_dir(model_path: Path, regulation_id: str, repo_root: Path) -> Path | None:
    """Locate working excerpts for this instrument relative to the model or repo."""
    rid = (regulation_id or "").strip()
    rid_l = rid.lower()
    candidates: list[Path] = []

    # Next to the model: .../dora/foo.tundra -> .../dora/sources
    parent = model_path.parent
    candidates.append(parent / "sources")
    # .../regulations/dora/*.tundra
    if parent.name.lower() == rid_l or parent.name.lower() == rid_l.replace(" ", "-"):
        candidates.append(parent / "sources")

    # examples/regulations/<id>/sources
    candidates.append(repo_root / "examples" / "regulations" / rid_l / "sources")
    # sources/<id> (consumer app convention)
    candidates.append(repo_root / "sources" / rid_l)
    candidates.append(repo_root / "sources" / rid)

    # Skill-bundled demo sources
    skill_src = (
        repo_root
        / ".grok"
        / "skills"
        / "tundra"
        / "references"
        / "sources"
    )
    candidates.append(skill_src)

    seen: set[Path] = set()
    for c in candidates:
        try:
            rp = c.resolve()
        except OSError:
            continue
        if rp in seen:
            continue
        seen.add(rp)
        if rp.is_dir():
            return rp
    return None


def article_file_candidates(article: str) -> list[str]:
    art = re.sub(r"[^\d]", "", str(article).strip()) or str(article).strip()
    names = []
    if art.isdigit():
        n = int(art)
        names.extend(
            [
                f"art-{n:02d}.md",
                f"art-{n}.md",
                f"article-{n:02d}.md",
                f"article-{n}.md",
                f"art{n:02d}.md",
                f"art{n}.md",
            ]
        )
    raw = str(article).strip()
    names.append(f"art-{raw}.md")
    names.append(f"article-{raw}.md")
    return names


def load_article_excerpt(sources_dir: Path, article: str) -> tuple[Path | None, str | None]:
    for name in article_file_candidates(article):
        p = sources_dir / name
        if p.is_file():
            return p, p.read_text(encoding="utf-8")
    # Fallback: search any *.md containing "## Article N" or "Article N"
    art_num = re.sub(r"[^\d]", "", str(article))
    if art_num:
        for p in sorted(sources_dir.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            if re.search(rf"(?i)##\s*article\s+{art_num}\b", text) or re.search(
                rf"(?i)\barticle\s+{art_num}\b", text[:500]
            ):
                return p, text
    return None, None


def parse_paragraph_markers(text: str) -> set[str]:
    """Return paragraph numbers as strings: '1', '2', ... and points '2(a)' style keys."""
    paragraphs: set[str] = set()
    # Top-level numbered paragraphs: "1." or "1. " at line start (allow leading spaces)
    for m in re.finditer(r"(?m)^\s*(\d+)\.\s+\S", text):
        paragraphs.add(m.group(1))
    return paragraphs


def parse_point_markers(text: str) -> set[str]:
    """Return point letters found as (a), (b), ... at line start."""
    points: set[str] = set()
    for m in re.finditer(r"(?m)^\s*\(([a-z])\)\s+\S", text):
        points.add(m.group(1))
    return points


def split_paragraph_point(paragraph: str | None) -> tuple[str | None, str | None]:
    """'2(a)' -> ('2', 'a'); '2' -> ('2', None); '2(a)(i)' -> ('2', 'a') for coarse check."""
    if not paragraph or not str(paragraph).strip():
        return None, None
    p = str(paragraph).strip()
    m = re.match(r"^(\d+)\s*\(([a-z])\)", p, re.I)
    if m:
        return m.group(1), m.group(2).lower()
    m2 = re.match(r"^(\d+)$", p)
    if m2:
        return m2.group(1), None
    # free text paragraph ref
    return p, None


def quote_in_excerpt(quote: str, excerpt: str) -> bool:
    nq = normalise_legal(quote)
    ne = normalise_legal(excerpt)
    if not nq:
        return True
    # Allow ellipsis in quote: match each segment
    if "..." in nq:
        parts = [p.strip() for p in nq.split("...") if p.strip()]
        pos = 0
        for part in parts:
            i = ne.find(part, pos)
            if i < 0:
                return False
            pos = i + len(part)
        return True
    return nq in ne


def iter_cites(data: dict[str, Any]) -> list[tuple[str, int, int, dict[str, Any]]]:
    """Yield (location, item_index, cite_index, cite_dict)."""
    out: list[tuple[str, int, int, dict[str, Any]]] = []
    for i, c in enumerate(data.get("contracts") or []):
        if not isinstance(c, dict):
            continue
        cites = c.get("cite")
        if not isinstance(cites, list):
            continue
        for j, ref in enumerate(cites):
            if isinstance(ref, dict):
                out.append((f"contract[{i}]", i, j, ref))
    for i, proc in enumerate(data.get("processes") or []):
        if not isinstance(proc, dict):
            continue
        cites = proc.get("cite")
        if not isinstance(cites, list):
            continue
        for j, ref in enumerate(cites):
            if isinstance(ref, dict):
                out.append((f"process[{i}]", i, j, ref))
    return out


def check_provenance(
    data: dict[str, Any],
    model_path: Path,
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for regulatory provenance rules."""
    errors: list[str] = []
    warnings: list[str] = []

    reg = data.get("regulation")
    cites = iter_cites(data)

    if cites and reg is None:
        errors.append(
            "cite: present on Contract/Process but model has no regulation: pin "
            "(orphan cites are not allowed)"
        )
        return errors, warnings

    if reg is None:
        return errors, warnings

    if not isinstance(reg, dict):
        errors.append("regulation: must be a mapping")
        return errors, warnings

    edition = reg.get("edition")
    rid = reg.get("id") if isinstance(reg.get("id"), str) else ""
    sources_dir = find_sources_dir(model_path, rid, repo_root) if rid else None

    # Regulatory models: every Contract must be object with cite.article
    has_any_article = False
    for i, c in enumerate(data.get("contracts") or []):
        if isinstance(c, str):
            errors.append(
                f"contract[{i}]: regulatory models require object Contracts with cite "
                f"(bare string has no legal provenance)"
            )
            continue
        if not isinstance(c, dict):
            continue
        cites_c = c.get("cite")
        if not cites_c or not isinstance(cites_c, list):
            errors.append(
                f"contract[{i}]: regulatory model Contract missing cite "
                f"(need article/paragraph provenance)"
            )
            continue
        for j, ref in enumerate(cites_c):
            if not isinstance(ref, dict):
                errors.append(f"contract[{i}] cite[{j}]: must be a mapping")
                continue
            art = ref.get("article")
            if not (isinstance(art, str) and art.strip()):
                errors.append(f"contract[{i}] cite[{j}]: article is required")
            else:
                has_any_article = True
            if ref.get("page") is not None and not (
                isinstance(edition, str) and edition.strip()
            ):
                warnings.append(
                    f"contract[{i}] cite[{j}]: page set but regulation.edition missing"
                )

    for loc, _i, j, ref in cites:
        art = ref.get("article")
        if isinstance(art, str) and art.strip():
            has_any_article = True
        if ref.get("page") is not None and not (
            isinstance(edition, str) and edition.strip()
        ):
            if not loc.startswith("contract"):  # contracts already warned
                warnings.append(
                    f"{loc} cite[{j}]: page set but regulation.edition missing"
                )

    if not has_any_article:
        errors.append(
            "regulation: present but no cite with article on any Contract/Process"
        )

    # Resolve against sources when available
    if sources_dir is None:
        if cites:
            warnings.append(
                f"regulation {rid!r}: no sources/ directory found next to the model "
                f"or under examples/regulations/{rid.lower()}/sources — "
                f"cannot verify quotes or article numbers"
            )
        return errors, warnings

    excerpt_cache: dict[str, tuple[Path | None, str | None]] = {}

    for loc, _i, j, ref in cites:
        art = ref.get("article")
        if not isinstance(art, str) or not art.strip():
            continue
        key = art.strip()
        if key not in excerpt_cache:
            excerpt_cache[key] = load_article_excerpt(sources_dir, key)
        path, excerpt = excerpt_cache[key]
        if excerpt is None:
            # Sources tree exists for this instrument — missing article is a hard fail
            errors.append(
                f"{loc} cite[{j}]: no excerpt file for article {key!r} under {sources_dir} "
                f"(unknown article for this pin, or add art-NN.md working excerpt)"
            )
            continue

        para = ref.get("paragraph")
        para_s = str(para).strip() if para is not None else ""
        if para_s:
            pnum, point = split_paragraph_point(para_s)
            paras = parse_paragraph_markers(excerpt)
            points = parse_point_markers(excerpt)
            if pnum and pnum.isdigit() and pnum not in paras:
                errors.append(
                    f"{loc} cite[{j}]: paragraph {pnum!r} not found in {path.name} "
                    f"(known paragraphs: {', '.join(sorted(paras, key=lambda x: int(x) if x.isdigit() else 0)) or 'none'})"
                )
            if point and point not in points:
                # points may only appear under para 2; still require letter present
                errors.append(
                    f"{loc} cite[{j}]: point ({point}) not found in {path.name}"
                )

        quote = ref.get("quote")
        if isinstance(quote, str) and quote.strip():
            if not quote_in_excerpt(quote, excerpt):
                errors.append(
                    f"{loc} cite[{j}]: quote not found in {path.name} "
                    f"(normalised match failed — check verbatim wording)"
                )

    return errors, warnings


def enumerate_source_coverage(sources_dir: Path) -> dict[str, dict[str, Any]]:
    """article -> {paragraphs: set, points: set, file: name}"""
    out: dict[str, dict[str, Any]] = {}
    for p in sorted(sources_dir.glob("*.md")):
        if p.name.lower() in ("readme.md",):
            continue
        text = p.read_text(encoding="utf-8")
        m = re.search(r"(?i)article\s+(\d+)", text)
        if not m:
            m2 = re.search(r"art-(\d+)", p.stem, re.I)
            if not m2:
                continue
            art = str(int(m2.group(1)))
        else:
            art = str(int(m.group(1)))
        out[art] = {
            "paragraphs": parse_paragraph_markers(text),
            "points": parse_point_markers(text),
            "file": p.name,
        }
    return out


def cites_from_models(model_paths: list[Path], yaml) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for path in model_paths:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(data, dict):
            continue
        for loc, _i, _j, ref in iter_cites(data):
            art = ref.get("article")
            if not isinstance(art, str):
                continue
            para = ref.get("paragraph")
            found.append(
                {
                    "article": art.strip(),
                    "paragraph": str(para).strip() if para is not None else "",
                    "loc": f"{path.name}:{loc}",
                }
            )
    return found
