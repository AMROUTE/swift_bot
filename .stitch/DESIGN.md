# Swift Bot Design System

## 1. Product Feel

Swift Bot is a professional AI knowledge-base dashboard for local RAG workflows. It should feel calm, precise, auditable, and built for repeated daily use.

Avoid landing-page composition, decorative hero sections, oversized marketing typography, nested cards, gradient blobs, and visual noise.

## 2. Layout

- Desktop-first three-pane workbench.
- Left panel: knowledge library and upload workflow.
- Center panel: grounded chat workspace.
- Right panel: citation source inspector.
- Medium screens: source panel moves below.
- Mobile: panels stack vertically.

## 3. Color Tokens

| Role | Color |
| --- | --- |
| Background | `#EEF3F6` |
| Surface | `#FFFFFF` |
| Primary Action | `#1D716B` |
| Primary Text | `#172635` |
| Secondary Text | `#607587` |
| Border | `#D7E0E5` |
| Warning Surface | `#FFF4DD` |
| Error Surface | `#FFE8E8` |

## 4. Typography

- Font: Inter or similar modern sans-serif.
- Dashboard hierarchy, compact and legible.
- No viewport-scaled text.
- Letter spacing should stay at `0` except tiny uppercase eyebrow labels.

## 5. Components

- Panels use thin borders and white or translucent white surfaces.
- Cards max radius: `8px`.
- Buttons use clear action states; icon buttons use familiar symbols.
- Upload zone uses dashed border, drag state, and processing state.
- Citation chips are compact, scannable, and clickable.
- Source snippets use readable monospace with scroll behavior.

## 6. Design System Notes for Stitch Generation

**DESIGN SYSTEM (REQUIRED):**
- Platform: Web, desktop-first dashboard, responsive down to tablet and mobile.
- Palette: Background Mist Blue Gray `#EEF3F6`, Surface White `#FFFFFF`, Primary Action Deep Teal `#1D716B`, Primary Text Ink Navy `#172635`, Secondary Text Blue Gray `#607587`, Border Cool Gray `#D7E0E5`, Warning `#FFF4DD`, Error `#FFE8E8`.
- Typography: Inter or similar modern sans-serif, compact dashboard hierarchy, no oversized hero typography.
- Styles: 8px maximum radius for cards and panels, thin borders, flat-to-whisper-soft elevation, no decorative orbs, no purple gradient theme, no nested cards.
- UI density: professional internal AI tooling dashboard, optimized for scanning, document auditability, and repeated work.
- Iconography: minimalist line icons for upload, refresh, delete, source, search, document, and activity status.
