# Swift Bot

Swift Bot 是本地知识库问答产品，用 RAG 思路把用户上传的文本资料变成可检索、可引用的问答体验。

## Language

**知识库问答**:
基于用户上传资料检索相关片段，并返回带引用回答的产品能力。
_Avoid_: AI知识库 Chatbot, 文档问答, RAG 应用

**RAG**:
实现知识库问答的技术方式：先检索资料片段，再基于片段组织回答。
_Avoid_: AI, 搜索, 普通聊天

**知识库**:
当前单机实例里的全部已上传资料集合。
_Avoid_: workspace, project, tenant

**文档**:
用户上传到知识库的一份文件。
_Avoid_: 资料, 文件, 知识源

**片段**:
从文档切分出来、用于检索和引用的最小文本单元。
_Avoid_: chunk, 分块, 段落

**引用**:
回答中指向某个片段的可点击依据。
_Avoid_: 参考文献, 来源文档, 模型解释

**引用回答**:
由检索到的片段组织出的回答，必须带引用。
_Avoid_: AI回答, 总结, 模型回答

**命中分**:
片段与问题的检索相关性分数，仅用于排序和调试。
_Avoid_: 置信度, 准确率, 质量分

**文档入库**:
文档被接收、切成片段、写入知识库并变得可检索的过程。
_Avoid_: 上传成功, 摄取, 索引

**检索**:
系统根据用户问题找到相关片段的知识库问答内部步骤。
_Avoid_: 搜索, 查询, 查找

**清空知识库**:
删除知识库中所有文档和片段的操作。
_Avoid_: 重置, 删除全部, 清理

## Relationships

- **知识库问答** uses **RAG**
- A **知识库** contains zero or more **文档**
- A **文档** produces one or more **片段**
- A **引用** points to exactly one **片段**
- A **引用回答** contains one or more **引用** unless no supporting **片段** is found
- A **片段** may have a **命中分** for a specific question
- **文档入库** adds one **文档** and its **片段** to a **知识库**
- **检索** selects **片段** from a **知识库**
- **清空知识库** removes all **文档** and **片段** from a **知识库**

## Example dialogue

> **Dev:** “用户问问题时，是直接让模型自由回答吗？”
> **Domain expert:** “不是，**知识库问答** 必须先用 **RAG** 找到资料片段，再返回带引用的回答。”

## Flagged ambiguities

- “AI知识库 Chatbot”“RAG”“文档问答”曾混用；resolved: 产品能力叫 **知识库问答**，**RAG** 只表示实现方式。
- “知识库”不表示多用户 workspace；resolved: 当前只表示单机实例里的全部资料集合。
- “资料”“文件”“知识源”曾混用；resolved: 领域实体叫 **文档**，“知识源”只作为 UI 区域文案。
- “chunk”“分块”“段落”曾混用；resolved: 领域术语叫 **片段**。
- “引用”不表示整篇文档或参考文献；resolved: **引用** 必须指向一个 **片段**。
- “AI回答”“总结”“模型回答”曾混用；resolved: 当前能力叫 **引用回答**，因为 MVP 不调用 LLM。
- “score”不表示置信度或准确率；resolved: 产品术语叫 **命中分**，只代表检索相关性。
- “上传成功”“摄取”“索引”曾混用；resolved: 用户可见流程叫 **文档入库**。
- “搜索”“查询”“查找”曾混用；resolved: 知识库问答内部步骤叫 **检索**。
- “重置”“删除全部”“清理”曾混用；resolved: 用户操作叫 **清空知识库**。
