#!/usr/bin/env python3
"""
Deterministic Plain-Human Scientific Writing Auditor (v3).
Calibrated on 12 anonymized human-authored top-journal and pre-LLM scientific manuscripts
(61,560+ prose words), adversarially co-reviewed, and validated against AI-obscured
and number-dumping contrast drafts.

Hard FAIL gates enforce:
  1. Strict numeric restraint (no >=4-number dump sentences; no 3+ consecutive number walls)
  2. Zero quotation marks framing words/concepts in prose
  3. Zero em dashes and zero spaced parenthetical dashes
  4. Zero coined AI compounds / triple-hyphen stacks / excess novel hyphenation
  5. Zero long/nested clauses and zero long trailing relative/subordinate clauses (>16w)
  6. Plain everyday verbs/nouns with scientific domain sense-guards (ban rare/pompous
     non-scientific verbs, nouns, modifiers, archaic connectors, and inanimate meta-actors)
  7. Explicit Subject-Verb-Object (S-V-O) clarity (no nominalized weak verbs, no
     buried-subject expletives / "the fact that" / "serves to" / hedge stacks / litotes,
     no >=16w pre-verb subjects, >=22w front-loaded openers, 3+-of chains, or heavy SV interrupters)
  8. Zero underscore identifiers/subscripts, internal workflow codes, or opaque short-code soup

Usage:
    python plain_human_audit.py <path_to_txt_md_or_docx> [--json]
    python plain_human_audit.py --text "Paste English prose here..."
"""

import argparse
import json
import os
import re
import statistics
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _load_lexicon():
    lex_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "references",
        "lexicon_rules.json",
    )
    if os.path.exists(lex_path):
        with open(lex_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_LEX = _load_lexicon()

BANNED_AI_VERBS = set(_LEX.get("tier1_fail_verbs", [
    "leverage", "leverages", "leveraged", "leveraging",
    "harness", "harnesses", "harnessed", "harnessing",
    "unravel", "unravels", "unraveled", "unraveling",
    "disentangle", "disentangles", "disentangled", "disentangling",
    "illuminate", "illuminates", "illuminated", "illuminating",
    "orchestrate", "orchestrates", "orchestrated", "orchestrating",
    "modulate", "modulates", "modulated", "modulating",
    "attenuate", "attenuates", "attenuated", "attenuating",
    "amplify", "amplifies", "amplified", "amplifying",
    "bolster", "bolsters", "bolstered", "bolstering",
    "foster", "fosters", "fostered", "fostering",
    "catalyze", "catalyzes", "catalyzed", "catalyzing",
    "precipitate", "precipitates", "precipitated",
    "underpin", "underpins", "underpinned", "underpinning",
    "reshape", "reshapes", "reshaped", "reshaping",
    "reconfigure", "reconfigures", "reconfigured", "reconfiguring",
    "spearhead", "spearheads", "spearheaded",
    "necessitate", "necessitates", "necessitated", "necessitating",
    "corroborate", "corroborates", "corroborated",
    "substantiate", "substantiates", "substantiated",
    "perpetuate", "perpetuates", "perpetuated",
    "entail", "entails", "entailed",
    "delineate", "delineates", "delineated", "delineating",
    "elucidate", "elucidates", "elucidated", "elucidating",
    "decipher", "deciphers", "deciphered", "deciphering",
    "utilize", "utilizes", "utilized", "utilizing",
    "underscore", "underscores", "underscored", "underscoring",
    "unveil", "unveils", "unveiled", "unveiling",
]))

BANNED_AI_BUZZWORDS = set(_LEX.get("tier1_fail_nouns_and_modifiers", [
    "crucially", "intriguingly", "remarkably", "fundamentally", "profoundly",
    "starkly", "strikingly", "concomitant", "concomitantly",
    "notwithstanding", "heretofore", "hitherto", "quintessential",
    "actionable", "granular", "imperative", "nuanced", "overarching",
    "architecture", "complexities", "cornerstone", "intricacies",
    "linchpin", "nexus", "paradigm", "realm", "synergy", "tapestry",
    "trajectory", "trajectories", "underpinnings", "multifaceted",
    "pivotal", "paramount", "holistic", "intricate", "interplay",
]))

TIER2_STYLE_WORDS = set(_LEX.get("tier2_style_warn_words", []))

SENSE_GUARDS = {
    k.lower(): re.compile(v, re.I)
    for k, v in _LEX.get("sense_guards", {}).items()
}

ALLOWED_TRIPLE_HYPHENS = {
    "inverted-u-shaped", "leave-one-out", "root-mean-square", "out-of-bag",
    "low-to-mid-latitude", "mid-to-high-latitude", "high-to-low-latitude",
    "west-to-east", "east-to-west", "north-to-south", "south-to-north",
    "root-to-shoot", "nitrogen-to-phosphorus", "carbon-to-nitrogen",
    "land-use-change", "non-n-fixing", "n-deposition-induced",
    "n-deposition-related", "high-n-deposition", "mid-21st-century",
    "warm-temperate-deciduous", "c-to-n", "n-to-p", "above-and-belowground",
    "data-driven-process",
    "needle-broadleaved-mixed", "soil-plant-atmosphere", "plant-soil-microbe",
    "water-energy-food", "food-energy-water",
}

BANNED_AI_COMPOUNDS = {
    "inventory-scale", "density-based", "density-coupled", "stock-weighted",
    "density-weighted", "pixel-weighted", "inventory-weighted", "climate-forcing",
    "n-side", "c-side", "p-side", "hydroclimate-driven", "climate-modulated",
    "depth-resolved", "layer-resolved", "profile-resolved", "depth-stratified",
    "layer-stratified", "wetland-specific", "wetland-type", "policy-relevant",
    "decision-relevant", "management-relevant", "process-level", "regime-level",
    "system-level", "profile-level", "stock-level", "framework-level",
    "pixel-level", "interpolation-like", "extrapolation-like", "target-like",
    "diagnostic-like", "screening-like", "baseline-like",
    "nitrogen-lagging", "n-lagging", "c-lagging", "carbon-lagging",
    "microbial-root", "depth-explicit", "spatially-explicit",
    "mechanistically-grounded", "biogeochemically-driven", "domain-wide",
    "horizon-specific", "layer-specific", "scenario-based",
}

COINED_COMPOUND_RE = re.compile(
    r"(?:-(?:resolved|stratified|lagging|modulated|organized|forcing)$|"
    r"^(?:n|c|p|carbon|nitrogen|soil|climate)-side$|"
    r"(?:interpolation|extrapolation|target|diagnostic|screening|inventory|baseline|regime)-like$)",
    re.I,
)

INANIMATE_OBSCURE_PATTERNS = [
    (
        "INANIMATE_DIAGNOSTIC_ACTOR",
        re.compile(
            r"\b(?:robustness|sensitivity|hydroclimatic|supplementary|statistical)\s+diagnostics?\s+"
            r"(?:confirm|confirmed|confirms|suggest|suggested|suggests|show|showed|shows|indicate|indicated|reveal|revealed|demonstrate|demonstrated)\b",
            re.I,
        ),
        "Replace inanimate diagnostic meta-noun actor with plain voice (e.g., Sensitivity tests showed... or We tested whether...).",
    ),
    (
        "METAPHORICAL_ORGANIZED_BY",
        re.compile(r"\b(?:nonlinearly|linearly|spatially|hierarchically|systematically)\s+organized\s+by\b", re.I),
        "Replace abstract organized by with plain showed a nonlinear relationship with or varied with.",
    ),
    (
        "CRYPTIC_SUPPORT_JARGON",
        re.compile(r"\b(?:common|unified)\s+spatial\s+and\s+depth\s+support\b", re.I),
        "Replace cryptic spatial and depth support with the same study area and soil depths.",
    ),
    (
        "COINED_STRUCTURING",
        re.compile(r"\b(?:vertical|spatial|regional|wetland-type|biome-level|depth)\s+(?:and\s+[\w-]+\s+)?structuring\b", re.I),
        "Replace abstract structuring with differences across or variation with.",
    ),
    (
        "AI_METAPHOR_CLICHE",
        re.compile(r"\b(?:paves?\s+the\s+way|unlocks?\s+the\s+potential|opens?\s+new\s+avenues?)\b", re.I),
        "Delete decorative metaphor; state the concrete scientific next step directly.",
    ),
    (
        "CLICHE_PARTICIPLE_TAIL",
        re.compile(
            r",\s+(?:thereby\s+|thus\s+|ultimately\s+)?(?:underscoring|illuminating|reshaping|unveiling|highlighting|bolstering|fostering|amplifying|attenuating|catalyzing)\b",
            re.I,
        ),
        "Replace AI-cliche trailing participle with a separate plain sentence or leading to / indicating / suggesting.",
    ),
    (
        "CRYPTIC_HELD_FIXED_OR_CONTEXT",
        re.compile(r"\b(?:retained\s+in\s+a\s+\w+\s+context|held\s+fixed|scenario\s+substitution)\b", re.I),
        "State plainly what was included or kept unchanged (e.g., we kept X unchanged).",
    ),
]

# --- v3 S-V-O Clarity, Nominalization & Obscure-Syntax Patterns ---

_ACTION_NOUN = (
    r"(?:evaluation|assessment|examination|investigation|comparison|estimation|calculation|"
    r"quantification|determination|identification|characterization|exploration|validation|"
    r"optimization|reduction|improvement)"
)
_LIGHT_VERB = (
    r"(?:perform|performs|performed|performing|conduct|conducts|conducted|conducting|"
    r"carr(?:y|ies|ied|ying)\s+out|undert(?:ake|akes|ook|aken)|make|makes|made|achiev(?:e|es|ed))"
)

SVO_SYNTAX_FAIL_PATTERNS = [
    (
        "NOMINALIZED_WEAK_VERB",
        re.compile(rf"\b{_LIGHT_VERB}\s+(?:an?|the)\s+(?:[A-Za-z-]+\s+){{0,2}}{_ACTION_NOUN}\s+(?:of|between|for)\b", re.I),
        "Unpack nominalized action noun into a direct active verb (e.g., 'evaluated X' instead of 'performed an evaluation of X').",
    ),
    (
        "NOMINALIZED_WEAK_VERB",
        re.compile(
            r"\bThe\s+(?:[A-Za-z-]+\s+)?[A-Za-z]+(?:tion|sion|ment)\s+of\b[^.;]{1,65}?"
            r"\b(?:was|were|is|are)\s+(?:then\s+)?(?:performed|conducted|carried\s+out|undertaken|achieved|accomplished|implemented|executed)\b"
        ),
        "Move the real action into an active main verb with an explicit subject (e.g., 'We estimated X' instead of 'The estimation of X was performed').",
    ),
    (
        "TREND_NOMINALIZATION",
        re.compile(
            r"\b(?:exhibit|display|demonstrat|experienc|underw)[a-z]*\s+an?\s+(?:[A-Za-z-]+\s+){0,2}"
            r"(?:declining|decreasing|increasing|rising|downward|upward|growing)\s+(?:trend|tendency|pattern)\b",
            re.I,
        ),
        "Replace verbose trend nominalization with a direct verb (e.g., 'increased significantly' or 'declined steadily').",
    ),
    (
        "BURIED_SUBJECT_OPENER",
        re.compile(
            r"^(?:(?:However|Thus|Therefore|Moreover|Furthermore|In addition),\s+)?(?:"
            r"It\s+is\s+(?:noteworthy|interesting|crucial|imperative)\s+(?:that\b|noting\b|to\s+(?:note|mention|emphasi[sz]e|highlight|stress|point\s+out))"
            r"|There\s+(?:is|are|remains?|exists?)\s+an?\s+(?:urgent|pressing|critical|growing|increasing)\s+need\b"
            r"|With\s+the\s+(?:rapid\s+)?(?:development|advancement|progress|growth)\s+of\b"
            r"|In\s+the\s+context\s+of\b[^,]{3,90},\s+(?:an?|the)\b[^,]{1,60}?\b(?:was|were)\s+(?:conducted|performed|developed|carried\s+out)\b)",
            re.I,
        ),
        "Delete empty filler opener and start directly with the concrete subject and active verb.",
    ),
    (
        "FACT_THAT_BLOAT",
        re.compile(
            r"\b(?:(?:due|owing|attributable)\s+to|in\s+(?:light|view|spite)\s+of|despite|given|considering|regardless\s+of)\s+the\s+fact\s+that\b|\bthe\s+fact\s+that\b",
            re.I,
        ),
        "Replace 'the fact that' wordiness with plain 'because', 'although', or a direct subject.",
    ),
    (
        "ARCHAIC_CONNECTOR",
        re.compile(
            r"\b(?:whereby|whereof|thereof|therein|hereby|henceforth|"
            r"inasmuch\s+as|insofar\s+as|vis-[àa]-vis|albeit|whilst|ergo|thusly|"
            r"by\s+virtue\s+of|in\s+the\s+event\s+that|for\s+the\s+purpose\s+of|"
            r"with\s+a\s+view\s+to|subsequent\s+to|pertaining\s+to)\b",
            re.I,
        ),
        "Replace archaic/legalistic connector with plain everyday English (e.g., 'where', 'because', 'although', 'to', 'after', 'about').",
    ),
    (
        "SERVES_TO_BLOAT",
        re.compile(r"\b(?:serves?|served|serving)\s+to\s+(?!be\b)[a-z]+\b", re.I),
        "Delete 'serves to' and use the real verb directly (e.g., 'increases' instead of 'serves to increase').",
    ),
    (
        "HEDGE_STACK",
        re.compile(
            r"\b(?:(?:may|might|can)\s+(?:potentially|possibly|perhaps|conceivably)|"
            r"could\s+(?:possibly|perhaps|conceivably)|"
            r"(?:appears?|seems?)\s+to\s+(?:suggest|indicate|imply)|"
            r"may\s+be\s+likely\s+to)\b",
            re.I,
        ),
        "Remove stacked double hedge; keep one clear hedge verb (e.g., 'may', 'could', or 'suggests').",
    ),
    (
        "LITOTES_OBSCURITY",
        re.compile(r"\bnot\s+(?:uncommon|unusual|unlikely|insignificant|unimportant|inconsiderable|dissimilar|unreasonable)\b", re.I),
        "Replace awkward double negative with a direct positive statement (e.g., 'common', 'likely', 'similar').",
    ),
]

STYLE_ADVISORY_PATTERNS = [
    (
        "STYLE_EXPLETIVE_FILLER",
        re.compile(
            r"^(?:(?:However|Thus|Therefore|In addition),\s+)?(?:"
            r"It\s+is\s+(?:worth\s+noting|important\s+to\s+note)\s+that"
            r"|It\s+should\s+be\s+(?:noted|mentioned|emphasized|pointed\s+out)\s+that"
            r"|It\s+(?:is|has\s+been)\s+(?:widely|well|generally)\s+(?:known|accepted|recognized)\s+that)\b",
            re.I,
        ),
        "Consider trimming filler opener and starting directly with the concrete subject.",
    ),
    (
        "STYLE_WORDY_PHRASE",
        re.compile(
            r"\b(?:in\s+terms\s+of|with\s+regard\s+to|in\s+relation\s+to|in\s+close\s+proximity\s+to|"
            r"the\s+(?:former|latter)|wherein|herein|could\s+potentially|"
            r"(?:exert|exerts|exerted)\s+an?\s+(?:[A-Za-z-]+\s+)?(?:effect|impact|influence)\s+on|"
            r"play[a-z]*\s+an?\s+(?:key|important|critical|crucial|major|vital|central)\s+role\s+in|"
            r"(?:it|this|which|that)\s+(?:functions?|acts?)\s+to\s+[a-z]+)\b",
            re.I,
        ),
        "Consider replacing wordy academic phrase with a simpler direct verb or preposition.",
    ),
    (
        "STYLE_WITH_RESPECT_TO",
        re.compile(r"\bwith\s+respect\s+to\b", re.I),
        "Consider replacing 'with respect to' with 'for', 'in', or 'across' (ignored in calculus/derivative contexts).",
    ),
    (
        "STYLE_DANGLING_PURPOSE",
        re.compile(
            r"^(?:To|In\s+order\s+to)\s+[a-z]+\b[^,]{3,85},\s+(?:an?|the)\s+[^,]{1,55}?\b(?:was|were)\s+(?:[a-z]+ly\s+)?(?:[a-z]+ed|built|made|run|chosen)\b"
        ),
        "Purpose opener followed by passive main clause hides the actor; prefer 'To test X, we built...'.",
    ),
]

CALC_WRT_GUARD_RE = re.compile(r"\b(?:derivative|derivatives|differenti\w*|partial|gradient|slope|sensitivit\w*|∂)\b", re.I)

TYPO_GUARD_PATTERNS = [
    (
        "P013_RANGE_HYBRID",
        re.compile(r"\b(?:between|from)\s+\d+(?:\.\d+)?\s*[–\-]\s*\d+(?:\.\d+)?", re.I),
        "Do not mix between/from with an en-dash range; write between X and Y, from X to Y, or X–Y.",
    ),
    (
        "IN_RELATIVE_TO",
        re.compile(r"\bin\s+relative\s+to\b", re.I),
        "Write relative to (not in relative to).",
    ),
]

CLAUSE_RE = re.compile(
    r"\b(which|that(?!\s+(?:of|study|time|year|period|region|case|area|dataset|model|layer|depth|value|site|group|effect|pattern|metric)\b)|"
    r"where|whereas|while|although|though|because|since(?!\s+(?:18|19|20)\d{2}\b|\s+the\s+Industrial\b)|"
    r"when|if(?!\s+any\b)|whether|whereby|wherein|whereafter|unless|until)\b",
    re.I,
)
TRAILING_CLAUSE_RE = re.compile(
    r",\s+(which|whereas|although|though|while|whereby|wherein)\b([^.;!?]+)",
    re.I,
)
PARTICIPLE_TAIL_RE = re.compile(
    r",\s+(?:thereby\s+|thus\s+|potentially\s+|ultimately\s+|further\s+)?([a-z]+ing)\b"
)
PREPOSITIONAL_ING_ALLOW = {
    "including", "excluding", "using", "according", "depending",
    "ranging", "following", "considering", "assuming", "comparing",
    "corresponding", "representing", "containing", "spanning", "covering",
    "warming", "cooling", "rooting", "declining", "cycling", "grazing",
    "leaching", "burning", "harvesting", "weathering", "scaling", "mapping",
    "modeling", "modelling", "sampling", "filtering", "flooding", "drying",
    "wetting", "freezing", "thawing", "logging", "mining", "cropping",
    "planting", "trenching", "growing", "coupling", "decoupling", "mixing",
    "liming", "mowing", "draining", "shading",
}
GERUND_SUBJ_RE = re.compile(
    r"^([A-Z][a-z]+ing)\s+[^,]{3,60}?\s+(?:showed|revealed|indicated|suggested|demonstrated|confirmed)\s+that\b"
)

# SVO Subject-to-Verb distance helpers (abstain-when-unsure design)
SAFE_LEAD_CONN_RE = re.compile(
    r"^(?:However|Therefore|Thus|Moreover|Furthermore|Additionally|Meanwhile|Instead|Conversely|Similarly|"
    r"Nevertheless|Nonetheless|Consequently|Overall|Specifically|Notably|Also|Yet|But|"
    r"In\s+addition|In\s+contrast|For\s+example|For\s+instance|On\s+the\s+other\s+hand|As\s+a\s+result|On\s+this\s+basis),\s+|"
    r"^(?:But|Yet|And|So)\s+",
    re.I,
)
FRONT_PREP_OPENER_RE = re.compile(
    r"^(?:In\s+addition\s+to|According\s+to|Compared\s+(?:to|with)|Based\s+on|Due\s+to|Owing\s+to|Because\s+of|"
    r"In|For|Across|Under|Based|Compared|Given|Due|When|Although|Though|Because|After|Before|"
    r"By|Through|With|Without|During|Following|Regarding|Considering|Using|To|From|Within|Among|Despite|Unlike|"
    r"At|On|Over|Inspired|Accompanying|Given|Whereas|While|Since|Unless|Until|Once|Whether)\b",
    re.I,
)
UNIT_TOKENS = {
    "ha", "yr", "yrs", "kg", "kgn", "kgc", "pgc", "pgn", "tgc", "tgn", "mg", "g", "cm", "mm", "km", "m", "t", "tg", "pg", "l", "mj",
}
CORE_VERB_ANCHORS = {
    "is", "are", "was", "were", "has", "have", "had", "do", "does", "did",
    "can", "could", "may", "might", "will", "would", "should", "shall", "must",
    "show", "shows", "showed", "find", "finds", "found", "indicate", "indicates", "indicated",
    "suggest", "suggests", "suggested", "reveal", "reveals", "revealed",
    "demonstrate", "demonstrates", "demonstrated", "confirm", "confirms", "confirmed",
    "increase", "increases", "increased", "decrease", "decreases", "decreased",
    "reduce", "reduces", "reduced", "decline", "declines", "declined",
    "rise", "rises", "rose", "drop", "drops", "dropped", "fall", "falls", "fell",
    "grow", "grows", "grew", "change", "changes", "changed", "vary", "varies", "varied",
    "differ", "differs", "differed", "shift", "shifts", "shifted", "alter", "alters", "altered",
    "remain", "remains", "remained", "stay", "stays", "stayed", "persist", "persists", "persisted",
    "use", "uses", "used", "apply", "applies", "applied", "build", "builds", "built",
    "develop", "develops", "developed", "estimate", "estimates", "estimated",
    "calculate", "calculates", "calculated", "quantify", "quantifies", "quantified",
    "measure", "measures", "measured", "observe", "observes", "observed",
    "evaluate", "evaluates", "evaluated", "assess", "assesses", "assessed",
    "test", "tests", "tested", "compare", "compares", "compared", "check", "checks", "checked",
    "explain", "explains", "explained", "account", "accounts", "accounted",
    "contribute", "contributes", "contributed", "control", "controls", "controlled",
    "drive", "drives", "drove", "affect", "affects", "affected", "influence", "influences", "influenced",
    "cause", "causes", "caused", "lead", "leads", "led", "limit", "limits", "limited",
    "restrict", "restricts", "restricted", "suppress", "suppresses", "suppressed",
    "stimulate", "stimulates", "stimulated", "enhance", "enhances", "enhanced",
    "promote", "promotes", "promoted", "inhibit", "inhibits", "inhibited",
    "depend", "depends", "depended", "occur", "occurs", "occurred", "exist", "exists", "existed",
    "appear", "appears", "appeared", "seem", "seems", "seemed", "tend", "tends", "tended",
    "range", "ranges", "ranged", "span", "spans", "spanned", "cover", "covers", "covered",
    "store", "stores", "stored", "hold", "holds", "held", "contain", "contains", "contained",
    "include", "includes", "included", "reflect", "reflects", "reflected",
    "represent", "represents", "represented", "provide", "provides", "provided",
    "offer", "offers", "offered", "support", "supports", "supported",
    "require", "requires", "required", "need", "needs", "needed", "play", "plays", "played",
    "keep", "keeps", "kept", "combine", "combines", "combined", "compile", "compiles", "compiled",
    "collect", "collects", "collected", "extract", "extracts", "extracted",
    "obtain", "obtains", "obtained", "derive", "derives", "derived",
    "predict", "predicts", "predicted", "simulate", "simulates", "simulated",
    "map", "maps", "mapped", "yield", "yields", "yielded", "exceed", "exceeds", "exceeded",
    "outperform", "outperforms", "outperformed", "correspond", "corresponds", "corresponded",
    "follow", "follows", "followed", "stabilize", "stabilizes", "stabilized",
    "become", "becomes", "became", "make", "makes", "made", "allow", "allows", "allowed",
    "enable", "enables", "enabled", "help", "helps", "helped", "improve", "improves", "improved",
    "strengthen", "strengthens", "strengthened", "weaken", "weakens", "weakened",
    "exhibit", "exhibits", "exhibited", "display", "displays", "displayed",
    "capture", "captures", "captured", "describe", "describes", "described",
    "dominate", "dominates", "dominated", "accumulate", "accumulates", "accumulated",
    "produce", "produces", "produced", "release", "releases", "released",
    "emit", "emits", "emitted", "absorb", "absorbs", "absorbed", "report", "reports", "reported",
    "assume", "assumes", "assumed", "determine", "determines", "determined",
    "distinguish", "distinguishes", "distinguished", "express", "expresses", "expressed",
    "model", "models", "modeled", "modelled", "verify", "verifies", "verified",
    "validate", "validates", "validated", "identify", "identifies", "identified",
    "isolate", "isolates", "isolated", "separate", "separates", "separated",
    "respond", "responds", "responded", "act", "acts", "acted", "serve", "serves", "served",
    "outweigh", "outweighs", "outweighed", "underlie", "underlies", "underlay",
    "depict", "depicts", "depicted", "lack", "lacks", "lacked", "generalize", "generalizes", "generalized",
    "bridge", "bridges", "bridged", "suffer", "suffers", "suffered", "refer", "refers", "referred",
    "relate", "relates", "related", "link", "links", "linked", "connect", "connects", "connected",
    "correlate", "correlates", "correlated", "associate", "associates", "associated",
    "infer", "infers", "inferred", "explore", "explores", "explored", "examine", "examines", "examined",
    "characterize", "characterizes", "characterized", "enhance", "enhances", "enhanced",
    "prevent", "prevents", "prevented", "avoid", "avoids", "avoided", "miss", "misses", "missed",
    "reach", "reaches", "reached", "approach", "approaches", "approached", "match", "matches", "matched",
    "diverge", "diverges", "diverged", "converge", "converges", "converged",
}
NON_VERB_PREV = {"to", "a", "an", "the", "of", "in", "on", "for", "with", "by", "from", "at", "as", "into", "between", "among", "under", "over", "their", "our", "its", "his", "her", "this", "these", "those", "such"}
SV_INTERRUPTER_RE = re.compile(
    r",\s+(?:such\s+as|including|particularly|especially|together\s+with|along\s+with|as\s+well\s+as|which)\b[^,]{3,140},",
    re.I,
)

STANDARD_DOMAIN_HYPHENS = {
    "n-limited", "n-saturated", "long-term", "short-term", "site-level",
    "grid-level", "biome-mean", "biome-level", "country-specific",
    "region-specific", "ecoregion-specific", "large-scale", "small-scale",
    "global-scale", "regional-scale", "data-driven", "process-based",
    "low-level", "high-level", "well-coordinated", "old-growth",
    "above-ground", "below-ground", "non-experimental", "non-linear",
    "cross-validated", "cross-validation", "field-observed", "model-estimated",
    "area-weighted", "community-weighted", "volume-weighted", "mass-weighted",
    "depth-weighted", "biomass-weighted", "near-surface", "end-product",
    "dose-response", "net-zero", "mid-21st", "three-stage", "two-stage",
    "multi-year", "multi-model", "warm-temperate", "mid-subtropical",
    "south-subtropical", "north-subtropical", "broad-leaved", "needle-leaf",
    "evergreen", "ozone-depleting", "long-lived", "cost-effective",
    "by-product", "self-consistent", "c-limited", "p-limited", "k-limited",
    "water-limited", "n-rich", "n-poor", "c-rich", "c-poor", "carbon-rich", "nitrogen-rich",
    "high-latitude", "low-latitude", "mid-latitude", "real-world", "species-rich",
    "forest-covered", "non-wetland", "non-forest", "clear-cutting",
    "selective-cutting", "wetting-drying", "freezing-thawing", "time-series",
    "one-way", "two-way", "z-score", "p-value", "p-values",
    "land-atmosphere", "n-induced", "n-facilitated", "n-input", "n-addition",
    "n-deposition", "meta-analysis", "meta-analyses", "co-occurring",
    "well-known", "sub-surface", "high-socd", "low-tnd", "high-tnd",
    "low-socd", "n-fixing", "non-growing", "growing-season",
    "process-augmented", "back-trajectory", "semi-mechanistic", "semi-arid",
    "10-fold", "five-fold", "cross-scale", "site-specific",
}

STOPWORDS = set(
    "the a an of in on at to for with by from as is are was were be been being "
    "have has had do does did can could may might will would should shall that "
    "which who whom whose where when while whereas although though because since "
    "if whether and or but nor so yet not no than into onto over under between "
    "among through during before after without within across along around about "
    "this these those such it its they their them we our us he she his her there "
    "here both all each every some any many much more most less fewer other "
    "another only also just even still already then now per via vs e.g i.e".split()
)

# Quote and dash regexes
COORD_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*°(?:\s*\d+(?:\.\d+)?\s*[′'](?:\s*\d+(?:\.\d+)?\s*[″\"])?)?\s*[NSEW]?\b"
)
DOUBLE_QUOTE_RE = re.compile(r"“[^”\n]{1,160}”|\"[^\"\n]{1,160}\"|[“”\"]")
SINGLE_QUOTE_PAIR_RE = re.compile(r"‘[^’\n]{1,120}’|(?<![A-Za-z0-9])'[^'\n]{1,120}'(?![A-Za-z])")
EM_OR_DOUBLE_DASH_RE = re.compile(r"—|--")
SPACED_PAREN_DASH_RE = re.compile(
    r"(?:(?<=[A-Za-z]{2})|(?<=[\)\]])|(?<=[A-Za-z]{2}\s[A-Z]))[ \t]+[–\-][ \t]+(?=[A-Za-z\(])"
)

# Internal code and underscore identifier regexes (strict ASCII boundaries so CJK/symbol adjacency never bypasses)
URL_RE = re.compile(r"https?://\S+")
UNDERSCORE_ID_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+(?![A-Za-z0-9_])")
INTERNAL_CODE_LABEL_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    r"(?:Option|Track|Gate|Workflow|Pipeline|Package|Scheme|Variant|Config|Setup|Exp|Submodel|Model|Scenario|Baseline)\s*[-]?\s*(?:[A-Z]\d{0,2}[a-z]?|\d{1,2}[A-Za-z]?)"
    r"|Case\s*[-]?\s*[A-Z]\d{1,2}[a-z]?"
    r"|Run\s*[-]?\s*\d{1,2}[A-Za-z]?"
    r"|Sol\d+"
    r"|P0\d{2,}"
    r"|v0\d+(?!\.\d)"
    r"|v\d{2,}(?!\.\d)"
    r")(?![A-Za-z0-9_])"
)
CAMEL_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    r"[A-Z][a-z]{2,}[A-Z][a-z]{1,}[A-Za-z0-9]*"
    r"|[a-z]{2,}[A-Z][a-z]{2,}[A-Za-z0-9]*"
    r"|[A-Z][a-z]{2,}[A-Z]\d*"
    r")(?![A-Za-z0-9_])"
)
ALLOWED_CAMEL_WORDS = {
    "ArcGIS", "PowerPoint", "GitHub", "GitLab", "LaTeX", "BibTeX",
    "NetCDF", "GeoTIFF", "WorldClim", "BioClim", "TerraClimate", "DayMet",
    "SciPy", "NumPy", "PyTorch", "TensorFlow", "LightGBM", "CatBoost", "XGBoost",
    "RandomForest", "OpenStreetMap", "EarthEngine", "GoogleEarth",
    "JavaScript", "TypeScript", "PostgreSQL", "MySQL", "SQLite",
    "FluxNet", "AmeriFlux", "EuroFlux", "ChinaFlux", "BioScience", "GeoHealth",
    "OneEarth", "SciData", "NatCommun", "GlobalChange", "DeVries", "VanDer",
}
PUBLISHER_POINTER_RE = re.compile(
    r"\b(?:Supplementary\s+|Extended\s+Data\s+)?"
    r"(?:Figs?|Figures?|Tables?|Tabs?|Eqs?|Equations?|Box|Notes?|Texts?|Data|Code|Appendix|Section)\.?\s*"
    r"S?\d+[a-z]?(?:(?:\s*[,–\-&]\s*|\s+and\s+)S?\d*[a-z]?)*",
    re.I,
)
OPAQUE_SHORT_CODE_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Z]\d{1,2}[a-z]?)(?![A-Za-z0-9_]|\.\d)")
ALLOWED_SHORT_CODES = {
    "C3", "C4", "N2", "O2", "H2", "R2", "Q10", "K1",
    "C13", "C14", "N15", "O18", "P32", "S34", "U10",
}


def normalize_ligatures(text):
    t = text.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\ufb00", "ff").replace("\ufb03", "ffi").replace("\ufb04", "ffl")
    # Join PDF line-break hyphens ONLY (preserve suspended hyphens like "short- and long-term")
    return re.sub(r"([a-z])-\r?\n\s*([a-z])", r"\1\2", t)


def find_camel_codes(text):
    s = URL_RE.sub(" ", text)
    hits = []
    for m in CAMEL_CODE_RE.finditer(s):
        tok = m.group(0)
        if tok in ALLOWED_CAMEL_WORDS or tok.startswith(("Mc", "Mac")):
            continue
        hits.append(tok)
    return hits


def find_opaque_short_codes(sent):
    s = URL_RE.sub(" ", sent)
    s = PUBLISHER_POINTER_RE.sub(" ", s)
    s = re.sub(r"\b(?:SSP\d+[–\-]\d+\.\d+|RCP\d+\.\d+)\b", " ", s, flags=re.I)
    s = re.sub(r"\bF1(?=\s+score\b)", " ", s)
    s = re.sub(r"\bL[12](?=\s+(?:norm|regularization|penalty|loss)\b)", " ", s, flags=re.I)
    hits = []
    for m in OPAQUE_SHORT_CODE_RE.finditer(s):
        tok = m.group(1)
        if tok in ALLOWED_SHORT_CODES:
            continue
        hits.append(tok)
    return hits


def scan_headings_and_tables(raw_text, fails, underscore_hits, internal_code_hits, camel_code_hits, opaque_short_code_hits):
    """Audit Markdown headings and tables that clean_markdown strips from prose metrics."""
    in_code = False
    for line_no, raw_line in enumerate(raw_text.splitlines(), 1):
        s = raw_line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s:
            continue
        is_heading = s.startswith("#")
        is_table = s.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", s)
        if not (is_heading or is_table):
            continue
        kind = "heading" if is_heading else "table"
        s_clean = URL_RE.sub(" ", re.sub(r"`([^`]+)`", r"\1", s))
        u_hits = UNDERSCORE_ID_RE.findall(s_clean)
        if u_hits:
            underscore_hits.extend(u_hits)
            fails.append({
                "code": "UNDERSCORE_IDENTIFIER",
                "sent_idx": 0,
                "detail": f"Underscore identifier in {kind} line {line_no} ({list(dict.fromkeys(u_hits))[:5]}); replace with plain physical terms.",
                "sentence": s[:220],
            })
        ic_hits = INTERNAL_CODE_LABEL_RE.findall(s_clean)
        if ic_hits:
            internal_code_hits.extend(ic_hits)
            fails.append({
                "code": "INTERNAL_CODE_LABEL",
                "sent_idx": 0,
                "detail": f"Internal code label in {kind} line {line_no} ({list(dict.fromkeys(ic_hits))[:5]}); replace with plain descriptive names.",
                "sentence": s[:220],
            })
        cc_hits = find_camel_codes(s_clean)
        if cc_hits:
            camel_code_hits.extend(cc_hits)
            fails.append({
                "code": "CAMEL_CODE_IDENTIFIER",
                "sent_idx": 0,
                "detail": f"Camel-case code identifier in {kind} line {line_no} ({list(dict.fromkeys(cc_hits))[:5]}); replace with plain English words.",
                "sentence": s[:220],
            })
        sc_hits = find_opaque_short_codes(s_clean)
        if sc_hits:
            for sc in sc_hits:
                opaque_short_code_hits[sc] += 1
            if len(set(sc_hits)) >= 2:
                fails.append({
                    "code": "OPAQUE_SHORT_CODES",
                    "sent_idx": 0,
                    "detail": f"Opaque short codes in {kind} line {line_no} ({list(dict.fromkeys(sc_hits))[:6]}); use plain physical names.",
                    "sentence": s[:220],
                })


def check_svo_clarity(sp, idx, fails, warns, style_warns):
    """Check Subject-Verb-Object proximity and front-loading with strict abstain-on-ambiguity safety."""
    # Remove parentheticals and unit tokens so abbreviations/units never inflate spans
    s = re.sub(r"\([^)]*\)", " ", sp)
    s = re.sub(r"\s+", " ", s).strip()
    s = SAFE_LEAD_CONN_RE.sub("", s)

    # 1. Front-loaded adverbial/prepositional opener check
    main_clause = s
    if FRONT_PREP_OPENER_RE.match(s) and "," in s:
        lead, rest = s.split(",", 1)
        lead_toks = [t for t in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", lead) if t.lower() not in UNIT_TOKENS]
        lw = len(lead_toks)
        if lw > 22:
            fails.append({
                "code": "FRONT_LOADED_OPENER",
                "sent_idx": idx,
                "detail": f"Front-loaded opening phrase runs {lw} words before the main subject (>22w limit); move conditions after the main clause or split into two sentences.",
                "sentence": sp[:220],
            })
        elif lw > 15:
            warns.append({
                "code": "FRONT_LOADED_OPENER",
                "sent_idx": idx,
                "detail": f"Front-loaded opening phrase runs {lw} words before the main subject (recommended <=15w).",
                "sentence": sp[:220],
            })
        if lw <= 28:
            main_clause = rest.strip()
        else:
            return  # Opener already flagged as >22w FAIL; abstain on subsequent multi-clause span

    # Cut at semicolon, sentence end, or clause-joining comma (", but/yet/whereas/while/although/so ")
    main_clause = main_clause.split(";", 1)[0].strip()
    main_clause = re.split(r",\s+(?:but|yet|whereas|while|although|though|so|because)\b", main_clause, maxsplit=1, flags=re.I)[0].strip()
    if not main_clause or re.match(r"^(?:Please|Note|See|Compare)\b", main_clause):
        return

    # If a comma-delimited interrupter sits right after a short opening subject, skip tokens INSIDE the interrupter
    # when locating the main finite verb anchor!
    interrupter_match = SV_INTERRUPTER_RE.search(main_clause)
    interrupter_span = None
    if interrupter_match and interrupter_match.start() > 3:
        before_int_toks = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", main_clause[: interrupter_match.start()])
        if 1 <= len(before_int_toks) <= 10 and not any(t.lower() in CORE_VERB_ANCHORS for t in before_int_toks[1:]):
            interrupter_span = (interrupter_match.start(), interrupter_match.end())

    # Find verb anchor inside main_clause, preserving token positions
    toks_raw = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"[A-Za-z]+(?:-[A-Za-z]+)*", main_clause)]
    toks = [(w, a, b) for w, a, b in toks_raw if w.lower() not in UNIT_TOKENS]
    if len(toks) < 6:
        return

    # Skip imperative or immediate pronoun+verb ("We modeled...") or title-case heading fragments
    if toks[0][0].lower() in ("we", "it", "they", "there", "here") and len(toks) >= 2:
        return

    anchor_i = None
    for i, (w, a, b) in enumerate(toks):
        wl = w.lower()
        if i == 0:
            continue
        if interrupter_span and interrupter_span[0] <= a < interrupter_span[1]:
            continue
        prev_l = toks[i - 1][0].lower()
        if prev_l in NON_VERB_PREV:
            continue
        if wl in CORE_VERB_ANCHORS:
            anchor_i = i
            break
        # Abstain on earlier unrecognized finite verb candidates ("-ed" verb not in list) outside interrupter
        if not interrupter_span and i >= 2 and wl.endswith("ed") and "-" not in wl and prev_l not in ("was", "were", "is", "are", "been", "be", "and", "or"):
            if i < 12:
                return

    if anchor_i is None:
        return

    pre_verb_str = main_clause[: toks[anchor_i][1]].strip()
    span_len = anchor_i

    # Abstain if an unbracketed relative marker ("that/who/which") sits inside the subject span
    has_interrupter = bool(interrupter_span and interrupter_span[1] <= toks[anchor_i][1])
    if not has_interrupter and re.search(r"\b(?:which|that|who|whom|whose|where|when)\b", pre_verb_str, re.I):
        return

    # Check coordinated list exemption (2+ commas + 'and', no interrupter)
    is_coord_list = (pre_verb_str.count(",") >= 2 and bool(re.search(r"\band\b", pre_verb_str, re.I)) and not has_interrupter)

    # 2. 3+ 'of' chain inside pre-verb subject
    of_cnt = len(re.findall(r"\bof\b", pre_verb_str, re.I))
    if of_cnt >= 3 and span_len >= 12 and not is_coord_list:
        fails.append({
            "code": "OF_CHAIN_SUBJECT",
            "sent_idx": idx,
            "detail": f"Pre-verb subject chains {of_cnt} 'of' phrases ({span_len} words before verb '{toks[anchor_i][0]}'); simplify subject and put the actor first.",
            "sentence": sp[:220],
        })

    # 3. Center-embedded SV interrupter
    if has_interrupter:
        if span_len >= 14:
            fails.append({
                "code": "SV_INTERRUPTED",
                "sent_idx": idx,
                "detail": f"Subject and main verb '{toks[anchor_i][0]}' are separated by a comma interrupter ({span_len} words pre-verb); move the aside to the end or a second sentence.",
                "sentence": sp[:220],
            })
        elif span_len >= 9:
            style_warns.append({
                "code": "SV_INTERRUPTED",
                "sent_idx": idx,
                "detail": f"Comma interrupter sits between subject and verb '{toks[anchor_i][0]}' ({span_len} words pre-verb); consider moving aside after the verb.",
                "sentence": sp[:220],
            })
        return

    # 4. Long pre-verb subject span
    if is_coord_list:
        if span_len >= 20:
            style_warns.append({
                "code": "LONG_SUBJECT",
                "sent_idx": idx,
                "detail": f"Long coordinated subject list ({span_len} words before verb '{toks[anchor_i][0]}').",
                "sentence": sp[:220],
            })
    else:
        if span_len >= 16:
            fails.append({
                "code": "LONG_SUBJECT",
                "sent_idx": idx,
                "detail": f"Pre-verb subject runs {span_len} words before main verb '{toks[anchor_i][0]}' (>=16w limit); shorten subject so S-V-O is immediately clear.",
                "sentence": sp[:220],
            })
        elif span_len >= 12:
            warns.append({
                "code": "LONG_SUBJECT",
                "sent_idx": idx,
                "detail": f"Pre-verb subject runs {span_len} words before main verb '{toks[anchor_i][0]}' (recommended <=11w).",
                "sentence": sp[:220],
            })


def load_text_from_path(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        body = root.find(f"{W_NS}body")
        paras = []
        if body is not None:
            for child in body:
                if child.tag != f"{W_NS}p":
                    continue
                texts = []

                def walk(el):
                    if el.tag in (f"{W_NS}del", f"{W_NS}delText", f"{W_NS}moveFrom", f"{W_NS}instrText"):
                        return
                    if el.tag == f"{W_NS}t" and el.text:
                        texts.append(el.text)
                    for c in el:
                        walk(c)

                walk(child)
                line = "".join(texts).strip()
                if not line:
                    continue
                low = line.lower().strip()
                if re.match(
                    r"^(references|acknowledgements?|conflict of interest|competing interests|author contributions|figure captions|table captions)$",
                    low,
                ):
                    break
                paras.append(line)
        return "\n\n".join(paras)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def clean_markdown(text):
    text = normalize_ligatures(text)
    lines = []
    in_code = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if s.startswith("#") or s.startswith("|") or re.match(r"^[-*+]\s+\*\*.*\*\*:$", s):
            continue
        s = re.sub(r"^>\s*", "", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"\*([^*]+)\*", r"\1", s)
        lines.append(s)
    return "\n".join(lines)


def split_sentences(text):
    t = normalize_ligatures(text)
    t = re.sub(r"https?://\S+", "URL", t)
    abbrevs = [
        r"\bet al\.", r"\be\.g\.", r"\bi\.e\.", r"\bvs\.", r"\bFig\.", r"\bFigs\.",
        r"\bEq\.", r"\bEqs\.", r"\bRef\.", r"\bRefs\.", r"\bNo\.", r"\bDr\.", r"\bProf\.",
        r"\bSp\.", r"\bspp\.", r"\bapprox\.", r"\bvol\.", r"\bSuppl\.", r"\bTab\.",
        r"\bv\.\d+", r"\bU\.S\.",
    ]
    for ab in abbrevs:
        t = re.sub(ab, lambda m: m.group(0).replace(".", "<DOT>"), t)
    t = re.sub(r"(?<![a-z]\s)\b([A-Z])\.(?=\s+[A-Z])", r"\1<DOT>", t)
    t = re.sub(r"(?<=\d)\.(?=\d)", "<DOT>", t)
    t = re.sub(r"(?<=[A-Za-z])\.(?=cv\b|CV\b|se\b|mean\b|diff\b|hp\b)", "<DOT>", t)
    t = re.sub(r"([a-z\)])(?:\d+(?:[–\-,]\d+)*)\.\s+(?=[A-Z])", r"\1. ", t)
    t = re.sub(r"\.(?:\d+(?:[–\-,]\d+)*)\s+(?=[A-Z])", r". ", t)
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"\(])|\n\n+", t)
    sents = []
    for s in raw:
        s = re.sub(r"\s+", " ", s.replace("<DOT>", ".")).strip()
        words = re.findall(r"[A-Za-z][A-Za-z'’\-]*", s)
        if len(words) < 5:
            continue
        sents.append(s)
    return sents


def strip_citations(s):
    s2 = re.sub(
        r"\([^)=%±]*\b[A-Z][a-z]+\s+(?:et al\.|and\s+[A-Z][a-z]+|\&)\s*,?\s*(?:18|19|20)\d{2}[a-z]?[^)=%±]*\)",
        "",
        s,
    )
    s2 = re.sub(
        r"\([^)=%±]*\b[A-Z][a-z]+,\s*(?:18|19|20)\d{2}[a-z]?[^)=%±]*\)",
        "",
        s2,
    )
    s2 = re.sub(
        r"\(\s*(?:see\s+)?(?:Supplementary\s+|Extended\s+Data\s+)?(?:Figs?|Figures?|Tables?|Tabs?|Eqs?|Equations?|Box|Text|Note|Data|Code|Appendix)\.?\s*S?\d+[a-z]?(?:(?:\s*[,;–\-&]\s*|\s+and\s+)(?:Supplementary\s+)?(?:Figs?|Figures?|Tables?|Eqs?|Box|Text|Note)?\.?\s*S?\d*[a-z]?)*\s*\)",
        "",
        s2,
        flags=re.I,
    )
    s2 = re.sub(r"(?<=[a-z\)])\d+(?:[,–\-]\d+)*(?=[.;:\s]|$)(?!\.\d)(?!%)", "", s2)
    return re.sub(r"\s+", " ", s2).strip()


def count_data_numbers(sent):
    s = COORD_RE.sub("", sent)
    s = re.sub(
        r"\([^)=%±]*\b[A-Z][a-z]+\s+(?:et al\.|and\s+[A-Z][a-z]+|\&)\s*,?\s*(?:18|19|20)\d{2}[a-z]?[^)=%±]*\)",
        "",
        s,
    )
    s = re.sub(r"\([^)=%±]*\b[A-Z][a-z]+,\s*(?:18|19|20)\d{2}[a-z]?[^)=%±]*\)", "", s)
    s = re.sub(
        r"\b(?:Supplementary\s+|Extended\s+Data\s+)?(?:Figs?|Figures?|Tables?|Tabs?|Eqs?|Equations?|Box|Stage|Notes?|Texts?|Data|Code|Panels?|Layers?|Horizons?|Appendix|Section)\.?\s*S?\d+[a-z]?(?:(?:\s*[,–\-&]\s*|\s+and\s+)S?\d*[a-z]?)*",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(?:N2O|CO2|CH4|O2|N2|NH3|NH4|NO3|NO2|H2O|SO2|Q10|EF4|C45|C50|15N|13C|14C|C3|C4|19th|20th|21st|1st|2nd|3rd|PM2\.5|R2|R²|r2|r²|SSP\d+[–\-]\d+\.\d+|RCP\d+\.\d+)\b",
        "",
        s,
    )
    s = re.sub(r"\b(?:18|19|20)\d{2}(?:[–\-](?:18|19|20)\d{2})?s?\b", "", s)
    s = re.sub(r"(?:ha|yr|m|kg|g|L|MJ|day|cm|km|mol|hr|sec|d|y|kgN|kgC|gN|gC|PgC|TgN|N|C)[–\-−^]\d+", "", s)
    s = re.sub(r"\b(?:km|cm|mm|m)[23²³]\b", "", s)
    s = re.sub(r"(?<=[a-z\)])\d+(?:[,–\-]\d+)*(?=[.;:\s]|$)(?!\.\d)(?!%)", "", s)
    s = re.sub(
        r"\b\d+(?:\.\d+)?[–\-]\d+(?:\.\d+)?(?:,\s*\d+(?:\.\d+)?[–\-]\d+(?:\.\d+)?)+,?\s*(?:and\s+\d+(?:\.\d+)?[–\-]\d+(?:\.\d+)?\s*)?(?:cm|mm|m)\b",
        "<DEPTH_LIST>",
        s,
    )
    s = re.sub(
        r"[~≈<>≤≥±]?\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:±|\+/-|[–\-])\s*\d+(?:,\d{3})*(?:\.\d+)?%?",
        "<NUM>",
        s,
    )
    return re.findall(r"<NUM>|<DEPTH_LIST>|(?<![A-Za-z0-9])\d+(?:,\d{3})*(?:\.\d+)?%?(?![A-Za-z0-9])", s)


def content_lemmas(s):
    out = set()
    for t in re.findall(r"[A-Za-z][A-Za-z0-9\-]*", s.lower()):
        if t in STOPWORDS or len(t) <= 2:
            continue
        if t in (
            "fig", "figs", "figure", "figures", "table", "tables",
            "supplementary", "appendix", "note", "text", "data", "dataset",
        ):
            continue
        t2 = re.sub(r"ies$", "y", t)
        t2 = re.sub(r"(?:es|s|ed|ing)$", "", t2) if len(t) > 5 else t
        out.add(t2)
    return out


def split_paragraphs(cleaned_text):
    raw_paras = re.split(r"\n\s*\n+", cleaned_text.strip())
    paras = []
    for p in raw_paras:
        p2 = re.sub(r"\s+", " ", p).strip()
        words = re.findall(r"[A-Za-z][A-Za-z'’\-]*", p2)
        if len(words) >= 12:
            paras.append(p2)
    return paras


def audit_text(text):
    cleaned = clean_markdown(text)
    paras = split_paragraphs(cleaned)
    sents = split_sentences(cleaned)
    if not sents:
        return {"status": "ERROR", "message": "No prose sentences detected."}

    para_word_counts = []
    within_pairs = 0
    within_chained = 0
    disconnected_pairs = []
    for p in paras:
        psents = split_sentences(p)
        pw = sum(len(re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", strip_citations(s))) for s in psents)
        if pw >= 12:
            para_word_counts.append(pw)
        for i in range(len(psents) - 1):
            s1, s2 = strip_citations(psents[i]), strip_citations(psents[i + 1])
            within_pairs += 1
            if content_lemmas(s1) & content_lemmas(s2):
                within_chained += 1
            else:
                disconnected_pairs.append((s1[:90], s2[:90]))
    lex_chain_pct = round(100 * within_chained / within_pairs, 1) if within_pairs else 100.0

    fails = []
    warns = []
    style_warns = []

    prose_lens = []
    commas = []
    clause_counts = []
    num_counts = []
    participle_sents = 0
    quote_count = 0
    dash_count = 0
    em_dashes = 0
    we_words = 0
    we_starts = 0
    hyphen_words = []
    long_stacks = []
    banned_verb_hits = Counter()
    banned_buzz_hits = Counter()
    svo_fail_hits = 0
    underscore_hits = []
    internal_code_hits = []
    camel_code_hits = []
    opaque_short_code_hits = Counter()
    all_words = 0

    scan_headings_and_tables(
        text, fails, underscore_hits, internal_code_hits, camel_code_hits, opaque_short_code_hits
    )

    consec_num_streak = 0
    consec_start_idx = 0

    for idx, s in enumerate(sents, 1):
        sp = strip_citations(s)
        toks = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", sp)
        if len(toks) < 4:
            continue
        # Unit-stripped prose length (prevents kgN ha yr inflating length metrics)
        prose_toks = [t for t in toks if t.lower() not in UNIT_TOKENS]
        wlen = len(prose_toks)
        prose_lens.append(wlen)
        all_words += wlen
        commas.append(sp.count(","))

        # 1. Numeric restraint check
        dnums = count_data_numbers(s)
        dn = len(dnums)
        num_counts.append(dn)
        if dn >= 4:
            fails.append({
                "code": "NUMBER_DUMP_SENTENCE",
                "sent_idx": idx,
                "detail": f"{dn} standalone data numbers in one sentence ({dnums[:6]}); keep only 1–2 anchor numbers in prose and offload details to a Table/Figure.",
                "sentence": sp[:220],
            })
        if dn >= 2:
            if consec_num_streak == 0:
                consec_start_idx = idx
            consec_num_streak += 1
            if consec_num_streak == 3:
                fails.append({
                    "code": "CONSECUTIVE_NUMBER_WALL",
                    "sent_idx": consec_start_idx,
                    "detail": f"Sentences S{consec_start_idx}–S{idx} form 3+ consecutive number-heavy sentences (>=2 numbers each); narrate patterns first and move exhaustive values to Table/SI.",
                    "sentence": sp[:220],
                })
        else:
            consec_num_streak = 0

        # 2. Zero quotation marks check (excluding geographic degree/minute/second coordinates)
        sp_no_coord = COORD_RE.sub("", sp)
        dq_hits = DOUBLE_QUOTE_RE.findall(sp_no_coord)
        sq_hits = SINGLE_QUOTE_PAIR_RE.findall(sp_no_coord)
        q_hits = dq_hits + sq_hits
        if q_hits:
            quote_count += len(q_hits)
            fails.append({
                "code": "QUOTE_ABUSE",
                "sent_idx": idx,
                "detail": f"Quotation mark(s) found ({q_hits[:3]}); state concepts directly without quotes.",
                "sentence": sp[:220],
            })

        # 3. Zero em dashes and zero spaced parenthetical dashes
        em_hits = EM_OR_DOUBLE_DASH_RE.findall(sp)
        sp_dash_hits = SPACED_PAREN_DASH_RE.findall(sp)
        if em_hits or sp_dash_hits:
            em_dashes += len(em_hits)
            dash_count += len(em_hits) + len(sp_dash_hits)
            fails.append({
                "code": "EM_OR_SPACED_DASH",
                "sent_idx": idx,
                "detail": f"Prohibited em dash ({len(em_hits)}) or spaced parenthetical dash ({len(sp_dash_hits)}); use a plain comma, parentheses, or split into two sentences.",
                "sentence": sp[:220],
            })

        # 4. Stricter long/nested clause checks
        cl_matches = CLAUSE_RE.findall(sp)
        cl_n = len(cl_matches)
        clause_counts.append(cl_n)
        if (
            (cl_n >= 2 and wlen > 28)
            or (cl_n >= 3 and wlen > 22)
            or (wlen > 45 and cl_n >= 1)
            or (wlen > 38 and sp.count(",") >= 3)
        ):
            fails.append({
                "code": "LONG_COMPLEX_CLAUSE",
                "sent_idx": idx,
                "detail": f"{wlen} prose words with {cl_n} clause markers ({', '.join(cl_matches)}) and {sp.count(',')} commas; split into short flat sentences.",
                "sentence": sp[:220],
            })
        for tm in TRAILING_CLAUSE_RE.finditer(sp):
            tail_words = [w for w in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", tm.group(2)) if w.lower() not in UNIT_TOKENS]
            if len(tail_words) > 16:
                fails.append({
                    "code": "LONG_TRAILING_CLAUSE",
                    "sent_idx": idx,
                    "detail": f"Trailing ', {tm.group(1)} ...' clause runs {len(tail_words)} prose words (limit <=16); start a new sentence instead.",
                    "sentence": sp[:220],
                })

        # 5. Participle tail checks
        pt_raw = PARTICIPLE_TAIL_RE.findall(sp)
        pt_matches = [w for w in pt_raw if w.lower() not in PREPOSITIONAL_ING_ALLOW]
        if pt_matches:
            participle_sents += 1
            if len(pt_matches) >= 2:
                fails.append({
                    "code": "DOUBLE_PARTICIPLE_PILEUP",
                    "sent_idx": idx,
                    "detail": f"Chained participle tails: {', '.join(pt_matches)}",
                    "sentence": sp[:220],
                })

        if toks[0].lower() in ("we", "our"):
            we_starts += 1

        # 6. Token-level checks with scientific domain sense-guards & narrative-citation surname protection
        narrative_surnames = set(
            m.group(1).lower()
            for m in re.finditer(
                r"\b([A-Z][a-z]+)(?:\s+et\s+al\.|\s+(?:and|&)\s+[A-Z][a-z]+\s*\(\s*(?:18|19|20)\d{2}|\s*\(\s*(?:18|19|20)\d{2})",
                s,
            )
        )
        run = []
        for t in toks:
            tl = t.lower()
            if tl in ("we", "our", "us"):
                we_words += 1
            if t[0].isupper() and tl in narrative_surnames:
                continue
            guard = SENSE_GUARDS.get(tl)
            is_domain_safe = bool(guard and guard.search(sp))
            if tl in BANNED_AI_VERBS and not is_domain_safe:
                banned_verb_hits[tl] += 1
                fails.append({
                    "code": "BANNED_AI_VERB",
                    "sent_idx": idx,
                    "detail": f"Obscure/AI verb {t}; replace with a plain everyday workhorse verb.",
                    "sentence": sp[:220],
                })
            elif tl in BANNED_AI_BUZZWORDS and not is_domain_safe:
                banned_buzz_hits[tl] += 1
                fails.append({
                    "code": "BANNED_AI_BUZZWORD",
                    "sent_idx": idx,
                    "detail": f"Obscure/AI noun or modifier {t}; replace with a plain concrete word.",
                    "sentence": sp[:220],
                })
            elif tl in TIER2_STYLE_WORDS and not is_domain_safe:
                style_warns.append({
                    "code": "STYLE_TIER2_WORD",
                    "sent_idx": idx,
                    "detail": f"Tier-2 formal/ornamental word {t}; consider a simpler plain-English alternative.",
                    "sentence": sp[:220],
                })
            if "-" in tl and len(tl) > 4:
                hyphen_words.append(tl)
                if tl.count("-") >= 2 and tl not in ALLOWED_TRIPLE_HYPHENS:
                    fails.append({
                        "code": "COINED_TRIPLE_HYPHEN",
                        "sent_idx": idx,
                        "detail": f"Coined multi-hyphen compound {t}",
                        "sentence": sp[:220],
                    })
                elif (tl in BANNED_AI_COMPOUNDS or COINED_COMPOUND_RE.search(tl)) and tl not in STANDARD_DOMAIN_HYPHENS:
                    fails.append({
                        "code": "COINED_AI_COMPOUND",
                        "sent_idx": idx,
                        "detail": f"Coined AI compound {t}; unpack into established plain terms.",
                        "sentence": sp[:220],
                    })
            if tl not in STOPWORDS and len(tl) > 2:
                run.append(t)
            else:
                if len(run) >= 5:
                    long_stacks.append((idx, " ".join(run)))
                run = []
        if len(run) >= 5:
            long_stacks.append((idx, " ".join(run)))

        # 7. Phrase-level AI obscurity patterns & v3 S-V-O / nominalization / archaic-syntax patterns
        for code, pat, advice in INANIMATE_OBSCURE_PATTERNS:
            m = pat.search(sp)
            if m:
                fails.append({
                    "code": code,
                    "sent_idx": idx,
                    "detail": f"Matched {m.group(0)}. {advice}",
                    "sentence": sp[:220],
                })

        prev_fail_n = len(fails)
        for code, pat, advice in SVO_SYNTAX_FAIL_PATTERNS:
            m = pat.search(sp)
            if m:
                fails.append({
                    "code": code,
                    "sent_idx": idx,
                    "detail": f"Matched {m.group(0)}. {advice}",
                    "sentence": sp[:220],
                })

        # Subject-to-Verb proximity & front-loading check
        check_svo_clarity(sp, idx, fails, warns, style_warns)
        svo_fail_hits += len(fails) - prev_fail_n

        # Advisory style_warns (do not trigger false REVISE on clean human papers)
        for code, pat, advice in STYLE_ADVISORY_PATTERNS:
            m = pat.search(sp)
            if m:
                if code == "STYLE_WITH_RESPECT_TO" and CALC_WRT_GUARD_RE.search(sp):
                    continue
                style_warns.append({
                    "code": code,
                    "sent_idx": idx,
                    "detail": f"Matched {m.group(0)}. {advice}",
                    "sentence": sp[:220],
                })
        gm = GERUND_SUBJ_RE.match(sp)
        if gm and gm.group(1).lower() not in PREPOSITIONAL_ING_ALLOW:
            style_warns.append({
                "code": "STYLE_GERUND_SUBJECT",
                "sent_idx": idx,
                "detail": f"Gerund subject '{gm.group(1)} ... showed/indicated that' hides the actor; prefer 'When we ... , we found that'.",
                "sentence": sp[:220],
            })

        # 8. Grammar guard patterns
        for code, pat, advice in TYPO_GUARD_PATTERNS:
            m = pat.search(sp)
            if m:
                warns.append({
                    "code": code,
                    "sent_idx": idx,
                    "detail": f"Matched {m.group(0)}. {advice}",
                    "sentence": sp[:220],
                })

        # 9. Underscore identifiers, internal workflow labels, camel-case codes, and opaque short codes
        s_code_scan = URL_RE.sub(" ", s)
        s_code_scan = re.sub(
            r"\([^)=%±]*\b[A-Z][a-z]+\s+(?:et al\.|and\s+[A-Z][a-z]+|\&)\s*,?\s*(?:18|19|20)\d{2}[a-z]?[^)=%±]*\)",
            " ",
            s_code_scan,
        )
        u_hits = UNDERSCORE_ID_RE.findall(s_code_scan)
        if u_hits:
            underscore_hits.extend(u_hits)
            fails.append({
                "code": "UNDERSCORE_IDENTIFIER",
                "sent_idx": idx,
                "detail": f"Underscore identifier/subscript in prose ({list(dict.fromkeys(u_hits))[:5]}); replace code names with plain physical terms and use real formatted subscripts instead of raw underscores.",
                "sentence": sp[:220],
            })
        ic_hits = INTERNAL_CODE_LABEL_RE.findall(s_code_scan)
        if ic_hits:
            internal_code_hits.extend(ic_hits)
            fails.append({
                "code": "INTERNAL_CODE_LABEL",
                "sent_idx": idx,
                "detail": f"Internal workflow/option/scheme/model/run/version code in prose ({list(dict.fromkeys(ic_hits))[:5]}); replace with plain descriptive names.",
                "sentence": sp[:220],
            })
        cc_hits = find_camel_codes(s_code_scan)
        if cc_hits:
            camel_code_hits.extend(cc_hits)
            fails.append({
                "code": "CAMEL_CODE_IDENTIFIER",
                "sent_idx": idx,
                "detail": f"Camel-case code identifier in prose ({list(dict.fromkeys(cc_hits))[:5]}); replace with plain English words.",
                "sentence": sp[:220],
            })
        sc_hits = find_opaque_short_codes(s_code_scan)
        if sc_hits:
            for sc in sc_hits:
                opaque_short_code_hits[sc] += 1
            if len(set(sc_hits)) >= 2 or len(sc_hits) >= 3:
                fails.append({
                    "code": "OPAQUE_SHORT_CODES",
                    "sent_idx": idx,
                    "detail": f"Opaque alphanumeric short codes in one sentence ({list(dict.fromkeys(sc_hits))[:6]}); name models/scenarios/groups in plain English instead of alphanumeric tags.",
                    "sentence": sp[:220],
                })

    n = len(prose_lens)
    mean_len = round(statistics.mean(prose_lens), 1)
    med_len = round(statistics.median(prose_lens), 1)
    pct_le20 = round(100 * sum(1 for x in prose_lens if x <= 20) / n, 1)
    pct_gt35 = round(100 * sum(1 for x in prose_lens if x > 35) / n, 1)
    mean_commas = round(statistics.mean(commas), 2)
    pct_ge2_cl = round(100 * sum(1 for x in clause_counts if x >= 2) / n, 1)
    pct_part = round(100 * participle_sents / n, 1)
    data_nums_per_sent = round(sum(num_counts) / n, 2)
    pct_zero_num = round(100 * sum(1 for x in num_counts if x == 0) / n, 1)
    pct_ge3_num = round(100 * sum(1 for x in num_counts if x >= 3) / n, 1)
    em_1k = round(1000 * em_dashes / max(1, all_words), 2)
    we_1k = round(1000 * we_words / max(1, all_words), 1)
    novel_hyphens = [h for h in hyphen_words if h not in STANDARD_DOMAIN_HYPHENS]
    hyph_1k = round(1000 * len(hyphen_words) / max(1, all_words), 1)
    novel_hyph_1k = round(1000 * len(novel_hyphens) / max(1, all_words), 1)
    stacks_100 = round(100 * len(long_stacks) / n, 1)
    style_warn_1k = round(1000 * len(style_warns) / max(1, all_words), 1)

    # Document-level threshold checks
    if n >= 6 and (data_nums_per_sent > 0.90 or pct_ge3_num > 15.0):
        warns.append({
            "code": "NUMBER_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": (
                f"Data numbers/sent = {data_nums_per_sent} (0-num={pct_zero_num}%, >=3-num={pct_ge3_num}%); "
                f"top-journal benchmark: 0.31–0.65/sent, 72.5%–81.4% zero-number, <=8% >=3-num."
            ),
            "sentence": "",
        })
    if novel_hyph_1k > 18.0 and all_words >= 120:
        fails.append({
            "code": "NOVEL_HYPHEN_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": f"Excessive non-standard hyphenated compounds = {novel_hyph_1k}/1k words (total={hyph_1k}/1k; human <=4/1k, AI contrast=35.7/1k). Top novel: {Counter(novel_hyphens).most_common(6)}",
            "sentence": "",
        })
    elif novel_hyph_1k > 12.0 and all_words >= 100:
        warns.append({
            "code": "NOVEL_HYPHEN_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": f"Non-standard hyphenated compounds = {novel_hyph_1k}/1k words (total={hyph_1k}/1k). Top novel: {Counter(novel_hyphens).most_common(6)}",
            "sentence": "",
        })
    if n >= 4 and (med_len > 26 or mean_len > 29):
        warns.append({
            "code": "SENT_LEN_HIGH",
            "sent_idx": 0,
            "detail": f"Mean={mean_len}, Median={med_len} prose words (human benchmark: median 19–24, mean 21–27).",
            "sentence": "",
        })
    if pct_gt35 > 22.0 and n >= 12:
        warns.append({
            "code": "OVERLONG_RATIO",
            "sent_idx": 0,
            "detail": f"{pct_gt35}% of sentences >35 prose words (target <=20%).",
            "sentence": "",
        })
    if pct_ge2_cl > 12.0 and n >= 8:
        warns.append({
            "code": "CLAUSE_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": f"{pct_ge2_cl}% of sentences have >=2 clause markers (top-journal human benchmark: 2.6%–8.7%).",
            "sentence": "",
        })
    if mean_commas > 1.85 and n >= 12:
        warns.append({
            "code": "COMMA_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": f"Mean {mean_commas} commas/sentence (top-journal human benchmark: 1.06–1.35).",
            "sentence": "",
        })
    if stacks_100 > 26.0 and n >= 12:
        warns.append({
            "code": "MODIFIER_STACK_HIGH",
            "sent_idx": 0,
            "detail": f"5+ content-word stacks = {stacks_100}/100 sents (top-journal human benchmark: 19.2). Samples: {[x[1] for x in long_stacks[:4]]}",
            "sentence": "",
        })
    if all_words >= 250 and we_1k < 2.0:
        warns.append({
            "code": "LOW_HUMAN_AGENCY",
            "sent_idx": 0,
            "detail": f"we/our/us = {we_1k}/1k words (top-journal human benchmark: 8.7–13.2; AI contrast: 1.2).",
            "sentence": "",
        })
    if pct_part > 18.0 and n >= 15:
        warns.append({
            "code": "PARTICIPLE_TAIL_HIGH",
            "sent_idx": 0,
            "detail": f"{pct_part}% sentences have trailing participle clauses (human benchmark: 7.9%–14.7%).",
            "sentence": "",
        })
    if within_pairs >= 8 and lex_chain_pct < 60.0:
        sample_jumps = [f"{a}... -> {b}..." for a, b in disconnected_pairs[:3]]
        warns.append({
            "code": "LOW_LEXICAL_CHAINING",
            "sent_idx": 0,
            "detail": f"Within-paragraph lexical chaining = {lex_chain_pct}% ({within_chained}/{within_pairs} pairs; human benchmark: 64%–87%, AI contrast: 53.3%). Sample jumps: {sample_jumps}",
            "sentence": "",
        })
    if len(para_word_counts) >= 3:
        mean_pw = round(statistics.mean(para_word_counts), 1)
        if mean_pw < 45.0:
            warns.append({
                "code": "FRAGMENTED_PARAGRAPHS",
                "sent_idx": 0,
                "detail": f"Mean paragraph length = {mean_pw} words across {len(para_word_counts)} paragraphs (looks outline-fragmented; human benchmark: 75–220w).",
                "sentence": "",
            })
        wall_paras = [w for w in para_word_counts if w > 330]
        if wall_paras:
            warns.append({
                "code": "WALL_PARAGRAPH",
                "sent_idx": 0,
                "detail": f"{len(wall_paras)} paragraph(s) exceed 330 prose words ({wall_paras}); split by distinct scientific moves.",
                "sentence": "",
            })
    distinct_short_codes = len(opaque_short_code_hits)
    if distinct_short_codes >= 3:
        fails.append({
            "code": "OPAQUE_SHORT_CODE_DENSITY",
            "sent_idx": 0,
            "detail": f"{distinct_short_codes} distinct opaque alphanumeric short codes used across text ({opaque_short_code_hits.most_common(8)}); replace codebook tags with plain physical names.",
            "sentence": "",
        })
    elif distinct_short_codes >= 1:
        warns.append({
            "code": "OPAQUE_SHORT_CODE_DENSITY",
            "sent_idx": 0,
            "detail": f"{distinct_short_codes} opaque alphanumeric short code(s) found ({opaque_short_code_hits.most_common(4)}); prefer plain physical names over short tags.",
            "sentence": "",
        })

    # Density-gated style_warn escalation (prevents WARN overflow on clean human papers)
    if (all_words >= 250 and style_warn_1k > 14.0) or (all_words < 250 and len(style_warns) >= 5):
        warns.append({
            "code": "STYLE_ADVISORY_DENSITY_HIGH",
            "sent_idx": 0,
            "detail": f"High density of Tier-2 formal/wordy phrases: {len(style_warns)} hits ({style_warn_1k}/1k words); prune wordy phrases and formal verbs.",
            "sentence": "",
        })

    status = "PASS"
    if fails:
        status = "REVISE"
    elif len(warns) >= 3:
        status = "REVISE"
    elif warns:
        status = "PASS_WITH_WARNINGS"

    return {
        "status": status,
        "metrics": {
            "sentences": n,
            "prose_words": all_words,
            "mean_words": mean_len,
            "median_words": med_len,
            "pct_le20_words": pct_le20,
            "pct_gt35_words": pct_gt35,
            "mean_commas": mean_commas,
            "pct_ge2_clauses": pct_ge2_cl,
            "pct_participle_tail": pct_part,
            "data_nums_per_sent": data_nums_per_sent,
            "pct_zero_num_sents": pct_zero_num,
            "pct_ge3_num_sents": pct_ge3_num,
            "quote_count": quote_count,
            "dash_count": dash_count,
            "em_dash_per_1k": em_1k,
            "svo_syntax_fails": svo_fail_hits,
            "style_warn_count": len(style_warns),
            "style_warn_per_1k": style_warn_1k,
            "underscore_ids": len(underscore_hits),
            "internal_codes": len(internal_code_hits),
            "camel_codes": len(camel_code_hits),
            "opaque_short_codes_distinct": distinct_short_codes,
            "hyphen_per_1k": hyph_1k,
            "novel_hyphen_per_1k": novel_hyph_1k,
            "stacks_5plus_per_100s": stacks_100,
            "we_our_us_per_1k": we_1k,
            "we_starts_pct": round(100 * we_starts / n, 1),
            "lex_chain_pct": lex_chain_pct,
            "within_para_pairs": within_pairs,
            "paragraphs": len(para_word_counts),
        },
        "fail_count": len(fails),
        "warn_count": len(warns),
        "style_warn_count": len(style_warns),
        "fails": fails,
        "warns": warns,
        "style_warns": style_warns,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit English scientific prose against pure human plain-clarity benchmarks.")
    parser.add_argument("path", nargs="?", help="Path to .txt, .md, or .docx file")
    parser.add_argument("--text", help="Direct inline English text to audit")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.path:
        text = load_text_from_path(args.path)
    else:
        text = sys.stdin.read()

    res = audit_text(text)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        m = res.get("metrics", {})
        print(
            f"STATUS: {res['status']}  (FAIL={res.get('fail_count', 0)}, "
            f"WARN={res.get('warn_count', 0)}, STYLE_ADVISORY={res.get('style_warn_count', 0)})"
        )
        if m:
            print(
                f"METRICS: sents={m['sentences']}, words={m['prose_words']}, "
                f"mean={m['mean_words']}w, med={m['median_words']}w, <=20w={m['pct_le20_words']}%, >35w={m['pct_gt35_words']}%"
            )
            print(
                f"SYNTAX : commas/sent={m['mean_commas']}, >=2clauses={m['pct_ge2_clauses']}%, "
                f"participle={m['pct_participle_tail']}%, quotes={m['quote_count']}, dashes={m['dash_count']}, svo_fails={m['svo_syntax_fails']}"
            )
            print(
                f"NUMBERS: nums/sent={m['data_nums_per_sent']}, 0-num={m['pct_zero_num_sents']}%, >=3-num={m['pct_ge3_num_sents']}%"
            )
            print(
                f"CLARITY: hyphen/1k={m['hyphen_per_1k']} (novel={m['novel_hyphen_per_1k']}), 5+stacks/100s={m['stacks_5plus_per_100s']}, "
                f"we/1k={m['we_our_us_per_1k']} (we-starts={m['we_starts_pct']}%), lex_chain={m['lex_chain_pct']}% ({m['within_para_pairs']} pairs), "
                f"underscore_ids={m['underscore_ids']}, internal_codes={m['internal_codes']}, camel_codes={m['camel_codes']}, short_codes={m['opaque_short_codes_distinct']}"
            )
        if res.get("fails"):
            print("\n--- FAIL ITEMS (Must Fix) ---")
            for item in res["fails"][:25]:
                loc = f"[S{item['sent_idx']}] " if item["sent_idx"] else "[DOC] "
                print(f"  {loc}{item['code']}: {item['detail']}")
                if item["sentence"]:
                    print(f"       -> {item['sentence']}")
            if len(res["fails"]) > 25:
                print(f"  ... and {len(res['fails']) - 25} more FAIL items.")
        if res.get("warns"):
            print("\n--- WARN ITEMS (Review) ---")
            for item in res["warns"][:15]:
                loc = f"[S{item['sent_idx']}] " if item["sent_idx"] else "[DOC] "
                print(f"  {loc}{item['code']}: {item['detail']}")
                if item["sentence"]:
                    print(f"       -> {item['sentence']}")
        if res.get("style_warns"):
            print(f"\n--- STYLE ADVISORIES (Optional Prune: {len(res['style_warns'])}) ---")
            for item in res["style_warns"][:10]:
                loc = f"[S{item['sent_idx']}] " if item["sent_idx"] else "[DOC] "
                print(f"  {loc}{item['code']}: {item['detail']}")
                if item["sentence"]:
                    print(f"       -> {item['sentence']}")

    sys.exit(0 if res.get("status") in ("PASS", "PASS_WITH_WARNINGS") else 1)


if __name__ == "__main__":
    main()
