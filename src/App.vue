<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

const sampleDocs = [
  {
    name: 'AI知识库MVP方案.md',
    text: `AI知识库Chatbot MVP目标：让用户上传本地文档，系统完成切块、检索、引用回答。

MVP优先级：
1. 支持 txt、md、csv、json 等文本文件上传。
2. 每个文档按语义段落和窗口长度切块。
3. 查询时使用关键词和轻量TF-IDF混合检索。
4. 回答必须给出引用来源，包含文件名和片段编号。
5. 找不到依据时明确说明知识库没有足够信息。

后续增强：接入OpenAI Embeddings、pgvector、PDF解析、权限过滤、rerank、知识图谱。`,
  },
  {
    name: 'RAG运行手册.txt',
    text: `RAG流程包含摄取、清洗、切块、索引、检索、生成和评估。

摄取阶段保留metadata，例如source_file、chunk_id、section、created_at。
检索阶段推荐先做权限过滤，再做向量检索和关键词检索，最后rerank。
生成阶段模型只能基于检索上下文回答，并显示引用。

常见失败：切块太大导致噪声高，切块太小导致上下文不足，引用缺失导致答案不可审计。`,
  },
]

const documents = ref([])
const stats = ref({ documents: 0, chunks: 0, characters: 0 })
const question = ref('这个知识库 MVP 应该先做哪些功能？')
const messages = ref([])
const activeSource = ref(null)
const backendHealth = ref({ ok: false, database: { ok: false }, checked: false })
const activity = ref([])
const isDragging = ref(false)
const isLoading = ref(false)
const isAsking = ref(false)
const fileError = ref('')
const apiError = ref('')

const canAsk = computed(() => question.value.trim().length > 0 && stats.value.chunks > 0 && !isAsking.value)
const backendStatus = computed(() => {
  if (!backendHealth.value.checked) return { label: '检查中', tone: 'pending' }
  if (backendHealth.value.ok) return { label: '后端在线', tone: 'ok' }
  return { label: 'DB 未连接', tone: 'error' }
})
const retrievalSummary = computed(() => [
  { label: 'Top K', value: 5 },
  { label: '格式', value: 'Text' },
  { label: '模式', value: backendHealth.value.retrieval?.mode ?? 'hybrid' },
  {
    label: '向量',
    value: backendHealth.value.retrieval?.embeddings_configured ? 'OpenAI' : '未配置',
  },
])
const quickPrompts = [
  '这个知识库 MVP 应该先做哪些功能？',
  '当前项目怎么本地启动？',
  '后端不可用时应该检查什么？',
]

onMounted(() => {
  refreshHealth()
  refreshDocuments()
})

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail)
    throw new Error(payload.error || detail || `HTTP ${response.status}`)
  }

  return payload
}

async function refreshDocuments() {
  apiError.value = ''
  try {
    const payload = await apiFetch('/documents')
    documents.value = payload.documents ?? []
    stats.value = payload.stats ?? { documents: 0, chunks: 0, characters: 0 }
  } catch (error) {
    apiError.value = `后端不可用：${error.message}`
    await refreshHealth()
  }
}

async function refreshHealth() {
  try {
    const payload = await apiFetch('/health')
    backendHealth.value = { ...payload, checked: true }
  } catch {
    backendHealth.value = { ok: false, database: { ok: false }, checked: true }
  }
}

function addActivity(label, detail) {
  activity.value.unshift({
    id: crypto.randomUUID(),
    label,
    detail,
    time: new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  })
  activity.value = activity.value.slice(0, 5)
}

function useQuickPrompt(prompt) {
  question.value = prompt
}

async function ask() {
  const trimmed = question.value.trim()
  if (!trimmed || !stats.value.chunks) return

  apiError.value = ''
  isAsking.value = true

  try {
    const payload = await apiFetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: trimmed }),
    })

    messages.value.unshift({
      id: crypto.randomUUID(),
      question: trimmed,
      answer: payload.answer,
      citations: payload.citations ?? [],
      createdAt: new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    })

    activeSource.value = payload.citations?.[0] ?? null
    addActivity('完成检索', `${payload.citations?.length ?? 0} 个引用`)
  } catch (error) {
    apiError.value = `问答失败：${error.message}`
  } finally {
    isAsking.value = false
  }
}

async function uploadFiles(files) {
  if (!files.length) return

  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }

  const payload = await apiFetch('/documents', {
    method: 'POST',
    body: formData,
  })

  if (payload.skipped?.length) {
    fileError.value = '部分文件未上传：当前MVP先支持 txt、md、csv、json、log。'
  }

  if (payload.created?.length) {
    addActivity('文档入库', `${payload.created.length} 个文件`)
  }

  await refreshDocuments()
  await refreshHealth()
}

async function addFiles(fileList) {
  fileError.value = ''
  apiError.value = ''
  isLoading.value = true

  try {
    await uploadFiles([...fileList])
  } catch (error) {
    apiError.value = `上传失败：${error.message}`
  } finally {
    isLoading.value = false
  }
}

async function loadSamples() {
  const files = sampleDocs.map(
    (doc) => new File([doc.text], doc.name, { type: 'text/plain;charset=utf-8' }),
  )
  await addFiles(files)
}

async function clearKnowledgeBase() {
  apiError.value = ''
  isLoading.value = true

  try {
    await apiFetch('/documents/all', { method: 'DELETE' })
    messages.value = []
    activeSource.value = null
    addActivity('清空知识库', '所有文档已删除')
    await refreshDocuments()
  } catch (error) {
    apiError.value = `清空失败：${error.message}`
  } finally {
    isLoading.value = false
  }
}

async function removeDocument(id) {
  apiError.value = ''

  try {
    await apiFetch(`/documents?id=${encodeURIComponent(id)}`, { method: 'DELETE' })
    if (activeSource.value?.doc_id === id) activeSource.value = null
    addActivity('删除文档', '文档列表已更新')
    await refreshDocuments()
  } catch (error) {
    apiError.value = `删除失败：${error.message}`
  }
}

function handleDrop(event) {
  isDragging.value = false
  addFiles(event.dataTransfer.files)
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <main class="shell">
    <section class="library-panel" aria-label="知识库">
      <div class="brand-row">
        <div class="brand-lockup">
          <div class="brand-mark">SB</div>
          <div>
            <p class="eyebrow">Local RAG MVP</p>
            <h1>Swift Bot</h1>
          </div>
        </div>
        <button class="icon-button" type="button" title="载入示例" :disabled="isLoading" @click="loadSamples">
          ↺
        </button>
      </div>

      <div class="system-card" :class="`is-${backendStatus.tone}`">
        <div>
          <span class="status-dot"></span>
          <strong>{{ backendStatus.label }}</strong>
        </div>
        <button type="button" @click="refreshHealth">检查</button>
      </div>

      <label
        class="drop-zone"
        :class="{ 'is-dragging': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <input
          type="file"
          multiple
          accept=".txt,.md,.markdown,.csv,.json,.log"
          @change="addFiles($event.target.files)"
        />
        <b>+</b>
        <span>{{ isLoading ? '处理中...' : '上传或拖入文档' }}</span>
        <small>txt / md / csv / json / log</small>
      </label>

      <p v-if="fileError" class="notice">{{ fileError }}</p>
      <p v-if="apiError" class="notice error">{{ apiError }}</p>

      <div class="stat-grid">
        <div>
          <strong>{{ stats.documents }}</strong>
          <span>文档</span>
        </div>
        <div>
          <strong>{{ stats.chunks }}</strong>
          <span>片段</span>
        </div>
        <div>
          <strong>{{ stats.characters }}</strong>
          <span>字符</span>
        </div>
      </div>

      <div class="retrieval-panel">
        <div v-for="item in retrievalSummary" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <div class="section-title">
        <span>文档</span>
        <button type="button" :disabled="isLoading || !documents.length" @click="clearKnowledgeBase">清空</button>
      </div>

      <div class="document-list">
        <article v-for="doc in documents" :key="doc.id" class="document-card">
          <div>
            <strong>{{ doc.name }}</strong>
            <span>{{ formatSize(doc.size) }} · {{ doc.chunks }} 片段</span>
          </div>
          <button type="button" title="移除文档" @click="removeDocument(doc.id)">×</button>
        </article>
      </div>

      <div class="activity-panel">
        <div class="section-title compact">
          <span>活动</span>
        </div>
        <ol v-if="activity.length">
          <li v-for="item in activity" :key="item.id">
            <time>{{ item.time }}</time>
            <span>{{ item.label }}</span>
            <small>{{ item.detail }}</small>
          </li>
        </ol>
        <p v-else>上传、删除、检索动作会显示在这里。</p>
      </div>
    </section>

    <section class="chat-panel" aria-label="问答">
      <div class="chat-header">
        <div>
          <p class="eyebrow">Grounded answer</p>
          <h2>问知识库</h2>
        </div>
        <span :class="['status-pill', `is-${backendStatus.tone}`]">
          {{ stats.chunks ? '索引就绪' : '等待文档' }}
        </span>
      </div>

      <form class="ask-box" @submit.prevent="ask">
        <textarea
          v-model="question"
          rows="4"
          placeholder="问一个和文档有关的问题..."
          @keydown.meta.enter.prevent="ask"
          @keydown.ctrl.enter.prevent="ask"
        />
        <div class="ask-actions">
          <div class="quick-prompts" aria-label="快速问题">
            <button v-for="prompt in quickPrompts" :key="prompt" type="button" @click="useQuickPrompt(prompt)">
              {{ prompt }}
            </button>
          </div>
          <button class="ask-submit" type="submit" :disabled="!canAsk">
            {{ isAsking ? '检索中...' : '检索回答' }}
          </button>
        </div>
      </form>

      <div class="message-list">
        <article v-for="message in messages" :key="message.id" class="message-card">
          <div class="message-meta">
            <span>{{ message.createdAt }}</span>
            <span>{{ message.citations.length }} 个引用</span>
          </div>
          <h3>{{ message.question }}</h3>
          <p class="answer">{{ message.answer }}</p>
          <div class="citation-row">
            <button
              v-for="source in message.citations"
              :key="source.id"
              type="button"
              @click="activeSource = source"
            >
              [{{ source.index }}] {{ source.source }}
            </button>
          </div>
        </article>

        <article v-if="!messages.length" class="empty-state">
          <h3>后端 RAG 已接入</h3>
          <p>上传文档或载入示例后，问题会发送到本地后端并返回引用片段。</p>
          <div class="empty-actions">
            <button type="button" @click="loadSamples">载入示例</button>
            <button type="button" @click="refreshDocuments">刷新索引</button>
          </div>
        </article>
      </div>
    </section>

    <aside class="source-panel" aria-label="引用">
      <div class="source-header">
        <p class="eyebrow">Source</p>
        <h2>引用片段</h2>
      </div>

      <article v-if="activeSource" class="source-card">
        <div class="source-label">
          [{{ activeSource.index }}] {{ activeSource.source }}
          <span v-if="activeSource.score">命中分 {{ activeSource.score }}</span>
        </div>
        <pre>{{ activeSource.text }}</pre>
      </article>

      <article v-else class="empty-source">
        <strong>等待引用</strong>
        <p>选择引用后，这里显示后端返回的原文片段。</p>
      </article>
    </aside>
  </main>
</template>
