# Human Plain Scientific Writing (V1.2)

> 把已经写好的英文科研论文改顺、改平实，同时锁死各部分字数、文献管理器引文域和原稿 Word 排版，并默认保留 Word 原生字词级修订痕迹。也支持从中文提纲或图表直接起草清晰自然的英文章节。
>
> *Plain-language smoothing and drafting skill for scientific manuscripts with per-section word-count parity, Zotero/EndNote/NoteExpress/Mendeley citation protection, zero-layout-drift OOXML redlining, and zero external Python dependencies.*

---

## 它解决什么问题

用普通大模型润色英文论文，最常遇到四个翻车现场：

1. **悄悄删字或注水**：把 750 词的 Introduction 压缩到 550 词，或为了凑篇幅硬塞空洞套话。
2. **把句子越改越玄乎**：把 `use` 改成 `utilize`，塞满 `underscore`、`delve`、`tapestry`、长破折号、概念引号和带连字符的自造词。
3. **整段抹掉重写**：一开修订全屏飘红，根本看不清改了哪里，还容易顺手改歪原意和数值。
4. **改坏 Word 排版和引文域**：重写 `.docx` 后 Zotero、EndNote、NoteExpress 域失效，字体、斜体、上下标和公式跟着错位。

`human-plain-scientific-writing`（V1.2）基于 12 篇已脱敏的人类学者顶刊与前大模型时代论文（61,560 词）校准，把平实改写、字数守恒、引文保护和原生修订写成了确定性脚本门禁，不靠模型口头保证。

---

## 核心特性

| 维度 | 具体标准（脚本硬执行） |
|---|---|
| **两种模式** | **模式 1（默认）**：已成稿论文平实化平滑，锁死各节原字数与原逻辑骨架；<br>**模式 2**：从中文笔记、表格或提纲从零起草清晰英文段落。 |
| **逐部分字数守恒** | 逐节锁定字数（Abstract、Introduction、Methods、Results、Discussion、Conclusion、小节与图注）：理想波动 **≤ ±5%**，硬上限单节 **≤ ±8%**（150 词以下短节容差 12 词）、全文 **≤ ±5%**，超限自动拦截。 |
| **字词尺度微创修订** | 单次原子增删默认 **≤ 8 词**，保留原句主干（相似度 **≥ 0.65**），拒绝整段推倒重写，且不切碎单词内部字符。 |
| **引文与原稿零破坏** | 自动屏蔽 Zotero、EndNote、NoteExpress（`NE.Ref`）、Mendeley 及 Word 引文域、纯文本作者年份与编号引用、整段 References、公式（`m:oMath`）、图表、字体、样式、斜体与上下标；数字和算符（`< > ≤ ≥ = ± % ‰ × ~ ≈`）默认锁死；写完自动做完整性校验，任一项不通过立即回滚删除异常产物。 |
| **零第三方依赖** | 内置 `plain_human_audit.py` 与 `track_changes_writer.py` 仅使用 Python 标准库（无需安装 `python-docx` 或 `lxml`），Windows、macOS、Linux 开箱即用。 |

---

## 与 `scientific-editage-style`（V4.1）的分工

这两个技能定位互补，建议按顺序串联使用：

| 你当前的需求 | 用哪一个 |
|---|---|
| 句子拗口、中式长难句缠绕、AI 装腔词多、残留代码下划线变量，想**保字数把表达改自然**，或**从中文提纲起草英文** | **`human-plain-scientific-writing`（本技能）** |
| 表达已经平实通顺，投稿前只想按 Editage 习惯修**冠词、介词、主谓一致、时态、单复数、连接号与拼写** | [`scientific-editage-style`（V4.1）](https://github.com/PENGBOMR/scientific-editage-style) |

---

## 快速安装（30 秒）

要求：**Python 3.9+**，无需额外安装任何第三方包。

直接克隆到你所用代理工具的技能目录，重开新对话即可生效：

```bash
# Antigravity
git clone https://github.com/PENGBOMR/human-plain-scientific-writing.git ~/.gemini/config/skills/human-plain-scientific-writing

# Codex
git clone https://github.com/PENGBOMR/human-plain-scientific-writing.git ~/.codex/skills/human-plain-scientific-writing

# 通用 Agent 目录
git clone https://github.com/PENGBOMR/human-plain-scientific-writing.git ~/.agents/skills/human-plain-scientific-writing
```

---

## 怎么用

### 方式一：直接在对话里调用（推荐）

直接点名技能并指明稿件路径或范围即可。以下是可以直接复制的常用指令：

- **已成稿 Word 全文平实化（默认模式，保字数 + 留原生修订）**
  > 用 `human-plain-scientific-writing` 对 `manuscript.docx` 做平实化语言平滑。保持每个章节原字数不变，不动引文域、参考文献、数字和原稿排版，输出带 Word 原生修订的版本、纯净版和各节字数变化表。
- **只改某一个章节（Markdown 或粘贴文本）**
  > 用 `human-plain-scientific-writing` 平滑下面这段 Discussion：去掉装腔词、长破折号和嵌套长句，保留所有专业术语与数据，总字数控制在原文 ±5% 以内，给出修订对比和干净终稿。
- **处理含复杂引用或上下标的长稿（遇到高风险位置跳过不中断）**
  > 用 `human-plain-scientific-writing` 平滑 `draft.docx`，写 Word 修订时开启 `--on-unsafe query`，把紧贴引文域或跨格式无法安全直改的条目输出成作者确认清单。
- **从中文提纲或图表起草英文（模式 2）**
  > 用 `human-plain-scientific-writing` 的模式 2，根据下面这些中文要点和表格数据起草 Results 第 3.1 节，要求显性主谓宾、句间衔接自然、控制单句数字密度，不要编造未提供的统计值。

### 方式二：命令行直接运行内置脚本

#### 1. 体检文本可读性与 AI 痕迹（支持 `.docx` / `.md` / `.txt`）

```bash
python scripts/plain_human_audit.py manuscript.docx
python scripts/plain_human_audit.py draft.md --json
```

#### 2. 为 `.docx` 写入原生 Word 修订并自动跑字数守恒与格式校验

先由代理（或人工）生成修改提案 `edits.json`（每项含 `before`、`after`，可选 `paragraph_index`、`reason`），再执行：

```bash
python scripts/track_changes_writer.py docx source.docx edits.json \
  --tracked out_tracked.docx \
  --clean out_clean.docx \
  --log out_changes.json \
  --on-unsafe query
```

#### 3. 为 Markdown 或纯文本生成词级修订对比与分节字数表

```bash
python scripts/track_changes_writer.py text before.md after.md --out out_tracked.md
```

#### 4. 单独核查前后两稿的各节字数守恒或独立复验 Word 保护

```bash
python scripts/track_changes_writer.py parity before.docx after.docx
python scripts/track_changes_writer.py verify source.docx out_tracked.docx --tracked --clean out_clean.docx
```

---

## 输出产物说明

运行 `.docx` 模式后，原文件**绝不会被覆盖**，会生成 3 份独立产物：

- `out_tracked.docx`：原生 Word 单词边界修订版（`<w:del>` / `<w:ins>`），可直接在 Word 审阅栏逐条接受或拒绝。
- `out_clean.docx`：接受全部修订后的纯净版，经脚本核对与修订版的全部接受结果逐字、逐样式一致。
- `out_changes.json`：结构化审计日志，包含各节改前改后字数与漂移百分比、保护检查结果、每处修改相似度及跳过待确认的 `skipped_unsafe` 清单。

---

## 保护范围与诚实边界

- **保护学科正词，不乱误杀**：词库内置语境保护，生态学、地学、物理、化学和统计中的标准原义术语（如 `soil respiration`、`bulk density`、`random forest`、`cross-validation`、`attenuate`、`leverage`、`trajectory`、`precipitate`、`delineate`、`granular`、`nexus`）一律保留。
- **不承诺像素级页码完全不变**：字词微调后 Word 自动换行可能引起局部跨页变化，这属于正常重排，不代表修改了字体、行距或页边距。
- **引文插件刷新须实机确认**：OOXML 静态校验可确保引文域代码与显示文本一字未动，但无法替代在你本机装有 Zotero、EndNote 或 NoteExpress 插件的 Word 中打开副本执行一次刷新测试。

---

## 目录结构

```text
human-plain-scientific-writing/
├── SKILL.md                                   # 技能主规则与五阶段执行流程
├── references/
│   ├── original_manuscript_protection.md      # 原稿格式、引文域与字数守恒硬协议
│   ├── anti_obscurity_rules.md                # 装腔词替换与中式长难句拆解
│   ├── cohesion_and_plain_logic.md            # 主谓宾贴近与句间词汇咬合规则
│   ├── imrad_writing_blueprints.md            # 模式 2 分章节起草蓝图
│   ├── human_exemplar_bank.md                 # 人类学者平实范例库
│   ├── corpus_dna_and_benchmarks.md           # 12 篇脱敏人类顶刊统计基线
│   └── lexicon_rules.json                     # 单一来源词库与学科语境白名单
└── scripts/
    ├── plain_human_audit.py                   # 可读性与 AI 痕迹体检脚本
    └── track_changes_writer.py                # 零依赖原生 Word 修订与保护引擎
```
