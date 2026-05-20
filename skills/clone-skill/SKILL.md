---
name: clone-skill
description: |
  克隆一个人的思维系统或一个主题的方法论，自动完成分流、调研、提炼、组装、验证。
  当用户要“克隆某人/某主题”“做一个XX视角 skill”“复制某种思考方式”“更新已有克隆 skill”时触发。
---

# Clone Skill

> 不复制说过的话，复制的是思考问题的操作系统。

## 核心定位

`clone-skill` 不是角色扮演器，而是一个**思维系统克隆工厂**。

目标产物不是“像某人说话”，而是一个可运行的 skill：
- 有清晰触发条件
- 有稳定的回答工作流
- 有心智模型和决策启发式
- 有表达 DNA 和反模式
- 有诚实边界和调研来源

主文档只负责**分流、控制、检查点和产物契约**。
长说明、模板和方法论放在 `references/`，避免主上下文继续膨胀。

## 何时使用

当用户提出以下意图时触发：
- 明确要求克隆一个人或主题
- 想做一个某人的视角 / perspective / mode
- 想更新某个已有的人物 skill 或主题 skill
- 只有问题，没有人选，希望先推荐最适合克隆的对象

典型触发语：
- `克隆一个芒格 skill`
- `做个乔布斯视角`
- `复制 Paul Graham 的思考方式`
- `更新一下我现有的 naval skill`
- `我想找一个适合我的思维顾问`

不该直接触发的情况：
- 用户只是泛泛聊决策、写作、创业，没有表达“克隆 skill / 视角切换 / 生成人物 skill”的意图
- 用户只是想要普通建议，此时先回答问题或推荐候选，不直接进入完整克隆流程

## 架构选择

收到请求后，先明确本次走哪条架构路径：

| 路径 | 适用场景 | 核心产物 |
|------|---------|---------|
| 人物克隆 | 明确想复制某个人的思维系统 | `[person]-perspective/` |
| 主题克隆 | 想复制一个领域的方法论，而不是某个人 | `[topic]-framework/` |
| 更新模式 | 已有 skill，只补充最近变化与缺口 | 原 skill 增量更新 |

规则：
- 人物克隆优先保留个人张力、表达 DNA、时间线
- 主题克隆优先提炼流派分歧、共识框架、适用边界
- 更新模式只刷新变动最大的维度，不重做全量蒸馏

## 执行总流程

严格按以下工序推进：

1. 分流：判断是人物克隆、主题克隆还是更新模式
2. 澄清：最多追问 1-2 轮，补齐用途、范围、素材来源
3. 建目录：先创建 skill 目录和 research/sources 骨架
4. 采集：并行收集 6 个维度的信息，优先一手资料
5. Review：展示调研摘要，确认没有明显信息缺口
6. 提炼：按 `references/extraction-framework.md` 提取模型、启发式、DNA、张力和边界
7. 组装：按 `references/skill-template.md` 生成目标 skill
8. 验证：运行 `scripts/quality_check.py`，不通过则回退修正
9. 交付：展示结果、局限、下一步建议

## Phase 0: 入口分流

### 0A. 明确对象

如果用户已经给出明确名字或主题，先确认四件事：
- 克隆对象是谁 / 主题边界是什么
- 目标用途：思维顾问、写作伙伴、决策镜像、教学视角
- 新建还是更新
- 是否有本地一手素材（PDF、转录稿、字幕、文章、内部文档）

默认规则：
- 用户只说“克隆 XX”且没有补充时，默认做全面版人物克隆
- 没有本地素材时，自动进入网络调研模式

### 0B. 模糊需求诊断

如果用户不知道要克隆谁，只描述了问题：
- 最多追问 1-2 轮定位需求维度
- 推荐 2-3 个候选，不超过 3 个
- 候选可以混合人物与主题，但必须写清楚：
  - 核心镜片
  - 为什么适合
  - 明确局限

如果候选里已有现成 skill，可直接建议激活，不必重做克隆。

## Phase 0.5: 先创建目录，再开始调研

收到确认后，立刻创建目标目录，所有产物必须自包含在 skill 目录内部：

```text
.claude/skills/[target-name]/
├── SKILL.md
├── scripts/
└── references/
    ├── research/
    │   ├── 01-writings.md
    │   ├── 02-conversations.md
    │   ├── 03-expression-dna.md
    │   ├── 04-external-views.md
    │   ├── 05-decisions.md
    │   └── 06-timeline.md
    └── sources/
        ├── books/
        ├── transcripts/
        └── articles/
```

硬规则：
- 每个 research 文件都必须存在
- 调研文件必须写进目标 skill 目录内部，不能散落到外部工作目录
- 如果用户提供本地素材，优先放进 `references/sources/`
- 没有写入文件的调研，视为没有完成

## Phase 1: 信息采集

### 模式判断

| 模式 | 触发条件 | 执行策略 |
|------|---------|---------|
| 纯网络搜索 | 没有本地素材 | 6 个维度并行采集 |
| 本地素材优先 | 有 PDF / transcript / 字幕 / 文章 | 先吃本地素材，再定向补网 |
| 纯本地模式 | 用户明确限制只能用本地素材 | 不做外网搜索 |

### 六个标准维度

| 文件 | 维度 | 目标 |
|------|------|------|
| `01-writings.md` | 著作与系统论述 | 找反复出现的真信念 |
| `02-conversations.md` | 长对话与即兴思考 | 看被追问时怎么推理 |
| `03-expression-dna.md` | 碎片表达与风格 DNA | 找高频表达、禁忌词、节奏 |
| `04-external-views.md` | 他者观察与批评 | 找盲点、争议、外部评价 |
| `05-decisions.md` | 决策与行为记录 | 看言行是否一致 |
| `06-timeline.md` | 时间线与近期动态 | 看思想演化与最新变化 |

### 信息源规则

优先级：
- 用户提供的一手素材
- 本人著作 / 原始访谈 / 原始视频字幕 / 决策记录
- 权威媒体和高质量二手分析

黑名单：
- 知乎
- 微信公众号转载
- 百度百科 / 百度知道

### 工具入口

按需使用以下脚本：
- 下载 YouTube 字幕：`bash {baseDir}/scripts/download_subtitles.sh <url> [output_dir]`
- 字幕转 transcript：`python3 {baseDir}/scripts/srt_to_transcript.py <input.srt|input.vtt> [output.txt]`
- 汇总 research 摘要：`python3 {baseDir}/scripts/merge_research.py <skill_dir>`

## Phase 1.5: Research Review 检查点

所有 research 文件写完后，必须先做摘要检查，再进入提炼：

```bash
python3 {baseDir}/scripts/merge_research.py <skill_dir>
```

如果出现以下情况，先停下来修正：
- 缺失 research 文件
- 总来源太少
- 某个维度明显信息不足
- 矛盾没有记录

原则：
- 垃圾进，垃圾出
- 宁可承认缺口，也不要拿幻觉补齐

## Phase 2: 提炼

进入提炼前，先读取：
- `references/extraction-framework.md`

产物必须至少提炼出以下结构：
- 3-7 个核心心智模型
- 5-10 条决策启发式
- 表达 DNA
- 价值观与反模式
- 内在张力 / 领域冲突 / 观点演化
- 诚实边界

提炼判断规则：
- 通过三重验证的观点，才能升级为心智模型
- 只有部分证据的观点，降级成启发式
- 相互冲突的信息必须保留，不能抹平

## Phase 2.5: 提炼确认

在真正组装 skill 前，先给用户一个短摘要：
- 心智模型名称列表
- 决策启发式数量
- 表达 DNA 的 3 个关键特征
- 核心张力
- 诚实边界数量

如果用户认为方向不对，先回到提炼阶段，不要急着拼装最终 skill。

## Phase 3: 组装目标 Skill

进入构建前，读取：
- `references/skill-template.md`

组装时，最重要的不是堆内容，而是保证目标 skill **激活即执行**：
- 有清晰 description 和触发词
- 有身份卡
- 有回答工作流（Agentic Protocol）
- 有可运行的心智模型与启发式
- 有边界和来源

关键要求：
- 回答工作流必须包含 Step 1 / Step 2 / Step 3
- Step 2 的研究维度必须从目标对象的心智模型反推，不得写成空泛模板
- 诚实边界必须写明 `调研时间: YYYY-MM-DD`

## Phase 4: 质量验证

组装完成后，先运行自动检查：

```bash
python3 {baseDir}/scripts/quality_check.py <target_skill>/SKILL.md
```

默认必须过这些项：
- 心智模型数量
- 模型局限性
- 回答工作流
- 表达 DNA
- 诚实边界
- 调研时间
- 内在张力
- 一手来源占比
- 来源可追溯
- 身份卡

然后再做 3 类人工验证：
- 已知立场测试
- 边缘问题测试
- 风格辨识测试

最多迭代 2 轮。2 轮后仍有缺口，就在诚实边界中明确标注，不无限打磨。

## 更新模式

当用户要求更新已有克隆 skill：
- 读取旧版 SKILL.md
- 找出已有调研时间与最近变化
- 默认只补 Agent 2 / 5 / 6 对应的最新材料
- 强化原有模型、修正矛盾、刷新最新动态
- 除非结构失真，否则不整篇重写

## 强约束

- 不编造此人没说过的话
- 不把普通常识包装成独特模型
- 不因为信息少就伪造完整性
- 不输出只会“像”但不会“做事”的空壳 skill

## 交付格式

完成后，向用户交付：
- 新 skill 的路径
- 这次克隆的对象与模式
- 调研覆盖情况
- 自动检查结果
- 剩余薄弱点与建议下一步

## 资源说明

- 方法论：`references/extraction-framework.md`
- 目标 skill 模板：`references/skill-template.md`
- 调研摘要器：`scripts/merge_research.py`
- 最终质量检查：`scripts/quality_check.py`
- 字幕下载：`scripts/download_subtitles.sh`
- 字幕清洗：`scripts/srt_to_transcript.py`
