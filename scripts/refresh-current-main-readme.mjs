#!/usr/bin/env node
/** Deterministic bilingual documentation; figures describe contracts, not runs. */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const PROFILE = {
 "slug":"tsao-dft","title":"TsaoDFT Skill",
 "readmes":[{"path":"README.md","lang":"zh"},{"path":"README_EN.md","lang":"en"}],
 "zh":{"tagline":"从 Kohn–Sham 合同、周期几何与引擎身份到可证伪电子结构证据","stages":[["科学问题","体系、可观测量与精度"],["结构与周期性","晶胞、PBC 与邻居表"],["方法合同","泛函、基组/截断与 SCF"],["数值验收","能量、力、应力与等价"],["证据分级","L0–L3、哈希与责任边界"]],"boundary":"软件门禁只验证控制面、参考数值与证据合同；Gaussian、VASP、QE、CP2K 等外部引擎未在此自动执行，保持 EXTERNAL_HOLD。","strategy":["先核对安装环境、输入结构、单位、有效范围与执行权限。","按上面的源码锚点区分原生实现、解释性合同和外部执行要求。","先运行快速回归和完整质量门，再用固定提交执行长期回归。","逐项保存原始日志、机器报告和限制；任何缺失证据不得写成 PASS。"]},
 "en":{"tagline":"From Kohn–Sham contracts, periodic geometry and engine identity to falsifiable electronic-structure evidence","stages":[["Scientific question","System, observables and accuracy"],["Structure and periodicity","Cell, PBC and neighbour lists"],["Method contract","Functional, basis/cutoff and SCF"],["Numerical acceptance","Energy, forces, stress and parity"],["Evidence grading","L0–L3, hashes and authority"]],"boundary":"Software gates validate the control plane, reference numerics and evidence contracts only; external engines such as Gaussian, VASP, QE and CP2K are not executed here and remain EXTERNAL_HOLD.","strategy":["Check the installation environment, input structure, units, applicability and execution permissions.","Use the source mappings above to distinguish native implementation, explanatory contracts and external execution requirements.","Run focused regression and full quality gates before long-duration testing of pinned commits.","Preserve original logs, machine-readable reports and limitations; missing evidence must never be reported as PASS."]},
 "code":["skills/tsao-structure-prep/scripts/neighbor_list.py","scripts/build_release_acceptance.py","scripts/capture_compute_contract_evidence.py"],
 "math":[
  {"latex":"\\left[-\\tfrac12\\nabla^2+v_{\\mathrm{eff}}[n](\\mathbf r)\\right]\\psi_i(\\mathbf r)=\\varepsilon_i\\psi_i(\\mathbf r)","plain":["[−½∇² + v_eff[n]] ψ_i = ε_i ψ_i"],"zh":{"name":"Kohn–Sham 方法合同","note":"这是原子单位制下的电子结构方法说明，不是该仓库内置求解器的计算结果。泛函、赝势或基组、截断、k 点、占据、自旋与 SCF 容差属于外部引擎输入身份；必须保留真实外部执行和收敛证据。"},"en":{"name":"Kohn–Sham method contract","note":"This is the electronic-structure method in atomic units, not output from a built-in DFT solver. Functional, pseudopotentials or basis, cutoffs, k points, occupations, spin and SCF tolerances belong to external-engine input identity. Preserve actual execution and convergence evidence."},"code":["scripts/capture_compute_contract_evidence.py"]},
  {"latex":"\\mathbf n^\\star=\\operatorname*{arg\\,min}_{\\substack{\\mathbf n\\in\\mathbb Z^3\\\\ n_i=0\\ \\mathrm{on\\ nonperiodic\\ axes}}}\\|\\Delta\\mathbf r-\\mathbf n\\mathbf H\\|_2,\\qquad\\Delta\\mathbf r_{\\mathrm{MIC}}=\\Delta\\mathbf r-\\mathbf n^\\star\\mathbf H","plain":["n* = argmin_n ‖Δr − nH‖₂","Δr_MIC = Δr − n*H"],"zh":{"name":"行晶格的最近像","note":"H 的每一行是一个晶格矢量，Δr 与 n 均按行向量书写；非周期方向的整数平移固定为零。一般斜晶胞不能用逐分量四舍五入保证最短距离。实现采用有界候选搜索，超过安全边界时拒绝，不能把拒绝当成近似成功。"},"en":{"name":"Row-lattice minimum image","note":"Rows of H are lattice vectors; Δr and n are row vectors, and integer shifts on nonperiodic axes are zero. Componentwise fractional rounding does not guarantee the shortest distance in a general skew cell. The implementation uses bounded candidate search and rejects unsafe bounds rather than presenting rejection as approximate success."},"code":["skills/tsao-structure-prep/scripts/neighbor_list.py"]},
  {"latex":"|E-E_{\\mathrm{ref}}|\\le\\tau_E,\\qquad \\max_i\\|\\mathbf F_i-\\mathbf F_{i,\\mathrm{ref}}\\|_2\\le\\tau_F","plain":["|E − E_ref| ≤ τ_E","max_i ‖F_i − F_i,ref‖₂ ≤ τ_F"],"zh":{"name":"参考等价与资格分级","note":"这是能量与力的参考等价合同示例，阈值必须随具体基准、单位与方法身份声明，不是所有测试自动采用的统一数值。软件就绪、解析通过和 L0–L3 证据等级不能替代真实外部引擎验收；EXTERNAL_HOLD 不得被文档图示覆盖。"},"en":{"name":"Reference parity and grading","note":"These are example energy/force parity contracts. Declare thresholds with the benchmark, units and method identity; they are not one universal threshold applied automatically to all tests. Software readiness, parsing and L0–L3 evidence levels do not replace external-engine qualification. Documentation cannot override EXTERNAL_HOLD."},"code":["scripts/build_release_acceptance.py"]}
 ],
 "commands":["python scripts/quality_gate.py"],"accent":"#c4b5fd"
};
const START = '<!-- CURRENT_MAIN_ACCEPTANCE_V2:START -->';
const END = '<!-- CURRENT_MAIN_ACCEPTANCE_V2:END -->';
const esc = (value) => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&apos;');
const normalized = (value) => value.normalize('NFC').replaceAll('\r\n', '\n');

// Conservative em-width estimates determine wrapping; browser QA checks glyph bounds.
function widthEm(text) {
  return [...text].reduce((sum, char) => sum + (/\p{Script=Han}/u.test(char) ? 1 : /[MW@%]/u.test(char) ? 0.95 : /[il.,:;!| ]/u.test(char) ? 0.34 : 0.65), 0);
}
function lines(text, width, size) {
  const output = []; let line = '';
  for (const word of String(text).match(/\p{Script=Han}|[^\p{Script=Han}\s]+|\s+/gu) ?? []) {
    if (line && widthEm(line + word) * size > width) { output.push(line.trim()); line = ''; }
    if (widthEm(word) * size > width) {
      for (const char of word) {
        if (line && widthEm(line + char) * size > width) { output.push(line.trim()); line = ''; }
        line += char;
      }
    } else line += word;
  }
  if (line.trim()) output.push(line.trim());
  return output;
}
function textBlock(value, x, baseline, width, size, leading, maxLines, color = '#dbeafe', weight = 400) {
  const wrapped = lines(value, width, size);
  if (wrapped.length > maxLines) throw Error(`Text exceeds its layout box: ${value}`);
  return `<text x="${x}" y="${baseline}" font-size="${size}" font-weight="${weight}" fill="${color}" data-box="${x},${baseline - size * 1.3},${width},${leading * maxLines + size * 0.5}">${wrapped.map((line, index) => `<tspan x="${x}" dy="${index ? leading : 0}">${esc(line)}</tspan>`).join('')}</text>`;
}
function visual(lang) {
  const t = PROFILE[lang], zh = lang === 'zh', accent = PROFILE.accent;
  const stages = t.stages.map(([heading, detail], index) => {
    const x = 46 + 307 * index;
    return `<g><rect x="${x}" y="246" width="278" height="220" rx="20" fill="#0f2038" stroke="${accent}" stroke-opacity=".5"/><circle cx="${x + 31}" cy="279" r="15" fill="${accent}" fill-opacity=".16"/><text x="${x + 31}" y="284" text-anchor="middle" font-size="13" fill="${accent}">0${index + 1}</text>${textBlock(heading, x + 20, 326, 237, 23, 28, 2, '#f8fafc', 700)}${textBlock(detail, x + 20, 399, 237, 17, 25, 2)}</g>`;
  }).join('');
  const arrows = [0, 1, 2, 3].map((index) => `<path d="M${327 + 307 * index} 357h21" fill="none" stroke="${accent}" stroke-width="2" marker-end="url(#arrow)"/>`).join('');
  const equations = PROFILE.math.map((formula, index) => {
    const x = 46 + 506 * index;
    return `<g><rect x="${x}" y="510" width="476" height="161" rx="20" fill="#101827" stroke="#64748b" stroke-opacity=".65"/>${textBlock(`${String(index + 1).padStart(2, '0')}  ${formula[lang].name}`, x + 22, 544, 432, 17, 22, 1, accent, 650)}${formula.plain.map((line, row) => textBlock(line, x + 22, 588 + row * 29, 432, 19, 26, 1, '#f8fafc')).join('')}</g>`;
  }).join('');
  const boundary = textBlock(t.boundary, 73, 767, 1440, 18, 27, 2);
  return normalized(`<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc" lang="${zh ? 'zh-CN' : 'en'}">
<title id="title">${esc(PROFILE.title)} — ${zh ? '代码与数学合同' : 'Code and mathematical contracts'}</title>
<desc id="desc">${esc(t.tagline)} ${esc(t.boundary)}</desc>
<defs><linearGradient id="background" x2="1" y2="1"><stop stop-color="#070e1d"/><stop offset="1" stop-color="#172338"/></linearGradient><pattern id="grid" width="44" height="44" patternUnits="userSpaceOnUse"><path d="M44 0H0V44" fill="none" stroke="#cbd5e1" stroke-opacity=".055"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1L9 5L0 9" fill="none" stroke="${accent}" stroke-width="1.4"/></marker><style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei","PingFang SC","Noto Sans",Arial,sans-serif}</style></defs>
<rect width="1600" height="900" fill="url(#background)"/><rect width="1600" height="900" fill="url(#grid)"/><circle cx="1444" cy="70" r="178" fill="${accent}" opacity=".07"/>
<path d="M1350 26L1480 75L1410 162L1539 203M1480 75L1570 20M1410 162L1310 175" fill="none" stroke="${accent}" stroke-opacity=".22" stroke-width="2"/>
${textBlock(PROFILE.title, 48, 82, 1400, 49, 54, 1, '#f8fafc', 750)}
${textBlock(t.tagline, 49, 130, 1465, 22, 30, 2, accent)}
${textBlock(zh ? '概念架构图 · 非测量数据 · 不代表外部求解已经执行' : 'CONCEPTUAL ARCHITECTURE · NOT MEASURED DATA · NOT PROOF OF EXTERNAL EXECUTION', 49, 214, 1470, 15, 23, 1, '#94a3b8')}
${arrows}${stages}${equations}
<rect x="46" y="712" width="1488" height="111" rx="18" fill="#080f1b" stroke="#334155"/>
${textBlock(zh ? '资格与解释边界' : 'QUALIFICATION AND INTERPRETATION', 73, 741, 1440, 13, 20, 1, accent, 650)}${boundary}
${textBlock(zh ? '固定源码 · 有限数值 · 可复现证据 · 人工审阅' : 'PINNED SOURCE · FINITE NUMERICS · REPRODUCIBLE EVIDENCE · HUMAN REVIEW', 49, 871, 1470, 14, 20, 1, '#94a3b8')}
</svg>
`);
}
function mathSection(lang) {
  return PROFILE.math.map((formula) => {
    const t = formula[lang];
    return `#### ${t.name}\n\n$$\n${formula.latex}\n$$\n\n${t.note}\n\n${lang === 'zh' ? '源码对应' : 'Source mapping'}: ${formula.code.map((path) => `[\`${path}\`](${path})`).join(' · ')}`;
  }).join('\n\n');
}
function section(lang, markers = true) {
  const zh = lang === 'zh', t = PROFILE[lang];
  return [markers ? START : '', `## ${zh ? '当前实现：代码、数学与使用策略' : 'Current implementation: code, mathematics and usage'}`, '',
    `![${zh ? '中文代码与数学合同概念图' : 'English code and mathematical-contract concept'}](docs/current-main/${PROFILE.slug}-current-main-${lang}.svg)`, '',
    `> ${t.boundary}`, '', mathSection(lang), '', `### ${zh ? '使用与验收顺序' : 'Usage and acceptance sequence'}`, '',
    ...t.strategy.map((item, index) => `${index + 1}. ${item}`), '', '```bash', ...PROFILE.commands, '```', '',
    zh ? '每次修复均须绑定新提交重新测试。基线回归、两段各三小时的重复回归、浏览器图形检查和外部工程认证是不同证据，不可互相替代。没有原始回执时，不宣称已完成六小时验收。' : 'Retest every changed commit. Baseline regression, two three-hour regression segments, browser visual checks and external engineering qualification are distinct evidence classes. Without original receipts, no six-hour completion is claimed.', '',
    `${zh ? '源码锚点' : 'Implementation anchors'}: ${PROFILE.code.map((path) => `[\`${path}\`](${path})`).join(' · ')}`, '', markers ? END : '',
  ].join('\n').trim();
}
function inject(original, generated) {
  const start = original.indexOf(START), end = original.indexOf(END);
  if ((start === -1) !== (end === -1) || end < start) throw Error('Unbalanced generated-section markers');
  const text = start === -1 ? `${original.trimEnd()}\n\n${generated}\n` : original.slice(0, start) + generated + original.slice(end + END.length);
  return normalized(text.trimEnd() + '\n');
}
const output = new Map(['zh', 'en'].map((lang) => [`docs/current-main/${PROFILE.slug}-current-main-${lang}.svg`, visual(lang)]));
for (const spec of PROFILE.readmes) {
  const content = spec.lang === 'bi' ? `${START}\n${section('zh', false)}\n\n${section('en', false)}\n${END}` : section(spec.lang);
  output.set(spec.path, inject(readFileSync(join(ROOT, spec.path), 'utf8'), content));
}
output.set('docs/CURRENT_MAIN_ACCEPTANCE.md', `# ${PROFILE.title} — code-backed documentation\n\n${PROFILE.code.map((path) => `- [\`${path}\`](../${path})`).join('\n')}\n\n${PROFILE.zh.boundary}\n\n${PROFILE.en.boundary}\n\nThe equations and diagrams document the declared implementation and its interpretation limits. They are not an execution attestation.\n`);
for (const path of new Set([...PROFILE.code, ...PROFILE.math.flatMap((formula) => formula.code)])) if (!existsSync(join(ROOT, path))) throw Error(`Missing source mapping: ${path}`);
const bad = [String.fromCodePoint(0xfffd), String.fromCodePoint(0x951f, 0x65a4, 0x62f7)];
for (const [path, content] of output) {
  if (bad.some((token) => content.includes(token))) throw Error(`Invalid text: ${path}`);
  if (path.endsWith('.svg') && /<script\b|<foreignObject\b|\son[a-z]+\s*=|javascript:|(?:href|xlink:href)\s*=\s*["'](?:https?:|\/\/|data:)/iu.test(content)) throw Error(`Active or external SVG content: ${path}`);
}
if (process.argv.includes('--write')) for (const [path, content] of output) { mkdirSync(dirname(join(ROOT, path)), { recursive: true }); writeFileSync(join(ROOT, path), content, 'utf8'); }
const stale = [...output].filter(([path, content]) => !existsSync(join(ROOT, path)) || readFileSync(join(ROOT, path), 'utf8') !== content).map(([path]) => path);
if (stale.length) throw Error(`Stale documentation: ${stale.join(', ')}`);
console.log(JSON.stringify({ schemaVersion: 'readme-mathematics-v6', project: PROFILE.title, files: [...output.keys()], status: 'PASS', scope: 'source mapping, deterministic generation and text integrity; not external scientific acceptance' }, null, 2));
