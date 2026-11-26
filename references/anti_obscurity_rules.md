# Anti-Obscurity Rules: Plain Verbs, S-V-O Clarity & Fixing AI Writing Diseases

> **Single source of truth**: Every Tier-1 FAIL word, Tier-2 advisory word, and scientific domain sense-guard listed below is synchronized directly with [lexicon_rules.json](./lexicon_rules.json), which `scripts/plain_human_audit.py` loads at runtime.

## 1. Scientific Terminology Whitelist (NEVER Dumb Down Domain Terms)

Standard scientific terms are clear, precise, and expected by reviewers. Never replace or penalize them:
- **Biogeochemistry & ecology**: `soil respiration`, `sensible heat flux`, `latent heat`, `evapotranspiration`, `net radiation`, `bulk density`, `stoichiometry`, `mineralization`, `immobilization`, `nitrification`, `denitrification`, `methanogenesis`, `methanotrophy`, `priming`, `labile`, `recalcitrant`, `sequestration`, `homeostasis`, `exogenous`, `biphasic`, `saturation`, `leaching`, `partitioning`, `heterogeneity`, `threshold`, `tipping point`, `critical load`, `trade-off`, `feedback`, `trophic cascade`, `governing equation`, `microbially mediated`, `elevated CO2`.
- **Statistics & modeling**: `random forest`, `generalized additive model`, `cross-validation`, `extrapolation`, `interpolation`, `uncertainty`, `sensitivity analysis`, `attribution`, `bootstrap`, `ensemble`, `covariate`, `collinearity`, `autocorrelation`, `heteroscedasticity`, `robust regression`, `parsimonious`, `a priori`, `post hoc`, `stochastic`.
- **Sense-guarded terms** (blocked in figurative AI hype, **automatically allowed** in their real scientific sense by `lexicon_rules.json`):
  - `amplified` (`PCR amplified`, `16S/ITS`, `Arctic amplification`, `signal`)
  - `attenuated` (`light/radiation/PAR/flood/signal attenuation`)
  - `precipitated` (`CaCO3/carbonate/Fe/Al/mineral precipitation`)
  - `granular` (`granular soil/sand/aggregate/particle structure`)
  - `architecture` (`root/canopy/crown/plant/branch/neural/network architecture`)
  - `trajectory` (`HYSPLIT back-trajectory`, `air-mass`, `successional`, `emission/SSP trajectory`)
  - `realm` (`biogeographic/Palearctic/terrestrial/marine realm`)
  - `nexus` (`water-energy-food nexus`)
  - `nascent` (`nascent oxygen/radical/polymer/chain`)

## 2. Synchronized Obscure / Pompous Lexicon (61,560-Word Human Audit + Adversarial Co-Review)

- **Tier-1 hard FAIL — AI ornament & pompous literary verbs (0 hits in 61,560 human words, except rare near-zero markers)**:
  `leverage`, `harness`, `unravel`, `disentangle`, `illuminate`, `orchestrate`, `modulate`, `attenuate`*`, `amplify`*`, `bolster`, `foster`, `catalyze`, `precipitate`*`, `underpin`, `reshape`, `reconfigure`, `spearhead`, `necessitate`, `corroborate`, `substantiate`, `perpetuate`, `entail`, `delineate`, `elucidate`, `decipher`, `utilize`, `underscore`, `unveil`, `delve`, `embark`, `endeavor/endeavour`, `commence`, `ascertain`, `garner`, `glean`, `obviate`, `engender`, `evince`, `purport`, `effectuate`, `operationalize`, `contextualize`, `showcase`, `spotlight`, `galvanize`, `epitomize`, `juxtapose`, `curtail`, `dampen`, `circumvent`, `coalesce`, `elicit`, `emanate`, `eschew`, `impart`, `instantiate`, `permeate`, `portend`, `posit`, `preclude`, `promulgate`, `relegate`, `scrutinize`, `subsume`, `surmount`, `transcend`, `ameliorate`. *(Items marked `*` carry domain sense-guards above.)*
- **Tier-1 hard FAIL — Pompous nouns, modifiers & archaic connectors (0 hits in the 5 Tier-1 top-journal anchor manuscripts)**:
  `crucially`, `intriguingly`, `remarkably`, `fundamentally`, `profoundly`, `starkly`, `strikingly`, `concomitant(ly)`, `notwithstanding`, `heretofore`, `hitherto`, `quintessential`, `actionable`, `granular`*`, `imperative`, `nuance(d/s)`, `overarching`, `architecture`*`, `complexities`, `cornerstone`, `intricacies`, `linchpin`, `nexus`*`, `paradigm`, `realm`*`, `synergy`, `tapestry`, `trajectory/trajectories`*`, `underpinnings`, `multifaceted`, `pivotal`, `paramount`, `holistic`, `intricate`, `interplay`, `plethora`, `myriad`, `milieu`, `conundrum`, `ramification(s)`, `burgeoning`, `nascent`*`, `seminal`, `salient/salience`, `commendable`, `meticulous(ly)`, `invaluable`, `inextricably`, `ostensibly`, `putatively`, `purportedly`, `indubitably`, `unequivocally`, `dearth`, `surfeit`, `erstwhile`, `vantage`, `conduit`, `panacea`, `antithesis`, `enigma`, `epitome`, `hallmark`, `impetus`, `vestige`, `amelioration`, `aforementioned`, `aforesaid`; archaic connectors: `whereby`, `whereof`, `thereof`, `therein`, `hereby`, `henceforth`, `inasmuch as`, `insofar as`, `vis-a-vis`, `albeit`, `whilst`, `ergo`, `thusly`, `by virtue of`, `in the event that`, `for the purpose of`, `with a view to`, `subsequent to`, `pertaining to`.
- **Tier-2 advisory prune (`style_warns` — allowed occasionally in published human papers, prune when dense)**:
  `employ`, `render`, `deem`, `pinpoint`, `streamline`, `unpack`, `reconcile`, `compelling`, `pervasive`, `unprecedented`, `stark`, `striking`, `indispensable`, `noteworthy`, `notably`, `markedly`, `dichotomy`, `propensity`, `facet(s)`, `paucity`, `ubiquitous`, `in terms of`, `with respect to` (non-calculus), `with regard to`, `the former/the latter`, `wherein`, `herein`, `could potentially`, `It is worth/important/should be noted that`, `play a key/important role in`.

## 3. Plain Human Verb & S-V-O Replacement Table

| When AI or formal habits write... | Plain top-journal default (verified corpus counts) |
|---|---|
| `utilize`, `employ`, `leverage`, `harness` | `use` (530x) |
| `amplify`, `bolster`, `augment` (non-ML), `elevate` (non-CO2) | `increase` (202x), `enhance` (45x), `stimulate` |
| `attenuate`, `dampen`, `curtail`, `ameliorate` | `decrease` (108x), `reduce` (47x), `lower`, `suppress`, `improve` |
| `elucidate`, `delineate`, `unravel`, `disentangle`, `decipher`, `illuminate`, `ascertain`, `scrutinize` | `explain` (42x), `show` (47x), `find` (47x), `quantify`, `clarify`, `separate`, `check`, `test` |
| `underscore`, `corroborate`, `substantiate`, `evince`, `showcase` | `show`, `indicate` (71x), `suggest` (36x), `support`, `confirm` |
| `orchestrate`, `modulate`, `underpin`, `engender`, `elicit` | `affect` (79x), `control`, `drive`, `cause` (47x), `lead to` (62x) |
| `commence`, `endeavor`, `circumvent`, `eschew`, `preclude`, `obviate` | `start/begin`, `try/aim`, `avoid`, `prevent`, `remove the need for` |
| `necessitate` / `reshape`, `reconfigure` | `require`, `need` / `change`, `alter`, `shift` |
| `performed an evaluation/assessment of X` | `evaluated X` / `assessed X` |
| `The estimation of X was conducted` | `We estimated X` |
| `exhibited a significant declining trend` | `declined significantly` |
| `due/attributable to the fact that` / `serves to increase` | `because` / `increases` |
| `not uncommon` / `not insignificant` / `may potentially` | `common` / `substantial` / `may` |
| `was nonlinearly organized by X` | `showed a nonlinear relationship with X` |
| `remained spatially coherent under stricter conditions` | `changed little when we used stricter thresholds` |

## 4. Synthetic AI-Obscurity vs Plain-Human Rewrite Pairs

### Pair A — Coined pseudo-jargon & fake spatial vocabulary
- **AI obscure**: `However, this assumption has rarely been evaluated at a common spatial and depth support.`
  - Problem: `at a common spatial and depth support` invents cryptic jargon for a simple idea.
- **Plain human**: `However, this assumption has rarely been tested across the same study area and soil depths.`

### Pair B — Inanimate diagnostic actor + cryptic technical stack
- **AI obscure**: `Robustness diagnostics confirmed that the high-export state remained spatially coherent under stricter frost and snow depth split conditions.`
  - Problem: Fake actor (`Robustness diagnostics confirmed`), invented phrase (`spatially coherent`), stacked noun chain (`frost and snow depth split conditions`).
- **Plain human**: `Sensitivity tests showed that the spatial pattern of basins with high nitrate export changed little when we used stricter thresholds for snow depth and soil frost.`

### Pair C — Abstract metaphor verb + trailing `with ... modifying` clause
- **AI obscure**: `Supplementary hydroclimatic diagnostics further suggested that winter nitrate export was nonlinearly organized by snow depth and air temperature, with basin slope and soil texture modifying the relationship.`
  - Problem: `Supplementary hydroclimatic diagnostics`, metaphorical passive (`nonlinearly organized by`), wordy `with ... modifying` tail.
- **Plain human**: `Additional analyses suggested that winter nitrate export showed nonlinear relationships with snow depth and air temperature. These relationships also varied across basin slopes and soil textures.`

### Pair D — Coined hyphenated sensitivity jargon + `held fixed`
- **AI obscure**: `Future scenario substitution was interpreted as climate-side forcing sensitivity with current land cover, drainage area, and grid size held fixed.`
  - Problem: Coined labels (`Future scenario substitution`, `climate-side forcing sensitivity`), missing human subject (`We`).
- **Plain human**: `To isolate the effect of future climate on river nitrate, we kept current land cover, drainage area, and grid size unchanged while running future climate scenarios.`

### Pair E — Stacked pre-modifiers & coined `structuring`
- **AI obscure**: `We aimed to develop a basin-specific, depth-resolved soil carbon inventory of soil carbon storage in mountain meadows and quantify its vertical, climatic, and regional distribution. The inventory revealed strong vertical and biome-level structuring that could not be captured by surface samples alone.`
  - Problem: Redundant noun stack (`basin-specific, depth-resolved soil carbon inventory of soil carbon storage`), unnatural noun (`biome-level structuring`).
- **Plain human**: `We aimed to estimate soil carbon storage across four soil depths in mountain meadows and map its variation across depths, elevation zones, and regions. Soil carbon storage varied strongly with soil depth and elevation zone. Surface samples alone could not capture these patterns.`

### Pair F — Multi-clause AI bloat vs flat 1-clause human prose
- **AI obscure (42 words, 3 nested layers, 8 AI clichés)**:
  `Yet, empirical manipulations have yielded starkly divergent and seemingly paradoxical trajectories in stream nitrate responses across alpine catchments, fostering persistent conceptual ambiguity regarding the mechanistic underpinnings governing whether chronic winter warming amplifies or attenuates watershed nitrogen export.`
- **Plain human (32 words, 1 clause, plain everyday words)**:
  `However, field studies have reported both positive and negative effects of winter warming on stream nitrate export in mountain catchments, leading to debates on how snowpack loss alters watershed nitrogen retention.`

### Pair G — Multi-step mechanism: cramming into 1 sentence vs 4 crisp sequential sentences
- **AI obscure**:
  `Thin winter snowpacks can expose surface soils to repeated freezing that disrupts fine root tissues, while concomitantly shattering soil aggregates susceptible to leaching and accelerating early-spring microbial mineralization, thereby collectively precipitating a sharp nitrate export trajectory.`
- **Plain human (4 flat sentences)**:
  `When winter snowpacks thin, exposed surface soils freeze and thaw repeatedly. Repeated freezing damages fine plant roots and breaks down soil aggregates. These physical losses release dissolved organic matter that microbes convert into nitrate during early spring thaw. Together, these processes explain why stream nitrate export rises sharply once snow depth drops below a threshold.`

### Pair H — Nonstop Number Dumping (Reviewer Fatigue) vs Pattern-First Prose + Table Offload
- **Number-heavy draft (16 result numbers in 2 sentences)**:
  `Random CV described interpolation-like performance across four depth layers; soil carbon R2 values were 0.612, 0.584, 0.631, and 0.649 across the four layers, whereas bulk density R2 values were 0.704, 0.768, 0.781, and 0.752 for the gap-filled product. Spatial CV gave a conservative geographic extrapolation check, with soil carbon spatial-CV R2 values of 0.105, 0.124, 0.088, and 0.052 and bulk density spatial-CV R2 values of 0.091, 0.116, 0.138, and 0.084.`
  - Problem: Reads an entire supplementary table aloud in prose (16 three-digit decimals in 2 sentences), stacks coined compounds (`interpolation-like`, `spatial-CV`), and exhausts reviewers before they reach the main takeaway.
- **Plain human (2 compact ranges, details offloaded to Table 1)**:
  `Random cross-validation showed moderate to strong accuracy across all four soil layers for both soil carbon and bulk density (R2 = 0.58–0.78; Table 1). In contrast, spatial cross-validation showed much lower accuracy across layers (R2 <= 0.14), indicating higher uncertainty when the model predicted soil properties in unsampled regions.`

### Pair I — AI Quotation Marks, Dashes, Coined Words & Long Clauses (4 Combined AI Ticks)
- **AI obscure**:
  `In this study, we introduce a "density-coupled resilience framework"—an inventory-scale metric that evaluates whether marsh carbon and sediment accumulate synchronously across four "depth-stratified" soil horizons, which, when integrated with hydroclimate-driven spatial modeling, reveals that brackish marshes act as "carbon-rich, methane-lagging" hotspots.`
- **Plain human (0 quotes, 0 em dashes, 0 coined compounds, explicit `we` S-V-O)**:
  `In this study, we used the ratio of soil carbon burial to sediment accretion across four soil layers to test whether carbon and mineral sediment accumulate together in tidal marshes. When we combined these maps with salinity data, we found that polyhaline marshes store high soil carbon while keeping methane release low.`

### Pair J — Internal Code Names & Underscore Identifiers vs Plain Prose & Clear Sign-Off Briefs
- **Manuscript prose with code/underscore leakage (unreadable without a script codebook)**:
  `Under OptionB, Model_DynCond_v2 reduced bias relative to M0 and M1 across S1, S2, and S3 when wind_dir_deg, h_c, and x_90 were filtered by QC_flag in coastal_all.`
  - Problem: Leaks raw script strings (`Model_DynCond_v2`, `wind_dir_deg`, `QC_flag`, `coastal_all`), raw underscore subscripts (`h_c`, `x_90`), workflow labels (`OptionB`), and opaque alphanumeric short codes (`M0`, `M1`, `S1`, `S2`, `S3`).
- **Plain human manuscript prose (split into 2 crisp S-V-O sentences, <=24w each)**:
  `We removed low-quality observations and accounted for wind direction, canopy height, and the 90% footprint distance. In the coastal marsh dataset, the dynamic conductance model then produced smaller bias in sensible heat flux than the two baseline models across all three wind regimes.`
- **Author decision brief with internal codes (author cannot approve)**:
  `请拍板：本次是按 OptionB 走 run_v04 还是回退 S3 的 site_all 口径，另需确认 param_fit 和 R02 是否合并到 v12？`
- **Plain human decision brief (author can decide in 5 seconds)**:
  `请拍板两件事：（1）表 2 和正文结果中的表层土壤碳储量，是只纳入有实测容重的 380 个样点，还是纳入全部 620 个含推算容重的样点？前者数据更硬但高海拔样本减少近四成，后者覆盖更全但审稿人可能质疑推算误差。（2）方法第 2.3 节里是否把风向校正步骤写进主文，还是放进补充材料以节省主文字数？`

### Pair K — Buried Subject, Nominalized Weak Verbs & Rare Literary Words vs Explicit Plain S-V-O
- **Obscure formal prose (buried subject, nominalization, rare words, archaic connectors, hedge stack, litotes)**:
  `With the rapid advancement of remote sensing, there is an urgent need to ascertain whether deep coastal marsh soils exhibit a declining trend in carbon burial. In the context of a paucity of deep cores, the estimation of regional carbon burial rates across four layers was performed whereby spatial extrapolation may potentially suffer from not insignificant bias due to the fact that deep bulk density data remain sparse.`
  - Problem: Buried subjects (`With the rapid advancement...`, `there is an urgent need`, `In the context of...`), rare words (`ascertain`, `paucity`), nominalized passive (`The estimation of ... was performed`), trend nominalization (`exhibit a declining trend`), archaic `whereby`, hedge stack (`may potentially`), litotes (`not insignificant`), and wordy `due to the fact that`.
- **Plain human S-V-O (preserves standard scientific terms `extrapolation`, `bulk density`, zero fluff)**:
  `We need to know whether deep coastal marsh soils are storing less carbon. Because deep sediment cores are scarce, we estimated regional carbon burial rates across four soil layers. Spatial extrapolation into unsampled regions may still carry large bias because deep bulk density measurements remain sparse.`

## 5. Safe Connectors & Participles (Verified Human Frequencies)

- **Preferred sentence-initial connectors (use sparingly — most sentences start directly with the subject)**:
  `However`, `Therefore`, `Thus`, `In addition`, `Also`, `Moreover`, `Furthermore`, `Meanwhile`, `In contrast`, `Instead`, `For example`, `For instance`, `On the other hand`, `As a result`, `Consequently`, `Similarly`, `Overall`.
- **Never chain `Furthermore` / `Moreover` / `Additionally` on consecutive paragraphs**, and avoid `Crucially`, `Intriguingly`, `Importantly`, `Taken together`.
- **Safe trailing participles (max <=12% of sentences, never two in one sentence)**:
  `leading to`, `indicating`, `suggesting`, `causing`, `including`, `using`, `resulting in`, `accounting for`.
- **Avoid AI-cliché trailing participles**:
  `, underscoring`, `, illuminating`, `, reshaping`, `, highlighting`, `, unveiling`, `, demonstrating the pivotal`.
