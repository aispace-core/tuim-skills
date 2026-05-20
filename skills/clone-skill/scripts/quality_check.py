#!/usr/bin/env python3
"""
自动检查生成的SKILL.md是否通过Phase 4质量标准。
对照通过标准表格逐项检查，输出通过/不通过和具体原因。

用法:
    python3 quality_check.py <SKILL.md路径>

示例:
    python3 quality_check.py .claude/skills/elon-musk-perspective/SKILL.md
"""

import sys
import re
from pathlib import Path


def check_mental_models(content: str) -> tuple[bool, str]:
    """检查心智模型数量（3-7个）"""
    # 匹配 ### 模型N: 或 ### N. 等模式
    models = re.findall(r'^###\s+(?:模型|Model|心智模型)\s*\d', content, re.MULTILINE)
    if not models:
        # fallback: 数「### 」开头的行在心智模型section中
        in_section = False
        count = 0
        for line in content.split('\n'):
            if re.match(r'^##\s+.*心智模型|Mental Model', line, re.IGNORECASE):
                in_section = True
                continue
            if in_section and re.match(r'^##\s+', line) and '心智模型' not in line:
                break
            if in_section and re.match(r'^###\s+', line):
                count += 1
        if count > 0:
            passed = 3 <= count <= 7
            return passed, f"{count}个心智模型 {'✅' if passed else '❌ (应为3-7个)'}"

    count = len(models)
    if count == 0:
        return False, "未检测到心智模型section"
    passed = 3 <= count <= 7
    return passed, f"{count}个心智模型 {'✅' if passed else '❌ (应为3-7个)'}"


def check_limitations(content: str) -> tuple[bool, str]:
    """检查每个模型是否有局限性"""
    has_limitation = bool(re.search(r'局限|失效|不适用|盲区|limitation|blind spot', content, re.IGNORECASE))
    return has_limitation, "有局限性标注 ✅" if has_limitation else "❌ 未找到局限性描述"


def check_expression_dna(content: str) -> tuple[bool, str]:
    """检查表达DNA辨识度"""
    dna_section = bool(re.search(r'表达DNA|Expression DNA|表达风格', content, re.IGNORECASE))
    if not dna_section:
        return False, "❌ 未找到表达DNA section"

    # 检查是否有具体的风格描述（句式、词汇等）
    style_markers = len(re.findall(r'句式|词汇|语气|幽默|节奏|确定性|引用|口头禅', content))
    passed = style_markers >= 3
    return passed, f"表达DNA特征: {style_markers}项 {'✅' if passed else '❌ (应≥3项)'}"


def check_honest_boundary(content: str) -> tuple[bool, str]:
    """检查诚实边界（至少3条）"""
    # 找诚实边界section
    boundary_match = re.search(r'(?:##\s+.*诚实边界|## Honest Boundary)(.*?)(?=\n##\s|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not boundary_match:
        return False, "❌ 未找到诚实边界section"

    boundary_text = boundary_match.group(1)
    # 计算列表项
    items = re.findall(r'^[-*]\s+', boundary_text, re.MULTILINE)
    count = len(items)
    passed = count >= 3
    return passed, f"诚实边界: {count}条 {'✅' if passed else '❌ (应≥3条)'}"


def check_tensions(content: str) -> tuple[bool, str]:
    """检查内在张力（至少2对）"""
    tension_markers = len(re.findall(r'张力|矛盾|tension|paradox|一方面.*另一方面|既.*又', content, re.IGNORECASE))
    passed = tension_markers >= 2
    return passed, f"内在张力: {tension_markers}处 {'✅' if passed else '❌ (应≥2处)'}"


def check_primary_sources(content: str) -> tuple[bool, str]:
    """检查一手来源占比"""
    # 找调研来源section
    source_section = re.search(
        r'^(?:##\s+[^\n]*来源[^\n]*|##\s+[^\n]*Source[^\n]*|##\s+[^\n]*Reference[^\n]*)\n(.*?)(?=^##\s|\Z)',
        content,
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    if not source_section:
        return True, "未找到来源section（跳过检查）"

    source_text = source_section.group(1)
    primary = len(re.findall(r'一手|primary|本人著作|原始', source_text, re.IGNORECASE))
    secondary = len(re.findall(r'二手|secondary|转述|评论', source_text, re.IGNORECASE))
    total = primary + secondary
    if total == 0:
        return True, "未标记来源类型（跳过检查）"

    ratio = primary / total
    passed = ratio > 0.5
    return passed, f"一手来源占比: {primary}/{total} ({ratio:.0%}) {'✅' if passed else '❌ (应>50%)'}"

def check_agentic_protocol(content: str) -> tuple[bool, str]:
    """检查是否包含可执行的回答工作流（Agentic Protocol）"""
    protocol_match = re.search(
        r'(?:##\s+.*回答工作流|##\s+.*Agentic Protocol)(.*?)(?=\n##\s|\Z)',
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not protocol_match:
        return False, "❌ 未找到回答工作流（Agentic Protocol）section"

    protocol_text = protocol_match.group(1)
    has_step1 = bool(re.search(r'Step\s*1|步骤\s*1', protocol_text, re.IGNORECASE))
    has_step2 = bool(re.search(r'Step\s*2|步骤\s*2', protocol_text, re.IGNORECASE))
    has_step3 = bool(re.search(r'Step\s*3|步骤\s*3', protocol_text, re.IGNORECASE))
    passed = has_step1 and has_step2 and has_step3
    missing = []
    if not has_step1:
        missing.append("Step 1")
    if not has_step2:
        missing.append("Step 2")
    if not has_step3:
        missing.append("Step 3")
    if passed:
        return True, "回答工作流包含 Step 1-3 ✅"
    return False, f"❌ 回答工作流缺少: {', '.join(missing)}"


def check_research_cutoff_date(content: str) -> tuple[bool, str]:
    """检查诚实边界是否标注调研时间"""
    boundary_match = re.search(r'(?:##\s+.*诚实边界|## Honest Boundary)(.*?)(?=\n##\s|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not boundary_match:
        return False, "❌ 未找到诚实边界section"
    boundary_text = boundary_match.group(1)
    has_date = bool(re.search(r'调研时间\s*[:：]', boundary_text))
    return has_date, "调研时间已标注 ✅" if has_date else "❌ 诚实边界未标注调研时间（调研时间: YYYY-MM-DD）"


def check_identity_card(content: str) -> tuple[bool, str]:
    """检查身份卡是否存在且有第一人称自我介绍"""
    id_match = re.search(r'(?:##\s+身份卡|##\s+框架定位)(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
    if not id_match:
        return False, "❌ 未找到身份卡/框架定位 section"
    id_text = id_match.group(1)
    has_who = bool(re.search(r'我是谁|框架定位', id_text))
    has_first_person = bool(re.search(r'(^|\n).{0,20}我.{0,20}', id_text))
    has_topic_locator = bool(re.search(r'适用场景|适用边界|这个框架', id_text))
    passed = (has_who and has_first_person) or has_topic_locator
    if passed and has_first_person:
        return True, "身份卡包含第一人称自我介绍 ✅"
    if passed and has_topic_locator:
        return True, "主题框架包含定位说明 ✅"
    if not has_who and not has_topic_locator:
        return False, "❌ 缺少身份卡或主题框架定位信息"
    return False, "❌ 身份卡缺少明显第一人称表述"


def check_sources_minimum(content: str) -> tuple[bool, str]:
    """检查调研来源是否包含足够的可追溯引用"""
    source_section = re.search(
        r'^(?:##\s+[^\n]*调研来源[^\n]*|##\s+[^\n]*来源[^\n]*|##\s+[^\n]*Source[^\n]*|##\s+[^\n]*Reference[^\n]*)\n(.*?)(?=^##\s|\Z)',
        content,
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    if not source_section:
        return True, "未找到来源section（跳过检查）"
    text = source_section.group(1)
    urls = set(re.findall(r'https?://[^\s\)]+', text))
    list_items = re.findall(r'^\s*[-*]\s+', text, re.MULTILINE)
    score = max(len(urls), len(list_items))
    passed = score >= 5
    return passed, f"可追溯来源: {score}项 {'✅' if passed else '❌ (建议≥5项)'}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 quality_check.py <SKILL.md路径>")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    if not skill_path.exists():
        print(f"❌ 文件不存在: {skill_path}")
        sys.exit(1)

    content = skill_path.read_text(encoding='utf-8')

    checks = [
        ("心智模型数量", check_mental_models),
        ("模型局限性", check_limitations),
        ("回答工作流", check_agentic_protocol),
        ("表达DNA辨识度", check_expression_dna),
        ("诚实边界", check_honest_boundary),
        ("调研时间", check_research_cutoff_date),
        ("内在张力", check_tensions),
        ("一手来源占比", check_primary_sources),
        ("来源可追溯", check_sources_minimum),
        ("身份卡", check_identity_card),
    ]

    print(f"质量检查: {skill_path.name}")
    print("=" * 50)

    passed_count = 0
    total = len(checks)

    for name, check_fn in checks:
        passed, detail = check_fn(content)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<12} {status}  {detail}")
        if passed:
            passed_count += 1

    print("=" * 50)
    print(f"结果: {passed_count}/{total} 通过")

    if passed_count == total:
        print("🎉 全部通过，可以交付")
    elif passed_count >= total - 1:
        print("⚠️ 基本通过，建议修复不通过项后交付")
    else:
        print("❌ 多项不通过，建议回到Phase 2迭代")

    sys.exit(0 if passed_count == total else 1)


if __name__ == '__main__':
    main()
