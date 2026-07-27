# TsaoDFT README Visual Design System

This document records the design system used for the TsaoDFT README and versioned SVG assets. The workflow follows the same sequence promoted by UI/UX Pro Max: classify the product, choose an information pattern, synthesise style/color/typography, filter anti-patterns, and complete an accessibility-oriented pre-delivery check.

## Product classification

- Product type: scientific developer tool / computational-research infrastructure / documentation-led research operating system.
- Primary audience: computational chemists, materials researchers, scientific-software developers and reviewers.
- Reading context: GitHub desktop and tablet views, with figures frequently rendered at 50–100% README width.
- Information priority: scientific boundary → evidence chain → capability map → validated demonstrations → installation.

## Design pattern

- Primary pattern: **Hero-Centric Research OS**.
- Secondary pattern: **Evidence Dashboard + Bento Capability Grid**.
- Visual style: **Dark OLED Scientific UI**, **Data-Dense Dashboard**, **restrained Glassmorphism**, and **Swiss information hierarchy**.
- Design dials:
  - variance: `6/10`;
  - motion: `1/10` because all repository assets are static SVG;
  - density: `7/10`.

The v7 system deliberately restores the visual energy of the earlier dark TsaoDFT concepts while retaining the stricter evidence and accessibility rules introduced later.

## Core tokens

### Color

- Canvas: `#030816`
- Deep surface: `#061020`
- Card surface: `#07152A`
- Raised surface: `#0B2444`
- Primary text: `#F4F8FF`
- Secondary text: `#9FB5D2`
- Primary blue: `#2E8CFF`
- Cyan: `#18B7D4`
- Violet: `#765BFF`
- Magenta: `#C96BFF`
- Success: `#22C55E`
- Warning: `#F59E0B`
- Error: `#F24C5A`
- Border: `#23528C`
- Grid: `#173052`

### Typography

- Display and body: Inter-compatible system sans stack.
- Technical labels and identifiers: JetBrains Mono-compatible system monospace stack.
- Minimum body size in standalone SVGs: `13 px`.
- Minimum technical label size: `10 px`.
- Titles remain readable when a figure is embedded at half README width.

### Spacing and shape

- Spacing scale: `8 / 12 / 16 / 24 / 32 / 48 px`.
- Card radius: `14–18 px`.
- Hero radius: `22–24 px`.
- Border width: `1–2 px`.
- Glow is reserved for identity, active evidence nodes and major scientific motifs; it is not used as generic decoration.

## Composition rules

1. The conceptual overview is one full-width dark research-operating-system panel rather than a pale marketing banner.
2. The overview may communicate molecular, periodic, ML, kinetics and HPC domains, but the entire asset remains explicitly conceptual.
3. Deterministic figures use the same dark palette but contain no raster AI imagery.
4. Each deterministic figure has one dominant message, a compact evidence panel and a visible synthetic-data notice.
5. Color is never the only state signal; labels accompany every status.
6. Scientific-looking plots expose units, source type, acceptance stage or claim boundary where relevant.
7. The README uses four representative deterministic figures at a time and links the remaining assets instead of building an endless image wall.
8. Chinese and English README files use the same asset set and document order.

## Anti-patterns

The visual system rejects:

- pale generic SaaS cards that erase the computational-science identity;
- uncontrolled purple/pink AI gradients;
- decorative neon without information meaning;
- a gallery of unrelated visual styles;
- text embedded below readable GitHub size;
- colour-only success/failure encoding;
- screenshots that imply real engine output when none was executed;
- module-card repetition without an evidence hierarchy;
- fake badges, fake coverage numbers or unsupported L3 claims.

## Accessibility and delivery checklist

- [x] High-contrast dark surfaces and light text.
- [x] SVG `role="img"`, exact `<title>` and descriptive `<desc>`.
- [x] Visible AI / synthetic-data labels.
- [x] No external font, image or JavaScript dependency.
- [x] Fixed dimensions required by repository validators.
- [x] Labels accompany coloured states.
- [x] Bilingual README parity.
- [x] Raster preview review at full width and half width.
- [x] No conceptual image presented as scientific evidence.
