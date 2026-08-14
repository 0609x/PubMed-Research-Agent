import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createSearch, getHistory } from '@/api/search'
import { notifyError } from '@/api/http'
import type { Language, SearchListItem, SearchMode, SearchOut, SortBy } from '@/types'

export const useSearchStore = defineStore('search', () => {
  const loading = ref(false)
  const query = ref('')
  const language = ref<Language>('en')
  const searchMode = ref<SearchMode>('advanced')
  const sortBy = ref<SortBy>('relevance')
  const minYear = ref<number | null>(null)
  const maxYear = ref<number | null>(null)
  const minImpactFactor = ref<number | null>(null)
  const maxResults = ref(10)
  const result = ref<SearchOut | null>(null)
  const history = ref<SearchListItem[]>([])

  async function run(): Promise<void> {
    const q = query.value.trim()
    if (!q || loading.value) return
    loading.value = true
    result.value = null
    try {
      result.value = await createSearch({
        query: q,
        max_results: maxResults.value,
        language: language.value,
        search_mode: searchMode.value,
        sort_by: sortBy.value,
        min_year: minYear.value,
        max_year: maxYear.value,
        min_impact_factor: minImpactFactor.value
      })
      await refreshHistory()
    } catch (err) {
      notifyError(err)
    } finally {
      loading.value = false
    }
  }

  async function refreshHistory(): Promise<void> {
    try {
      history.value = await getHistory(20)
    } catch (err) {
      notifyError(err)
    }
  }

  return {
    loading,
    query,
    language,
    searchMode,
    sortBy,
    minYear,
    maxYear,
    minImpactFactor,
    maxResults,
    result,
    history,
    run,
    refreshHistory
  }
})
