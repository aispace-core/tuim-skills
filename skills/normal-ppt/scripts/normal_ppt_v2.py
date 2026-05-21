#!/usr/bin/env python3
import argparse, json, html, shutil, re
from pathlib import Path
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent
DEFAULT_TEMPLATES_PATH = SCRIPT_DIR.parent / 'configs' / 'ast-templates.yaml'
DEFAULT_STYLES_PATH = SCRIPT_DIR.parent / 'configs' / 'styles.yaml'

class TemplateRegistry:
    def __init__(self, yaml_path=None):
        self.templates = {}
        self.scene_keywords = {}
        self.styles = {}
        self._load(yaml_path)

    def _load(self, yaml_path=None):
        if yaml_path is None:
            yaml_path = DEFAULT_TEMPLATES_PATH

        if not YAML_AVAILABLE:
            print("Warning: PyYAML not installed, using fallback templates")
            self._load_fallback()
            return

        if not Path(yaml_path).exists():
            print(f"Warning: {yaml_path} not found, using fallback templates")
            self._load_fallback()
            return

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data and 'templates' in data:
                self.templates = data['templates']
                self.scene_keywords = data.get('scene_keywords', {})

            styles_path = yaml_path.parent / 'styles.yaml'
            if styles_path.exists():
                with open(styles_path, 'r', encoding='utf-8') as f:
                    style_data = yaml.safe_load(f)
                    if style_data and 'styles' in style_data:
                        self.styles = style_data['styles']
            else:
                self._load_fallback_styles()
        except Exception as e:
            print(f"Warning: Failed to load YAML: {e}, using fallback")
            self._load_fallback()

    def _load_fallback(self):
        self.templates = {
            "default": {
                "label": "通用演示",
                "roles": [
                    {"id": "hook", "label": "Hook / 钩子", "purpose": "抓住注意力，建立悬念"},
                    {"id": "conflict", "label": "Conflict / 冲突", "purpose": "打破旧认知，制造张力"},
                    {"id": "method", "label": "Method / 方法", "purpose": "解释新框架或方法"},
                    {"id": "proof", "label": "Proof / 证据", "purpose": "用证据建立信任"},
                    {"id": "takeaway", "label": "Takeaway / 结论", "purpose": "留下可带走的关键判断"},
                ],
                "default_style": "guizang-stable"
            }
        }
        self.scene_keywords = {}
        self._load_fallback_styles()

    def _load_fallback_styles(self):
        self.styles = {
            "guizang-stable": {
                "label": "中文稳定 / guizang-style",
                "bg": "#f6f1e8", "fg": "#171717", "accent": "#8b1e1e",
                "font": "-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif"
            },
            "zara-editorial": {
                "label": "风格探索 / Zara Editorial",
                "bg": "#111111", "fg": "#f7f1e8", "accent": "#d7b56d",
                "font": "Georgia,'Times New Roman','PingFang SC',serif"
            },
            "zara-contrast": {
                "label": "风格探索 / Zara Contrast",
                "bg": "#fafafa", "fg": "#111111", "accent": "#ff4d00",
                "font": "Inter,-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif"
            },
        }

    def detect_scene(self, title, text):
        combined = (title + " " + text).lower()
        scores = {}

        for scene, keywords in self.scene_keywords.items():
            score = sum(1 for kw in keywords if kw.lower() in combined)
            if score > 0:
                scores[scene] = score

        if scores:
            return max(scores, key=scores.get)
        return "default"

    def get_template(self, scene=None):
        if scene and scene in self.templates:
            return self.templates[scene]
        if "default" in self.templates:
            return self.templates["default"]
        return list(self.templates.values())[0] if self.templates else None

    def get_styles(self):
        return self.styles

    def list_templates(self):
        return [(k, v.get('label', k), v.get('description', '')) for k, v in self.templates.items()]

    def list_scenes(self):
        return list(self.templates.keys())

def read_source(path):
    text = Path(path).read_text(encoding='utf-8')
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith('#')]
    return text, lines

class ContentParser:
    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines()

    def extract_sections(self):
        sections = []
        current_section = {"type": "paragraph", "content": [], "indent": 0}

        for line in self.lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            indent = len(line) - len(line.lstrip())

            if stripped.startswith('- ') or stripped.startswith('* '):
                if current_section["content"]:
                    sections.append(current_section)
                sections.append({"type": "list_item", "content": [stripped[2:]], "indent": indent})
                current_section = {"type": "paragraph", "content": [], "indent": indent}
            elif re.match(r'^\d+\. ', stripped):
                if current_section["content"]:
                    sections.append(current_section)
                sections.append({"type": "list_item", "content": [re.sub(r'^\d+\. ', '', stripped)], "indent": indent})
                current_section = {"type": "paragraph", "content": [], "indent": indent}
            elif stripped.startswith('```'):
                if current_section["content"]:
                    sections.append(current_section)
                sections.append({"type": "code_block", "content": [stripped], "indent": indent})
                current_section = {"type": "paragraph", "content": [], "indent": indent}
            elif stripped.startswith('>'):
                if current_section["content"]:
                    sections.append(current_section)
                sections.append({"type": "quote", "content": [stripped[1:].strip()], "indent": indent})
                current_section = {"type": "paragraph", "content": [], "indent": indent}
            else:
                current_section["content"].append(stripped)

        if current_section["content"]:
            sections.append(current_section)

        return sections

    def extract_assets(self):
        assets = {"images": [], "links": [], "code_blocks": []}

        assets["images"] = re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', self.text)

        assets["links"] = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', self.text)

        code_blocks = re.findall(r'```(\w*)\n([\s\S]*?)```', self.text)
        for lang, code in code_blocks:
            assets["code_blocks"].append({"language": lang, "preview": code[:200]})

        return assets

    def extract_keywords(self, top_n=10):
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', self.text)
        stopwords = {'的', '了', '是', '在', '和', '与', '或', '等', '也', '就', '都', '而', '及', '对', '于', '但', '这', '那', '一个', '我们', '你们', '他们', '可以', '能够', '需要', '应该', '如何', '什么', '为什么', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'}

        word_freq = {}
        for word in words:
            if len(word) >= 2 and word.lower() not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]

    def extract_key_sentences(self, top_n=5):
        sentences = re.split(r'[。！？\n]', self.text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        scores = []
        for sent in sentences:
            score = 0
            score += len(re.findall(r'[\u4e00-\u9fa5]', sent))
            score += sent.count('！') * 2
            score += sent.count('？') * 2
            if any(kw in sent for kw in ['关键', '核心', '重要', '必须', '应该', '一定']):
                score += 3
            scores.append((sent, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scores[:top_n]]

    def parse(self):
        return {
            "sections": self.extract_sections(),
            "assets": self.extract_assets(),
            "keywords": self.extract_keywords(),
            "key_sentences": self.extract_key_sentences(),
            "stats": {
                "total_chars": len(self.text),
                "total_lines": len([l for l in self.lines if l.strip()]),
                "code_blocks": len(self.extract_assets()["code_blocks"]),
                "images": len(self.extract_assets()["images"]),
                "links": len(self.extract_assets()["links"])
            }
        }

def detect_content_type(text):
    patterns = {
        "code": r"```[\s\S]*?```|import |def |class |function ",
        "tutorial": r"步骤|教程|如何|学会|掌握|lesson|guide",
        "meeting": r"会议|讨论|Agenda|会议纪要|总结",
        "report": r"报告|分析|数据|同比增长|相比",
    }

    scores = {}
    for ctype, pattern in patterns.items():
        scores[ctype] = len(re.findall(pattern, text, re.IGNORECASE))

    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return None

def make_plan(title, lines, template, content_type=None, parsed_content=None):
    roles = template.get('roles', [])
    if not roles:
        return []

    key_sentences = []
    if parsed_content and 'key_sentences' in parsed_content:
        key_sentences = parsed_content['key_sentences']
    else:
        key_sentences = lines[:5] if lines else []

    keywords = []
    if parsed_content and 'keywords' in parsed_content:
        keywords = parsed_content['keywords']

    plan = []
    for i, role in enumerate(roles, 1):
        role_id = role.get('id', f'role_{i}')
        role_label = role.get('label', role_id)
        purpose = role.get('purpose', '')
        default_duration = role.get('default_duration', 60)
        visual_directive = role.get('visual_directive', '')

        base_msg = purpose
        if content_type == "code" and role_id == "method":
            base_msg = f"通过代码示例演示核心实现逻辑"
        elif content_type == "tutorial" and role_id == "demo":
            base_msg = f"分步骤演示操作流程"

        evidence_idx = (i - 1) % max(len(key_sentences), 1)
        evidence = key_sentences[evidence_idx] if key_sentences else base_msg
        if isinstance(evidence, str) and len(evidence) > 90:
            evidence = evidence[:87] + "..."

        asset_need = "无"
        if role_id in ("method", "demo", "proof"):
            asset_need = "截图/流程图"
        elif content_type == "code" and role_id == "solution":
            asset_need = "代码截图/终端演示"
        elif parsed_content and parsed_content.get('assets'):
            assets = parsed_content['assets']
            if assets.get('images'):
                asset_need = f"配图 ({len(assets['images'])}张)"
            elif assets.get('code_blocks'):
                asset_need = f"代码块 ({len(assets['code_blocks'])}段)"

        plan.append({
            "slide_id": f"S{i:02d}",
            "role": role_id,
            "role_label": role_label,
            "title": title if i == 1 else purpose.split('。')[0] if '。' in purpose else purpose[:20],
            "message": base_msg,
            "purpose": purpose,
            "visible_content": [base_msg, evidence] if evidence != base_msg else [base_msg],
            "speaker_intent": purpose,
            "estimated_duration_seconds": default_duration,
            "visual_directive": visual_directive,
            "asset_need": asset_need,
            "recommended_style": template.get('default_style', 'guizang-stable'),
            "keywords": keywords[:5] if keywords else []
        })
    return plan

def write_contracts(out, title, plan, template, detected_scene, parsed_content=None):
    out.mkdir(parents=True, exist_ok=True)

    template_info = f"模板: {template.get('label', detected_scene)} ({detected_scene})"
    roles_summary = '\n'.join([f"- **{p['role_label']}** ({p['role']}): {p['purpose']}" for p in plan])

    keywords_str = ""
    if parsed_content and parsed_content.get('keywords'):
        keywords_str = f"\n## Keywords\n{', '.join(parsed_content['keywords'])}"

    stats_str = ""
    if parsed_content and parsed_content.get('stats'):
        s = parsed_content['stats']
        stats_str = f"\n## Content Stats\n- 字符数: {s['total_chars']}\n- 行数: {s['total_lines']}\n- 代码块: {s['code_blocks']}\n- 图片: {s['images']}\n- 链接: {s['links']}"

    deck_brief = f"""# Deck Brief

## Deck Goal
{title}

## Audience
（待填写：目标观众是谁？他们的背景是什么？）

## Initial State
（待填写：观众在看到 PPT 之前是什么状态？）

## Desired State
（待填写：看完 PPT 后希望观众变成什么状态？）

## Core Tension
（待填写：最大的认知障碍或阻力是什么？）

## Success Criteria
（待填写：用什么标准判断 PPT 成功了？）
{keywords_str}{stats_str}

## Metadata
{template_info}
"""
    (out/'deck_brief.md').write_text(deck_brief, encoding='utf-8')

    ast_outline = f"""# AST Outline

## Template
- ID: {detected_scene}
- Label: {template.get('label', detected_scene)}
- Description: {template.get('description', '')}

## Audience
（待填写：详细描述目标观众）

## State
- Initial: （观众当前状态）
- Desired: （目标状态）
- Core Tension: （核心张力）

## Transfer
{roles_summary}
"""
    (out/'ast_outline.md').write_text(ast_outline, encoding='utf-8')

    (out/'slide_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')

    speaker_intents = []
    for p in plan:
        keywords_display = ', '.join(p.get('keywords', [])) if p.get('keywords') else '（待填写）'
        speaker_intents.append(f"""## {p['slide_id']} {p['role_label']}

**Purpose:** {p['purpose']}
**Duration:** ~{p['estimated_duration_seconds']}s
**Visual:** {p['visual_directive']}
**Keywords:** {keywords_display}

- Say: {p['message']}
- Do: {p['speaker_intent']}
- Avoid: （待填写：不要说什么）
""")
    (out/'speaker_intent.md').write_text('\n'.join(speaker_intents), encoding='utf-8')

    asset_lines = ["| asset_id | type | purpose | status |", "|---|---|---|---|"]
    asset_id = 1
    if parsed_content and parsed_content.get('assets'):
        assets = parsed_content['assets']
        for alt_text, url in assets.get('images', []):
            asset_lines.append(f"| asset-{asset_id:02d} | image | {alt_text or '配图'} | 待获取 |")
            asset_id += 1
        for text, url in assets.get('links', []):
            if not url.startswith('#'):
                asset_lines.append(f"| ref-{asset_id:02d} | link | {text} | 待确认 |")
                asset_id += 1
        for code in assets.get('code_blocks', []):
            lang = code.get('language', 'code')
            asset_lines.append(f"| code-{asset_id:02d} | code-block | {lang} 代码块 | 内联 |")
            asset_id += 1
    (out/'asset_manifest.md').write_text("# Asset Manifest\n\n" + '\n'.join(asset_lines) + "\n", encoding='utf-8')

    videos = []
    for i, p in enumerate(plan, 1):
        if p.get('visual_directive') and '视频' in p.get('visual_directive', ''):
            videos.append({
                "video_id": f"V{i:02d}",
                "slide_id": p['slide_id'],
                "purpose": p.get('purpose', ''),
                "duration_seconds": 15,
                "aspect_ratio": "16:9"
            })
    (out/'video_slots.json').write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding='utf-8')

def deck_html(title, plan, style_id, style):
    slides = []
    for p in plan:
        bullets = ''.join(f"<li>{html.escape(x)}</li>" for x in p.get('visible_content', []))
        slides.append(f"""
<section class='slide' id='{p['slide_id']}'>
  <div class='kicker'>{html.escape(style.get('label', style_id))} · {html.escape(p['role_label'])}</div>
  <h1>{html.escape(p['title'])}</h1>
  <p class='message'>{html.escape(p['message'])}</p>
  <ul>{bullets}</ul>
  <div class='meta'>
    <span class='duration'>⏱ {p.get('estimated_duration_seconds', 60)}s</span>
    <span class='visual'>{html.escape(p.get('visual_directive', ''))}</span>
  </div>
  <div class='footer'>{p['slide_id']} / {html.escape(title)}</div>
</section>""")

    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)} · {style_id}</title>
<style>
:root{{--bg:{style.get('bg','#fff')};--fg:{style.get('fg','#000')};--accent:{style.get('accent','#333')};--font:{style.get('font','sans-serif')};}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font);overflow:hidden}} .slide{{display:none;width:100vw;height:100vh;padding:7vh 8vw;position:relative}} .slide.active{{display:block}} .kicker{{color:var(--accent);font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:14px}} h1{{font-size:clamp(42px,7vw,104px);line-height:1.02;margin:5vh 0 3vh;max-width:1100px}} .message{{font-size:clamp(22px,2.6vw,38px);line-height:1.35;max-width:980px}} ul{{font-size:clamp(18px,1.6vw,28px);line-height:1.6;max-width:1000px;margin-top:5vh}} .meta{{margin-top:4vh;font-size:14px;color:var(--accent);opacity:.7}} .duration{{margin-right:20px}} .footer{{position:absolute;left:8vw;bottom:5vh;color:var(--accent);font-size:12px}} .nav{{position:fixed;right:24px;bottom:20px;font:16px system-ui;color:var(--fg);opacity:.7}} .progress{{position:fixed;top:0;left:0;height:3px;background:var(--accent);transition:width .3s}}
</style></head><body>
<div class='progress' id='progress'></div>
{''.join(slides)}
<div class='nav'>← / → 翻页 · 按 F 全屏</div>
<script>
const slides=[...document.querySelectorAll('.slide')];let i=Number(new URLSearchParams(location.search).get('slide')||0);function show(n){{i=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,k)=>s.classList.toggle('active',k===i));location.hash='slide-'+(i+1);document.getElementById('progress').style.width=((i+1)/slides.length*100)+'%';window.parent&&window.parent.postMessage({{type:'normal-slide',index:i,total:slides.length}},'*')}}
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')show(i+1);if(e.key==='ArrowLeft')show(i-1);if(e.key==='f'||e.key==='F'){{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen()}}}});show(i);
</script></body></html>"""

def write_styles(out, title, plan, registry):
    styles_dir = out / 'styles'
    styles_dir.mkdir(exist_ok=True)

    styles = registry.get_styles()
    cards = []

    for sid, style in styles.items():
        html_content = deck_html(title, plan, sid, style)
        (styles_dir / f'{sid}.html').write_text(html_content, encoding='utf-8')
        cards.append(f"<a class='card' href='{sid}.html'><b>{html.escape(style.get('label', sid))}</b><span>{html.escape(style.get('description', sid))}</span></a>")

    index = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>Normal PPT · 风格探索</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;margin:40px;background:#f6f3ee}}h1{{font-size:48px;margin-bottom:10px}}p{{color:#666;margin-bottom:30px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}.card{{display:block;padding:28px;border:1px solid #ddd;border-radius:20px;background:white;color:#111;text-decoration:none;transition:transform .2s,box-shadow .2s}}.card:hover{{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.1)}}.card b{{display:block;font-size:24px;margin-bottom:12px}}.card span{{color:#777;font-size:14px}}</style></head>
<body><h1>🎨 风格探索</h1><p>先用 AST 大纲生成多个方向，确定后再进入 presenter / deploy。</p><div class='grid'>{''.join(cards)}</div></body></html>"""
    (styles_dir / 'index.html').write_text(index, encoding='utf-8')

def write_presenter(out, title, plan, selected_style='guizang-stable', registry=None):
    pres = out / 'presenter'
    pres.mkdir(exist_ok=True)

    notes = [{
        "slide_id": p['slide_id'],
        "role": p['role'],
        "role_label": p['role_label'],
        "title": p['title'],
        "note": p['speaker_intent'],
        "say": p['message'],
        "duration_seconds": p.get('estimated_duration_seconds', 60),
        "visual_directive": p.get('visual_directive', '')
    } for p in plan]

    (pres / 'notes.json').write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding='utf-8')

    deck_src = f"../styles/{selected_style}.html"
    style_base = f"../styles/{selected_style}.html"

    styles = registry.get_styles() if registry else {}
    compare_iframes = ''.join([
        f"<iframe src='../styles/{sid}.html?slide=0'></iframe>"
        for sid in styles.keys()
    ])

    notes_json = json.dumps(notes, ensure_ascii=False)

    presenter_html = f"""<!doctype html>
<html lang='zh-CN'>
<head>
<meta charset='utf-8'>
<title>{html.escape(title)} · Presenter Mode</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;background:#0d0d0d;color:#f8f8f8;height:100vh;overflow:hidden}}
.wrap{{display:grid;grid-template-columns:1fr 340px;height:100vh;gap:16px;padding:16px}}
iframe{{width:100%;height:100%;border:0;border-radius:12px;background:white}}
.side{{display:flex;flex-direction:column;gap:12px;overflow:hidden}}
.panel{{background:#1b1b1b;border:1px solid #333;border-radius:12px;padding:14px;flex:1;overflow:auto;transition:opacity .3s}}
.panel.hidden-panel{{display:none}}
.panel h3{{font-size:12px;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:.05em;display:flex;align-items:center;gap:8px}}
.panel h3 .badge{{background:#8b1e1e;color:#fff;font-size:10px;padding:2px 6px;border-radius:4px}}
.note{{font-size:14px;line-height:1.6}}
.note b{{color:#fff;display:block;margin-bottom:8px;font-size:15px}}
.note hr{{border:none;border-top:1px solid #333;margin:12px 0}}
.note .duration{{color:#d7b56d;font-size:12px;display:block;margin-top:8px}}
.note .slide-list{{margin-top:12px;display:flex;flex-wrap:wrap;gap:4px}}
.note .slide-chip{{display:inline-block;padding:4px 8px;border-radius:6px;font-size:11px;cursor:pointer;background:#2a2a2a;color:#888;transition:all .2s}}
.note .slide-chip:hover{{background:#3a3a3a;color:#fff}}
.note .slide-chip.current{{background:#8b1e1e;color:#fff}}
.controls{{display:flex;flex-direction:column;gap:12px;flex-shrink:0}}
.controls-row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
button{{background:#2a2a2a;border:1px solid #3a3a3a;border-radius:8px;color:#fff;padding:8px 14px;font-size:13px;cursor:pointer;transition:all .2s}}
button:hover{{background:#3a3a3a;border-color:#4a4a4a}}
button.active{{background:#8b1e1e;border-color:#8b1e1e}}
button.danger{{background:#4a1a1a;border-color:#6a2a2a}}
#timer{{font-size:28px;font-weight:700;margin:0 12px;min-width:80px;text-align:center}}
#timer.warning{{color:#f59e0b}}
#timer.danger{{color:#ef4444;animation:pulse 1s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
.progress-bar{{height:8px;background:#2a2a2a;border-radius:4px;cursor:pointer;position:relative;overflow:hidden}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#8b1e1e,#d7b56d);border-radius:4px;transition:width .3s}}
.progress-thumb{{position:absolute;top:50%;transform:translate(-50%,-50%);width:14px;height:14px;background:#fff;border-radius:50%;opacity:0;transition:opacity .2s;box-shadow:0 2px 8px rgba(0,0,0,.3)}}
.progress-bar:hover .progress-thumb{{opacity:1}}
.shortcuts{{font-size:11px;color:#555;margin-top:8px;line-height:1.8}}
.shortcuts kbd{{background:#2a2a2a;padding:2px 6px;border-radius:4px;margin-right:4px;font-size:10px}}
.shortcuts kbd.active{{background:#8b1e1e}}
.alerts{{margin-top:12px;padding-top:12px;border-top:1px solid #333}}
.alert-item{{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:12px}}
.alert-item input{{width:60px;padding:4px 8px;border-radius:4px;border:1px solid #3a3a3a;background:#2a2a2a;color:#fff;font-size:12px}}
.alert-item input.warning{{color:#f59e0b}}
.alert-item input.danger{{color:#ef4444}}
.alert-item .status{{width:16px;text-align:center}}
.compare-view{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.95);z-index:1000;padding:20px}}
.compare-view.active{{display:grid;grid-template-columns:repeat({len(styles)},1fr);gap:10px;padding-top:50px}}
.compare-view .close-btn{{position:absolute;top:10px;right:20px;background:#333;padding:8px 16px}}
.compare-view iframe{{height:calc(100vh - 80px);border-radius:8px}}
.laser-dot{{position:fixed;width:20px;height:20px;background:radial-gradient(circle,rgba(255,0,0,.8) 0%,transparent 70%);border-radius:50%;pointer-events:none;z-index:9999;opacity:0;transition:opacity .1s}}
.laser-dot.active{{opacity:1}}
</style>
</head>
<body>
<div class='wrap'>
  <iframe id='current' src='{deck_src}'></iframe>
  <div class='side'>
    <div class='panel' id='notesPanel'>
      <h3>📝 演讲者备注 <span class='badge' id='slideCount'>1/{len(notes)}</span></h3>
      <div id='note' class='note'></div>
      <div class='slide-list' id='slideList'></div>
    </div>
    <div class='panel' id='controlsPanel'>
      <h3>🎮 控制面板</h3>
      <div class='controls'>
        <div class='controls-row'>
          <button onclick='go(-1)'>◀</button>
          <button onclick='go(1)'>▶</button>
          <span id='timer'>00:00</span>
        </div>
        <div class='controls-row'>
          <button onclick='toggleTimer()' id='timerBtn'>⏸</button>
          <button onclick='resetTimer()' title='重置计时器'>↺</button>
          <button onclick='toggleFullscreen()' id='fsBtn'>⛶</button>
          <button onclick='toggleLaser()' id='laserBtn' title='激光笔'>🔴</button>
        </div>
        <div class='controls-row'>
          <button onclick='toggleNotes()' id='notesBtn'>📝</button>
          <button onclick='showCompare()'>🎨 对比</button>
          <button onclick='go(0)' title='第一页'>⏮</button>
          <button onclick='go(notes.length-1)' title='最后一页'>⏭</button>
        </div>
      </div>
      <div class='progress-bar' id='progressBar' onclick='seekTo(event)'>
        <div class='progress-fill' id='progress'></div>
        <div class='progress-thumb' id='thumb'></div>
      </div>
      <div class='alerts'>
        <div class='alert-item'>
          <span class='status' id='alertWarning'>⚠️</span>
          <input type='number' id='warnTime' value='5' min='1' max='60' onclick='event.stopPropagation()'>
          <span>分钟警告</span>
          <button onclick='clearAlert("warning")' style='padding:4px 8px;font-size:11px'>✕</button>
        </div>
        <div class='alert-item'>
          <span class='status' id='alertDanger'>🚨</span>
          <input type='number' id='dangerTime' value='1' min='1' max='30' onclick='event.stopPropagation()'>
          <span>分钟结束</span>
          <button onclick='clearAlert("danger")' style='padding:4px 8px;font-size:11px'>✕</button>
        </div>
      </div>
      <div class='shortcuts'>
        <kbd id='k-left'>←</kbd><kbd id='k-right'>→</kbd> 翻页
        <kbd id='k-f'>F</kbd> 全屏
        <kbd id='k-t'>T</kbd> 暂停
        <kbd id='k-l'>L</kbd> 激光笔
        <kbd id='k-n'>N</kbd> 隐藏备注
        <kbd id='k-c'>C</kbd> 风格对比
      </div>
    </div>
  </div>
</div>
<div class='compare-view' id='compareView'>
  <button class='close-btn' onclick='hideCompare()'>✕ 关闭对比</button>
  {compare_iframes}
</div>
<div class='laser-dot' id='laserDot'></div>
<script>
const notes={notes_json};
let i=0,t=Date.now(),paused=false,elapsed=0;
let notesVisible=true,laserActive=false;
let alerted={{warning:false,danger:false}};
function sync(){{
  const note=notes[i];
  document.getElementById('current').src='{deck_src}?slide='+i;
  document.getElementById('progress').style.width=((i+1)/notes.length*100)+'%';
  document.getElementById('thumb').style.left=((i+1)/notes.length*100)+'%';
  document.getElementById('slideCount').textContent=(i+1)+'/'+notes.length;
  document.getElementById('note').innerHTML=
    '<b>'+note.slide_id+' '+note.role_label+'</b>'+
    '<div>'+note.note+'</div>'+
    '<hr>'+
    '<div>'+note.say+'</div>'+
    '<span class="duration">⏱ '+note.duration_seconds+'s · '+note.visual_directive+'</span>';
  renderSlideList();
  syncCompareFrames();
}}
function renderSlideList(){{
  const list=document.getElementById('slideList');
  list.innerHTML=notes.map((n,idx)=>
    '<span class="slide-chip'+(idx===i?' current':'')+'" onclick="go('+idx+')">'+n.slide_id+'</span>'
  ).join('');
}}
function go(n){{i=Math.max(0,Math.min(notes.length-1,n));sync()}}
function seekTo(e){{
  const bar=document.getElementById('progressBar');
  const rect=bar.getBoundingClientRect();
  const pct=(e.clientX-rect.left)/rect.width;
  go(Math.floor(pct*notes.length));
}}
function toggleTimer(){{
  if(paused){{t=Date.now()-elapsed;paused=false;document.getElementById('timerBtn').textContent='⏸';document.getElementById('k-t').classList.remove('active');}}
  else{{elapsed=Date.now()-t;paused=true;document.getElementById('timerBtn').textContent='▶';document.getElementById('k-t').classList.add('active');}}
}}
function resetTimer(){{t=Date.now();elapsed=0;alerted={{warning:false,danger:false}};document.getElementById('timer').className='';document.getElementById('alertWarning').textContent='⚠️';document.getElementById('alertDanger').textContent='🚨';}}
function toggleFullscreen(){{
  if(!document.fullscreenElement){{document.documentElement.requestFullscreen();document.getElementById('fsBtn').classList.add('active');document.getElementById('k-f').classList.add('active');}}
  else{{document.exitFullscreen();document.getElementById('fsBtn').classList.remove('active');document.getElementById('k-f').classList.remove('active');}}
}}
function toggleNotes(){{
  notesVisible=!notesVisible;
  document.getElementById('notesPanel').classList.toggle('hidden-panel',!notesVisible);
  document.getElementById('notesBtn').classList.toggle('active',!notesVisible);
  document.getElementById('k-n').classList.toggle('active',!notesVisible);
}}
function toggleLaser(){{
  laserActive=!laserActive;
  document.getElementById('laserBtn').classList.toggle('active',laserActive);
  document.getElementById('k-l').classList.toggle('active',laserActive);
  document.getElementById('laserDot').classList.toggle('active',laserActive);
}}
function showCompare(){{document.getElementById('compareView').classList.add('active');document.getElementById('k-c').classList.add('active');syncCompareFrames();}}
function hideCompare(){{document.getElementById('compareView').classList.remove('active');document.getElementById('k-c').classList.remove('active');}}
function syncCompareFrames(){{
  if(document.getElementById('compareView').classList.contains('active')){{
    document.querySelectorAll('#compareView iframe').forEach(iframe=>{{iframe.src='{style_base}?slide='+i;}});
  }}
}}
function clearAlert(type){{alerted[type]=false;document.getElementById('timer').classList.remove(type==='warning'?'warning':'danger');}}
document.addEventListener('keydown',e=>{{
  if(e.key==='ArrowRight'||e.key===' '){{e.preventDefault();go(i+1);}}
  if(e.key==='ArrowLeft'){{e.preventDefault();go(i-1);}}
  if(e.key==='f'||e.key==='F')toggleFullscreen();
  if(e.key==='t'||e.key==='T')toggleTimer();
  if(e.key==='l'||e.key==='L')toggleLaser();
  if(e.key==='n'||e.key==='N')toggleNotes();
  if(e.key==='c'||e.key==='C'){{
    const cv=document.getElementById('compareView');
    cv.classList.contains('active')?hideCompare():showCompare();
  }}
}});
document.addEventListener('mousemove',e=>{{
  if(laserActive){{
    const dot=document.getElementById('laserDot');
    dot.style.left=(e.clientX-10)+'px';
    dot.style.top=(e.clientY-10)+'px';
  }}
}});
setInterval(()=>{{
  if(!paused){{
    let s=Math.floor((Date.now()-t)/1000);
    let m=Math.floor(s/60);
    document.getElementById('timer').textContent=String(m).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
    const warnVal=parseInt(document.getElementById('warnTime').value)||5;
    const dangerVal=parseInt(document.getElementById('dangerTime').value)||1;
    if(m>=warnVal&&!alerted.warning){{
      alerted.warning=true;
      document.getElementById('timer').classList.add('warning');
      document.getElementById('alertWarning').textContent='✅';
    }}
    if(m>=dangerVal&&!alerted.danger){{
      alerted.danger=true;
      document.getElementById('timer').classList.add('danger');
      document.getElementById('alertDanger').textContent='🔴';
    }}
  }}
}},500);
sync();
</script>
</body>
</html>"""
    (pres / 'index.html').write_text(presenter_html, encoding='utf-8')

def write_deploy(out):
    dep = out / 'deploy'
    dep.mkdir(exist_ok=True)

    shutil.copytree(out / 'styles', dep / 'styles', dirs_exist_ok=True)
    shutil.copytree(out / 'presenter', dep / 'presenter', dirs_exist_ok=True)

    (dep / 'index.html').write_text(
        "<meta charset='utf-8'><h1>Normal PPT Deploy Package</h1>"
        "<ul><li><a href='styles/index.html'>🎨 风格探索</a></li>"
        "<li><a href='presenter/index.html'>🎤 演讲者模式</a></li></ul>",
        encoding='utf-8'
    )
    (dep / 'presenter.html').write_text("<meta http-equiv='refresh' content='0; url=presenter/index.html'>", encoding='utf-8')

def main():
    ap = argparse.ArgumentParser(description='Normal PPT V2 - AST-based outline director')
    ap.add_argument('--source', help='Source markdown file')
    ap.add_argument('--out', help='Output directory')
    ap.add_argument('--title', default='Normal PPT Demo', help='Presentation title')
    ap.add_argument('--scene', '--template', dest='scene', default=None,
                   help='AST template/scene to use (default: auto-detect)')
    ap.add_argument('--style', default='guizang-stable',
                   help='Default style for presenter (default: guizang-stable)')
    ap.add_argument('--list-templates', action='store_true',
                   help='List available templates and exit')
    ap.add_argument('--templates-path', default=None,
                   help='Custom path to templates YAML')
    args = ap.parse_args()

    registry = TemplateRegistry(args.templates_path)

    if args.list_templates:
        print("Available AST Templates:")
        for tid, label, desc in registry.list_templates():
            print(f"  {tid:20} - {label}")
            if desc:
                print(f"  {'':20}   {desc}")
        print(f"\nAvailable Styles: {', '.join(registry.get_styles().keys())}")
        return

    if not args.source or not args.out:
        ap.error("--source and --out are required unless --list-templates is used")

    out = Path(args.out)
    text, lines = read_source(args.source)

    parser = ContentParser(text)
    parsed_content = parser.parse()

    detected_scene = args.scene if args.scene else registry.detect_scene(args.title, text)
    template = registry.get_template(detected_scene)

    if not template:
        print("Error: No template available")
        return

    content_type = detect_content_type(text)

    print(f"🤖 Normal PPT V2")
    print(f"   Title: {args.title}")
    print(f"   Detected Scene: {detected_scene}")
    print(f"   Template: {template.get('label', detected_scene)}")
    if content_type:
        print(f"   Content Type: {content_type}")
    print(f"   Source Lines: {len(lines)}")
    print(f"   Keywords: {', '.join(parsed_content['keywords'][:5])}")
    if parsed_content['stats']['code_blocks'] > 0:
        print(f"   Code Blocks: {parsed_content['stats']['code_blocks']}")
    if parsed_content['stats']['images'] > 0:
        print(f"   Images: {parsed_content['stats']['images']}")

    plan = make_plan(args.title, lines, template, content_type, parsed_content)

    write_contracts(out, args.title, plan, template, detected_scene, parsed_content)
    write_styles(out, args.title, plan, registry)
    write_presenter(out, args.title, plan, args.style, registry)
    write_deploy(out)

    result = {
        "ok": True,
        "title": args.title,
        "scene": detected_scene,
        "template_label": template.get('label', detected_scene),
        "slide_count": len(plan),
        "out": str(out),
        "files": {
            "deck_brief": str(out / 'deck_brief.md'),
            "ast_outline": str(out / 'ast_outline.md'),
            "slide_plan": str(out / 'slide_plan.json'),
            "speaker_intent": str(out / 'speaker_intent.md'),
            "style_index": str(out / 'styles' / 'index.html'),
            "presenter": str(out / 'presenter' / 'index.html'),
            "deploy": str(out / 'deploy' / 'index.html')
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
