from __future__ import annotations

from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {'repo': 'TsaoDFT_skill', 'readmes': {'zh': 'README.md', 'en': 'README_EN.md'}, 'paths': {'zh': 'docs/localized-vision/tsao-dft-vision-zh.svg', 'en': 'docs/localized-vision/tsao-dft-vision-en.svg'}, 'anchors': {'zh': '> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 唯一 AI 封面与 AI-assisted SVG 只表达系统结构、数理合同和使用策略。分子、晶格、轨道、能带、势能面、服务器与界面都不是 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD 或实验产生的数据。所有技术图均标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`；定量结论只能来自通过验收的输入、输出、Parser、哈希与机器证据。', 'en': '> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** The governed AI cover and AI-assisted SVGs communicate system architecture, mathematical contracts and usage strategy only. Molecules, lattices, orbitals, bands, energy surfaces, servers and interfaces are not data produced by Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD or experiments. Every technical figure is labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`; quantitative claims must come from accepted inputs, outputs, parsers, hashes and machine evidence.'}, 'zh': {'eyebrow': 'TSAODFT · 第一性原理与证据锁定工作流', 'title': '从 Kohn–Sham 方程到材料与分子证据链', 'subtitle': '方法指纹 · 周期几何 · 外部引擎交接 · Parser/SCF · 科学资格', 'vision_label': '项目愿景', 'vision': '让每个电子结构结论都能追溯到方法、输入、引擎、收敛和证据身份', 'vision_note': '仓库验证控制面与适配器；真实 Gaussian/VASP/QE/CP2K 结果保持外部资格。', 'formula_label': '核心第一性原理与数值合同', 'formula_rows': ['ĤKS[ρ]ψᵢ=εᵢψᵢ   ·   ρ(r)=Σ fᵢ|ψᵢ(r)|²   ·   Rₙ=||ρ⁽ⁿ⁺¹⁾−ρ⁽ⁿ⁾||≤τρ', 'n* = argminₙ∈ℤᴾ ||Δr−nH||₂   ·   Hrun=SHA256(input∥engine∥method∥parser∥environment)'], 'cards': [{'title': '方法指纹', 'subtitle': 'Functional · Basis · PP', 'formula': 'M=(XC,basis,PP,cutoff,k)', 'formula_note': '方法不可静默混用', 'lines': ['泛函与色散', '基组/赝势族', '自旋与参考态']}, {'title': '结构与周期几何', 'subtitle': 'Molecule · Cell · MIC', 'formula': 'ΔrMIC=Δr−n*H', 'formula_note': '三斜/部分周期精确', 'lines': ['结构规范化', '晶胞与周期轴', '邻居表与距离']}, {'title': '引擎交接', 'subtitle': 'Gaussian · VASP · QE · CP2K', 'formula': 'Hinput=SHA256(bytes)', 'formula_note': 'L1/L2 不冒充 L3', 'lines': ['输入生成', '许可证与版本', '调度与硬件身份']}, {'title': '解析与收敛', 'subtitle': 'Parser · SCF · Forces', 'formula': 'Rₙ≤τρ ∧ finite', 'formula_note': '正常退出不等于收敛', 'lines': ['fatal marker 优先', '能量/力/应力', '单位与有限数']}, {'title': '证据与资格', 'subtitle': 'Receipt · Equivalence', 'formula': 'δ=|y−yref|/max(|yref|,ε)', 'formula_note': '正确性先于性能', 'lines': ['结果与环境哈希', '参考值与容差', '外部签署审查']}], 'disclaimer': 'AI辅助概念设计 · 非科学数据 · 公式对应软件合同而非运行结果', 'footer': 'TsaoDFT Skill · 中文第一性原理愿景', 'accessible_title': 'TsaoDFT 中文第一性原理与证据链愿景图', 'accessible_desc': '从方法指纹、结构周期几何、外部引擎交接、解析收敛到证据资格的中文概念设计图。', 'readme_heading': '中文项目愿景图：从 Kohn–Sham 方程到材料与分子证据链', 'readme_alt': 'TsaoDFT 中文第一性原理工作流与数理证据架构', 'readme_note': '图中公式用于解释代码中的方法身份、周期几何、Parser、SCF 与证据门；图不是电子密度、能带、轨道或真实 DFT 计算结果。'}, 'en': {'eyebrow': 'TSAODFT · FIRST-PRINCIPLES AND EVIDENCE-LOCKED WORKFLOW', 'title': 'From Kohn–Sham Equations to Molecular and Materials Evidence', 'subtitle': 'Method fingerprint · periodic geometry · engine handoff · parser/SCF · scientific qualification', 'vision_label': 'VISION', 'vision': 'Make every electronic-structure conclusion traceable to method, input, engine, convergence and evidence identity', 'vision_note': 'The repository validates the control plane and adapters; real Gaussian/VASP/QE/CP2K results remain external.', 'formula_label': 'CORE FIRST-PRINCIPLES AND NUMERICAL CONTRACTS', 'formula_rows': ['ĤKS[ρ]ψᵢ=εᵢψᵢ   ·   ρ(r)=Σ fᵢ|ψᵢ(r)|²   ·   Rₙ=||ρ⁽ⁿ⁺¹⁾−ρ⁽ⁿ⁾||≤τρ', 'n* = argminₙ∈ℤᴾ ||Δr−nH||₂   ·   Hrun=SHA256(input∥engine∥method∥parser∥environment)'], 'cards': [{'title': 'Method fingerprint', 'subtitle': 'Functional · Basis · PP', 'formula': 'M=(XC,basis,PP,cutoff,k)', 'formula_note': 'no silent method mixing', 'lines': ['functional & dispersion', 'basis/pseudopotential', 'spin & reference state']}, {'title': 'Structure & geometry', 'subtitle': 'Molecule · Cell · MIC', 'formula': 'ΔrMIC=Δr−n*H', 'formula_note': 'exact triclinic/partial PBC', 'lines': ['structure normalization', 'cell and periodic axes', 'neighbor list & distance']}, {'title': 'Engine handoff', 'subtitle': 'Gaussian · VASP · QE · CP2K', 'formula': 'Hinput=SHA256(bytes)', 'formula_note': 'L1/L2 never impersonate L3', 'lines': ['input generation', 'license and version', 'scheduler/hardware identity']}, {'title': 'Parsing & convergence', 'subtitle': 'Parser · SCF · Forces', 'formula': 'Rₙ≤τρ ∧ finite', 'formula_note': 'exit is not convergence', 'lines': ['fatal markers dominate', 'energy/force/stress', 'units and finite values']}, {'title': 'Evidence qualification', 'subtitle': 'Receipt · Equivalence', 'formula': 'δ=|y−yref|/max(|yref|,ε)', 'formula_note': 'correctness before speed', 'lines': ['result/environment hashes', 'references and tolerance', 'external signed review']}], 'disclaimer': 'AI-ASSISTED CONCEPTUAL DESIGN · NOT SCIENTIFIC DATA', 'footer': 'TsaoDFT Skill · English first-principles vision', 'accessible_title': 'TsaoDFT English first-principles and evidence-chain vision', 'accessible_desc': 'English conceptual design from method fingerprint and periodic geometry through engine handoff, parsing, convergence and evidence qualification.', 'readme_heading': 'Project vision: from Kohn–Sham equations to molecular and materials evidence', 'readme_alt': 'TsaoDFT English first-principles workflow and mathematical evidence architecture', 'readme_note': 'The equations explain method identity, periodic geometry, parsing, SCF and evidence gates in the code. The figure is not electron density, a band structure, an orbital or a real DFT result.'}}

FONT = "Inter,'Noto Sans SC','Noto Sans CJK SC','Microsoft YaHei','PingFang SC','WenQuanYi Micro Hei','Segoe UI',Arial,sans-serif"
MATH_FONT = "'STIX Two Math','Cambria Math','Noto Sans Math','Noto Sans SC',serif"


def text(value: object) -> str:
    return escape(str(value), quote=True)


def render_svg(spec: dict[str, object]) -> str:
    cards = list(spec['cards'])
    colors = ['#22d3ee', '#818cf8', '#c084fc', '#34d399', '#fbbf24']
    x_positions = [78, 370, 662, 954, 1246]
    card_markup: list[str] = []
    for index, card in enumerate(cards):
        x = x_positions[index]
        color = colors[index]
        lines = list(card['lines'])
        formula = card['formula']
        card_markup.append(f'''<g transform="translate({x} 250)" filter="url(#shadow)">
  <rect width="250" height="390" rx="26" fill="#0d2034" stroke="{color}" stroke-width="2"/>
  <circle cx="42" cy="42" r="23" fill="{color}"/><text x="42" y="48" text-anchor="middle" class="step">{index + 1}</text>
  <text x="24" y="93" class="card-title">{text(card['title'])}</text>
  <text x="24" y="124" class="card-sub">{text(card['subtitle'])}</text>
  <rect x="20" y="151" width="210" height="76" rx="15" fill="#081522" stroke="#334155"/>
  <text x="125" y="184" text-anchor="middle" class="formula-small">{text(formula)}</text>
  <text x="125" y="207" text-anchor="middle" class="micro">{text(card['formula_note'])}</text>
  <circle cx="34" cy="274" r="6" fill="{color}"/><text x="51" y="280" class="body">{text(lines[0])}</text>
  <circle cx="34" cy="316" r="6" fill="{color}"/><text x="51" y="322" class="body">{text(lines[1])}</text>
  <circle cx="34" cy="358" r="6" fill="{color}"/><text x="51" y="364" class="body">{text(lines[2])}</text>
</g>''')
    arrows = []
    for x in [330, 622, 914, 1206]:
        arrows.append(f'<path d="M{x} 445h28" stroke="#94a3b8" stroke-width="4"/><path d="M{x+28} 445l-12-8v16z" fill="#94a3b8"/>')

    formula_rows = list(spec['formula_rows'])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc">
<title id="title">{text(spec['accessible_title'])}</title>
<desc id="desc">{text(spec['accessible_desc'])}</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#06121f"/><stop offset="0.55" stop-color="#10233f"/><stop offset="1" stop-color="#1f2554"/></linearGradient>
  <radialGradient id="halo" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="#22d3ee" stop-opacity=".30"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
  <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#020617" flood-opacity=".42"/></filter>
  <pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse"><path d="M38 0H0V38" fill="none" stroke="#dbeafe" stroke-opacity=".055"/></pattern>
  <style>
    text{{font-family:{FONT}}}
    .eyebrow{{font-size:17px;letter-spacing:3.5px;font-weight:800;fill:#67e8f9}}
    .title{{font-size:50px;font-weight:850;fill:#f8fafc}}
    .subtitle{{font-size:21px;fill:#cbd5e1}}
    .vision{{font-size:18px;font-weight:700;fill:#dbeafe}}
    .card-title{{font-size:23px;font-weight:800;fill:#f8fafc}}
    .card-sub{{font-size:15px;fill:#9fb1c8}}
    .body{{font-size:15px;fill:#d5deea}}
    .micro{{font-size:12px;fill:#8ea2ba}}
    .step{{font-size:15px;font-weight:900;fill:#07111f}}
    .formula{{font-family:{MATH_FONT};font-size:22px;fill:#e0f2fe}}
    .formula-small{{font-family:{MATH_FONT};font-size:17px;fill:#f0f9ff}}
    .disclaimer{{font-size:12px;font-weight:850;letter-spacing:1.1px;fill:#111827}}
  </style>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<rect width="1600" height="900" fill="url(#grid)"/>
<ellipse cx="800" cy="188" rx="610" ry="190" fill="url(#halo)"/>
<g transform="translate(78 54)">
  <text class="eyebrow">{text(spec['eyebrow'])}</text>
  <text class="title" y="63">{text(spec['title'])}</text>
  <text class="subtitle" y="105">{text(spec['subtitle'])}</text>
</g>
<g transform="translate(1030 68)" filter="url(#shadow)">
  <rect width="490" height="104" rx="24" fill="#0a1829" stroke="#334155"/>
  <text x="24" y="36" class="vision">{text(spec['vision_label'])}</text>
  <text x="24" y="70" class="formula-small">{text(spec['vision'])}</text>
  <text x="24" y="92" class="micro">{text(spec['vision_note'])}</text>
</g>
{''.join(card_markup)}
{''.join(arrows)}
<g transform="translate(78 686)" filter="url(#shadow)">
  <rect width="1444" height="128" rx="25" fill="#091827" stroke="#334155"/>
  <text x="24" y="34" class="vision">{text(spec['formula_label'])}</text>
  <text x="24" y="68" class="formula">{text(formula_rows[0])}</text>
  <text x="24" y="100" class="formula">{text(formula_rows[1])}</text>
</g>
<g transform="translate(78 842)">
  <rect width="640" height="28" rx="14" fill="#f8fafc" opacity=".95"/>
  <text x="320" y="19" text-anchor="middle" class="disclaimer">{text(spec['disclaimer'])}</text>
  <text x="1440" y="20" text-anchor="end" class="micro">{text(spec['footer'])}</text>
</g>
</svg>'''


def localized_block(language: str, image_path: str, spec: dict[str, object]) -> str:
    marker = f'LOCALIZED_VISION_{language.upper()}'
    return f'''<!-- {marker}:START -->
## {spec['readme_heading']}

<p align="center">
  <img src="{image_path}" width="100%" alt="{spec['readme_alt']}">
</p>

> {spec['readme_note']}

<!-- {marker}:END -->'''


def replace_or_insert(path: Path, language: str, image_path: str, spec: dict[str, object], anchor: str) -> None:
    content = path.read_text(encoding='utf-8')
    marker = f'LOCALIZED_VISION_{language.upper()}'
    pattern = re.compile(
        rf'<!-- {re.escape(marker)}:START -->.*?<!-- {re.escape(marker)}:END -->',
        flags=re.DOTALL,
    )
    block = localized_block(language, image_path, spec)
    if pattern.search(content):
        content = pattern.sub(block, content, count=1)
    elif anchor and anchor in content:
        content = content.replace(anchor, anchor + '\n\n' + block, 1)
    elif '</div>' in content[:5000]:
        content = content.replace('</div>', '</div>\n\n' + block, 1)
    else:
        first_break = content.find('\n\n')
        if first_break < 0:
            raise RuntimeError(f'{path}: no safe insertion point')
        content = content[:first_break] + '\n\n' + block + content[first_break:]
    path.write_text(content, encoding='utf-8', newline='\n')


def main() -> None:
    for language in ('zh', 'en'):
        svg_path = ROOT / CONFIG['paths'][language]
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_svg(CONFIG[language]), encoding='utf-8', newline='\n')
        parsed = ET.parse(svg_path).getroot()
        if not parsed.tag.endswith('svg') or not parsed.attrib.get('viewBox'):
            raise RuntimeError(f'{svg_path}: invalid SVG root/viewBox')
        raw = svg_path.read_text(encoding='utf-8')
        if '\ufffd' in raw or '<script' in raw.lower() or 'javascript:' in raw.lower():
            raise RuntimeError(f'{svg_path}: unsafe or corrupted content')

    replace_or_insert(ROOT / CONFIG['readmes']['zh'], 'zh', CONFIG['paths']['zh'], CONFIG['zh'], CONFIG['anchors']['zh'])
    replace_or_insert(ROOT / CONFIG['readmes']['en'], 'en', CONFIG['paths']['en'], CONFIG['en'], CONFIG['anchors']['en'])

    for language in ('zh', 'en'):
        target = ROOT / CONFIG['readmes'][language]
        if CONFIG['paths'][language] not in target.read_text(encoding='utf-8'):
            raise RuntimeError(f'{target}: localized image reference missing')
    print(f"localized README vision generated for {CONFIG['repo']}")


if __name__ == '__main__':
    main()
