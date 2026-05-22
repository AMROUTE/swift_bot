# Next-stage issue drafts

GitHub publishing is blocked because the GitHub connector has no installed accounts and the local `gh` CLI is not installed. These drafts are ready to publish in dependency order.

## 1. OpenAI 引用回答

Label: `ready-for-human`

## What to build

让知识库问答在完成检索后，调用 OpenAI 生成引用回答。回答必须只基于命中的片段组织内容，并保留可点击引用；当片段不足以支持回答时，应明确说明知识库里没有找到足够依据。

该 slice 需要先确认产品边界：回答风格、是否允许无法判断、引用是否必须逐句绑定片段，以及 OpenAI 请求失败时前端如何提示。

## Acceptance criteria

- [ ] 用户提问后，系统先检索片段，再基于片段生成引用回答。
- [ ] 引用回答中的每个关键结论都能追溯到一个或多个引用。
- [ ] 当没有足够片段支撑时，回答明确说明知识库里没有找到足够依据。
- [ ] OpenAI 请求失败时，API 和前端返回清晰错误，不吞掉已有引用信息。
- [ ] 覆盖核心 API 测试，包括有片段、无片段、OpenAI 失败三类路径。

## Blocked by

None - can start immediately

## 2. 文档入库状态与失败提示

Label: `ready-for-agent`

## What to build

让用户在文档入库过程中看到清晰状态，包括文档接收、片段生成、embedding 生成、入库完成和失败原因。OpenAI embeddings 失败时，系统应明确展示失败原因，并保持已有关键词检索路径可用。

## Acceptance criteria

- [ ] 文档入库 API 返回每个文档的入库状态和失败原因。
- [ ] 前端文档列表或状态区能展示入库完成、向量未配置、向量失败等状态。
- [ ] OpenAI embeddings 失败时，不产生无提示的半成功体验。
- [ ] 没有 `OPENAI_API_KEY` 时，用户能看懂系统正在使用关键词检索兜底。
- [ ] 覆盖 API 和前端关键状态测试。

## Blocked by

None - can start immediately

## 3. 前端一键重建向量

Label: `ready-for-agent`

## What to build

让用户在 dashboard 里触发已有片段的向量重建，不需要手动执行 curl。该能力用于用户先上传文档、后配置 `OPENAI_API_KEY` 的场景。

## Acceptance criteria

- [ ] 前端提供重建向量入口，并在 OpenAI embeddings 未配置时禁用或提示。
- [ ] 点击后调用后端重建向量接口，并展示进行中、成功、失败状态。
- [ ] 成功后刷新文档和检索状态，让用户知道已有片段已具备向量。
- [ ] 后端错误能映射为清晰用户提示。
- [ ] 覆盖 API 调用和 UI 状态测试。

## Blocked by

- 文档入库状态与失败提示

## 4. PDF/Word 文档入库

Label: `ready-for-agent`

## What to build

让知识库支持常见办公文档入库，包括 PDF 和 Word。用户上传这些文档后，系统抽取文本、生成片段、写入知识库，并能在引用回答中展示引用。

## Acceptance criteria

- [ ] 上传校验允许 PDF 和 Word 文档，并保留现有文本类格式。
- [ ] 后端能从 PDF 和 Word 中抽取文本并进入现有文档入库流程。
- [ ] 抽取失败、空文本、超限文件都返回明确错误。
- [ ] 前端上传区展示新增支持格式和失败原因。
- [ ] 覆盖抽取、入库、检索、引用展示的测试。

## Blocked by

- 文档入库状态与失败提示

## 5. 检索调试面板

Label: `ready-for-agent`

## What to build

让用户或开发者能查看每次知识库问答的检索细节，包括检索模式、命中片段、命中分、引用顺序和是否使用向量。该面板用于判断引用回答是否可靠。

## Acceptance criteria

- [ ] `/ask` 返回检索元数据，包括模式、命中片段数量、命中分和是否使用向量。
- [ ] 前端展示检索调试信息，不干扰主要聊天体验。
- [ ] 用户能从调试面板定位到对应引用和片段。
- [ ] 关键词、向量、hybrid 三种模式都有可验证输出。
- [ ] 覆盖 API 和前端展示测试。

## Blocked by

- OpenAI 引用回答

## 6. 会话历史

Label: `ready-for-agent`

## What to build

保存用户的问题、引用回答和引用，让用户刷新页面后仍能查看过去的知识库问答记录。会话历史应服务于单知识库、单机实例，不引入多用户权限。

## Acceptance criteria

- [ ] 用户每次提问后，问题、引用回答和引用被保存。
- [ ] 前端能加载历史记录，并恢复引用查看体验。
- [ ] 用户能删除单条历史或清空会话历史。
- [ ] 清空知识库时，对历史引用失效的表现有明确处理。
- [ ] 覆盖数据库、API 和前端关键路径测试。

## Blocked by

- OpenAI 引用回答

## 7. 最小检索评测集

Label: `ready-for-agent`

## What to build

提供一个最小检索评测集，用固定文档和问题验证知识库问答的检索质量。该能力用于后续修改检索、embedding、引用回答时防止质量退化。

## Acceptance criteria

- [ ] 仓库内提供一组小型评测文档和问题。
- [ ] 评测命令能检查指定问题是否命中预期片段或引用。
- [ ] 评测输出包含通过/失败、命中片段、命中分和检索模式。
- [ ] CI 或本地测试命令能稳定运行，不依赖真实 OpenAI 网络请求。
- [ ] 文档说明如何扩展评测集。

## Blocked by

- OpenAI 引用回答
- 检索调试面板
