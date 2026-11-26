#!/usr/bin/env python3
"""
Zero-Dependency Track-Changes, Per-Section Word-Count Parity & Original-Manuscript
Protection Engine for Human Plain Scientific Writing (V1.2).

Uses Python standard library ONLY (no lxml, no python-docx) so the skill remains
100% self-contained and portable across Windows, macOS, and Linux.

V1.2 Protection & Parity Stack:
  1. Per-section word-count parity (ideal <=±5%, hard cap <=±8% per section with
     12-word short-section floor; whole-manuscript cap <=±5%) preventing both silent
     shrinking and artificial filler padding during plain-language smoothing.
  2. Strict surgical word-scale granularity (Unicode-lossless tokenization;
     max <=8 words per atomic op, min similarity >=0.65 by default; zero ghost
     NBSP/curly-quote revisions).
  3. Provider-agnostic Citation & Reference-List Shield: protects Zotero, EndNote,
     NoteExpress (NE.Ref), Mendeley, and Word bibliographic fields (w:fldChar,
     w:fldSimple, w:sdt, w:hyperlink), citation bookmarks, superscript numeric
     citations, plain-text parenthetical/narrative author-year and bracketed numeric
     citations, plus the entire immutable References/Bibliography section.
  4. Strict OOXML Run-Style & Layout Protection: paragraph-own projection (nested
     textbox paragraphs never shift offsets), refuses edits crossing differently
     formatted runs (protects italics/bold/subscripts), prevents superscript/italic
     bleed on pure insertions, refuses ambiguous insertions next to equations/drawings,
     and enforces number + math/statistical operator invariance (< > ≤ ≥ = ± % ‰ × ~ ≈).
  5. Two-pass original-coordinate overlap validation + --on-unsafe block|query
     (routes citation-adjacent or cross-format conflicts to Author Queries cleanly).
  6. Automatic post-write Original-Document Format & Reference Audit with atomic
     rollback: verifies byte-for-byte identity of all non-text ZIP parts (styles,
     fonts, numbering, themes, media, headers/footers, rels), non-text OOXML skeleton
     invariance, per-character surviving rPr identity, tracked reject==source and
     accept==clean equivalence, and exact citation/bibliography preservation.

Subcommands:
    docx   : Apply native Word Track Changes + parity + full post-write protection audit.
    text   : Generate word-boundary Markdown/HTML tracked diff + per-section parity table.
    parity : Check per-section word-count parity between any two .docx/.md/.txt files.
    verify : Independently audit format, citation, and parity protection on DOCX outputs.

Usage:
    python track_changes_writer.py docx source.docx edits.json \\
        --tracked out_tracked.docx [--clean out_clean.docx] [--log out_log.json] \\
        [--author "Plain Scientific Writer"] [--max-op-words 8] [--min-sim 0.65] \\
        [--max-section-drift 0.08] [--max-total-drift 0.05] \\
        [--on-unsafe block|query] [--allow-structural] [--allow-length-change] \\
        [--allow-number-change]

    python track_changes_writer.py text before.md after.md \\
        --out out_tracked.md [--format markdown|html] [--max-op-words 8] \\
        [--min-sim 0.65] [--max-section-drift 0.08] [--max-total-drift 0.05] \\
        [--allow-structural] [--allow-length-change] [--allow-number-change]

    python track_changes_writer.py parity before_file after_file \\
        [--max-section-drift 0.08] [--max-total-drift 0.05] [--json]

    python track_changes_writer.py verify source.docx edited.docx \\
        [--tracked] [--clean clean.docx] [--json]
"""

from __future__ import annotations

import argparse
from copy import copy, deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

W_URI = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_URI = "http://schemas.openxmlformats.org/officeDocument/2006/math"
XML_URI = "http://www.w3.org/XML/1998/namespace"
W_PREFIX = "{" + W_URI + "}"
M_PREFIX = "{" + M_URI + "}"
XML_SPACE = "{" + XML_URI + "}space"

# Unicode-lossless tokenizer (handles Latin, accented surnames, Greek, CJK, underscores, symbols)
CJK_RANGE = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
TOKEN_RE = re.compile(
    rf"[{CJK_RANGE}]"
    rf"|(?:[^\W_{CJK_RANGE}]+(?:['’][^\W_{CJK_RANGE}]+)*)"
    rf"|_"
    rf"|\s+"
    rf"|[^\w\s]",
    re.UNICODE,
)
WORD_COUNT_RE = re.compile(
    rf"[{CJK_RANGE}]|(?:[^\W_{CJK_RANGE}]+(?:['’\-][^\W_{CJK_RANGE}]+)*)",
    re.UNICODE,
)
NS_DECL_RE = re.compile(rb'xmlns(?::([A-Za-z0-9_\-]+))?="([^"]+)"')
NUM_TOKEN_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:[Ee][-+]?\d+)?")
OP_SYMBOL_RE = re.compile(r"[<>≤≥=±%‰×~≈]")

DEFAULT_MAX_OP_WORDS = 8
DEFAULT_MIN_SIMILARITY = 0.65
DEFAULT_TARGET_SECTION_DRIFT = 0.05
DEFAULT_MAX_SECTION_DRIFT = 0.08
DEFAULT_MAX_TOTAL_DRIFT = 0.05
DEFAULT_SHORT_SECTION_FLOOR_WORDS = 12

REFERENCE_HEADING_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:references|bibliography|literature\s+cited|works\s+cited|reference\s+list|参考文献|参考文献目录)\s*:?$",
    re.I,
)
MD_HEADING_RE = re.compile(r"^#{1,4}\s+(.+?)\s*#*$")
PLAIN_SECTION_HEADING_RE = re.compile(
    r"^(?:"
    r"(?:\d+(?:\.\d+)*\.?\s+)[A-Z][A-Za-z0-9\s,\-–:/&()]{1,90}"
    r"|(?:abstract|summary|highlights|keywords|introduction|background|"
    r"materials\s+and\s+methods|methods|methodology|study\s+area|data\s+and\s+methods|"
    r"results|results\s+and\s+discussion|discussion|conclusions?|concluding\s+remarks|"
    r"limitations|data\s+availability|code\s+availability|author\s+contributions|"
    r"acknowledgements?|competing\s+interests|conflict\s+of\s+interest|"
    r"figure\s+captions?|table\s+captions?|supplementary\s+information)"
    r")\s*:?$",
    re.I,
)
DOCX_HEADING_STYLE_RE = re.compile(r"^(?:heading\s*[1-4]|title|subtitle|\d+)$", re.I)

# Conservative plain-text citation detectors (false positives protect citations rather than corrupt them)
PAREN_CITE_RE = re.compile(
    r"\((?=[^()]{0,260}(?:[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÿ'’\-]+\s*,?\s*(?:18|19|20)\d{2}[a-z]?\b|"
    r"et\s+al\.\s*,?\s*(?:18|19|20)\d{2}[a-z]?\b))[^()]{0,260}\)"
)
NARRATIVE_CITE_RE = re.compile(
    r"\b[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÿ'’\-]+(?:\s+et\s+al\.)?"
    r"(?:\s+(?:and|&)\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÿ'’\-]+)?\s*\((?:18|19|20)\d{2}[a-z]?\)"
)
NUMERIC_CITE_RE = re.compile(r"(?<!\w)\[(?:\s*\d{1,4}(?:\s*[-–,;]\s*\d{1,4})*\s*)\]")
SUP_CITE_TEXT_RE = re.compile(r"^[\s,;\-–0-9]+$")
CITATION_BOOKMARK_RE = re.compile(
    r"zotero|endnote|mendeley|noteexpress|citation|csl|ne\.ref|en\.cite",
    re.I,
)

TYPOGRAPHY_TRANS = str.maketrans({
    "\u00a0": " ",  # NBSP
    "\u2009": " ",  # thin space
    "\u202f": " ",  # narrow NBSP
    "\u2007": " ",  # figure space
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2212": "-",  # Unicode minus sign
})


def q(local: str) -> str:
    return W_PREFIX + local


def mq(local: str) -> str:
    return M_PREFIX + local


class TrackChangeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Unicode-lossless tokenization, typography & numeric/operator guards
# ---------------------------------------------------------------------------

def tokenize_with_offsets(s: str):
    out = [(m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(s)]
    if "".join(t[0] for t in out) != s:
        raise TrackChangeError(f"Tokenizer lossless invariant violated for input length {len(s)}")
    return out


def normalize_typography(s: str) -> str:
    return unicodedata.normalize("NFC", s).translate(TYPOGRAPHY_TRANS)


def is_invisible_only_diff(a: str, b: str) -> bool:
    return a != b and normalize_typography(a) == normalize_typography(b)


def extract_numbers(s: str):
    return NUM_TOKEN_RE.findall(s)


def same_numbers_and_operators(a: str, b: str) -> tuple[bool, str]:
    if NUM_TOKEN_RE.findall(a) != NUM_TOKEN_RE.findall(b):
        return False, "numerical tokens altered"
    if OP_SYMBOL_RE.findall(a) != OP_SYMBOL_RE.findall(b):
        return False, "mathematical or statistical operator/symbol altered (< > ≤ ≥ = ± % ‰ × ~ ≈)"
    return True, ""


def count_span_words(s: str) -> int:
    return len(WORD_COUNT_RE.findall(s))


def word_level_opcodes(before: str, after: str):
    """Return Unicode-lossless word/token-aligned opcodes (tag, a0, a1, b0, b1)."""
    tb = tokenize_with_offsets(before)
    ta = tokenize_with_offsets(after)
    b_toks = [x[0] for x in tb]
    a_toks = [x[0] for x in ta]
    raw_ops = SequenceMatcher(None, b_toks, a_toks, autojunk=False).get_opcodes()

    char_ops = []
    for tag, i1, i2, j1, j2 in raw_ops:
        a0 = tb[i1][1] if i1 < len(tb) else len(before)
        a1 = tb[i2 - 1][2] if (i2 > i1 and i2 - 1 < len(tb)) else a0
        b0 = ta[j1][1] if j1 < len(ta) else len(after)
        b1 = ta[j2 - 1][2] if (j2 > j1 and j2 - 1 < len(ta)) else b0
        char_ops.append([tag, a0, a1, b0, b1])

    merged = []
    for op in char_ops:
        if not merged:
            merged.append(op)
            continue
        prev = merged[-1]
        if prev[0] != "equal" and op[0] != "equal":
            merged[-1] = ["replace", prev[1], op[2], prev[3], op[4]]
        elif (
            len(merged) >= 2
            and merged[-1][0] == "equal"
            and merged[-2][0] != "equal"
            and op[0] != "equal"
            and before[merged[-1][1] : merged[-1][2]].isspace()
            and after[merged[-1][3] : merged[-1][4]].isspace()
        ):
            merged.pop()
            prev_edit = merged.pop()
            merged.append(["replace", prev_edit[1], op[2], prev_edit[3], op[4]])
        else:
            merged.append(op)
    return [tuple(x) for x in merged]


def locate_and_reconcile_typography(para_txt: str, before: str, after: str):
    """Locate `before` in `para_txt`; fall back to normalized typography matching cleanly.

    Preserves original NBSP/curly quotes on unchanged tokens so zero ghost diffs appear.
    """
    cnt = para_txt.count(before)
    if cnt == 1:
        return para_txt.index(before), before, after
    if cnt > 1:
        return None

    norm_para = normalize_typography(para_txt)
    norm_before = normalize_typography(before)
    if len(norm_para) != len(para_txt) or len(norm_before) != len(before):
        return None
    if norm_para.count(norm_before) != 1:
        return None
    start = norm_para.index(norm_before)
    actual_before = para_txt[start : start + len(before)]
    norm_after = normalize_typography(after)
    if norm_before == norm_after or len(norm_after) != len(after):
        return None

    ops = word_level_opcodes(norm_before, norm_after)
    rebuilt = []
    for tag, a0, a1, b0, b1 in ops:
        rebuilt.append(actual_before[a0:a1] if tag == "equal" else after[b0:b1])
    return start, actual_before, "".join(rebuilt)


def check_surgical_granularity(
    before: str,
    after: str,
    codes,
    label: str,
    max_op_words: int = DEFAULT_MAX_OP_WORDS,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    allow_structural: bool = False,
):
    """Block whole-sentence / whole-paragraph rewrites in default surgical mode."""
    non_eq = [op for op in codes if op[0] != "equal"]
    max_del_w = max((count_span_words(before[a0:a1]) for _, a0, a1, _, _ in non_eq), default=0)
    max_ins_w = max((count_span_words(after[b0:b1]) for _, _, _, b0, b1 in non_eq), default=0)
    sim = SequenceMatcher(None, before, after, autojunk=False).ratio()

    if not allow_structural:
        if max(max_del_w, max_ins_w) > max_op_words:
            raise TrackChangeError(
                f"EDIT_TOO_WIDE ({label}): atomic change span is too large "
                f"(del={max_del_w} words, ins={max_ins_w} words > cap {max_op_words}). "
                "Keep edits surgical at the word/short-phrase scale instead of rewriting whole "
                "sentences or paragraphs. For an unavoidable structural split, get author approval "
                "and unlock that single item with allow_structural."
            )
        if sim < min_similarity and max(max_del_w, max_ins_w) > 3 and count_span_words(before) >= 8:
            raise TrackChangeError(
                f"REWRITE_TOO_HEAVY ({label}): text similarity dropped to {sim:.2f} "
                f"(< floor {min_similarity:.2f}; del={max_del_w}w, ins={max_ins_w}w). "
                "Preserve the original sentence skeleton and edit only problematic words/phrases; "
                "for an unavoidable structural rewrite, get author approval and unlock with allow_structural."
            )
    return max_del_w, max_ins_w, round(sim, 3)


# ---------------------------------------------------------------------------
# XML namespace preservation & canonicalization helpers (stdlib only)
# ---------------------------------------------------------------------------

def canonical_xml(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return ET.canonicalize(ET.tostring(el, encoding="unicode"))


def extract_root_namespaces(raw_xml: bytes):
    end = raw_xml.find(b">")
    if raw_xml.startswith(b"<?xml"):
        decl_end = raw_xml.find(b"?>")
        if decl_end != -1:
            start_root = raw_xml.find(b"<", decl_end + 2)
            end = raw_xml.find(b">", start_root)
            head = raw_xml[start_root : end + 1]
        else:
            head = raw_xml[: end + 1]
    else:
        head = raw_xml[: end + 1]
    decls = []
    for m in NS_DECL_RE.finditer(head):
        prefix = m.group(1).decode("utf-8") if m.group(1) else ""
        uri = m.group(2).decode("utf-8")
        decls.append((prefix, uri))
    return decls


def parse_xml_preserve_ns(raw_xml: bytes):
    decls = extract_root_namespaces(raw_xml)
    for prefix, uri in decls:
        ET.register_namespace(prefix, uri)
    root = ET.fromstring(raw_xml)
    return root, decls


def serialize_xml_preserve_ns(root: ET.Element, orig_decls) -> bytes:
    for prefix, uri in orig_decls:
        ET.register_namespace(prefix, uri)
    body = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    first_gt = body.find(b">")
    if first_gt != -1:
        open_tag = body[:first_gt]
        missing = []
        for prefix, uri in orig_decls:
            attr = (f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"').encode("utf-8")
            key = (f"xmlns:{prefix}=" if prefix else "xmlns=").encode("utf-8")
            if key not in open_tag:
                missing.append(attr)
        if missing:
            insert_pos = first_gt - 1 if body[first_gt - 1 : first_gt] == b"/" else first_gt
            body = body[:insert_pos] + b" " + b" ".join(missing) + body[insert_pos:]
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body


# ---------------------------------------------------------------------------
# Strict paragraph-own OOXML projection (nested textbox w:p isolated)
# ---------------------------------------------------------------------------

def own_elements_with_ancestors(p: ET.Element):
    """Yield (element, ancestors_below_p) owned strictly by paragraph p.

    Subtrees rooted at any nested <w:p> (e.g. inside <w:txbxContent>) are skipped
    so nested textbox paragraphs never shift offsets or leak field state.
    """
    stack = [(ch, ()) for ch in reversed(list(p))]
    while stack:
        el, anc = stack.pop()
        if el.tag == q("p"):
            continue
        yield el, anc
        children = list(el)
        if children:
            next_anc = anc + (el,)
            for ch in reversed(children):
                stack.append((ch, next_anc))


def element_visible_text(el: ET.Element, own_paragraph: bool = False) -> str:
    """Accepted visible text (excludes <w:del>, <w:delText>, <w:moveFrom>, <w:instrText>)."""
    parts = []
    if own_paragraph:
        for node, anc in own_elements_with_ancestors(el):
            if node.tag == q("t") and node.text:
                if not any(a.tag in (q("del"), q("moveFrom"), q("instrText")) for a in anc):
                    parts.append(node.text)
        return "".join(parts)

    def walk(node, skip_nested_p=False):
        if skip_nested_p and node.tag == q("p"):
            return
        if node.tag in (q("del"), q("delText"), q("moveFrom"), q("instrText")):
            return
        if node.tag == q("t") and node.text:
            parts.append(node.text)
        for ch in node:
            walk(ch, skip_nested_p=True)

    walk(el, skip_nested_p=False)
    return "".join(parts)


def element_accepted_text(p: ET.Element) -> str:
    return element_visible_text(p, own_paragraph=True)


def element_rejected_text(p: ET.Element) -> str:
    """Text projection if all <w:ins>/<w:moveTo> are rejected and <w:delText> restored."""
    parts = []
    for node, anc in own_elements_with_ancestors(p):
        if node.tag in (q("t"), q("delText")) and node.text:
            if not any(a.tag in (q("ins"), q("moveTo"), q("instrText")) for a in anc):
                parts.append(node.text)
    return "".join(parts)


def project_paragraph_chars(p: ET.Element, view: str = "accepted"):
    """Return [(char, canonical_rPr_sig), ...] owned strictly by paragraph p."""
    items = []
    for node, anc in own_elements_with_ancestors(p):
        if node.tag not in (q("t"), q("delText")):
            continue
        if any(a.tag == q("instrText") for a in anc):
            continue
        has_del = node.tag == q("delText") or any(a.tag in (q("del"), q("moveFrom")) for a in anc)
        has_ins = any(a.tag in (q("ins"), q("moveTo")) for a in anc)
        include = (not has_del) if view == "accepted" else (not has_ins)
        if not include:
            continue
        run = next((a for a in reversed(anc) if a.tag == q("r")), None)
        if run is None:
            continue
        sig = canonical_xml(run.find(q("rPr")))
        for ch in (node.text or ""):
            items.append((ch, sig))
    return items


def is_plain_text_run(r: ET.Element) -> bool:
    if r.tag != q("r"):
        return False
    children = [ch for ch in r if ch.tag != q("rPr")]
    return bool(children) and all(ch.tag == q("t") for ch in children)


def is_plain_or_del_run(r: ET.Element) -> bool:
    if r.tag != q("r"):
        return False
    return all(ch.tag in (q("rPr"), q("t"), q("delText")) for ch in r)


def run_style_sig(r: ET.Element) -> str:
    return canonical_xml(r.find(q("rPr")))


def run_has_special_format(r: ET.Element) -> bool:
    """True if run carries superscript/subscript (vertAlign) or explicit italic (w:i)."""
    rpr = r.find(q("rPr"))
    if rpr is None:
        return False
    va = rpr.find(q("vertAlign"))
    if va is not None and (va.get(q("val")) or "").lower() in ("superscript", "subscript"):
        return True
    ital = rpr.find(q("i"))
    if ital is not None:
        val = (ital.get(q("val")) or "true").lower()
        if val not in ("0", "false", "off"):
            return True
    return False


def has_existing_revisions(root: ET.Element) -> bool:
    for tag in (q("ins"), q("del"), q("moveFrom"), q("moveTo")):
        if root.find(".//" + tag) is not None:
            return True
    return False


def collect_body_paragraphs(body: ET.Element):
    """Return [(parent_el, p_el), ...] for every <w:p> inside <w:body> in document order."""
    records = []

    def walk(parent: ET.Element):
        for ch in list(parent):
            if ch.tag == q("p"):
                records.append((parent, ch))
            walk(ch)

    walk(body)
    return records


def find_references_start_index(paras) -> int:
    for idx, p in enumerate(paras):
        txt = element_accepted_text(p).strip()
        if REFERENCE_HEADING_RE.match(txt):
            return idx
    return len(paras)


# ---------------------------------------------------------------------------
# Provider-agnostic Citation & Reference-List Protection Shield
# ---------------------------------------------------------------------------

def _merge_spans(regions):
    if not regions:
        return []
    out = []
    for a, b, reason in sorted(regions, key=lambda x: (x[0], x[1])):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            old = out.pop()
            labels = set(old[2].split("; ")) | set(reason.split("; "))
            out.append((old[0], max(old[1], b), "; ".join(sorted(labels))))
        else:
            out.append((a, b, reason))
    return out


def detect_plain_text_citation_spans(text: str):
    """Detect conservative plain-text citation spans in Markdown/text or DOCX prose."""
    regs = []
    for pat, label in (
        (PAREN_CITE_RE, "AUTHOR_YEAR_CITATION"),
        (NARRATIVE_CITE_RE, "NARRATIVE_CITATION"),
        (NUMERIC_CITE_RE, "NUMERIC_CITATION"),
    ):
        for m in pat.finditer(text):
            regs.append((m.start(), m.end(), label))
    return _merge_spans(regs)


def paragraph_protected_regions(p: ET.Element, in_references: bool = False):
    """Compute immutable citation/field/bookmark spans on accepted text offsets of p."""
    whole = element_accepted_text(p)
    if in_references:
        return ([(0, len(whole), "REFERENCE_LIST")] if whole else []), whole

    regs = []
    pos = 0
    field_depth = 0
    bookmark_starts = {}

    for node, anc in own_elements_with_ancestors(p):
        if any(a.tag in (q("del"), q("moveFrom"), q("instrText")) for a in anc):
            continue
        if node.tag == q("fldChar"):
            ft = node.get(q("fldCharType"))
            if ft == "begin":
                field_depth += 1
            elif ft == "end":
                field_depth = max(0, field_depth - 1)
            continue
        if node.tag == q("bookmarkStart"):
            bname = node.get(q("name")) or ""
            bid = node.get(q("id"))
            if bid is not None and CITATION_BOOKMARK_RE.search(bname):
                bookmark_starts[bid] = pos
            continue
        if node.tag == q("bookmarkEnd"):
            bid = node.get(q("id"))
            if bid in bookmark_starts:
                regs.append((bookmark_starts.pop(bid), pos, "CITATION_BOOKMARK"))
            continue
        if node.tag != q("t"):
            continue

        val = node.text or ""
        end = pos + len(val)
        in_container = any(
            a.tag in (q("fldSimple"), q("sdt"), q("hyperlink"), q("smartTag"), mq("oMath"), mq("oMathPara"))
            for a in anc
        )
        run = next((a for a in reversed(anc) if a.tag == q("r")), None)
        is_sup_num = False
        if run is not None and val.strip():
            rpr = run.find(q("rPr"))
            va = rpr.find(q("vertAlign")) if rpr is not None else None
            if va is not None and (va.get(q("val")) or "").lower() == "superscript":
                if SUP_CITE_TEXT_RE.match(val.strip()) and any(ch.isdigit() for ch in val):
                    is_sup_num = True

        if val and (field_depth > 0 or in_container or is_sup_num):
            kind = "SUPERSCRIPT_NUMERIC_CITATION" if (is_sup_num and field_depth == 0 and not in_container) else "WORD_FIELD_OR_CONTAINER"
            regs.append((pos, end, kind))
        pos = end

    for a, b, label in detect_plain_text_citation_spans(whole):
        regs.append((a, b, label))

    return _merge_spans(regs), whole


def build_reference_manifest(doc_root: ET.Element):
    body = doc_root.find(q("body"))
    if body is None:
        return []
    paras = [p for _, p in collect_body_paragraphs(body)]
    ref_start = find_references_start_index(paras)
    out = []
    for i, p in enumerate(paras):
        in_refs = i >= ref_start
        regions, text = paragraph_protected_regions(p, in_references=in_refs)
        out.append({
            "index": i,
            "in_refs": in_refs,
            "text": text,
            "regions": regions,
            "protected": [(text[a:b], label) for a, b, label in regions],
        })
    return out


def assert_edit_safe_for_citations(
    manifest_row: dict,
    offset: int,
    before: str,
    after: str,
    codes,
    allow_references: bool = False,
):
    if manifest_row["in_refs"] and not allow_references:
        raise TrackChangeError(
            f"REFERENCE_LIST_PROTECTED (paragraph {manifest_row['index']}): "
            "References/Bibliography entries are immutable during plain-language smoothing."
        )
    for tag, a0, a1, _, _ in codes:
        if tag == "equal":
            continue
        left, right = offset + a0, offset + a1
        for rs, re_, kind in manifest_row["regions"]:
            overlaps = (left < re_ and right > rs) if left < right else (rs <= left <= re_)
            if overlaps:
                raise TrackChangeError(
                    f"PROTECTED_CITATION_OR_FIELD (paragraph {manifest_row['index']}): "
                    f"edit touches protected {kind} span ({rs}:{re_}). Keep citations untouched or route to Author Query."
                )


def assert_text_citations_preserved(before: str, after: str, label: str):
    """Ensure plain-text citations in Markdown/text diffs are never altered or deleted."""
    b_cites = [before[a:b] for a, b, _ in detect_plain_text_citation_spans(before)]
    a_cites = [after[a:b] for a, b, _ in detect_plain_text_citation_spans(after)]
    if b_cites != a_cites:
        raise TrackChangeError(
            f"PROTECTED_CITATION_ALTERED ({label}): in-text citations changed "
            f"(before={b_cites[:4]}, after={a_cites[:4]}). Keep all citations verbatim."
        )


# ---------------------------------------------------------------------------
# V1.1/V1.2 Per-Section Word-Count Parity Engine (DOCX + Markdown/Plain Text)
# ---------------------------------------------------------------------------

def detect_text_heading(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None
    m = MD_HEADING_RE.match(s)
    if m:
        return m.group(1).strip()
    wc = count_span_words(s)
    if 1 <= wc <= 14 and not s.endswith((".", "?", "!")) and PLAIN_SECTION_HEADING_RE.match(s):
        return s.rstrip(":").strip()
    return None


def segment_text_sections(text: str):
    """Split Markdown or plain text into ordered sections with body word counts."""
    buckets = []
    cur_name = None
    cur_words = 0

    for raw_line in text.splitlines():
        s = raw_line.strip()
        if not s:
            continue
        heading = detect_text_heading(s)
        if heading is not None:
            if REFERENCE_HEADING_RE.match(heading):
                break
            if cur_name is not None and cur_words > 0:
                buckets.append({"section": cur_name, "words": cur_words})
            cur_name = heading
            cur_words = 0
            continue
        if cur_name is None:
            cur_name = "Body"
        cur_words += count_span_words(s)

    if cur_name is not None and cur_words > 0:
        buckets.append({"section": cur_name, "words": cur_words})
    if not buckets:
        buckets.append({"section": "Body", "words": 0})
    return buckets


def detect_docx_heading(parent: ET.Element, body: ET.Element, p: ET.Element, text: str) -> str | None:
    if parent is not body:
        return None
    s = text.strip()
    if not s:
        return None
    ppr = p.find(q("pPr"))
    if ppr is not None:
        pstyle = ppr.find(q("pStyle"))
        if pstyle is not None:
            val = (pstyle.get(q("val")) or "").strip()
            wc = count_span_words(s)
            if DOCX_HEADING_STYLE_RE.match(val) and 1 <= wc <= 18 and not s.endswith((".", "?", "!")):
                return s.rstrip(":").strip()
    return detect_text_heading(s)


def segment_docx_sections(para_records, body: ET.Element, ref_start: int):
    """Map body paragraphs before References into ordered (section_name, [para_indices])."""
    groups = []
    cur_name = None
    cur_indices = []
    cur_words = 0

    for idx in range(ref_start):
        parent, p = para_records[idx]
        txt = element_accepted_text(p).strip()
        if not txt:
            continue
        heading = detect_docx_heading(parent, body, p, txt)
        if heading is not None:
            if cur_name is not None and cur_words > 0:
                groups.append((cur_name, cur_indices))
            cur_name = heading
            cur_indices = []
            cur_words = 0
            continue
        if cur_name is None:
            cur_name = "Body"
        cur_indices.append(idx)
        cur_words += count_span_words(txt)

    if cur_name is not None and cur_words > 0:
        groups.append((cur_name, cur_indices))
    if not groups:
        groups.append(("Body", []))
    return groups


def evaluate_section_parity(
    before_sections,
    after_sections,
    max_section_drift: float = DEFAULT_MAX_SECTION_DRIFT,
    target_section_drift: float = DEFAULT_TARGET_SECTION_DRIFT,
    max_total_drift: float = DEFAULT_MAX_TOTAL_DRIFT,
    short_section_floor: int = DEFAULT_SHORT_SECTION_FLOOR_WORDS,
    allow_length_change: bool = False,
):
    """Verify per-section and whole-manuscript word-count parity."""
    rows = []
    failures = []
    warnings = []
    if len(before_sections) != len(after_sections):
        msg = (
            f"SECTION_STRUCTURE_CHANGED: before has {len(before_sections)} section(s) "
            f"({[s['section'] for s in before_sections]}), after has {len(after_sections)} section(s) "
            f"({[s['section'] for s in after_sections]})."
        )
        if not allow_length_change:
            raise TrackChangeError(
                msg + " Keep every manuscript section intact or pass --allow-length-change after author approval."
            )
        failures.append(msg)

    n_pairs = min(len(before_sections), len(after_sections))
    for i in range(n_pairs):
        name = before_sections[i]["section"]
        bw = int(before_sections[i]["words"])
        aw = int(after_sections[i]["words"])
        delta = aw - bw
        drift_pct = (delta / bw) if bw > 0 else (0.0 if aw == 0 else 1.0)
        allowed_delta = max(short_section_floor, round(bw * max_section_drift))
        target_delta = max(8, round(bw * target_section_drift))

        if abs(delta) > allowed_delta:
            st = "FAIL"
            failures.append(
                f"{name}: {bw} -> {aw} ({delta:+d}w, {drift_pct * 100:+.1f}%; cap ±{allowed_delta}w / ±{max_section_drift * 100:.0f}%)"
            )
        elif abs(delta) > target_delta:
            st = "WARN"
            warnings.append(
                f"{name}: {bw} -> {aw} ({delta:+d}w, {drift_pct * 100:+.1f}%; ideal <=±{target_section_drift * 100:.0f}%)"
            )
        else:
            st = "PASS"

        rows.append({
            "section": name,
            "before_words": bw,
            "after_words": aw,
            "delta_words": delta,
            "drift_pct": round(drift_pct * 100, 1),
            "allowed_delta_words": allowed_delta,
            "status": st,
        })

    total_b = sum(int(s["words"]) for s in before_sections)
    total_a = sum(int(s["words"]) for s in after_sections)
    total_delta = total_a - total_b
    total_drift = (total_delta / total_b) if total_b > 0 else 0.0
    allowed_total = max(short_section_floor, round(total_b * max_total_drift))
    if abs(total_delta) > allowed_total:
        total_status = "FAIL"
        failures.append(
            f"TOTAL: {total_b} -> {total_a} ({total_delta:+d}w, {total_drift * 100:+.1f}%; cap ±{allowed_total}w / ±{max_total_drift * 100:.0f}%)"
        )
    else:
        total_status = "PASS"

    overall = "FAIL" if failures else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    result = {
        "status": overall,
        "target_section_drift_pct": round(target_section_drift * 100, 1),
        "max_section_drift_pct": round(max_section_drift * 100, 1),
        "max_total_drift_pct": round(max_total_drift * 100, 1),
        "short_section_floor_words": short_section_floor,
        "sections": rows,
        "total": {
            "before_words": total_b,
            "after_words": total_a,
            "delta_words": total_delta,
            "drift_pct": round(total_drift * 100, 1),
            "allowed_delta_words": allowed_total,
            "status": total_status,
        },
        "failures": failures,
        "warnings": warnings,
    }

    if failures and not allow_length_change:
        raise TrackChangeError(
            "SECTION_WORD_DRIFT: Per-section word-count parity exceeded cap while smoothing manuscript -> "
            + "; ".join(failures)
            + ". Restore dropped details (without adding empty filler) so each section stays close to its original length, "
            "or get explicit author approval and pass --allow-length-change."
        )
    return result


def format_parity_markdown_table(parity: dict) -> str:
    lines = [
        "| Section | Before | After | Delta | Drift | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in parity["sections"]:
        lines.append(
            f"| {row['section']} | {row['before_words']} | {row['after_words']} | "
            f"{row['delta_words']:+d}w | {row['drift_pct']:+.1f}% | {row['status']} |"
        )
    tot = parity["total"]
    lines.append(
        f"| **TOTAL** | **{tot['before_words']}** | **{tot['after_words']}** | "
        f"**{tot['delta_words']:+d}w** | **{tot['drift_pct']:+.1f}%** | **{tot['status']}** |"
    )
    return "\n".join(lines)


def extract_sections_from_file(path: str):
    p = Path(path)
    if p.suffix.lower() == ".docx":
        with zipfile.ZipFile(p, "r") as zi:
            doc_root, _ = parse_xml_preserve_ns(zi.read("word/document.xml"))
        body = doc_root.find(q("body"))
        if body is None:
            raise TrackChangeError(f"DOCX missing <w:body>: {path}")
        para_records = collect_body_paragraphs(body)
        paras = [pr for _, pr in para_records]
        ref_start = find_references_start_index(paras)
        groups = segment_docx_sections(para_records, body, ref_start)
        return [
            {
                "section": name,
                "words": sum(count_span_words(element_accepted_text(paras[i])) for i in indices),
            }
            for name, indices in groups
        ]
    txt = p.read_text(encoding="utf-8", errors="replace")
    return segment_text_sections(txt)


# ---------------------------------------------------------------------------
# DOCX paragraph patching (strict run-style & zero-length block protection)
# ---------------------------------------------------------------------------

def clone_run_with_text(template_run: ET.Element, text: str, deletion: bool = False) -> ET.Element:
    rn = ET.Element(q("r"), dict(template_run.attrib))
    rpr = template_run.find(q("rPr"))
    if rpr is not None:
        rn.append(deepcopy(rpr))
    t = ET.SubElement(rn, q("delText" if deletion else "t"))
    t.text = text
    if text[:1].isspace() or text[-1:].isspace():
        t.set(XML_SPACE, "preserve")
    return rn


def wrap_revision(tag_name: str, rev_id: int, runs, author: str, when: str) -> ET.Element:
    node = ET.Element(q(tag_name))
    node.set(q("id"), str(rev_id))
    node.set(q("author"), author)
    node.set(q("date"), when)
    for r in runs:
        node.append(r)
    return node


def analyze_paragraph_segments(p: ET.Element):
    """Project direct children of <w:p> into (elem, text, editable, zero_len_immutable)."""
    metadata_tags = {
        q("pPr"),
        q("bookmarkStart"),
        q("bookmarkEnd"),
        q("commentRangeStart"),
        q("commentRangeEnd"),
        q("proofErr"),
        q("permStart"),
        q("permEnd"),
    }
    immutable_containers = {
        q("hyperlink"),
        q("sdt"),
        q("fldSimple"),
        q("smartTag"),
        mq("oMath"),
        mq("oMathPara"),
    }
    allowed = metadata_tags | immutable_containers | {q("r"), q("ins"), q("del")}
    unsupported = [ch.tag.rsplit("}", 1)[-1] for ch in p if ch.tag not in allowed]
    if unsupported:
        raise TrackChangeError("UNSUPPORTED_PARAGRAPH_XML: " + ",".join(sorted(set(unsupported))))

    segments = []
    field_depth = 0
    for ch in list(p):
        if ch.tag in metadata_tags:
            continue
        if ch.tag == q("r"):
            start_depth = field_depth
            has_fld = False
            for sub, _ in own_elements_with_ancestors(ch):
                if sub.tag == q("fldChar"):
                    has_fld = True
                    ft = sub.get(q("fldCharType"))
                    if ft == "begin":
                        field_depth += 1
                    elif ft == "end":
                        field_depth = max(0, field_depth - 1)
            in_field = has_fld or start_depth > 0 or field_depth > 0
            txt = element_visible_text(ch, own_paragraph=False)
            plain = (not in_field) and is_plain_text_run(ch)
            has_non_text = any(
                sub.tag in (q("drawing"), q("pict"), q("object"), q("tab"), q("br"), q("cr"), q("lastRenderedPageBreak"))
                for sub in ch
            )
            zero_imm = (not plain) and (len(txt) == 0) and (has_non_text or has_fld)
            segments.append((ch, txt, plain, zero_imm))
        elif ch.tag == q("ins"):
            txt = element_visible_text(ch, own_paragraph=False)
            segments.append((ch, txt, False, len(txt) == 0))
        elif ch.tag == q("del"):
            segments.append((ch, "", False, False))
        elif ch.tag in immutable_containers:
            txt = element_visible_text(ch, own_paragraph=False)
            is_math = ch.tag in (mq("oMath"), mq("oMathPara"))
            segments.append((ch, txt, False, is_math or len(txt) == 0))

    if "".join(t for _, t, _, _ in segments) != element_accepted_text(p):
        raise TrackChangeError("Paragraph segment projection mismatch; refusing unsafe XML structure.")
    return segments


def patch_paragraph_span(
    p: ET.Element,
    start: int,
    end: int,
    replacement: str,
    rev_id: int,
    author: str,
    when: str,
) -> int:
    segments = analyze_paragraph_segments(p)
    if not segments:
        raise TrackChangeError("Paragraph contains no text segments.")
    whole = "".join(t for _, t, _, _ in segments)
    if not (0 <= start <= end <= len(whole)):
        raise TrackChangeError("Replacement span out of bounds.")
    if start == end and not replacement:
        return rev_id

    offset = 0
    spans = []
    for ch, t, editable, zero_imm in segments:
        spans.append((offset, offset + len(t), ch, t, editable, zero_imm))
        offset += len(t)

    if start < end:
        touched = [s for s in spans if s[0] < end and s[1] > start]
        if not touched:
            raise TrackChangeError("Target span does not intersect paragraph text.")
        if not all(s[4] for s in touched):
            raise TrackChangeError(
                "PROTECTED_FIELD_OR_CONTAINER: Edit touches a protected citation field, "
                "equation, drawing, hyperlink, SDT control, break, or existing revision."
            )
        # Refuse edits crossing differently formatted runs (protects italics, bold, sub/superscripts)
        if len({run_style_sig(s[2]) for s in touched}) > 1:
            raise TrackChangeError(
                "CROSS_FORMAT_RUN_BOUNDARY: Edit crosses runs with different character formatting "
                "(e.g. italic/bold/subscript/superscript). Split the edit or route to Author Query."
            )
        first, last = touched[0], touched[-1]
        prefix_text = first[3][: max(0, start - first[0])]
        suffix_text = last[3][max(0, end - last[0]) :]
        removed_text = whole[start:end]
    else:
        # Pure insertion: refuse boundary next to zero-length equation/drawing/field
        if any(s[5] and s[0] == start for s in spans):
            raise TrackChangeError(
                "INSERTION_AT_IMMUTABLE_OBJECT: Pure insertion sits adjacent to an equation, drawing, "
                "break, or field boundary; expand context or route to Author Query."
            )
        left_cands = [s for s in spans if s[0] < start <= s[1]]
        right_cands = [s for s in spans if s[0] <= start < s[1]]
        left_s = left_cands[-1] if left_cands else None
        right_s = right_cands[0] if right_cands else None

        chosen = None
        if left_s and right_s and left_s is right_s:
            if not left_s[4]:
                raise TrackChangeError("Insertion point lies inside a non-plain run, container, or Word field.")
            chosen = left_s
        else:
            left_plain = bool(left_s and left_s[4])
            right_plain = bool(right_s and right_s[4])
            left_special = bool(left_plain and run_has_special_format(left_s[2]))
            right_special = bool(right_plain and run_has_special_format(right_s[2]))
            if left_plain and not left_special:
                chosen = left_s
            elif right_plain and not right_special:
                chosen = right_s
            elif left_special or right_special:
                raise TrackChangeError(
                    "SPECIAL_FORMAT_BLEED: Pure insertion adjacent to superscript/subscript/italic run "
                    "would inherit special formatting; expand span or route to Author Query."
                )
            else:
                raise TrackChangeError("Insertion point has no safe surrounding plain run.")

        touched = [chosen]
        first = chosen
        split = start - first[0]
        prefix_text = first[3][:split]
        suffix_text = first[3][split:]
        removed_text = ""

    new_nodes = []
    if prefix_text:
        new_nodes.append(clone_run_with_text(first[2], prefix_text, deletion=False))
    if removed_text:
        new_nodes.append(wrap_revision("del", rev_id, [clone_run_with_text(first[2], removed_text, deletion=True)], author, when))
        rev_id += 1
    if replacement:
        new_nodes.append(wrap_revision("ins", rev_id, [clone_run_with_text(first[2], replacement, deletion=False)], author, when))
        rev_id += 1
    if suffix_text:
        new_nodes.append(clone_run_with_text(first[2], suffix_text, deletion=False))

    children = list(p)
    insert_idx = children.index(first[2])
    for s in touched:
        p.remove(s[2])
    for idx_off, node in enumerate(new_nodes):
        p.insert(insert_idx + idx_off, node)
    return rev_id


def make_clean_accepted_tree(doc_root: ET.Element, settings_root: ET.Element):
    clean_doc = deepcopy(doc_root)
    clean_settings = deepcopy(settings_root)

    def accept_walk(parent: ET.Element):
        children = list(parent)
        i = 0
        while i < len(children):
            el = children[i]
            if el.tag == q("del"):
                parent.remove(el)
                children = list(parent)
                continue
            if el.tag == q("ins"):
                idx = list(parent).index(el)
                inner = list(el)
                parent.remove(el)
                for off, ch in enumerate(inner):
                    parent.insert(idx + off, ch)
                children = list(parent)
                continue
            accept_walk(el)
            i += 1

    accept_walk(clean_doc)
    for tr in list(clean_settings.findall(q("trackRevisions"))):
        clean_settings.remove(tr)
    return clean_doc, clean_settings


def next_revision_id(root: ET.Element) -> int:
    max_id = 0
    id_attr = q("id")
    for el in root.iter():
        val = el.get(id_attr)
        if val and val.isdigit():
            max_id = max(max_id, int(val))
    return max_id + 1


# ---------------------------------------------------------------------------
# Post-Write Original-Document Format & Reference Integrity Gate (stdlib only)
# ---------------------------------------------------------------------------

def _strip_only_plain_run_nodes(doc_root: ET.Element) -> str:
    """Keep all paragraph/table/section/field/math/drawing XML while stripping plain text runs."""
    cp = deepcopy(doc_root)
    for p in cp.iter(q("p")):
        for node in list(p):
            if is_plain_or_del_run(node):
                p.remove(node)
            elif node.tag in (q("ins"), q("del")) and len(node) and all(is_plain_or_del_run(ch) for ch in node):
                p.remove(node)
    return canonical_xml(cp)


def _check_character_styles(src_chars, dst_chars):
    orig = "".join(c for c, _ in src_chars)
    new = "".join(c for c, _ in dst_chars)
    matcher = SequenceMatcher(None, orig, new, autojunk=False)
    mismatch = 0
    first = None
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(a, b), range(c, d)):
                if src_chars[i][1] != dst_chars[j][1]:
                    mismatch += 1
                    if first is None:
                        first = {"original_index": i, "edited_index": j, "character": orig[i]}
        elif tag in ("insert", "replace") and c < d:
            local = {sig for _, sig in src_chars[a:b]}
            if not local:
                if a > 0:
                    local.add(src_chars[a - 1][1])
                if a < len(src_chars):
                    local.add(src_chars[a][1])
            if local:
                for j in range(c, d):
                    if dst_chars[j][1] not in local:
                        mismatch += 1
                        if first is None:
                            first = {
                                "original_index": a,
                                "edited_index": j,
                                "character": new[j],
                                "reason": "inserted text has foreign run style",
                            }
    return mismatch, first


def audit_docx_protection(
    source_path: str,
    target_path: str,
    view: str = "clean",
    allow_references: bool = False,
    max_flags: int = 30,
):
    """Strict post-write OOXML format, package, style, and citation protection audit."""
    if view not in ("clean", "tracked"):
        raise ValueError(f"view must be 'clean' or 'tracked', got {view!r}")
    errors = []

    with zipfile.ZipFile(source_path, "r") as zs, zipfile.ZipFile(target_path, "r") as zd:
        s_names = set(zs.namelist())
        d_names = set(zd.namelist())
        if s_names != d_names:
            errors.append({
                "type": "PACKAGE_MEMBERS_CHANGED",
                "removed": sorted(s_names - d_names)[:10],
                "added": sorted(d_names - s_names)[:10],
            })
        for name in sorted(s_names & d_names):
            if name in ("word/document.xml", "word/settings.xml"):
                continue
            if zs.read(name) != zd.read(name):
                errors.append({"type": "PROTECTED_PART_CHANGED", "file": name})
                if len(errors) >= max_flags:
                    break

        sr, _ = parse_xml_preserve_ns(zs.read("word/document.xml"))
        dr, _ = parse_xml_preserve_ns(zd.read("word/document.xml"))

        if _strip_only_plain_run_nodes(sr) != _strip_only_plain_run_nodes(dr):
            errors.append({
                "type": "DOCUMENT_NON_TEXT_STRUCTURE_OR_FORMAT_CHANGED",
                "note": "Check paragraph properties, section/page settings, tables, equations, images, fields, and protected OOXML nodes.",
            })

        s_body = sr.find(q("body"))
        d_body = dr.find(q("body"))
        sp = [p for _, p in collect_body_paragraphs(s_body)] if s_body is not None else []
        dp = [p for _, p in collect_body_paragraphs(d_body)] if d_body is not None else []
        if len(sp) != len(dp):
            errors.append({"type": "PARAGRAPH_COUNT_CHANGED", "source": len(sp), "edited": len(dp)})

        for n, (p_src, p_dst) in enumerate(zip(sp, dp)):
            x = project_paragraph_chars(p_src, view="accepted")
            if view == "tracked":
                rejected = project_paragraph_chars(p_dst, view="rejected")
                if x != rejected:
                    errors.append({"type": "ORIGINAL_TEXT_OR_FORMAT_NOT_RECOVERABLE", "paragraph_index": n})
                y = project_paragraph_chars(p_dst, view="accepted")
            else:
                y = project_paragraph_chars(p_dst, view="accepted")
            if x and not y:
                errors.append({"type": "NONEMPTY_PARAGRAPH_ERASED", "paragraph_index": n})
            mism, first = _check_character_styles(x, y)
            if mism:
                errors.append({
                    "type": "SURVIVING_TEXT_FONT_OR_RUN_STYLE_CHANGED",
                    "paragraph_index": n,
                    "characters": mism,
                    "first": first,
                })
            if len(errors) >= max_flags:
                break

        # Citation & bibliography manifest verification (evaluated on accepted view)
        s_man = build_reference_manifest(sr)
        if view == "tracked":
            acc_doc, _ = make_clean_accepted_tree(dr, ET.Element(q("settings")))
            d_man = build_reference_manifest(acc_doc)
        else:
            d_man = build_reference_manifest(dr)
        if len(s_man) != len(d_man):
            errors.append({"type": "REFERENCE_PARAGRAPH_COUNT_CHANGED", "from": len(s_man), "to": len(d_man)})
        else:
            for sm, dm in zip(s_man, d_man):
                if sm["in_refs"] != dm["in_refs"]:
                    errors.append({"type": "REFERENCE_SECTION_BOUNDARY_CHANGED", "paragraph_index": sm["index"]})
                elif sm["in_refs"] and not allow_references and sm["text"] != dm["text"]:
                    errors.append({"type": "BIBLIOGRAPHY_TEXT_CHANGED", "paragraph_index": sm["index"]})
                elif not sm["in_refs"] and sm["protected"] != dm["protected"]:
                    errors.append({
                        "type": "CITATION_OR_FIELD_RESULT_CHANGED",
                        "paragraph_index": sm["index"],
                        "before": sm["protected"][:6],
                        "after": dm["protected"][:6],
                    })
                if len(errors) >= max_flags:
                    break

        # Settings.xml: only <w:trackRevisions> may differ
        so, _ = parse_xml_preserve_ns(zs.read("word/settings.xml"))
        do, _ = parse_xml_preserve_ns(zd.read("word/settings.xml"))
        for root_s in (so, do):
            for tr in list(root_s.findall(q("trackRevisions"))):
                root_s.remove(tr)
        if canonical_xml(so) != canonical_xml(do):
            errors.append({"type": "WORD_SETTINGS_CHANGED", "note": "Only the trackRevisions flag may differ."})

        if view == "clean":
            if has_existing_revisions(dr):
                errors.append({"type": "CLEAN_HAS_REVISIONS"})
        else:
            for tag in ("rPrChange", "pPrChange", "sectPrChange", "tblPrChange"):
                if dr.find(".//" + q(tag)) is not None:
                    errors.append({"type": "FORMATTING_REVISION_FOUND", "tag": tag})

    return {
        "status": "PASS" if not errors else "BLOCK",
        "source": str(source_path),
        "target": str(target_path),
        "view": view,
        "errors": errors[:max_flags],
        "protected_reference_paragraphs": sum(1 for m in s_man if m["in_refs"]),
        "paragraphs_with_inline_citations": sum(1 for m in s_man if (not m["in_refs"]) and m["protected"]),
        "limitation": (
            "OOXML file-level validation only; does not execute live Zotero/EndNote/NoteExpress Word add-in refresh "
            "and does not guarantee identical page breaks when legitimate wording length changes."
        ),
    }


def audit_docx_pair(source_path: str, tracked_path: str, clean_path: str, allow_references: bool = False):
    x = audit_docx_protection(source_path, tracked_path, view="tracked", allow_references=allow_references)
    y = audit_docx_protection(source_path, clean_path, view="clean", allow_references=allow_references)
    errors = list(x["errors"]) + list(y["errors"])
    if x["status"] == "PASS" and y["status"] == "PASS":
        with zipfile.ZipFile(tracked_path, "r") as zt, zipfile.ZipFile(clean_path, "r") as zc:
            dt, _ = parse_xml_preserve_ns(zt.read("word/document.xml"))
            dc, _ = parse_xml_preserve_ns(zc.read("word/document.xml"))
        tp = [p for _, p in collect_body_paragraphs(dt.find(q("body")))]
        cp = [p for _, p in collect_body_paragraphs(dc.find(q("body")))]
        for i, (pt, pc) in enumerate(zip(tp, cp)):
            if project_paragraph_chars(pt, "accepted") != project_paragraph_chars(pc, "accepted"):
                errors.append({"type": "TRACKED_ACCEPTED_AND_CLEAN_MISMATCH", "paragraph_index": i})
                break
    return {"status": "PASS" if not errors else "BLOCK", "tracked": x, "clean": y, "errors": errors}


# ---------------------------------------------------------------------------
# Main DOCX Track-Changes Engine (Two-Pass + Rollback)
# ---------------------------------------------------------------------------

def apply_docx_tracked_changes(
    source_path: str,
    edits,
    tracked_out: str,
    clean_out: str | None = None,
    log_out: str | None = None,
    author: str = "Plain Scientific Writer",
    allow_references: bool = False,
    max_op_words: int = DEFAULT_MAX_OP_WORDS,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    allow_structural: bool = False,
    max_section_drift: float = DEFAULT_MAX_SECTION_DRIFT,
    max_total_drift: float = DEFAULT_MAX_TOTAL_DRIFT,
    short_section_floor: int = DEFAULT_SHORT_SECTION_FLOOR_WORDS,
    allow_length_change: bool = False,
    allow_number_change: bool = False,
    on_unsafe: str = "block",
):
    if on_unsafe not in ("block", "query"):
        raise TrackChangeError(f"on_unsafe must be 'block' or 'query', got {on_unsafe!r}")

    src = Path(source_path).resolve()
    trk = Path(tracked_out).resolve()
    cln = Path(clean_out).resolve() if clean_out else None

    if src == trk or (cln is not None and (src == cln or trk == cln)):
        raise TrackChangeError("Refusing to overwrite source or collide tracked/clean output paths.")

    with zipfile.ZipFile(src, "r") as zi:
        names = set(zi.namelist())
        if "word/document.xml" not in names or "word/settings.xml" not in names:
            raise TrackChangeError("Invalid DOCX: missing word/document.xml or word/settings.xml.")
        raw_doc = zi.read("word/document.xml")
        raw_settings = zi.read("word/settings.xml")
        doc_root, doc_decls = parse_xml_preserve_ns(raw_doc)
        settings_root, settings_decls = parse_xml_preserve_ns(raw_settings)

        if has_existing_revisions(doc_root):
            raise TrackChangeError(
                "Source DOCX already contains tracked revisions; accept/reject existing revisions first "
                "or provide a clean baseline copy so tracked changes stay unambiguous."
            )

        body = doc_root.find(q("body"))
        if body is None:
            raise TrackChangeError("DOCX missing <w:body>.")

        para_records = collect_body_paragraphs(body)
        paras = [p for _, p in para_records]
        orig_texts = [element_accepted_text(p) for p in paras]
        ref_start = find_references_start_index(paras)
        ref_manifest = build_reference_manifest(doc_root)

        # Detect front-matter indices (before Abstract) for transparent reporting
        abstract_idx = next(
            (i for i, t in enumerate(orig_texts[:20]) if t.strip().lower().rstrip(":") == "abstract"),
            None,
        )
        front_matter_indices = set(range(abstract_idx)) if abstract_idx is not None else set()

        docx_section_groups = segment_docx_sections(para_records, body, ref_start)
        before_sections = [
            {
                "section": name,
                "words": sum(count_span_words(orig_texts[i]) for i in indices),
            }
            for name, indices in docx_section_groups
        ]

        rev_id = next_revision_id(doc_root)
        when = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        skipped_unsafe = []
        planned_by_para: dict[int, list[dict]] = {}
        para_occupied_spans: dict[int, list[tuple[int, int, int]]] = {}

        def handle_unsafe(edit_idx: int, edit_obj: dict, msg: str):
            if on_unsafe == "block":
                raise TrackChangeError(msg)
            skipped_unsafe.append({
                "edit_index": edit_idx,
                "paragraph_index": edit_obj.get("paragraph_index"),
                "before": edit_obj.get("before", ""),
                "after": edit_obj.get("after", ""),
                "reason": msg,
            })

        # Pass 1: Validate every edit in ORIGINAL paragraph coordinates
        for idx, edit in enumerate(edits):
            before = edit.get("before")
            after = edit.get("after")
            if not isinstance(before, str) or not before or not isinstance(after, str):
                handle_unsafe(idx, edit, f"Edit {idx}: 'before' must be non-empty and 'after' a string.")
                continue
            if before == after:
                continue
            if is_invisible_only_diff(before, after):
                handle_unsafe(idx, edit, f"Edit {idx}: invisible-only typography diff (NBSP/curly quotes); refusing ghost revision.")
                continue

            item_allow_num = bool(allow_number_change or edit.get("allow_number_change", False))
            ok_num, num_msg = same_numbers_and_operators(before, after)
            if not ok_num and not item_allow_num:
                handle_unsafe(
                    idx,
                    edit,
                    f"Edit {idx}: NUMBER_OR_OPERATOR_ALTERED ({num_msg}); keep numeric values and math/stat operators verbatim "
                    "or pass allow_number_change after author authorization.",
                )
                continue

            if edit.get("paragraph_index") is not None:
                pi = int(edit["paragraph_index"])
                if 0 <= pi < len(paras):
                    loc = locate_and_reconcile_typography(orig_texts[pi], before, after)
                    candidates = [(pi, loc)] if loc is not None else []
                else:
                    candidates = []
            else:
                candidates = []
                for j, txt in enumerate(orig_texts):
                    loc = locate_and_reconcile_typography(txt, before, after)
                    if loc is not None:
                        candidates.append((j, loc))

            if len(candidates) != 1:
                handle_unsafe(
                    idx,
                    edit,
                    f"Edit {idx}: expected exactly 1 matching paragraph for 'before', found {len(candidates)}. "
                    "Provide a more specific 'before' phrase or explicit 'paragraph_index'.",
                )
                continue

            p_idx, (start, actual_before, actual_after) = candidates[0]
            if actual_before == actual_after or is_invisible_only_diff(actual_before, actual_after):
                handle_unsafe(idx, edit, f"Edit {idx}: invisible-only diff after typography reconciliation.")
                continue

            codes = word_level_opcodes(actual_before, actual_after)
            non_eq = [op for op in codes if op[0] != "equal"]
            if not non_eq:
                continue
            if any(is_invisible_only_diff(actual_before[a0:a1], actual_after[b0:b1]) for _, a0, a1, b0, b1 in non_eq):
                handle_unsafe(idx, edit, f"Edit {idx}: contains invisible-only typography sub-diff (NBSP/curly quotes).")
                continue

            item_allow_structural = bool(allow_structural or edit.get("allow_structural", False))
            try:
                max_del_w, max_ins_w, sim_ratio = check_surgical_granularity(
                    actual_before,
                    actual_after,
                    codes,
                    label=f"Edit {idx}, paragraph {p_idx}",
                    max_op_words=max_op_words,
                    min_similarity=min_similarity,
                    allow_structural=item_allow_structural,
                )
            except TrackChangeError as exc:
                handle_unsafe(idx, edit, str(exc))
                continue

            # Overlap check in original paragraph coordinates
            sub_spans = [(start + a0, start + a1) for _, a0, a1, _, _ in non_eq]
            occupied = para_occupied_spans.setdefault(p_idx, [])
            overlapped = False
            for s0, s1 in sub_spans:
                for o0, o1, prev_i in occupied:
                    is_ov = (
                        (s0 < o1 and o0 < s1)
                        if (s0 < s1 and o0 < o1)
                        else (s0 == o0 and s1 == o1) or (o0 < s0 < o1) or (s0 < o0 < s1)
                    )
                    if is_ov:
                        handle_unsafe(
                            idx,
                            edit,
                            f"Edit {idx}: overlapping target span with Edit {prev_i} in paragraph {p_idx} ({s0}:{s1} vs {o0}:{o1}).",
                        )
                        overlapped = True
                        break
                if overlapped:
                    break
            if overlapped:
                continue

            # Provider-agnostic citation & reference-list safety check
            try:
                assert_edit_safe_for_citations(
                    ref_manifest[p_idx],
                    start,
                    actual_before,
                    actual_after,
                    codes,
                    allow_references=allow_references,
                )
            except TrackChangeError as exc:
                handle_unsafe(idx, edit, f"Edit {idx}: {exc}")
                continue

            for s0, s1 in sub_spans:
                occupied.append((s0, s1, idx))

            planned_by_para.setdefault(p_idx, []).append({
                "edit_index": idx,
                "edit": edit,
                "paragraph_index": p_idx,
                "start": start,
                "before": actual_before,
                "after": actual_after,
                "codes": codes,
                "similarity": sim_ratio,
                "max_del_w": max_del_w,
                "max_ins_w": max_ins_w,
                "allow_structural": item_allow_structural,
            })

        # Pass 2: Apply planned edits per paragraph right-to-left in original coordinates
        audit_entries = []
        front_matter_touched = []
        for p_idx, plan_list in sorted(planned_by_para.items()):
            plan_list.sort(key=lambda x: x["start"], reverse=True)
            for item in plan_list:
                parent_el, orig_p = para_records[p_idx]
                current_txt = element_accepted_text(orig_p)
                start = item["start"]
                actual_before = item["before"]
                actual_after = item["after"]
                codes = item["codes"]
                idx = item["edit_index"]
                if current_txt[start : start + len(actual_before)] != actual_before:
                    handle_unsafe(idx, item["edit"], f"Edit {idx}: coordinate drift detected in paragraph {p_idx}.")
                    continue

                proposed = deepcopy(orig_p)
                local_start_id = rev_id
                ops_log = []
                try:
                    for tag, a0, a1, b0, b1 in reversed(codes):
                        if tag == "equal":
                            continue
                        rev_id = patch_paragraph_span(
                            proposed,
                            start + a0,
                            start + a1,
                            actual_after[b0:b1],
                            rev_id,
                            author,
                            when,
                        )
                        ops_log.append({
                            "kind": tag,
                            "deleted": actual_before[a0:a1],
                            "inserted": actual_after[b0:b1],
                        })
                    expected_after = current_txt[:start] + actual_after + current_txt[start + len(actual_before) :]
                    if element_accepted_text(proposed) != expected_after:
                        raise TrackChangeError(f"Edit {idx}: Accept-All text projection mismatch.")
                    if element_rejected_text(proposed) != orig_texts[p_idx]:
                        raise TrackChangeError(f"Edit {idx}: Reject-All text projection mismatch.")
                except TrackChangeError as exc:
                    rev_id = local_start_id
                    handle_unsafe(idx, item["edit"], str(exc))
                    continue

                pos = list(parent_el).index(orig_p)
                parent_el.remove(orig_p)
                parent_el.insert(pos, proposed)
                para_records[p_idx] = (parent_el, proposed)
                paras[p_idx] = proposed
                if p_idx in front_matter_indices:
                    front_matter_touched.append(p_idx)

                nums_before = extract_numbers(actual_before)
                nums_after = extract_numbers(actual_after)
                audit_entries.append({
                    "edit_index": idx,
                    "paragraph_index": p_idx,
                    "reason": item["edit"].get("reason", ""),
                    "granularity": "structural_unlocked" if item["allow_structural"] else "surgical_word_scale",
                    "similarity": item["similarity"],
                    "max_atomic_del_words": item["max_del_w"],
                    "max_atomic_ins_words": item["max_ins_w"],
                    "numbers_changed": nums_before != nums_after,
                    "numbers_before": nums_before,
                    "numbers_after": nums_after,
                    "revision_ids": list(range(local_start_id, rev_id)),
                    "word_ops": ops_log[::-1],
                })

        audit_entries.sort(key=lambda x: x["edit_index"])

        # Per-section word-count parity check (evaluated on accepted prose)
        after_sections = [
            {
                "section": name,
                "words": sum(count_span_words(element_accepted_text(paras[i])) for i in indices),
            }
            for name, indices in docx_section_groups
        ]
        parity_report = evaluate_section_parity(
            before_sections,
            after_sections,
            max_section_drift=max_section_drift,
            max_total_drift=max_total_drift,
            short_section_floor=short_section_floor,
            allow_length_change=allow_length_change,
        )

        # Enable Word Track Changes mode in settings.xml when edits were applied
        if audit_entries and settings_root.find(q("trackRevisions")) is None:
            settings_root.insert(0, ET.Element(q("trackRevisions")))

        tracked_doc_bytes = serialize_xml_preserve_ns(doc_root, doc_decls)
        tracked_settings_bytes = serialize_xml_preserve_ns(settings_root, settings_decls)
        ET.fromstring(tracked_doc_bytes)
        ET.fromstring(tracked_settings_bytes)

        trk.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(trk, "w") as zo:
            for info in zi.infolist():
                if info.filename == "word/document.xml":
                    data = tracked_doc_bytes
                elif info.filename == "word/settings.xml":
                    data = tracked_settings_bytes
                else:
                    data = zi.read(info.filename)
                zo.writestr(copy(info), data)

        with zipfile.ZipFile(trk, "r") as zchk:
            if zchk.testzip() is not None:
                trk.unlink(missing_ok=True)
                raise TrackChangeError(f"ZIP CRC verification failed for {trk}")

        if cln is not None:
            clean_doc_root, clean_settings_root = make_clean_accepted_tree(doc_root, settings_root)
            clean_doc_bytes = serialize_xml_preserve_ns(clean_doc_root, doc_decls)
            clean_settings_bytes = serialize_xml_preserve_ns(clean_settings_root, settings_decls)
            ET.fromstring(clean_doc_bytes)
            ET.fromstring(clean_settings_bytes)
            cln.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(cln, "w") as zo:
                for info in zi.infolist():
                    if info.filename == "word/document.xml":
                        data = clean_doc_bytes
                    elif info.filename == "word/settings.xml":
                        data = clean_settings_bytes
                    else:
                        data = zi.read(info.filename)
                    zo.writestr(copy(info), data)
            with zipfile.ZipFile(cln, "r") as zchk:
                if zchk.testzip() is not None:
                    trk.unlink(missing_ok=True)
                    cln.unlink(missing_ok=True)
                    raise TrackChangeError(f"ZIP CRC verification failed for {cln}")

        # Automatic Post-Write Original-Document Format & Reference Integrity Audit (with atomic rollback)
        if cln is not None:
            prot = audit_docx_pair(str(src), str(trk), str(cln), allow_references=allow_references)
        else:
            prot = audit_docx_protection(str(src), str(trk), view="tracked", allow_references=allow_references)

        if prot["status"] != "PASS":
            trk.unlink(missing_ok=True)
            if cln is not None:
                cln.unlink(missing_ok=True)
            raise TrackChangeError(
                "PROTECTION_AUDIT_FAILED: Output DOCX failed original-document format/citation protection "
                "(outputs rolled back): " + json.dumps(prot["errors"][:5], ensure_ascii=False)
            )

        status = (
            "PASS_PARTIAL_WITH_QUERIES"
            if skipped_unsafe
            else ("PASS" if audit_entries else "PASS_UNCHANGED")
        )
        report = {
            "status": status,
            "source": str(src),
            "tracked_output": str(trk),
            "clean_output": str(cln) if cln else None,
            "edit_count": len(audit_entries),
            "skipped_unsafe_count": len(skipped_unsafe),
            "numbers_changed_count": sum(1 for e in audit_entries if e["numbers_changed"]),
            "front_matter_paragraphs_touched": sorted(set(front_matter_touched)),
            "format_and_citation_protection": "PASS",
            "protection_limitation": (
                "OOXML file-level validation only; test live Zotero/EndNote/NoteExpress add-in refresh on a copy "
                "and visually inspect page layout in Word/LibreOffice."
            ),
            "section_word_counts": parity_report,
            "skipped_unsafe": skipped_unsafe,
            "edits": audit_entries,
        }
        if log_out:
            lp = Path(log_out)
            lp.parent.mkdir(parents=True, exist_ok=True)
            lp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report


# ---------------------------------------------------------------------------
# Markdown / Plain-text word-boundary tracked diff mode
# ---------------------------------------------------------------------------

def render_word_diff(before: str, after: str, fmt: str = "markdown") -> str:
    codes = word_level_opcodes(before, after)
    out = []
    for tag, a0, a1, b0, b1 in codes:
        if tag == "equal":
            out.append(before[a0:a1])
        elif tag == "delete":
            seg = before[a0:a1]
            out.append(f"<del>{seg}</del>" if fmt == "html" else f"~~{seg}~~")
        elif tag == "insert":
            seg = after[b0:b1]
            out.append(f"<ins>{seg}</ins>" if fmt == "html" else f"**{seg}**")
        elif tag == "replace":
            dseg = before[a0:a1]
            iseg = after[b0:b1]
            if fmt == "html":
                out.append(f"<del>{dseg}</del><ins>{iseg}</ins>")
            else:
                out.append(f"~~{dseg}~~ **{iseg}**")
    return "".join(out)


def build_text_tracked_diff(
    before_text: str,
    after_text: str,
    fmt: str = "markdown",
    max_op_words: int = DEFAULT_MAX_OP_WORDS,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    allow_structural: bool = False,
    max_section_drift: float = DEFAULT_MAX_SECTION_DRIFT,
    max_total_drift: float = DEFAULT_MAX_TOTAL_DRIFT,
    short_section_floor: int = DEFAULT_SHORT_SECTION_FLOOR_WORDS,
    allow_length_change: bool = False,
    allow_number_change: bool = False,
):
    before_sections = segment_text_sections(before_text)
    after_sections = segment_text_sections(after_text)
    parity = evaluate_section_parity(
        before_sections,
        after_sections,
        max_section_drift=max_section_drift,
        max_total_drift=max_total_drift,
        short_section_floor=short_section_floor,
        allow_length_change=allow_length_change,
    )

    b_paras = [p.strip() for p in re.split(r"\n\s*\n+", before_text.strip()) if p.strip()]
    a_paras = [p.strip() for p in re.split(r"\n\s*\n+", after_text.strip()) if p.strip()]

    lines = [
        "# Tracked Changes (Word-Boundary Surgical Revision View)",
        "",
        "Legend: deleted text is marked with strikethrough (`~~old~~` / `<del>`) and inserted text is marked in bold (`**new**` / `<ins>`).",
        "",
        "## Per-Section Word-Count Parity",
        "",
        format_parity_markdown_table(parity),
        "",
        "## Revised Text",
        "",
    ]

    sm = SequenceMatcher(None, b_paras, a_paras, autojunk=False)
    changed_blocks = 0
    for block_idx, (tag, i1, i2, j1, j2) in enumerate(sm.get_opcodes(), 1):
        if tag == "equal":
            for p in b_paras[i1:i2]:
                lines.append(p)
                lines.append("")
        elif tag == "replace":
            changed_blocks += 1
            b_chunk = "\n\n".join(b_paras[i1:i2])
            a_chunk = "\n\n".join(a_paras[j1:j2])
            assert_text_citations_preserved(b_chunk, a_chunk, label=f"Paragraph block {block_idx}")
            if not allow_number_change:
                ok_num, num_msg = same_numbers_and_operators(b_chunk, a_chunk)
                if not ok_num:
                    raise TrackChangeError(
                        f"NUMBER_OR_OPERATOR_ALTERED (Paragraph block {block_idx}): {num_msg}. "
                        "Keep numbers and math/stat operators intact or pass --allow-number-change after author approval."
                    )
            codes = word_level_opcodes(b_chunk, a_chunk)
            check_surgical_granularity(
                b_chunk,
                a_chunk,
                codes,
                label=f"Paragraph block {block_idx}",
                max_op_words=max_op_words,
                min_similarity=min_similarity,
                allow_structural=allow_structural,
            )
            lines.append(render_word_diff(b_chunk, a_chunk, fmt=fmt))
            lines.append("")
        elif tag == "delete":
            changed_blocks += 1
            if not allow_structural:
                raise TrackChangeError(
                    f"WHOLE_PARAGRAPH_DELETE (block {block_idx}): deleting whole paragraph(s) is blocked in default surgical mode; "
                    "pass --allow-structural after author approval."
                )
            for p in b_paras[i1:i2]:
                lines.append(f"<del>{p}</del>" if fmt == "html" else f"~~{p}~~")
                lines.append("")
        elif tag == "insert":
            changed_blocks += 1
            if not allow_structural:
                raise TrackChangeError(
                    f"WHOLE_PARAGRAPH_INSERT (block {block_idx}): inserting whole paragraph(s) is blocked in default surgical mode; "
                    "pass --allow-structural after author approval."
                )
            for p in a_paras[j1:j2]:
                lines.append(f"<ins>{p}</ins>" if fmt == "html" else f"**{p}**")
                lines.append("")

    if changed_blocks == 0:
        lines.append("*(No differences detected between before and after drafts.)*")
    return "\n".join(lines).rstrip() + "\n", parity


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_docx = sub.add_parser("docx", help="Apply native Word Track Changes (<w:del>/<w:ins>) with full protection.")
    p_docx.add_argument("source", help="Input baseline .docx file (never overwritten)")
    p_docx.add_argument("edits_json", help="JSON file of {before, after, reason?, paragraph_index?, allow_structural?, allow_number_change?} objects")
    p_docx.add_argument("--tracked", required=True, help="Output tracked-changes .docx path")
    p_docx.add_argument("--clean", help="Optional output clean accepted .docx path")
    p_docx.add_argument("--log", help="Optional JSON audit log output path")
    p_docx.add_argument("--author", default="Plain Scientific Writer", help="Revision author name shown in Word")
    p_docx.add_argument("--allow-references", action="store_true", help="Allow editing inside the References section")
    p_docx.add_argument("--max-op-words", type=int, default=DEFAULT_MAX_OP_WORDS)
    p_docx.add_argument("--min-sim", type=float, default=DEFAULT_MIN_SIMILARITY)
    p_docx.add_argument("--max-section-drift", type=float, default=DEFAULT_MAX_SECTION_DRIFT)
    p_docx.add_argument("--max-total-drift", type=float, default=DEFAULT_MAX_TOTAL_DRIFT)
    p_docx.add_argument("--short-section-floor", type=int, default=DEFAULT_SHORT_SECTION_FLOOR_WORDS)
    p_docx.add_argument("--on-unsafe", choices=["block", "query"], default="block", help="block stops on unsafe edits; query skips them into Author Queries")
    p_docx.add_argument("--allow-structural", action="store_true")
    p_docx.add_argument("--allow-length-change", action="store_true")
    p_docx.add_argument("--allow-number-change", action="store_true")

    p_text = sub.add_parser("text", help="Generate a word-boundary tracked diff + parity table for Markdown/text.")
    p_text.add_argument("before_file", help="Original draft .md/.txt path")
    p_text.add_argument("after_file", help="Revised draft .md/.txt path")
    p_text.add_argument("--out", required=True, help="Output tracked diff .md path")
    p_text.add_argument("--format", choices=["markdown", "html"], default="markdown")
    p_text.add_argument("--max-op-words", type=int, default=DEFAULT_MAX_OP_WORDS)
    p_text.add_argument("--min-sim", type=float, default=DEFAULT_MIN_SIMILARITY)
    p_text.add_argument("--max-section-drift", type=float, default=DEFAULT_MAX_SECTION_DRIFT)
    p_text.add_argument("--max-total-drift", type=float, default=DEFAULT_MAX_TOTAL_DRIFT)
    p_text.add_argument("--short-section-floor", type=int, default=DEFAULT_SHORT_SECTION_FLOOR_WORDS)
    p_text.add_argument("--allow-structural", action="store_true")
    p_text.add_argument("--allow-length-change", action="store_true")
    p_text.add_argument("--allow-number-change", action="store_true")

    p_parity = sub.add_parser("parity", help="Check per-section word-count parity between two .docx/.md/.txt files.")
    p_parity.add_argument("before_file", help="Original manuscript path (.docx/.md/.txt)")
    p_parity.add_argument("after_file", help="Smoothed manuscript path (.docx/.md/.txt)")
    p_parity.add_argument("--max-section-drift", type=float, default=DEFAULT_MAX_SECTION_DRIFT)
    p_parity.add_argument("--max-total-drift", type=float, default=DEFAULT_MAX_TOTAL_DRIFT)
    p_parity.add_argument("--short-section-floor", type=int, default=DEFAULT_SHORT_SECTION_FLOOR_WORDS)
    p_parity.add_argument("--json", action="store_true")

    p_ver = sub.add_parser("verify", help="Independently audit original-document format, citation, and parity protection on DOCX outputs.")
    p_ver.add_argument("source", help="Original baseline .docx path")
    p_ver.add_argument("edited", help="Edited .docx path (tracked if --tracked, else clean)")
    p_ver.add_argument("--tracked", action="store_true", help="Treat edited as tracked-changes copy")
    p_ver.add_argument("--clean", help="Optional clean copy to cross-check against tracked copy")
    p_ver.add_argument("--allow-references", action="store_true")
    p_ver.add_argument("--max-section-drift", type=float, default=DEFAULT_MAX_SECTION_DRIFT)
    p_ver.add_argument("--max-total-drift", type=float, default=DEFAULT_MAX_TOTAL_DRIFT)
    p_ver.add_argument("--short-section-floor", type=int, default=DEFAULT_SHORT_SECTION_FLOOR_WORDS)
    p_ver.add_argument("--json", action="store_true")

    args = parser.parse_args()
    try:
        if args.cmd == "docx":
            raw = json.loads(Path(args.edits_json).read_text(encoding="utf-8"))
            edits = raw["edits"] if isinstance(raw, dict) else raw
            report = apply_docx_tracked_changes(
                args.source,
                edits,
                args.tracked,
                clean_out=args.clean,
                log_out=args.log,
                author=args.author,
                allow_references=args.allow_references,
                max_op_words=args.max_op_words,
                min_similarity=args.min_sim,
                allow_structural=args.allow_structural,
                max_section_drift=args.max_section_drift,
                max_total_drift=args.max_total_drift,
                short_section_floor=args.short_section_floor,
                allow_length_change=args.allow_length_change,
                allow_number_change=args.allow_number_change,
                on_unsafe=args.on_unsafe,
            )
            tot = report["section_word_counts"]["total"]
            print(
                f"STATUS: {report['status']} | protection={report['format_and_citation_protection']} "
                f"| parity={report['section_word_counts']['status']} "
                f"| total_words={tot['before_words']}->{tot['after_words']} ({tot['delta_words']:+d}w, {tot['drift_pct']:+.1f}%) "
                f"| edits={report['edit_count']} | skipped_unsafe={report['skipped_unsafe_count']} "
                f"| tracked={report['tracked_output']}"
                + (f" | clean={report['clean_output']}" if report["clean_output"] else "")
            )
            print(format_parity_markdown_table(report["section_word_counts"]))
            if report["skipped_unsafe_count"] > 0 and args.on_unsafe == "query":
                sys.exit(3)
        elif args.cmd == "text":
            b_txt = Path(args.before_file).read_text(encoding="utf-8", errors="replace")
            a_txt = Path(args.after_file).read_text(encoding="utf-8", errors="replace")
            diff_md, parity = build_text_tracked_diff(
                b_txt,
                a_txt,
                fmt=args.format,
                max_op_words=args.max_op_words,
                min_similarity=args.min_sim,
                allow_structural=args.allow_structural,
                max_section_drift=args.max_section_drift,
                max_total_drift=args.max_total_drift,
                short_section_floor=args.short_section_floor,
                allow_length_change=args.allow_length_change,
                allow_number_change=args.allow_number_change,
            )
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(diff_md, encoding="utf-8")
            tot = parity["total"]
            print(
                f"STATUS: PASS | parity={parity['status']} "
                f"| total_words={tot['before_words']}->{tot['after_words']} ({tot['delta_words']:+d}w, {tot['drift_pct']:+.1f}%) "
                f"| tracked_diff={out_p}"
            )
            print(format_parity_markdown_table(parity))
        elif args.cmd == "parity":
            b_secs = extract_sections_from_file(args.before_file)
            a_secs = extract_sections_from_file(args.after_file)
            parity = evaluate_section_parity(
                b_secs,
                a_secs,
                max_section_drift=args.max_section_drift,
                max_total_drift=args.max_total_drift,
                short_section_floor=args.short_section_floor,
                allow_length_change=True,
            )
            if args.json:
                print(json.dumps(parity, ensure_ascii=False, indent=2))
            else:
                print(f"PARITY STATUS: {parity['status']}")
                print(format_parity_markdown_table(parity))
            if parity["status"] == "FAIL":
                sys.exit(1)
        else:
            if args.clean:
                prot = audit_docx_pair(args.source, args.edited, args.clean, allow_references=args.allow_references)
            else:
                prot = audit_docx_protection(
                    args.source,
                    args.edited,
                    view="tracked" if args.tracked else "clean",
                    allow_references=args.allow_references,
                )
            b_secs = extract_sections_from_file(args.source)
            a_secs = extract_sections_from_file(args.clean or args.edited)
            parity = evaluate_section_parity(
                b_secs,
                a_secs,
                max_section_drift=args.max_section_drift,
                max_total_drift=args.max_total_drift,
                short_section_floor=args.short_section_floor,
                allow_length_change=True,
            )
            combined = {
                "status": "PASS" if (prot["status"] == "PASS" and parity["status"] != "FAIL") else "BLOCK",
                "protection": prot,
                "section_word_counts": parity,
            }
            if args.json:
                print(json.dumps(combined, ensure_ascii=False, indent=2))
            else:
                print(f"VERIFY STATUS: {combined['status']} | protection={prot['status']} | parity={parity['status']}")
                if prot["errors"]:
                    print("PROTECTION ERRORS:", json.dumps(prot["errors"][:5], ensure_ascii=False))
                print(format_parity_markdown_table(parity))
            if combined["status"] != "PASS":
                sys.exit(2)
    except (TrackChangeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"TRACK_CHANGE_ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
