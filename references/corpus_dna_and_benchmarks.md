# Corpus DNA & Quantitative Benchmarks (12 Anonymized Human Manuscripts)

All benchmarks below were measured on clean body prose (excluding titles, affiliations, references, tables, figure captions, and parenthetical citations) extracted from an anonymized curation of 12 human-authored environmental and earth-science manuscripts (61,560+ prose words), contrasted against anonymized AI-edited and number-heavy drafts. All author names, source filenames, and manuscript identities have been stripped to preserve privacy.

## 1. Anonymized Corpus Composition

- **Tier 1 — Primary Top-Journal Clarity Anchor (5 published high-impact articles + 1 conference abstract, 29,199 prose words)**:
  - `Anchor-1` through `Anchor-5`: five peer-reviewed earth-science and macroecology articles published in flagship international journals.
- **Tier 2 — Supporting Human-Written Set (7 manuscripts, 32,361+ prose words)**:
  - `Support-1`: one peer-reviewed global-change ecology article.
  - `Support-2` through `Support-7`: six pre-LLM or human-drafted ecological synthesis manuscripts.
- **Negative Diagnostic Contrasts (excluded from positive training)**:
  - `AI-Contrast-1`: AI-edited draft exhibiting dense coined hyphenated compounds, low first-person agency, and weak sentence-to-sentence chaining.
  - `Number-Contrast-2`: number-heavy draft reading layer-by-layer and region-by-region tables aloud in Results prose.

## 2. Measured Stylometric Benchmarks (Prose Words Excluding Citations)

| Anonymized Source | Sents | Prose Words | Mean | Median | IQR | <=15w (%) | <=20w (%) | >35w (%) | Commas/Sent | Clause Markers/Sent | <=1 Clause (%) | Participle Tail (%) | We/Our/Us per 1k | Em-Dash per 1k |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Anchor-1` | 275 | 7,394 | 26.9 | 24.0 | 16–33 | 20.4 | 37.1 | 19.6 | 1.31 | 0.49 | 91.3 | 10.2 | 9.1 | 0.44 |
| `Anchor-2` | 278 | 6,495 | 23.4 | 20.5 | 14–29 | 31.7 | 50.0 | 14.0 | 1.33 | 0.31 | 96.8 | 9.0 | 9.4 | 0.31 |
| `Anchor-3` | 201 | 4,904 | 24.4 | 21.0 | 15–32 | 28.9 | 49.3 | 20.4 | 1.35 | 0.29 | 96.0 | 12.9 | 8.7 | 0.00 |
| `Anchor-4` | 234 | 5,083 | 21.7 | 19.0 | 14–28 | 34.6 | 54.3 | 12.4 | 1.06 | 0.28 | 97.4 | 10.7 | 10.2 | 0.00 |
| `Anchor-5` | 239 | 5,312 | 22.2 | 20.0 | 14–29 | 31.8 | 51.0 | 11.7 | 1.21 | 0.33 | 95.8 | 7.9 | 13.2 | 0.00 |
| `Support-1` | 251 | 6,351 | 25.3 | 24.0 | 16–32 | 22.7 | 39.4 | 18.7 | 1.49 | 0.42 | 93.6 | 14.7 | 8.9 | 0.00 |
| `Support-2` | 177 | 4,432 | 25.0 | 23.0 | 16–30 | 24.9 | 44.1 | 15.8 | 2.15 | 0.34 | 95.5 | 11.9 | 2.7 | 0.00 |
| `Support-3` | 204 | 4,956 | 24.3 | 23.0 | 16–31 | 22.1 | 40.2 | 12.7 | 1.95 | 0.27 | 96.1 | 10.8 | 4.8 | 0.00 |
| `Support-4` | 154 | 3,192 | 20.7 | 19.0 | 14–26 | 32.5 | 57.8 | 5.8 | 1.56 | 0.27 | 96.1 | 7.1 | 5.3 | 0.00 |
| `Support-5` | 209 | 4,784 | 22.9 | 22.0 | 15–28 | 25.4 | 44.0 | 9.6 | 1.64 | 0.31 | 95.2 | 10.0 | 3.6 | 0.00 |
| `Support-6` | 170 | 4,635 | 27.3 | 25.0 | 18–33 | 18.2 | 32.9 | 18.2 | 2.21 | 0.40 | 94.1 | 14.7 | 1.3 | 0.00 |
| `Support-7` | 206 | 4,659 | 22.6 | 21.0 | 15–29 | 25.7 | 46.1 | 10.7 | 1.30 | 0.35 | 97.5 | 12.6 | 3.8 | 0.00 |
| **Negative Contrast: `AI-Contrast-1`** | **345** | **6,870** | **19.9** | **19.0** | **14–25** | **30.7** | **56.5** | **5.2** | **1.60** | **0.36** | **95.7** | **3.8** | **1.2** | **0.00** |

## 3. Why Simple Surface Metrics Miss AI Obscurity

Notice `AI-Contrast-1` has short sentences (median 19w) and zero em dashes, yet reads stiff and cryptic. The real discriminators exposed by empirical comparison are:

| Hidden AI-Obscurity Signal | Tier-1 Top-Journal Anchors (5 papers) | Tier-2 Supporting Human Set (7 papers) | `AI-Contrast-1` |
|---|---:|---:|---:|
| Hyphenated compound density (per 1,000 words) | **16.4** | **11.8** | **38.7** (2.4x–3.3x higher) |
| 5+ non-stopword modifier stacks (per 100 sents) | **19.2** | **32.9** | **36.2** |
| Sentences opening with `We` / `Our` (%) | **5.0%** | **3.7%** | **0.6%** (8x lower) |
| First-person agency (`we/our/us` per 1,000 words) | **8.7–13.2** | **1.3–8.9** | **1.2** |
| Adjacent-sentence lexical chaining (`lex_chain%`) | **68.1%–87.2%** | **64.3%–78.9%** | **53.3%** |
| 3+ syllable words (%) | **20.9%** | **22.3%** | **22.4%** |
| 4+ syllable words (%) | **9.4%** | **11.1%** | **10.3%** |
| Plain workhorse `use/used/using` (raw count) | **238** | **292** | rare relative to coined nominal framing |

### Section-Level Writing Budgets (Top-Journal Human Benchmarks)

| IMRaD Section | Typical Paragraphs | Mean Words/Para | Mean Sents/Para | Lexical Chaining (`Anchor-1`) | Sentence-Initial Connectors |
|---|---:|---:|---:|---:|---:|
| **Abstract** | 1 | 140–250 | 6–10 | **100.0%** | ~20–40% |
| **Introduction** | 5–6 | 140–200 | 4–7 | **82.9%** | ~22% |
| **Methods** | 12–29 | 80–130 | 3–5 | **84.1%** | ~14% |
| **Results** | 8–15 | 75–130 | 3–5 | **86.8%** | **~10.5%** |
| **Discussion** | 7–12 | 150–220 | 5–7 | **91.4%** | ~21% |
| **Conclusion** | 1 | 100–170 | 4–6 | — | ~15–20% |

### Quantitative Restraint Benchmark (Why Top Journals Never Read Tables Aloud)

Measured across 6 published top-journal articles vs number-heavy contrast drafts (counting standalone data numbers only, excluding years, chemical formulas, citations, and Fig/Table pointers):

| Source | Data Numbers / Sentence | 0-Number Sentences (%) | >=3-Number Sentences (%) | >=4-Number Sentences | Em / Spaced Parenthetical Dashes |
|---|---:|---:|---:|---:|---:|
| `Anchor-1` — Results | **0.42** | **74.0%** | **4.0%** | **0** (max 3) | 6 (whole 7.4k paper) |
| `Anchor-1` — Discussion | **0.40** | **73.6%** | **1.4%** | **0** (max 3) | — |
| `Anchor-2` — Full body | **0.65** | **72.5%** | **8.3%** | 11 | 7 (whole 6.5k paper) |
| `Anchor-3` — Full body | **0.37** | **75.8%** | **1.8%** | 2 (max 4) | **0** |
| `Anchor-4` — Full body | **0.31** | **79.3%** | **2.2%** | 1 (max 4) | 2 |
| `Anchor-5` — Full body | **0.53** | **75.4%** | **6.3%** | 7 | 2 |
| `Support-1` — Full body | **0.47** | **81.4%** | **5.9%** | 10 | **0** |
| **Contrast: `AI-Contrast-1` Results** | **1.31** (3.1x Anchor-1) | 62.9% | **25.7%** | **8** (max 6) | — |
| **Contrast: `Number-Contrast-2` Results** | **2.43** (5.8x Anchor-1) | 42.9% | **40.0%** | **14** (max 8) | — |

## 4. Empirical Limits & Guardrails

1. **Domain scope**: All 12 benchmark manuscripts come from environmental, ecological, and earth-system sciences. Do not treat these numeric ranges as universal laws for legal, humanities, or pure mathematics writing.
2. **Do not imitate accidental non-native slips**: Avoid common manuscript blemishes (`between 15–100` -> write `between 15 and 100` or `15–100`; `in relative to` -> `relative to`; subject-verb mismatch in relative clauses).
3. **Prose-only sentence-length baseline**: Stripping parenthetical citations `(Author et al., 2020; ...)` and superscript pointers reveals a true human prose median of **19–24 words**, with **37%–54% of sentences <= 20 words**, and a median main-clause subject-to-verb distance of **3 words**.
