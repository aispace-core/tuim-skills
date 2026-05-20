# examples

这里放 `clone-skill` 的最小可运行示例。

## minimal-clone

`minimal-clone/` 是一个演示用的 mock 克隆产物，包含：
- 6 个 `references/research/*.md` 样例文件
- 1 个示例 `SKILL.md`

用途：
- 测试 `scripts/merge_research.py`
- 测试 `scripts/quality_check.py`

在仓库根目录执行：

```bash
python3 clone-skill/scripts/merge_research.py clone-skill/examples/minimal-clone
python3 clone-skill/scripts/quality_check.py clone-skill/examples/minimal-clone/SKILL.md
```

说明：
- 该示例是为了验证流程和脚本，不代表真实人物调研质量
- 里面的研究内容是结构化 mock 数据，重点是让测试链路打通
