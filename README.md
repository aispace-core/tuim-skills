# My Skills

## 安装

安装全部技能：

```bash
npx skills add tim/tuim-my-skills
```

安装单个技能：

```bash
npx skills add tim/tuim-my-skills -s clone-skill
```

列出可安装技能：

```bash
npx skills add tim/tuim-my-skills --list
```

## 当前可安装技能

- `clone-skill`
- `my-design-video-gen`
- `my-ppt`
- `my-roundtable`
- `my-web-design`

## 仓库约定

- 顶层可安装技能统一放在 `skills/<skill-name>/SKILL.md`
- `SKILL.md` 的 frontmatter `name` 必须与目录名一致
- 示例、模板、内部样例可以放在技能子目录内，但不应作为顶层技能暴露

## 维护命令

列出当前顶层技能：

```bash
npm run list
```

校验所有技能结构：

```bash
npm run validate
```

生成发布 manifest：

```bash
npm run pack
```
