---
name: normal-ppt
description: 基于 AST 理论的人感 PPT 大纲导演 Skill。在从原始素材生成 PPT/HTML 幻灯片之前使用。
version: 0.2.0
author: LearnPrompt
license: MIT
metadata:
  tags: [presentation, ppt, html-slides, normal, ast, workflow, templates]
---

# Normal PPT

当用户想把原始素材、笔记、语音转录、文档、链接或旧 PPT 变成可演示的大纲时，使用此 Skill。

## 定位

Normal PPT 是一个 **大纲导演** 和 **Agent 团队编排器**，不是幻灯片渲染器。

它应该在下游 PPT/HTML 幻灯片 Skill 之前运行。它的职责是生成干净的 AST 生产说明书，让渲染器不直接摄入原始噪音素材。

在 Agent 团队模式下，主 Normal PPT Agent 加载此 Skill 并控制专家 Agent：

- **Guizang Agent**：中文稳定渲染
- **Zara Agent**：风格探索、HTML 生成和部署
- **HyperFrames Agent**：视频插槽
- **Presenter Agent**：大纲确定后的演讲者模式
- **QA Agent**：内容、视觉、路径和交付检查

## AST 理论

AST 是 **Audience-State-Transfer** 的缩写。

- **Audience（观众）**：谁在听，他们已经知道什么，他们抵触什么，为什么他们会继续听
- **State（状态）**：观众在 PPT 之前和之后的状态，以及阻碍状态转换的核心张力
- **Transfer（转移）**：将观众从初始状态带到目标状态的逐页路径

核心观点：

> **PPT 不是信息容器，而是观众状态转移工具。**

## 必需的输出契约

每次 Normal PPT 运行必须产出：

1. `deck_brief.md` — 观众、目标、张力、成功标准
2. `ast_outline.md` — AST 地图和叙事弧线
3. `slide_plan.json` — 逐页计划
4. `speaker_intent.md` — 演讲者在每一页应该做什么
5. `asset_manifest.md` — 截图、图表、图片、视频需求
6. `video_slots.json` — 可选的 HyperFrames/视频插入计划

## 推荐的 OPC 工作流

```text
O — Outline Director（大纲导演）
  Normal PPT: 原始素材 → AST 大纲 + 生产说明书

P — Presentation Production（演示生产）
  guizang 路径: 中文稳定 HTML PPT
  Zara 路径: 风格探索和 HTML 生产

C — Complete / Control（完成/控制）
  HyperFrames 视频适配器
  Presenter 适配器外壳
  部署/导出适配器
  QA 检查清单
```

## 规则

1. 当 Normal PPT 可以先产出 AST 契约时，不要让幻灯片渲染器直接消费原始素材
2. 把演讲者模式作为后处理适配器，而不是一种风格
3. 把部署和演讲者模式分开
4. 吸收 normal 工具的 AI 写作清理原则，但不要把 Normal PPT 降格为文本润色
5. 优先选择经过验证的小工作流，而不是未经证实的广泛承诺
6. 对于公开 Skill 发布，创建/推送仓库，从 GitHub 本地安装，运行一个安全的完整示例，验证风格探索 + 演讲者模式 + 部署 URL，然后才能完善 README 细节
7. 对于 Agent 团队开发，在接入真正的下游 Skill 之前，输出 `router_plan.json`、`run_manifest.json`、有边界的 `commands/*.md` 和单独的 `outputs/<agent>/` 目录

## 操作参考

- `references/agent-teams-public-preview.md` — Agent 团队架构、专家 Agent 命令协议、公开预览发布循环和 README 分拆约定

## 本地演示

如果仓库已安装本地，运行：

```bash
python3 scripts/normal_ppt_v2.py \
  --source examples/01-ai-tool-update/source.md \
  --out .normal-ppt-runs/ai-tool-update \
  --title "AI 工具更新，不只是功能清单"
```

## V2 功能

### AST 模板

Normal PPT V2 支持场景化 AST 模板：

| 模板 | 适用场景 | 角色 |
|------|----------|------|
| `default` | 通用演示 | hook, conflict, method, proof, takeaway |
| `workshop` | 动手工作坊 | hook, context, demo, exercise, takeaway |
| `product_launch` | 产品发布 | hook, problem, solution, proof, cta |
| `tech_talk` | 技术分享 | hook, background, solution, demo, takeaway |
| `training` | 培训教育 | hook, concept, example, practice, qna, summary |

自动检测：V2 根据标题和内容中的关键词自动检测合适的模板。

### 增强的演讲者模式

演讲者模式包含：

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 全屏 | `F` | 切换全屏演示 |
| 暂停计时 | `T` | 暂停/恢复计时器 |
| 激光笔 | `L` | 红色激光点跟随鼠标 |
| 隐藏备注 | `N` | 切换备注面板可见性 |
| 风格对比 | `C` | 全屏并排显示所有风格 |
| 进度点击 | （点击） | 跳转到指定幻灯片 |
| 时间告警 | （可配置） | 警告/危险颜色变化 |

### 使用示例

```bash
# 列出可用模板
python3 scripts/normal_ppt_v2.py --list-templates

# 自动检测模板
python3 scripts/normal_ppt_v2.py \
  --source examples/02-hermes-install-guide/source.md \
  --out .normal-ppt-runs/hermes \
  --title "把 Hermes 装成一个真正能干活的 Agent"

# 强制指定模板
python3 scripts/normal_ppt_v2.py \
  --source source.md \
  --out output \
  --scene workshop  # 使用工作坊模板
```
