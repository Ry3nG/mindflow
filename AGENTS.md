# AGENTS.md

本文件描述本工作区的 **Owner**，供所有 agent 共享参考——理解他是谁、研究什么、看重什么，以及这个 notebook 如何组织。各 agent 自身的身份与职责由各自的 instruction / 项目级 CLAUDE.md 定义，本文件不覆盖那些。

## 工作区边界（先读）

本仓库是研究技能与工具依赖，不是 Zerui 的个人笔记库。日常工作目录是 `/home/zrgong/projects/obsidian/`。即使从本子模块或兼容链接 `~/projects/MindFlow` 启动，也不要把这里的历史内容当作个人阅读记录。

- 先读取父 vault 的 `AGENTS.md` 与 `00 Home.md`，遵循其目录和写入规则。
- 查询“我们最近读了哪些论文”：查父 vault `Library/Papers/`、`Daily/` 的 Reading 记录及对应 Git 历史；不要查询本仓库 `Papers/` 或 `Workbench/registry/papers.json` 来回答个人阅读历史。
- 新 digest 写到父 vault 的 `Library/Papers/`，阅读记录写到 `Daily/`。此处 `skills/`、`tools/`、`references/` 提供方法与实现，不决定最终笔记目录。
- 本仓库保留的 `Papers/`、`Topics/`、`DomainMaps/` 等是上游历史参考，不是 Zerui 的经历或当前工作。不得自动导入父 vault，也不得为了改 Owner 重写作者署名。
- 记录日期以笔记中的明确日期、Daily 和 Git 提交为证；文件名中的年月可能是论文月份，mtime 可能是检出时间，都不能单独代表阅读日期。已整理笔记也不自动证明本人已读完。
- 若父 vault 不可访问，明确报告无法查到个人记录；不要以本仓库旧笔记代替。

## Owner

Gong Zerui（Zerui），本工作区的所有者和重要决策的最终审批人。研究重点包括机器人学习、具身智能与世界模型。

本仓库是 `Ry3nG/MindFlow`，基于 `liqing-ustc/MindFlow` 的科研知识库与工作流。保留上游作者署名及历史笔记，但上游笔记中的个人经历、项目状态和安排不代表 Zerui 的经历或当前任务。`CLAUDE.md` 链接到本文件，统一维护此处即可。

## 研究兴趣

Multimodal Understanding: VLM, Video LLM, Video Understanding, Visual Reasoning
AI Agent: LLM Agent, Computer-use Agent, GUI Agent, Agentic RL
Embodied AI: VLA, World Model, Spatial Intelligence, Robot Manipulation & Navigation

## 研究原则

Owner 的研究品味——做研究相关工作时与之对齐：

### 1. Research Taste — 重要的问题，简洁的方法

- 区分 "publishable" 和 "important"，追求后者。+0.3% SOTA 不是 insight
- 追求 **simple, scalable, generalizable** 的方法。复杂往往是理解不够深的信号
- 不 scale 的方法大概率方向不对；不 generalize 的方法大概率在 exploit bias
- 有勇气 pivot——sunk cost 不是坚持的理由

### 2. Think from First Principles — 追问 Why

- 理解**为什么 work、什么条件下会 break**，而非收集结论
- Convention 不等于 truth。"大家都这么做" 不是理由，证据才是
- 问对问题比解对问题更重要——关注 problem formulation

### 3. Honest & Evidence-Driven — 诚实面对认知边界，用证据而非直觉做判断

- 严格区分**已知**、**推测**、**不知道**。每个 claim 标注 grounding：论文、实验、还是推理
- 不 overclaim，不掩盖错误。对自己的 idea 和对别人的论文施加同等的审视标准
- 先想清楚 "什么结果能推翻假说" 再动手。Negative result 同等重要

### 4. Read Critically — 论文不是圣经

- 每篇论文都有隐含假设和适用边界，找出它们
- Ablation、failure case、baseline 选择往往比 main result 更有信息量
- 影响力不等于正确性，对高引论文同样保持批判

### 5. Connect and Compound — 让知识产生复利

- 单篇论文是数据点，跨论文 pattern 才是 knowledge。矛盾是最有价值的信号
- 每次阅读都应更新 mental model，而非仅增加一条记录
- 定期修剪知识库——过时的认知比无知更危险

### 6. Explore Efficiently — 聪明地分配注意力

- Breadth 和 depth 动态平衡。20% 的论文包含 80% 的 insight
- 连续探索无产出时换角度，而非更用力。每个 action 要有清晰的 expected information gain

### 7. Write Clearly — 写不清楚说明想不清楚

- 先结论再论据，先 what 再 how 再 why
- 用术语是因为精确，不是因为显得高级

## Anti-Patterns

Owner 警惕的失败模式：

- **Literature hoarding**: 读很多但没有自己的判断
- **Method worship**: 迷恋方法精巧而忽略问题本身
- **Confirmation bias**: 只看支持自己假设的证据
- **Premature convergence**: 未充分探索就锁定方向
- **Perfectionism paralysis**: 等完美方案而错过行动窗口

## Directory Structure

以下是上游参考 notebook 的目录布局，不是 Zerui 的个人 vault 布局；个人笔记位置以本文件顶部及父 vault 契约为准：

- `DomainMaps/` — 核心认知地图，每个 domain 一个文件，`_index.md` 为索引页
- `Papers/` — 论文笔记（YYMM-ShortTitle.md）
- `Topics/` — 文献调研与分析报告
- `Ideas/` — 研究 idea
- `Projects/` - 项目记录
- `Reports/` — 生成的报告
- `Meetings/` — 会议记录
- `Workbench/` — 工作状态
- `skills/` — 科研技能库
- `references/` — 协议文档
- `Templates/` — 各类笔记模板

**语言**：中英文，技术术语（模型名、方法名、数据集名等）保持英文不翻译

**Markdown 语法**：写笔记前先参考 [[references/obsidian-syntax|references/obsidian-syntax.md]]——公式 / 表格 / 图片 / 视频 / wikilink alias / 表格内 pipe 转义 / `*` 字面字符等坑都在那里。

各 agent 必须认真使用和维护这个 notebook！
