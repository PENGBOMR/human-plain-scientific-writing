# Original-Manuscript, Citation & Format Protection Protocol (V1.2)

During Mode 1 (plain-language smoothing of an already-written manuscript), the original `.docx` file is the sole authoritative layout and bibliographic master. Smoothing alters **ordinary prose text only**—never layout, formatting, scientific objects, or bibliographic data.

## 1. Strictly Immutable Manuscript Elements

1. **Citation Managers & Bibliographic Fields (Provider-Agnostic)**:
   - Never modify, unlink, flatten, or overwrite Word complex fields (`w:fldChar` begin..end, `w:instrText`, field display results), inline containers (`w:fldSimple`, `w:sdt`, `w:hyperlink`, `w:smartTag`), or citation bookmarks (`w:bookmarkStart..bookmarkEnd` for Zotero, EndNote, NoteExpress, Mendeley, CSL, `ADDIN ZOTERO_ITEM`, `ADDIN EN.CITE`, `ADDIN EN.REFLIST`, `ADDIN NE.Ref`, Word `CITATION`/`BIBLIOGRAPHY`).
   - Protect **plain-text citations** as well: parenthetical author-year `(Smith et al., 2020)`, narrative `Smith et al. (2020)`, bracketed numeric `[1, 3–5]`, and superscript numeric runs (`w:vertAlign="superscript"` containing digits/ranges).
   - **References / Bibliography / Literature Cited** paragraphs are strictly read-only. Never re-sort, re-punctuate, spellcheck, or alter reference entries during prose smoothing.
   - Safe prose **adjacent** to a citation remains editable as long as the edit does not intersect any protected span. When no clean separation exists, skip the edit and raise an Author Query (`--on-unsafe query`).
2. **Original Layout, Styles & Scientific Objects**:
   - Never alter fonts, sizes, colors, italic/bold/subscript/superscript attributes (`w:rPr`), paragraph spacing/indentation/alignment (`w:pPr`), numbering (`word/numbering.xml`), styles (`word/styles.xml`), page margins/orientation/sections (`w:sectPr`), headers/footers, drawings, figures, tables, equations (`m:oMath`, `m:oMathPara`), footnotes, or any other non-text ZIP parts.
   - Never rebuild a `.docx` through `python-docx Document().save(...)`. Patch `word/document.xml` in place via `scripts/track_changes_writer.py`.
   - Never cross differently formatted runs in a single replacement (prevents silently wiping italics or subscripts), and never allow pure insertions adjacent to superscript/subscript/italic runs to inherit special formatting.
3. **Numbers & Mathematical/Statistical Operators**:
   - By default, edits that alter numeric tokens or mathematical/statistical operators (`< > ≤ ≥ = ± % ‰ × ~ ≈`) are blocked unless explicitly authorized by the author (`allow_number_change`).
4. **Zero Ghost Typography Revisions**:
   - Invisible-only diffs (non-breaking space vs regular space, curly vs straight quotes, Unicode minus vs ASCII hyphen) are refused so Track Changes stays clean and noise-free.

## 2. Automatic Verification & Atomic Rollback

Every run of `scripts/track_changes_writer.py docx` automatically executes a post-write integrity gate across both `*_tracked.docx` and `*_clean.docx`:
- Exact ZIP member set and byte-for-byte identity for every package part outside `word/document.xml` and `word/settings.xml`.
- Exact non-text OOXML skeleton invariance (tables, equations, images, fields, `pPr`, `sectPr`).
- Exact `word/settings.xml` invariance except `<w:trackRevisions/>`.
- Zero formatting revision tags (`rPrChange`, `pPrChange`, `sectPrChange`, `tblPrChange`).
- Paragraph count invariance and zero erased non-empty paragraphs.
- Per-character `w:rPr` style invariance for surviving text, and nearby source-style inheritance for inserted text.
- Tracked Reject-All view equals exact source text+styles; Tracked Accept-All view equals exact clean copy text+styles.
- Exact source-vs-output citation and bibliography manifest equality.
- **Atomic rollback**: if any check fails, the generated outputs are deleted immediately and the command exits with `PROTECTION_AUDIT_FAILED`.

Run the standalone check anytime on any pair of `.docx` files:

```bash
python <skill-dir>/scripts/track_changes_writer.py verify <source.docx> <out_tracked.docx> --tracked --clean <out_clean.docx>
```

## 3. Honest Conservative Limits (Never Over-Promise)

- **Live citation-manager refresh**: Passing OOXML protection verifies file-level XML structure, field instructions, bookmarks, and visible text—it does **not** execute the author's live Zotero/EndNote/NoteExpress Word add-in. Authors should still test one citation refresh on a copy in Word before submission.
- **Pagination reflow**: Even when zero layout properties change, legitimate word-length changes can naturally shift line wraps or page breaks in Word or LibreOffice. Never shrink font sizes or margins to force identical page breaks, and visually inspect rendered pages before final submission.
