import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ragQuery } from '@/api/rag'
import { notifyError } from '@/api/http'
import type { Language, RagSource } from '@/types'

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
  sources?: RagSource[]
}

export const useChatStore = defineStore('chat', () => {
  const turns = ref<ChatTurn[]>([])
  const loading = ref(false)
  const topK = ref(5)
  const language = ref<Language>('zh')

  async function ask(question: string): Promise<void> {
    const q = question.trim()
    if (!q || loading.value) return
    turns.value.push({ role: 'user', content: q })
    loading.value = true
    try {
      const out = await ragQuery({
        query: q,
        top_k: topK.value,
        language: language.value
      })
      turns.value.push({ role: 'assistant', content: out.answer, sources: out.sources })
    } catch (err) {
      notifyError(err)
      turns.value.push({ role: 'assistant', content: '请求失败，请确认已执行过文献检索（向量库非空）后重试。' })
    } finally {
      loading.value = false
    }
  }

  function clear(): void {
    turns.value = []
  }

  return { turns, loading, topK, language, ask, clear }
})
