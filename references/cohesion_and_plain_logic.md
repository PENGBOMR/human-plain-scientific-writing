# Sentence Cohesion & Plain-Explanation Mechanics

Why does AI-written scientific prose often feel cryptic, jumpy, or pretentious even when individual words look acceptable?
Because LLMs write **disconnected punchlines** (each sentence launches a fresh abstract noun phrase or rotates synonyms), whereas top-journal human authors build **interlocking logical staircases**.

---

## 1. Empirical Proof: The Given-New Lexical Chaining Law

Measured across the 12 anonymized human-authored manuscripts versus an AI-edited contrast draft (`AI-Contrast-1`):

| Anonymized Manuscript | Adjacent-Sentence Lexical Overlap (`lex_chain%`) | `This/These/Such + Noun` Openings | Sentence-Initial Connector Rate |
|---|---:|---:|---:|
| `Anchor-1` — Full paper | **87.2%** (Abstract 100%, Discussion 91.4%, Results 86.8%, Intro 82.9%) | **9.4%** (Discussion 13.8%) | **17.7%** (Results 10.5%) |
| `Support-1` | **78.9%** | — | — |
| `Anchor-4` | **76.4%** | — | — |
| `Support-3` | **73.1%** | 3.6% | 14.7% |
| `Anchor-2` | **70.1%** | — | — |
| `Anchor-3` | **69.7%** | — | — |
| `Support-4` | **68.4%** | 11.3% | 10.2% |
| `Anchor-5` | **68.1%** | — | — |
| `Support-2` | **64.5%** | 4.1% | 12.8% |
| `Support-5` | **64.3%** | 1.6% | 16.7% |
| **Negative Contrast: `AI-Contrast-1`** | **53.3%** *(nearly half of sentence pairs disconnect!)* | 14.0% | 12.5% |

**Writing law**: In pure human writing, **65%–87% of adjacent sentences share an exact content noun/variable**—typically taking the new concept introduced at the tail of Sentence `k` and making it the subject or opening anchor of Sentence `k+1`.

---

## 2. The 5 Human Sentence-to-Sentence Linking Moves

Use these five mechanisms in order of frequency instead of spamming `Furthermore / Moreover / Importantly / Notably`:

### Move A: Tail-to-Head Exact Noun Chaining (Primary Engine — ~50%+ of transitions)
Carry the exact concept from the end of Sentence `k` to the start of Sentence `k+1` (do **not** swap it for a synonym).
- Synthetic example (Abstract):
  - S1: `Mountain snowpacks supply summer streamflow to millions of downstream residents and strongly regulate river nitrate export.`
  - S2: `However, field studies have reported both rising and falling stream nitrate concentrations during warmer winters, creating debate over how snowpack loss alters watershed nitrogen retention.`
  - S3: `We built a catchment synthesis model using long-term water chemistry records from 142 mountain watersheds and paired soil frost measurements across temperate and boreal zones.`
  - S4: `Our model predicted observed winter nitrate export with an accuracy of 83% across independent validation sites.`

### Move B: Demonstrative + Plain Summary Noun (~9%–14% in Results & Discussion)
Compress the entire previous sentence (or preceding 2–3 sentences) into `This / These / Such + [plain domain noun]` as the grammatical subject of the next sentence:
- `This finding` / `These results` / `These factors` / `This discrepancy` / `This cooling effect` / `Such threshold shifts` / `Such contrasting responses` / `This change in salinity`.
- Synthetic example (Discussion):
  - S1: `Dense tree canopies block incoming solar radiation and directly lower daytime pavement temperatures.`
  - S2: `Well-watered trees also transpire steadily, converting incoming energy into latent heat rather than sensible heat.`
  - S3: `In contrast, narrow planting pits surrounded by asphalt restrict root growth and dry out quickly during heat waves.`
  - S4: **`Together, these factors` explain why park woodlands cool the air much more effectively than isolated street trees.**

### Move C: Parallel Scope Framing (Ideal for Contrasts, Zones, Stages, or Depths)
Hold the grammatical skeleton identical across 2–3 consecutive sentences while swapping only the group/zone/threshold at the front:
- Synthetic example (Results):
  - `When winter snow depth stayed above 40 cm, stream nitrate export remained low and nearly constant across both alpine and subalpine sites.`
  - `When snow depth dropped between 15 and 40 cm, winter nitrate export rose sharply as soil freezing intensified.`
  - `Below 15 cm of snow, nitrate export leveled off at high values.`

### Move D: Plain Logical Pivot (Only ~10%–20% of Sentences — Must Carry Real Logic)
Use a short everyday pivot ONLY when logic genuinely turns:
- Contrast / reversal: `However,`, `In contrast,`, `Instead,`, `On the other hand,`, `Yet,`
- Consequence: `Therefore,`, `Thus,`, `As a result,`, `Consequently,`
- Counterfactual refutation: `...; otherwise, ... would have ... . Instead, ...`
- Concrete illustration: `For example,`, `For instance,`, `Specifically,`
- Simple addition (sparingly): `In addition,`, `Also,`, `Meanwhile,`

### Move E: Zero-Connector Concrete Elaboration
Sentence `k` makes a clean claim; Sentence `k+1` immediately supplies the exact number, site, or mechanism with **no connector word at all**:
- Synthetic example (Results):
  - `Soil clay content was the strongest predictor of surface carbon retention across all grassland zones. Across sites, soil texture explained 34% to 45% of the spatial variation in topsoil organic carbon.`

---

## 3. Explicit S-V-O Architecture (Keeping Subject, Verb, and Object Visible at a Glance)

Measured on the primary top-journal human anchor (`Anchor-1`), the median distance from the start of the main clause to its finite verb is **only 3 words** (4 words from sentence start). Readers struggle with AI and formal drafts whenever the subject is buried or pushed far away from its verb. Enforce 5 surgical S-V-O mechanics:

1. **Subject First, Verb Immediately After (<=8w target; warn 12–15w; fail >=16w)**:
   - Bad (18w pre-verb subject + 3 `of` chain): `The spatial distribution of the ratio of the burial rate of organic carbon to the rate of sediment supply across four marsh zones varied strongly.`
   - Plain S-V-O (3w pre-verb subject): `Carbon burial ratios varied strongly across marsh zones and salinity classes.`
2. **Keep Framing Openers Short (<=12w target; warn 16–22w; fail >22w)**:
   - Bad (17w pre-subject opener): `By placing the winter snowpack depth and soil frost observations within a unified mountain catchment grid across elevation zones, the framework evaluates...`
   - Plain S-V-O: `We mapped winter snowpack depth and soil frost on the same mountain catchment grid. This map shows whether...`
3. **Never Wedge Long Interrupters Between Subject and Verb**:
   - Bad: `Deep marsh sediment cores, including coastal horizons below 50 cm that are often missed by shallow estuarine surveys, stored nearly half of the regional carbon pool.`
   - Plain S-V-O: `Deep marsh sediments below 50 cm stored nearly half of the regional carbon pool. Shallow estuarine surveys often miss these deep layers.`
4. **Move Real Actions Out of Nominalizations Into Finite Verbs**:
   - Bad: `We performed a quantitative evaluation of model accuracy` / `The estimation of burial rates was carried out` / `Topsoil organic carbon exhibited a significant declining trend.`
   - Plain S-V-O: `We evaluated model accuracy` / `We estimated burial rates` / `Topsoil organic carbon declined significantly.`
   - *(Methods boilerplate such as `Statistical analyses were performed in R` and `We performed a meta-analysis` stays allowed.)*
5. **Cut Empty Openers, `the fact that`, `serves to`, Archaic Connectors, Hedge Stacks & Litotes**:
   - Delete `There is an urgent need to`, `With the rapid development of`, `It is noteworthy to mention that`, `due to the fact that` (`because`), `serves to reduce` (`reduces`), `whereby/inasmuch as/albeit/whilst/pertaining to`, `may potentially` (`may`), `not uncommon` (`common`).
   - Prefer explicit agents over gerund/dangling openers: `When we combined X with Y, we found...` instead of `Combining X with Y showed that...`; `To test X, we built a model` instead of `To test X, a model was built`.

---

## 4. The 4 Plain-Explanation Mechanics (How Clear Authors Make Hard Ideas Easy)

When explaining a mathematical model, statistical parameter, ecological mechanism, or assumption, never hide behind dense nominalizations. Apply one of these four verified human techniques:

1. **Immediate Plain-English Translation (`meaning that ...` / `(i.e., ...)` / `That is, ...`)**
   - `The area-weighted mean threshold was 40 cm, meaning that winter nitrate export rose once snowpacks thinned below 40 cm.`
   - `High salinity suppressed methane emissions in polyhaline marshes (i.e., sites where porewater salinity exceeds 18 ppt).`
   - `The default frost sensitivity factor is 0.05 (winter nitrate export may rise by 5% for each additional freeze-thaw cycle).`

2. **One Concrete Numeric or Regional Example (`For example, ...` / `For instance, ...`)**
   - `For example, the frost-response ratio at a snow depth of 20 cm was calculated using catchments with winter snow depths between 15 and 25 cm.`
   - `For instance, in steep granitic basins where mineral soils are shallow, winter nitrate loads nearly doubled after thin snowpack years (Fig. 4).`

3. **One Cause Per Sentence + Wrap-Up Sentence**
   - Never compress 3 mechanisms into 1 multi-clause sentence. Give each cause its own 12–22 word sentence, then conclude with `These factors may explain...` or `Together, these processes explain...`.

4. **Plain Deductive Reasoning (`A likely reason is that...` / `This suggests...; otherwise...; Instead...`)**
   - `Heavy grazing reduced topsoil carbon more strongly in dry grasslands than in wet meadows (Fig. 5). A likely reason is that trampling removes sparse plant cover in dry sites and accelerates wind erosion.`

---

## 5. Worked Drafting Demo: Chinese Notes -> Plain Human Paragraph

**Raw Chinese Notes (Synthetic Input for a Results/Discussion Paragraph)**:
- 高寒流域里，薄雪流域占全部监测站点的 28%，却贡献了 41% 的冬季硝态氮负荷，而总冬季径流量只占 19%。
- 改用更严格的积雪深度阈值后，高输出流域的空间格局几乎没变。
- 冬季硝态氮输出与积雪深度和表层土温呈非线性关系，而且在不同坡度和土壤质地流域之间存在差异。

**Step 1 — Lock Terms**: `winter nitrate export`, `catchments with thin snowpacks`, `snow depth`, `surface soil temperature`, `basin slopes`, `soil textures`.

**Step 2 — Map Sentence Slots (Explicit S-V-O + Given -> New Chain)**:
- S1 (Lead directly with concrete spatial actor): Across the monitored mountain basins, catchments with thin snowpacks made up 28% of all sites.
- S2 (Chain via `These catchments` + contrast): These catchments produced 41% of winter nitrate loads but supplied only 19% of total winter runoff.
- S3 (Plain meaning via `Thus` + exact term chain): Thus, high winter nitrate export does not simply follow high streamflow.
- S4 (Sensitivity check with explicit human agency `we`): When we applied stricter thresholds for snow depth, the spatial pattern of these catchments changed little.
- S5 (Physical driver — plain verb, no metaphor): In addition, winter nitrate export showed nonlinear relationships with snow depth and surface soil temperature.
- S6 (Regional/site variation chained via `These relationships`): These relationships also varied across basin slopes and soil textures.

**Step 3 — Resulting Plain Human English (6 flat S-V-O sentences, 100% factual fidelity, 0 AI clichés)**:
> Across the monitored mountain basins, catchments with thin snowpacks made up 28% of all sites. These catchments produced 41% of winter nitrate loads but supplied only 19% of total winter runoff. Thus, high winter nitrate export does not simply follow high streamflow. When we applied stricter thresholds for snow depth, the spatial pattern of these catchments changed little. In addition, winter nitrate export showed nonlinear relationships with snow depth and surface soil temperature. These relationships also varied across basin slopes and soil textures.
