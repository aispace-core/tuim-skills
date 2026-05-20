# clone-skill

`clone-skill` 是一个“思维系统克隆工厂”。

它不复制金句，而是把一个人的思考方式或一个主题的方法论，克隆成一个可运行的 skill：
- 有触发条件
- 有研究与回答工作流
- 有心智模型与启发式
- 有表达 DNA、边界和来源

## 目录

- `SKILL.md`: 主控制器，负责分流、流程和检查点
- `references/extraction-framework.md`: 提炼方法论
- `references/skill-template.md`: 最终产物模板
- `scripts/merge_research.py`: 汇总 6 个 research 文件
- `scripts/quality_check.py`: 自动检查生成 skill 的结构完整性
- `scripts/download_subtitles.sh`: 下载 YouTube 字幕
- `scripts/srt_to_transcript.py`: 清洗字幕为 transcript

## 设计原则

- 主文档尽量短，只保留控制逻辑
- 方法论和模板下沉到 `references/`
- 先写入 artifact，再继续推进
- 宁可承认信息不足，也不伪造完整性

## 适用任务

- 克隆某个人的思维系统
- 克隆某个主题的方法论
- 更新已有人物 skill / 主题 skill
- 先诊断需求，再推荐要克隆的对象
