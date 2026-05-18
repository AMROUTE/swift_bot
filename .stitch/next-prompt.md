---
page: dashboard
---
Professional AI knowledge-base Chatbot dashboard for Swift Bot. The page is an actual usable product dashboard, not a marketing landing page. It should feel calm, precise, trustworthy, and optimized for document-grounded AI workflows.

**DESIGN SYSTEM (REQUIRED):**
- Platform: Web, desktop-first dashboard, responsive down to tablet and mobile.
- Palette: Background Mist Blue Gray `#EEF3F6`, Surface White `#FFFFFF`, Primary Action Deep Teal `#1D716B`, Primary Text Ink Navy `#172635`, Secondary Text Blue Gray `#607587`, Border Cool Gray `#D7E0E5`, Warning `#FFF4DD`, Error `#FFE8E8`.
- Typography: Inter or similar modern sans-serif, compact dashboard hierarchy, no oversized hero typography.
- Styles: 8px maximum radius for cards and panels, thin borders, flat-to-whisper-soft elevation, no decorative orbs, no purple gradient theme, no nested cards.
- UI density: professional internal AI tooling dashboard, optimized for scanning, document auditability, and repeated work.
- Iconography: minimalist line icons for upload, refresh, delete, source, search, document, and activity status.

**PAGE STRUCTURE:**
1. **Left Knowledge Library Panel:** Fixed-width sidebar around 300px. Brand block with "Swift Bot" and "Local RAG MVP". Upload drop zone with idle, dragging, and processing states. Stats row for Documents, Chunks, Characters. Document list with file name, size, chunk count, and remove icon button. Alert area for unsupported files or backend unavailable state.
2. **Center Chat Workspace:** Main flexible column. Header "问知识库" with status pill "后端索引就绪" or "等待文档". Large question composer with textarea and primary "检索回答" button. Conversation feed with answer cards, timestamp, citation count, user question, grounded answer text, and citation chips.
3. **Right Citation Source Panel:** Width around 340px. Header "引用片段". Selected citation card with file name, citation index, score, and original text in readable monospace block. Empty state says "选择引用后，这里显示后端返回的原文片段。"
4. **Interaction States:** Disabled ask button when no chunks exist. Loading state for upload and query. Hover states on document rows, citation chips, and icon buttons. Active citation state clearly selected.
5. **Responsive Behavior:** Desktop uses three columns. Medium width uses left + center with source panel below. Mobile stacks panels vertically with full-width controls and compact typography.

**CONTENT DETAILS:**
- Use Chinese UI labels: "上传或拖入文档", "知识源", "清空", "检索回答", "引用片段".
- Example document names: `AI知识库MVP方案.md`, `RAG运行手册.txt`, `README.md`.
- Example answer includes numbered citations like `[1]`, `[2]`.

**QUALITY BAR:**
Design should look production-ready for an internal AI tooling dashboard. Prioritize clarity, fast scanning, trust, citation auditability, and stable layout over decorative visuals.
