---
name: human-plain-scientific-writing
description: >-
  Scientific PLAIN-LANGUAGE SMOOTHING & WRITING skill (V1.2). Primary mission: smooth
  already-written scientific manuscripts (.docx, .md, .txt, or pasted prose) into clear,
  natural human English while STRICTLY PRESERVING (1) PER-SECTION WORD COUNTS (ideal
  <=±5%, hard cap <=±8% per section, <=±5% total — no silent shrinking, no filler
  padding) and (2) ORIGINAL MANUSCRIPT INTEGRITY (provider-agnostic Zotero/EndNote/
  NoteExpress/Mendeley/plain-text citation shield, immutable References, zero layout/
  style/font/table/equation/number-operator corruption, automatic post-write OOXML
  rollback, and surgical word/short-phrase track changes preserved by default). Also
  supports from-scratch plain-English drafting from Chinese notes, tables, or outlines.
  Calibrated on 12 anonymized human-authored top-journal and pre-LLM scientific
  manuscripts (61,560 prose words) with quantitative stylometric, S-V-O proximity,
  lexical-chaining, per-section parity, and citation/format protection gates.
  Use whenever the user asks to smooth an already-written paper into plain human English,
  preserve section word counts and citation/Word formatting while removing AI obscurity,
  rare words, buried subjects, nested clauses, internal codes, or underscores with tracked
  changes, or draft clear English manuscript sections from notes (已成稿论文平实化、
  保字数平滑语言、引文与原稿格式保护、去玄乎微创修改、字词尺度保留修改痕迹、
  各部分字数不变、人味写作、说人话写作、去内部代号与下划线).
  Do NOT use for strict Editage house-style mechanical proofread rules (P001–P016)—use
  scientific-editage-style when specifically running the Editage proofing pipeline.
---

# Human Plain Scientific Writing V1.2 (已成稿平实化保字数 + 引文与原稿保护 Skill)

This skill runs in **two explicitly separated modes**, with **Mode 1 as the primary V1.1 mission**:

1. **Mode 1 (Primary Default — Plain-Language Smoothing of Completed Manuscripts / 已成稿论文平实化与语言平滑)**:
   Take an already-written English manuscript (`.docx`, `.md`, `.txt`, or pasted sections) and smooth stiff, obscure, AI-sounding, or convoluted sentences into natural, plain human scientific English **while keeping EVERY section's word count as close to the original as possible**, preserving every scientific detail, argument, citation, and paragraph skeleton, with **surgical word-scale track changes preserved by default**.
2. **Mode 2 (Secondary — From-Scratch Plain Drafting / 从中文提纲或图表起草)**:
   Construct clear, plain-English manuscript sections from scratch when no prior English prose exists (applying the IMRaD paragraph and numeric-restraint blueprints).

Core philosophy calibrated from 12 anonymized human-authored top-journal and pre-LLM scientific manuscripts (61,560 prose words):
**High-impact science reads smoothly because every sentence uses everyday verbs, explicit Subject-Verb-Object order, tight sentence-to-sentence lexical chaining (68%–87%), and zero decorative jargon—without stripping away scientific substance.**

## Clear Division of Labor: Plain-Language Smoothing vs Editage Mechanical Proofing

| Dimension | `human-plain-scientific-writing` V1.2 (THIS SKILL) | `scientific-editage-style` (SEPARATE EDITAGE PROOFING SKILL) |
|---|---|---|
| Primary task | **Mode 1 (Default)**: Plain-language smoothing of completed manuscripts with **per-section word-count parity**, **citation/format protection**, and surgical track changes; **Mode 2**: from-scratch plain drafting | Editage-style mechanical grammar/idiom proofing (`COARSE <=6w`, `FINE <=10w`) on an already plain `.docx` |
| Word-count & manuscript protection | **Per-section parity + zero-dependency OOXML format/citation guard** (`<=±5%` ideal, `<=±8%` cap / `12w` floor; shields Zotero/EndNote/NoteExpress/Mendeley/plain citations, styles, runs, equations, numbers & operators `< > ≤ ≥ ± %`, auto-rollback on error) | Word/short-phrase OOXML `<w:ins>/<w:del>` redlining with Editage `P001–P016` gate |
| Edit granularity & track changes | **Surgical word/short-phrase scale + track changes preserved by default** (`<=8` words per atomic change, similarity `>=0.65`, `--on-unsafe query` Author-Query fallback) | Word/short-phrase OOXML redlining (`COARSE <=6w`, `FINE <=10w`) |
| Focus | Smooth plain verbs & nouns with domain-term protection, explicit S-V-O clarity, untangling long clauses while keeping all original substance, zero internal codes/underscores, 68%–87% Given-New chaining | Articles, prepositions, Editage editor conventions, pre-submission mechanical polish |
| When to switch | Start here to smooth an already-written paper into natural plain English (preserving each section's length, citations, and Word layout) or to draft new plain sections | Hand off to `scientific-editage-style` for final pre-submission Editage mechanical proofing |

## V1.2 Hard Laws: Per-Section Word-Count Parity, Original-Manuscript Protection & Surgical Track Changes

Whenever revising **any already-written English manuscript or section (Mode 1)**, enforce **ALL THREE protections by default** (full protocol in [original_manuscript_protection.md](./references/original_manuscript_protection.md)):

1. **Preserve Every Section's Word Count (逐部分字数守恒硬规程)**:
   - Measure and lock the original word count of **every individual part** (Abstract, Introduction, Methods, Results, Discussion, Conclusion, every numbered subsection such as 2.1/2.2/3.1/3.2, and Figure Captions) before editing.
   - **Target parity band**: keep every section within **±5%** of its original word count (and whole-manuscript total within **±5%**).
   - **Hard script cap (`track_changes_writer.py`)**: fails automatically (`SECTION_WORD_DRIFT`) if any edited section drifts beyond **±8%** (with a 12-word absolute floor for short sections under 150 words) or if the whole manuscript drifts beyond **±5%**, unless explicitly unlocked (`--allow-length-change`) after author approval.
   - **Zero silent compression**: Never condense a 750-word Introduction to 550 words or delete clauses, qualifiers, mechanisms, or result sentences just to make prose look shorter.
   - **Zero artificial padding**: Never stuff empty filler (`it should be noted`, `in general`, `furthermore`, redundant restatements) just to hit a word target. Maintain parity naturally by balancing two real smoothing moves: replacing wordy nominalizations (`due to the fact that -> because`, `performed an evaluation of -> evaluated`) while unpacking cramped noun stacks (`basin-specific depth-resolved soil carbon inventory -> soil carbon storage across four soil depths in mountain basins`) and turning dense nested clauses into explicit, well-chained short sentences that keep 100% of the author's original meaning.
   - **Mandatory parity report**: Always report a clean per-section table (`Section | Before | After | Delta | Drift %`) to the author after running `track_changes_writer.py`.
2. **Word/short-phrase surgery — NEVER whole-paragraph rewrites**:
   - Keep the original sentence skeleton and word order wherever possible. If changing 1–3 words fixes an AI ornament verb (`utilized -> used`, `elucidate -> explain`), removes an internal code (`Model_DynCond_v2 -> the dynamic conductance model`), deletes scare quotes/dashes, or splits a long clause cleanly at a comma (`, which amplified -> . This increased`), **touch only those exact words** and leave the rest of the sentence untouched.
   - Default hard script cap: **max `<=8` words per atomic deletion/insertion** and **minimum similarity `>=0.65`** (enforced automatically by `scripts/track_changes_writer.py`).
   - **No silent big rewrites**: If an isolated sentence is truly an unsalvageable 3-layer tangle that cannot be fixed within the word cap, **do NOT silently rewrite the whole paragraph**. Flag that specific sentence plainly for the author first, and only unlock that single item (`"allow_structural": true`) after author approval.
3. **Never overwrite the source file**: Always write new output files alongside or in a working folder, keeping the original draft untouched.
4. **Original-Manuscript, Citation & Number/Operator Protection (V1.2)**:
   - **Citations & References are immutable**: Protect Zotero, EndNote, NoteExpress (`NE.Ref`), Mendeley, and Word bibliographic fields (`w:fldChar`, `w:fldSimple`, `w:sdt`, `w:hyperlink`), citation bookmarks, superscript numeric citations, plain-text author-year and bracketed numeric `[1–3]` citations, and the entire References section. Never flatten or unlink citation fields.
   - **Layout, run styles & scientific objects are immutable**: Never alter fonts, sizes, margins, tables, equations (`m:oMath`), drawings, or headers/footers. Never cross differently formatted runs (protects italics/subscripts) or let pure insertions bleed superscript/italic formatting.
   - **Numbers & math/stat operators are locked**: Edits altering numeric values or `< > ≤ ≥ = ± % ‰ × ~ ≈` are blocked by default unless explicitly authorized (`allow_number_change`).
   - **Safe Author-Query fallback**: On complex real manuscripts where 1–2 edits sit right against a citation field or cross-format run, pass `--on-unsafe query` so safe edits apply cleanly while risky items are logged in `skipped_unsafe` for manual author review.
   - **Post-write audit + automatic rollback**: Every `docx` run automatically audits all ZIP parts, non-text OOXML skeleton, character `rPr` styles, reject==source / accept==clean projections, and citation manifests—deleting broken outputs immediately if any check fails.
5. **For `.docx` drafts**: Always run the bundled zero-dependency script `scripts/track_changes_writer.py docx` to produce:
   - `*_tracked.docx`: genuine native Word word-boundary revisions (`<w:del>` / `<w:ins>`) with Word Track Changes turned on, preserving original fonts, layout, equations, figures, and all citation fields (never recreate with `python-docx`).
   - `*_clean.docx`: the clean accepted copy verified to match the tracked Accept-All projection character-for-character and style-for-style.
   - `*_changes.json`: structured audit log recording per-section word counts (before/after/delta/drift%), protection audit status, any `skipped_unsafe` Author Queries, similarity, and max atomic word span.
6. **For `.md` / `.txt` files or pasted chat text**: Always run `scripts/track_changes_writer.py text` (enforcing surgical cap, plain-text citation preservation, number/operator invariance, and per-section word-count parity) to produce the per-section word-count table + word-level tracked diff (`~~deleted~~` / `**inserted**`) **plus** the clean final prose.
7. **For Mode 2 (brand-new from-scratch drafting with no prior English text)**: Deliver the clean draft on round 1; from round 2 onward, enforce Mode 1 surgical word-scale edits, per-section word-count parity, citation protection, and track changes against the previous draft.

## Supporting Craft Manuals & Scripts (Load Only What the Current Section Needs)

- **Original-manuscript, citation & format protection protocol (V1.2)**: [original_manuscript_protection.md](./references/original_manuscript_protection.md)
- **Section-by-section writing recipes** (used for Mode 2 drafting; in Mode 1, honor the manuscript's existing section word counts instead of shrinking to Mode 2 budgets): [imrad_writing_blueprints.md](./references/imrad_writing_blueprints.md)
- **Sentence chaining, S-V-O & plain-explanation mechanics**: [cohesion_and_plain_logic.md](./references/cohesion_and_plain_logic.md)
- **Anti-obscurity lexicon & AI-vs-Human contrast**: [anti_obscurity_rules.md](./references/anti_obscurity_rules.md)
- **Single-source lexicon & scientific sense-guards**: [lexicon_rules.json](./references/lexicon_rules.json)
- **Move-annotated plain-human exemplars**: [human_exemplar_bank.md](./references/human_exemplar_bank.md)
- **Anonymized corpus benchmarks & guardrails**: [corpus_dna_and_benchmarks.md](./references/corpus_dna_and_benchmarks.md)
- **Executable writing-quality gate**: [plain_human_audit.py](./scripts/plain_human_audit.py)
- **Zero-dependency track-changes & per-section word-count parity engine**: [track_changes_writer.py](./scripts/track_changes_writer.py)

## 5-Stage Plain-Smoothing & Writing Engine (Mandatory Order)

### Stage 1: Section Word-Count Baseline & Concept Lock (先锁各部分字数与核心术语)
1. **Mode 1 (Completed Manuscript Smoothing)**: Record the exact starting word count of every section/subsection (or run `track_changes_writer.py parity` on baseline vs draft) and extract the manuscript's **Locked Term Table** (3–6 core variables/groups). Keep every section's original argument sequence, paragraph count, and approximate word count intact; never replace locked scientific terms with ad-hoc synonyms.
2. **Mode 2 (From-Scratch Drafting)**: Lock 3–6 permanent plain English terms and one clear scientific question/finding from the author's notes before writing. Never fabricate missing numbers, units, sample sizes, p-values, or citations.

### Stage 2: Diagnosis Before Touching Prose (先诊断病灶，再定微调点)
- **In Mode 1**: Scan each section sentence-by-sentence to pinpoint ONLY genuine smoothing targets: obscure/AI verbs and nouns, buried subjects, `>=12w` pre-verb subjects, nested clauses, scare quotes, em dashes, coined hyphen compounds, internal code names, underscore fake subscripts, and abrupt sentence-to-sentence jumps. Leave already-clear sentences untouched!
- **In Mode 2**: Map each paragraph to one clear job using [imrad_writing_blueprints.md](./references/imrad_writing_blueprints.md).

### Stage 3: Smooth Plain Revision / Chained Drafting (平实平滑与咬合起草)
Load [cohesion_and_plain_logic.md](./references/cohesion_and_plain_logic.md) and [anti_obscurity_rules.md](./references/anti_obscurity_rules.md), then apply these **9 non-negotiable language laws**:

1. **Zero Internal Codes & Zero Underscore Identifiers — Across Headings, Tables, Prose, and Author Briefs**:
   - Translate script variable names, CSV column names, model-run strings, camel-case code identifiers, and workflow codes (`Model_DynCond_v2`, `wind_dir_deg`, `param_fit`, `coastal_all`, `run_v04`, `OptionB`, `M0/M1`, `S1–S8`) into plain physical English.
   - Replace raw underscore fake subscripts (`R_n`, `T_a`, `h_c`, `x_90`) with plain physical names or true formatted subscripts. Standard literature symbols (`CO2`, `N2O`, `CH4`, `R2`, `Fig. S1`, `Table S2`, `SSP5-8.5`) remain allowed.
   - Keep author decision briefs free of opaque internal IDs; state the section/figure/dataset, the concrete difference, and the risk of each option in plain language.
2. **Numeric Restraint — Harmonized With Mode 1 Length Parity**:
   - **Mode 1 (Smoothing completed manuscripts)**: **Do NOT silently delete result numbers or data sentences to shrink a section.** If a single sentence packs `>=4` data numbers in one breath, smooth it by splitting across 2 crisp sentences (keeping all numbers and section word count intact). If an entire Results paragraph reads a whole table aloud and genuinely needs offloading to a Table/SI (which would cut section length beyond ±5%), smooth it in place first and flag the optional Table-offload recommendation separately for author approval.
   - **Mode 2 (From-scratch drafting)**: Match the top-journal benchmark (`0.31–0.65` data numbers/sentence, `72.5%–81.4%` zero-number sentences, max 3/sentence), putting headline totals, start-to-end ranges, and thresholds in prose while offloading exhaustive breakdowns to Tables/Figures.
3. **Zero Coined Words & Ad-Hoc Hyphenated Labels**:
   - Replace invented compound labels (`inventory-scale metric`, `climate-side forcing sensitivity`, `common spatial and depth support`, `biome-level structuring`, `depth-resolved baseline`, `interpolation-like`) with plain prepositional phrases (`of`, `in`, `across`, `for`, `with`).
4. **Zero Scare Quotes & Zero Em/Spaced Dashes**:
   - Remove quotation marks framing normal words or concepts; remove em dashes (`—`) and spaced parenthetical dashes (` – `, ` - `) inserting clauses. Keep closed en dashes (`–`) strictly for numeric ranges and standard pairs (`0–20 cm`, `1985–2015`, `C–N`).
5. **Explicit S-V-O Clarity & Smooth Clause Flow**:
   - Put the concrete subject near the start (framing opener `<=12w`, hard fail `>22w`) and place the finite verb close behind (`<=8w` target, hard fail `>=16w`; top-journal human median = **3 words**). Break `>=3`-`of` subject chains and move heavy comma interrupters out from between subject and verb.
   - Move real actions out of nominalizations into finite verbs (`performed an evaluation of X -> evaluated X`, `exhibited a declining trend -> declined`, `due to the fact that -> because`, `serves to increase -> increases`, `may potentially -> may`, `not uncommon -> common`), and replace archaic connectors (`whereby`, `thereof`, `inasmuch as`, `albeit`, `whilst`, `pertaining to`, `subsequent to`). Keep standard Methods phrases (`Statistical analyses were performed in R`) intact.
   - Split convoluted `>=2`-clause sentences (>28w) and long trailing `, which / , whereas / , while` clauses (>16w) into 2 flat sequential sentences **without dropping any clause's factual content**.
6. **Smooth Sentence-to-Sentence Lexical Chaining (Given -> New Flow)**:
   - Smooth abrupt transitions by repeating an exact locked noun/variable across adjacent sentences or linking via `This/These/Such + summary noun` or parallel scope (`In grazed plots, ...` / `In ungrazed plots, ...`). Target **>=68% adjacent-sentence lexical overlap** (top-journal human benchmark: **68%–87%**).
7. **Plain Everyday Verbs & Nouns — Strictly Protecting Standard Scientific Terms**:
   - Preserve established domain terminology (`soil respiration`, `sensible heat flux`, `evapotranspiration`, `bulk density`, `net radiation`, `heterogeneity`, `stoichiometry`, `nitrification`, `denitrification`, `methanogenesis`, `random forest`, `cross-validation`, `uncertainty`, `threshold`, `nonlinear`, `extrapolation`, `sensitivity analysis`, `PCR amplified`, `light attenuated`, `carbonate precipitated`, `granular soil`, `root/canopy/network architecture`, `HYSPLIT back-trajectory`, `water-energy-food nexus`, `robust regression`). All domain sense-guards live in [lexicon_rules.json](./references/lexicon_rules.json).
   - Replace LLM ornament and pompous literary verbs (`leverage`, `harness`, `unravel`, `disentangle`, `illuminate`, `orchestrate`, `modulate`, `bolster`, `foster`, `catalyze`, `underpin`, `reshape`, `elucidate`, `delineate`, `underscore`, `utilize`, `unveil`, `delve`, `embark`, `endeavor`, `commence`, `ascertain`, `garner`, `glean`, `obviate`, `engender`, `evince`, `purport`, `showcase`, `juxtapose`, `curtail`, `dampen`, `circumvent`, `elicit`, `eschew`, `preclude`, `scrutinize`, `subsume`, `surmount`, `transcend`, `ameliorate`) and pompous abstract nouns (`plethora`, `myriad`, `milieu`, `conundrum`, `ramifications`, `dearth`, `surfeit`, `panacea`, `enigma`, `hallmark`, `impetus`, `tapestry`, `linchpin`, `cornerstone`, `paradigm`, `underpinnings`) with everyday workhorse words (`use`, `show`, `find`, `increase`, `decrease`, `reduce`, `change`, `explain`, `indicate`, `suggest`, `affect`, `cause`, `lead to`, `depend on`, `differ`, `remain`, `keep`, `test`, `compare`, `estimate`, `calculate`, `measure`, `observe`, `check`, `support`, `control`, `limit`).
8. **Human Agency, Concrete Subjects & Exact Term Repetition**:
   - Prefer active `We` + plain verb for author actions (`We compiled`, `We built`, `We tested`) and concrete physical subjects for nature (`Soil texture`, `Higher temperatures`, `Root biomass`), never meta-nouns (`Robustness diagnostics confirmed...`). Repeat locked variable names consistently instead of rotating synonyms.
9. **Clean Grammar & Zero Empty Hype**:
   - Fix clear slips (`between 15–100` -> `between 15 and 100`, `in relative to` -> `relative to`). Cut hype modifiers (`crucially`, `intriguingly`, `remarkably`, `pivotal`, `paramount`, `nuanced`, `multifaceted`, `overarching`).

### Stage 4: Deterministic Quality Audit, Per-Section Word-Count Parity & Track Changes (强制三项脚本验收)
1. **Plain-Language Quality Audit**: Run `scripts/plain_human_audit.py` on the smoothed clean prose and revise until `PASS`:

```bash
python <skill-dir>/scripts/plain_human_audit.py <draft.txt>
```

2. **Surgical Track Changes + Per-Section Word-Count Parity Gate (Mandatory for Mode 1)**: Run `scripts/track_changes_writer.py`, which enforces BOTH surgical word-scale granularity (`<=8` words/op, similarity `>=0.65`) AND per-section word-count parity (ideal `<=±5%`, hard cap `<=±8%` per section with 12w short-section floor, `<=±5%` total) without overwriting the source file:

```bash
# For an existing .docx manuscript (native Word <w:del>/<w:ins> + clean copy + parity + automatic format/citation protection):
python <skill-dir>/scripts/track_changes_writer.py docx <source.docx> <edits.json> \
    --tracked <out_tracked.docx> --clean <out_clean.docx> --log <out_changes.json> \
    --on-unsafe query

# Independent format, citation, and per-section parity audit on any DOCX pair:
python <skill-dir>/scripts/track_changes_writer.py verify <source.docx> <out_tracked.docx> \
    --tracked --clean <out_clean.docx>

# For an existing .md or .txt manuscript (per-section parity table + citation/number lock + word-boundary tracked diff):
python <skill-dir>/scripts/track_changes_writer.py text <before.md> <after.md> --out <out_tracked.md>

# Standalone per-section word-count parity check between any two .docx/.md/.txt files:
python <skill-dir>/scripts/track_changes_writer.py parity <before_file> <after_file>
```

If `track_changes_writer.py` blocks with `SECTION_WORD_DRIFT`, inspect which section shrank or expanded, restore dropped scientific details (or trim accidental wordiness) rather than padding with filler, and re-run. Only pass `--allow-length-change` after explicit author approval.

### Stage 5: Final Verification Before Delivery
Before delivering smoothed prose or tracked files, verify all five items:
- **Per-section word-count parity**: Every section sits within target (`<=±5%`, hard cap `<=±8%` / `12w` floor) and the Before / After / Delta / Drift % table is reported to the author.
- **Surgical granularity & track changes preserved**: Edits stay at minimal word/short-phrase scale, tracked output + clean output are delivered, the original file is untouched, and Word citation fields/equations/layout remain intact.
- **Zero internal codes**: Zero underscore identifiers, zero raw underscore subscripts, zero camel-case code strings, and zero opaque short-code soup.
- **Fact & number fidelity**: Every number, unit, sample size, statistical metric, and figure/table pointer matches the source verbatim; any intentionally moved/edited numbers are explicitly listed.
- **Claim boundary**: Correlation is never upgraded to causation; caveats and limitations remain intact.
