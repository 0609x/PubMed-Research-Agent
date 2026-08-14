// Shared TypeScript types mirroring the FastAPI schemas.

export interface Author {
  last_name: string
  fore_name: string
  initials: string
  affiliation: string
}

export interface Article {
  pmid: string
  title: string
  abstract: string
  doi: string
  authors: Author[]
  journal: string
  publish_date: string
  publication_type: string
  impact_factor?: number | null
}

export type Language = 'en' | 'zh'

export type SearchMode = 'keyword' | 'advanced'

export type SortBy = 'relevance' | 'date_desc' | 'date_asc'

export interface SearchCreate {
  query: string
  max_results: number
  language: Language
  search_mode: SearchMode
  sort_by: SortBy
  min_year?: number | null
  max_year?: number | null
  min_impact_factor?: number | null
}

export interface Hotspot {
  topic: string
  description: string
  evidence: string[]
}

export interface ExperimentalMethod {
  method: string
  purpose: string
  frequency: number
}

export interface FutureDirection {
  topic: string
  rationale: string
  challenges: string[]
}

export interface SearchAnalysis {
  research_background: string
  current_hotspots: Hotspot[]
  main_findings: string[]
  experimental_methods: ExperimentalMethod[]
  future_directions: FutureDirection[]
  model_used: string
}

export interface SearchOut {
  id: number
  query_text: string
  pubmed_query: string
  search_mode: string
  sort_by: string
  max_results: number
  total_found: number
  status: string
  error_message: string
  created_at: string
  articles: Article[]
  analysis: SearchAnalysis | null
}

export interface SearchListItem {
  id: number
  query_text: string
  status: string
  total_found: number
  created_at: string
}

export interface RagQueryIn {
  query: string
  top_k: number
  language: Language
}

export interface RagSource {
  pmid: string
  title: string
  relevance_score: number
}

export interface RagQueryOut {
  answer: string
  sources: RagSource[]
}

export interface HealthResponse {
  status: string
  app_name: string
  app_version: string
}

export interface TranslateIn {
  text: string
  target_language: Language
}

export interface TranslateOut {
  translated_text: string
  model_used: string
}

// Knowledge graph (Neo4j)
export interface GraphStats {
  ready: boolean
  papers: number
  authors: number
  journals: number
  error: string
}

export interface RelatedPaper {
  pmid: string
  title: string
  overlap: number
}

export interface RelatedPapersOut {
  pmid: string
  related: RelatedPaper[]
}

// Personal library (localStorage-backed favorites)
export interface SavedArticle {
  pmid: string
  title: string
  abstract: string
  doi: string
  authors: Author[]
  journal: string
  publish_date: string
  publication_type: string
  impact_factor?: number | null
  saved_at: string
}

// Research dashboard aggregation (GET /search/stats)
export interface JournalStat {
  name: string
  count: number
}

export interface YearStat {
  year: number
  count: number
}

export interface ImpactFactorBucket {
  bucket: string
  count: number
}

export interface KeywordStat {
  keyword: string
  count: number
}

export interface DashboardStats {
  total_searches: number
  total_articles: number
  journals: JournalStat[]
  years: YearStat[]
  impact_factor_buckets: ImpactFactorBucket[]
  top_keywords: KeywordStat[]
  excluded_keywords: string[]
}

// Knowledge graph subgraph (visualization)
export interface GraphNode {
  id: string
  type: string
  label: string
  pmid: string
}

export interface GraphLink {
  source: string
  target: string
  type: string
}

export interface GraphSubgraph {
  pmid: string
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface KeywordActionOut {
  excluded_keywords: string[]
}
