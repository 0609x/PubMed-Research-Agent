import { get, post } from './http'
import type { DashboardStats, KeywordActionOut, SearchCreate, SearchListItem, SearchOut } from '@/types'

export function createSearch(payload: SearchCreate): Promise<SearchOut> {
  return post<SearchOut>('/search', payload)
}

export function getSearch(id: number): Promise<SearchOut> {
  return get<SearchOut>(`/search/${id}`)
}

export function getHistory(limit = 20): Promise<SearchListItem[]> {
  return get<SearchListItem[]>(`/search/history?limit=${limit}`)
}
export function getSearchStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/search/stats')
}

export function excludeKeyword(keyword: string): Promise<KeywordActionOut> {
  return post<KeywordActionOut>('/search/keywords/exclude', { keyword })
}

export function restoreKeyword(keyword: string): Promise<KeywordActionOut> {
  return post<KeywordActionOut>('/search/keywords/restore', { keyword })
}

export function restoreAllKeywords(): Promise<KeywordActionOut> {
  return post<KeywordActionOut>('/search/keywords/restore-all', {})
}
