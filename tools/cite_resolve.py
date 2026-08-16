"""Resolve Contract/Process cites against instrument working excerpts.

Sources are bound to regulation.id — never silently verify against another instrument.
Quotes are matched inside the cited paragraph (and point) span, not the whole article.
Regulatory cites require a quote; ellipsis splices and crude modality mismatches are flagged.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any

# Ellipsis in quotes: any use is a warning; large gaps are errors (splice risk)
_ELLIPSIS_RE = re.compile(r"\.\.\.|…")
_MAX_ELISION_WORDS = 12
_MAX_ELISION_CHARS = 80


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


def parse_source_meta(text: str) -> dict[str, str]:
    """Read instrument id / trust fields from excerpt front-matter or HTML comment."""
    meta: dict[str, str] = {}
    # <!-- tundra-source: id=DORA instrument="…" source_url="…" retrieved="…" sha256="…" -->
    m = re.search(r"<!--\s*tundra-source:\s*([^>]+?)-->", text, re.I)
    if m:
        blob = m.group(1)
        for km in re.finditer(
            r"""(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+))""", blob
        ):
            key = km.group(1).lower()
            val = km.group(2) or km.group(3) or km.group(4) or ""
            meta[key] = val.strip()
        return meta
    # YAML front matter
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip().lower()] = v.strip().strip("\"'")
    return meta


def split_source_frontmatter(text: str) -> tuple[str, str]:
    """Return (front_matter_including_trailing_ws, body)."""
    text = text.lstrip("\ufeff")
    m = re.match(r"(?s)^(\s*<!--\s*tundra-source:.*?-->\s*)(.*)$", text, re.I)
    if m:
        return m.group(1), m.group(2)
    stripped = text.lstrip()
    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) >= 3:
            fm = "---" + parts[1] + "---"
            return fm, parts[2].lstrip("\n")
    return "", text


def excerpt_body_for_hash(text: str) -> str:
    """Body bytes hashed for sha256: (content after front-matter), rstrip + single newline."""
    _, body = split_source_frontmatter(text)
    return body.rstrip() + "\n"


def compute_excerpt_sha256(text: str) -> str:
    return hashlib.sha256(excerpt_body_for_hash(text).encode("utf-8")).hexdigest()


def verify_excerpt_hash(text: str) -> tuple[bool, str | None, str]:
    """
    If front-matter has sha256, compare to body hash.
    Returns (ok, declared_or_None, actual_hash).
    ok True if no sha256 declared or match.
    """
    meta = parse_source_meta(text)
    actual = compute_excerpt_sha256(text)
    declared = (meta.get("sha256") or "").strip().lower()
    if not declared:
        return True, None, actual
    return declared == actual, declared, actual


def quote_elision_issues(quote: str, span: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for ellipsis handling."""
    errors: list[str] = []
    warnings: list[str] = []
    if not _ELLIPSIS_RE.search(quote):
        return errors, warnings
    # Disallow ellipsis: splices can delete microenterprise carve-outs etc.
    errors.append(
        "quote must not use ellipsis (…/...); use a continuous verbatim snippet "
        "from the cited span"
    )
    return errors, warnings


_SCOPE_CUES = re.compile(
    r"("
    r"\bother than\b|"
    r"\bunless\b|"
    r"\bwhere applicable\b|"
    r"\bshall not apply\b|"
    r"\bdoes not apply to\b|"
    r"\bdo not apply to\b|"
    r"\bmicroenterprises?\b|"
    r"\bwith the exception of\b|"
    r"\bexcept for\b|"
    r"\bexcluding\b"
    r")",
    re.I,
)

_SOFT_MODAL = re.compile(
    r"("
    r"\bshould\b|"
    r"\bmay consider\b|"
    r"\bwhere practical\b|"
    r"\bwhere possible\b|"
    r"\bas appropriate\b|"
    r"\bas far as possible\b|"
    r"\bendeavour\b|"
    r"\bendeavor\b|"
    r"\bwhere practicable\b"
    r")",
    re.I,
)


def _sentence_window_around_quote(span: str, quote: str) -> str:
    """
    Prefer the sentence(s) in span that contain the quote match.
    Avoids flagging carve-outs in other sentences of a long paragraph.
    """
    nq = normalise_legal(quote)
    ne = normalise_legal(span)
    if not nq or nq not in ne:
        return span
    # Map approx using original: find first 40 chars of quote in span
    probe = re.sub(r"\s+", " ", quote.strip())[:60]
    idx = span.lower().find(probe[:40].lower()) if len(probe) >= 20 else -1
    if idx < 0:
        # try first words
        words = probe.split()[:6]
        chunk = " ".join(words)
        idx = span.lower().find(chunk.lower()) if chunk else -1
    if idx < 0:
        return span
    # sentence bounds: . ! ? or start/end
    start = idx
    while start > 0 and span[start - 1] not in ".!?\n":
        start -= 1
    end = idx + max(len(probe), 20)
    while end < len(span) and span[end - 1] not in ".!?\n":
        end += 1
    return span[start:end]


def scope_qualifier_warnings(span: str, quote: str, paragraph_label: str) -> list[str]:
    """Warn when the quoted sentence's span has scope carve-outs the quote omits."""
    if not span or not quote:
        return []
    window = _sentence_window_around_quote(span, quote)
    nquote = normalise_legal(quote)
    found = []
    for m in _SCOPE_CUES.finditer(window):
        cue = normalise_legal(m.group(0))
        if cue and cue not in nquote:
            found.append(m.group(0).strip())
    if not found:
        return []
    seen: set[str] = set()
    uniq = []
    for f in found:
        k = f.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    sample = ", ".join(repr(u) for u in uniq[:3])
    return [
        f"cited paragraph {paragraph_label!r} contains scope qualifier(s) "
        f"not present in the quote ({sample}) — risk of over-application"
    ]


def modality_mismatch_warnings(contract_text: str, quote: str) -> list[str]:
    """Crude shall/must vs not-required / softened mismatch (warnings only)."""
    ct = contract_text.lower()
    qt = quote.lower()
    out: list[str] = []
    quote_shall_not = bool(re.search(r"\bshall not\b|\bmust not\b", qt))
    quote_shall = bool(re.search(r"\bshall\b", qt)) and not quote_shall_not
    contract_not_required = bool(
        re.search(
            r"\bis not required\b|\bneed not\b|\bnot required to\b|\bmay leave\b|"
            r"\bno obligation\b",
            ct,
        )
    )
    contract_must = bool(re.search(r"\bmust\b|\bshall\b", ct)) and not re.search(
        r"\bmust not\b|\bshall not\b|\bis not required\b", ct
    )
    contract_soft = bool(_SOFT_MODAL.search(ct))
    if quote_shall and contract_not_required:
        out.append(
            "possible modality mismatch: quote uses shall/must but Contract denies the duty"
        )
    if quote_shall and contract_soft and not contract_must:
        out.append(
            "possible modality mismatch: quote uses shall but Contract softens "
            "(should / where practical / as appropriate / consider)"
        )
    if quote_shall and contract_soft and contract_must:
        # "must … where practical" still softens
        if _SOFT_MODAL.search(contract_text):
            out.append(
                "possible modality mismatch: quote uses shall but Contract softens "
                "the obligation (should / where practical / as appropriate)"
            )
    if quote_shall_not and contract_must and "not" not in ct:
        out.append(
            "possible modality mismatch: quote uses shall not but Contract reads as positive duty"
        )
    if re.search(r"\bmay\b", qt) and not re.search(r"\bshall\b|\bmust\b", qt):
        if contract_must and "remain" not in ct and "still" not in ct:
            out.append(
                "possible modality mismatch: quote is a permission (may) but Contract uses must"
            )
    return out


def _dir_declares_instrument(sources_dir: Path, regulation_id: str) -> bool:
    """True if directory is for this pin (path name or file front-matter)."""
    rid = regulation_id.strip()
    rid_l = rid.lower()
    # Path segment match: .../dora/sources or .../sources/dora
    parts_l = [p.lower() for p in sources_dir.parts]
    if rid_l in parts_l or rid_l.replace(" ", "-") in parts_l:
        return True
    # Any excerpt front-matter id match
    for p in sources_dir.glob("*.md"):
        if p.name.lower() == "readme.md":
            continue
        try:
            meta = parse_source_meta(p.read_text(encoding="utf-8")[:2000])
        except OSError:
            continue
        mid = (meta.get("id") or "").strip()
        if mid and mid.lower() == rid_l:
            return True
    return False


def find_sources_dir(
    model_path: Path, regulation_id: str, repo_root: Path
) -> Path | None:
    """Locate working excerpts **for this regulation.id only** (no cross-instrument fallback)."""
    rid = (regulation_id or "").strip()
    if not rid:
        return None
    rid_l = rid.lower()
    rid_slug = rid_l.replace(" ", "-")

    candidates: list[Path] = []

    parent = model_path.parent
    # Model beside sources only if parent folder names the instrument
    if parent.name.lower() in (rid_l, rid_slug):
        candidates.append(parent / "sources")
    # Parent is sources/ itself?
    if parent.name.lower() == "sources" and parent.parent.name.lower() in (
        rid_l,
        rid_slug,
    ):
        candidates.append(parent)

    candidates.append(repo_root / "examples" / "regulations" / rid_l / "sources")
    candidates.append(repo_root / "examples" / "regulations" / rid_slug / "sources")
    candidates.append(repo_root / "sources" / rid_l)
    candidates.append(repo_root / "sources" / rid_slug)
    candidates.append(repo_root / "sources" / rid)

    # Skill demo sources — only for DEMO-REG
    if rid_l in ("demo-reg", "demoreg"):
        candidates.append(
            repo_root / ".grok" / "skills" / "tundra" / "references" / "sources"
        )

    seen: set[Path] = set()
    for c in candidates:
        try:
            rp = c.resolve()
        except OSError:
            continue
        if rp in seen or not rp.is_dir():
            continue
        seen.add(rp)
        if _dir_declares_instrument(rp, rid):
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


def load_article_excerpt(
    sources_dir: Path, article: str
) -> tuple[Path | None, str | None]:
    for name in article_file_candidates(article):
        p = sources_dir / name
        if p.is_file():
            return p, p.read_text(encoding="utf-8")
    art_num = re.sub(r"[^\d]", "", str(article))
    if art_num:
        for p in sorted(sources_dir.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            text = p.read_text(encoding="utf-8")
            if re.search(rf"(?i)##\s*article\s+{art_num}\b", text) or re.search(
                rf"(?i)\barticle\s+{art_num}\b", text[:800]
            ):
                return p, text
    return None, None


def _slice_by_markers(
    text: str,
    pattern: re.Pattern[str],
    key_fn,
    *,
    max_indent: int | None = None,
) -> dict[str, str]:
    """Slice text into spans keyed by regex match groups (first key wins)."""
    matches = list(pattern.finditer(text))
    spans: dict[str, str] = {}
    for i, m in enumerate(matches):
        if max_indent is not None:
            indent = len(m.group(1).replace("\t", "    "))
            if indent > max_indent:
                continue
        key = key_fn(m)
        if not key or key in spans:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        spans[key] = text[start:end]
    return spans


def parse_paragraph_spans(text: str) -> dict[str, str]:
    """Map paragraph number -> body text until the next top-level N. marker."""
    return _slice_by_markers(
        text,
        re.compile(r"(?m)^(\s*)(\d+)\.\s+"),
        lambda m: m.group(2),
        max_indent=3,
    )


def parse_paragraph_markers(text: str) -> set[str]:
    return set(parse_paragraph_spans(text).keys())


def parse_point_spans(para_body: str) -> dict[str, str]:
    """Map point letter -> body within one paragraph."""
    return _slice_by_markers(
        para_body,
        re.compile(r"(?m)^(\s*)\(([a-z])\)\s+"),
        lambda m: m.group(2).lower(),
    )


def parse_point_markers(text: str) -> set[str]:
    return set(parse_point_spans(text).keys())


def split_paragraph_point(paragraph: str | None) -> tuple[str | None, str | None]:
    """'2(a)' -> ('2', 'a'); '2' -> ('2', None)."""
    if not paragraph or not str(paragraph).strip():
        return None, None
    p = str(paragraph).strip()
    m = re.match(r"^(\d+)\s*\(([a-z])\)", p, re.I)
    if m:
        return m.group(1), m.group(2).lower()
    m2 = re.match(r"^(\d+)$", p)
    if m2:
        return m2.group(1), None
    return p, None


def quote_in_span(quote: str, span: str) -> bool:
    nq = normalise_legal(quote)
    ne = normalise_legal(span)
    if not nq:
        return True
    # Ellipsis normalised to ...
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


def elision_gap_too_large(quote: str, span: str) -> bool:
    """True if ... fragments leave a large gap in the span (splice risk)."""
    nq = normalise_legal(quote)
    ne = normalise_legal(span)
    if "..." not in nq:
        return False
    parts = [p.strip() for p in nq.split("...") if p.strip()]
    if len(parts) < 2:
        return False
    pos = 0
    for i, part in enumerate(parts):
        j = ne.find(part, pos)
        if j < 0:
            return False
        if i > 0:
            gap = ne[pos:j]
            if len(gap) > _MAX_ELISION_CHARS or len(gap.split()) > _MAX_ELISION_WORDS:
                return True
        pos = j + len(part)
    return False


def resolve_cite_span(
    excerpt: str, paragraph: str | None
) -> tuple[str | None, str | None, str]:
    """
    Return (pnum, point, text_span_to_match).
    If paragraph omitted, span is the full excerpt.
    """
    if not paragraph or not str(paragraph).strip():
        return None, None, excerpt
    pnum, point = split_paragraph_point(str(paragraph).strip())
    spans = parse_paragraph_spans(excerpt)
    if not pnum or pnum not in spans:
        return pnum, point, ""
    body = spans[pnum]
    if point:
        pts = parse_point_spans(body)
        if point not in pts:
            return pnum, point, ""
        return pnum, point, pts[point]
    return pnum, point, body


def iter_cites(data: dict[str, Any]) -> list[tuple[str, int, int, dict[str, Any]]]:
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
        # translation_review
        tr = c.get("translation_review")
        if tr is None:
            warnings.append(
                f"contract[{i}]: regulatory Contract has no translation_review "
                f"(status: unreviewed|reviewed) — green cite checks are not a human fidelity sign-off"
            )
        elif isinstance(tr, dict):
            st = tr.get("status")
            if st not in ("unreviewed", "reviewed"):
                warnings.append(
                    f"contract[{i}]: translation_review.status should be "
                    f"'unreviewed' or 'reviewed'"
                )
        else:
            warnings.append(f"contract[{i}]: translation_review must be a mapping")

        for j, ref in enumerate(cites_c):
            if not isinstance(ref, dict):
                errors.append(f"contract[{i}] cite[{j}]: must be a mapping")
                continue
            art = ref.get("article")
            if not (isinstance(art, str) and art.strip()):
                errors.append(f"contract[{i}] cite[{j}]: article is required")
            else:
                has_any_article = True
            q = ref.get("quote")
            if not (isinstance(q, str) and q.strip()):
                errors.append(
                    f"contract[{i}] cite[{j}]: quote is required on regulatory cites "
                    f"(verbatim snippet from the cited paragraph)"
                )
            if ref.get("page") is not None and not (
                isinstance(edition, str) and edition.strip()
            ):
                warnings.append(
                    f"contract[{i}] cite[{j}]: page set but regulation.edition missing"
                )

        # Anti-gaming: too many paragraphs on one Contract
        paras_hit: set[str] = set()
        for ref in cites_c:
            if not isinstance(ref, dict):
                continue
            p = ref.get("paragraph")
            if p is not None and str(p).strip():
                pnum, _ = split_paragraph_point(str(p).strip())
                if pnum:
                    paras_hit.add(f"{ref.get('article')}:{pnum}")
        if len(paras_hit) > 2:
            warnings.append(
                f"contract[{i}]: cites {len(paras_hit)} distinct article-paragraphs "
                f"(possible catch-all; prefer one duty per independently testable failure)"
            )

    # Process cites: require quote + article
    for i, proc in enumerate(data.get("processes") or []):
        if not isinstance(proc, dict):
            continue
        cites_p = proc.get("cite")
        if not cites_p:
            continue
        if not isinstance(cites_p, list):
            continue
        for j, ref in enumerate(cites_p):
            if not isinstance(ref, dict):
                continue
            if isinstance(ref.get("article"), str) and ref["article"].strip():
                has_any_article = True
            q = ref.get("quote")
            if not (isinstance(q, str) and q.strip()):
                errors.append(
                    f"process[{i}] cite[{j}]: quote is required on regulatory cites"
                )

    n_contracts = sum(
        1
        for c in (data.get("contracts") or [])
        if isinstance(c, (str, dict))
    )
    if n_contracts and len(cites) / max(n_contracts, 1) > 3:
        warnings.append(
            f"regulation: cites/contracts ratio is {len(cites)}/{n_contracts} "
            f"(>3 — possible coverage padding)"
        )

    if not has_any_article:
        errors.append(
            "regulation: present but no cite with article on any Contract/Process"
        )

    if sources_dir is None:
        if cites:
            warnings.append(
                f"regulation {rid!r}: no excerpts for pin {rid!r} — cites unverified "
                f"(add examples/regulations/{rid.lower()}/sources/ or sources/{rid.lower()}/ "
                f"bound to this id; will not use another instrument's excerpts)"
            )
        return errors, warnings

    excerpt_cache: dict[str, tuple[Path | None, str | None]] = {}
    meta_warned: set[str] = set()
    hash_checked: set[str] = set()

    # Map loc -> contract text for modality checks
    contract_texts: dict[int, str] = {}
    for i, c in enumerate(data.get("contracts") or []):
        if isinstance(c, dict) and isinstance(c.get("text"), str):
            contract_texts[i] = c["text"]

    for loc, i, j, ref in cites:
        art = ref.get("article")
        if not isinstance(art, str) or not art.strip():
            continue
        key = art.strip()
        if key not in excerpt_cache:
            excerpt_cache[key] = load_article_excerpt(sources_dir, key)
        path, excerpt = excerpt_cache[key]
        if excerpt is None:
            errors.append(
                f"{loc} cite[{j}]: no excerpt file for article {key!r} under "
                f"sources for pin {rid!r} ({sources_dir}) "
                f"(unknown article for this pin, or add art-NN.md)"
            )
            continue

        meta = parse_source_meta(excerpt)
        mid = (meta.get("id") or "").strip()
        if mid and mid.lower() != rid.lower():
            errors.append(
                f"{loc} cite[{j}]: excerpt {path.name} declares id={mid!r} "
                f"but model pins regulation.id={rid!r}"
            )
            continue
        if path and str(path) not in meta_warned:
            meta_warned.add(str(path))
            if not mid:
                warnings.append(
                    f"sources: {path.name} has no tundra-source front-matter id= "
                    f"(add <!-- tundra-source: id={rid} --> to bind excerpt to pin)"
                )
            if not (meta.get("source_url") or "").strip():
                warnings.append(
                    f"sources: {path.name} missing source_url= in tundra-source front-matter"
                )
            if not (meta.get("retrieved") or "").strip():
                warnings.append(
                    f"sources: {path.name} missing retrieved= (ISO date) in front-matter"
                )
            if str(path) not in hash_checked:
                hash_checked.add(str(path))
                ok, declared, actual = verify_excerpt_hash(excerpt)
                if declared is None:
                    warnings.append(
                        f"sources: {path.name} missing sha256= in front-matter "
                        f"(run tools/verify_sources.py --write to stamp)"
                    )
                elif not ok:
                    errors.append(
                        f"sources: {path.name} sha256 mismatch "
                        f"(declared {declared[:12]}… actual {actual[:12]}… — "
                        f"excerpt body changed without updating hash)"
                    )

        para = ref.get("paragraph")
        para_s = str(para).strip() if para is not None else ""
        quote = ref.get("quote")
        has_quote = isinstance(quote, str) and quote.strip()
        if not has_quote:
            continue  # already errored above

        spans_all = parse_paragraph_spans(excerpt)
        if spans_all and not para_s:
            errors.append(
                f"{loc} cite[{j}]: paragraph is required when the article excerpt "
                f"has numbered paragraphs (1., 2., …) — found {', '.join(sorted(spans_all, key=lambda x: int(x) if x.isdigit() else 0))}"
            )
            continue

        # Ellipsis / splice
        ee, ew = quote_elision_issues(quote, excerpt)
        for msg in ee:
            errors.append(f"{loc} cite[{j}]: {msg}")
        for msg in ew:
            warnings.append(f"{loc} cite[{j}]: {msg}")

        span = excerpt
        if para_s:
            pnum, point, span = resolve_cite_span(excerpt, para_s)
            spans = parse_paragraph_spans(excerpt)
            if pnum and pnum.isdigit() and pnum not in spans:
                errors.append(
                    f"{loc} cite[{j}]: paragraph {pnum!r} not found in {path.name} "
                    f"(known: {', '.join(sorted(spans, key=lambda x: int(x) if x.isdigit() else 0)) or 'none'})"
                )
                continue
            if point:
                if pnum and pnum in spans:
                    pts = parse_point_spans(spans[pnum])
                    if point not in pts:
                        errors.append(
                            f"{loc} cite[{j}]: point ({point}) not found under "
                            f"paragraph {pnum} in {path.name}"
                        )
                        continue
                elif not span:
                    errors.append(
                        f"{loc} cite[{j}]: point ({point}) not found in {path.name}"
                    )
                    continue

            if not span:
                errors.append(
                    f"{loc} cite[{j}]: cannot resolve paragraph span for "
                    f"{para_s!r} in {path.name}"
                )
            elif not quote_in_span(quote, span):
                if quote_in_span(quote, excerpt):
                    errors.append(
                        f"{loc} cite[{j}]: quote not found in cited paragraph "
                        f"{para_s!r} of {path.name} (text appears elsewhere in "
                        f"the article — possible misattribution)"
                    )
                else:
                    errors.append(
                        f"{loc} cite[{j}]: quote not found in paragraph "
                        f"{para_s!r} of {path.name} "
                        f"(normalised match failed — check verbatim wording)"
                    )
            elif elision_gap_too_large(quote, span):
                errors.append(
                    f"{loc} cite[{j}]: ellipsis gap too large in paragraph {para_s!r} "
                    f"(possible scope splice)"
                )
            elif span and quote_in_span(quote, span):
                for msg in scope_qualifier_warnings(span, quote, para_s):
                    warnings.append(f"{loc} cite[{j}]: {msg}")
        else:
            if not quote_in_span(quote, excerpt):
                errors.append(
                    f"{loc} cite[{j}]: quote not found in {path.name} "
                    f"(normalised match failed — check verbatim wording)"
                )

        # Modality heuristic (contract text vs quote)
        if loc.startswith("contract[") and i in contract_texts:
            for msg in modality_mismatch_warnings(contract_texts[i], quote):
                warnings.append(f"{loc}: {msg}")

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
        spans = parse_paragraph_spans(text)
        points: set[str] = set()
        for body in spans.values():
            points |= set(parse_point_spans(body).keys())
        out[art] = {
            "paragraphs": set(spans.keys()),
            "points": points,
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
        # contract index for demonstration later
        contracts = data.get("contracts") or []
        for loc, i, _j, ref in iter_cites(data):
            art = ref.get("article")
            if not isinstance(art, str):
                continue
            para = ref.get("paragraph")
            quote = ref.get("quote")
            cid = ""
            ctext = ""
            if loc.startswith("contract[") and i < len(contracts):
                c = contracts[i]
                if isinstance(c, dict):
                    cid = str(c.get("id") or "")
                    ctext = str(c.get("text") or "")
            found.append(
                {
                    "article": art.strip(),
                    "paragraph": str(para).strip() if para is not None else "",
                    "quote": str(quote).strip() if isinstance(quote, str) else "",
                    "contract_id": cid,
                    "contract_text": ctext,
                    "model": str(path),
                    "loc": f"{path.name}:{loc}",
                }
            )
    return found
