<template>
  <div class="search-view">
    <el-card shadow="never" class="query-card">
      <template #header>
        <div class="query-head">
          <span class="query-title">PubMed Research Agent</span>
          <span class="query-sub">输入研究问题，AI 自动检索并生成综述报告</span>
        </div>
      </template>

      <div class="query-row">
        <el-input
          v-model="store.query"
          size="large"
          placeholder='例如：SEC61G in Lung Cancer'
          clearable
          @keyup.enter="store.run()"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button
          type="primary"
          size="large"
          :loading="store.loading"
          @click="store.run()"
        >
          {{ store.loading ? '分析中…' : '开始检索' }}
        </el-button>
      </div>

      <div class="options-row">
        <span class="opt-label">检索方式</span>
        <el-radio-group v-model="store.searchMode" size="small">
          <el-radio-button value="advanced">高级检索</el-radio-button>
          <el-radio-button value="keyword">关键词检索</el-radio-button>
        </el-radio-group>
        <span class="opt-label" style="margin-left: 20px">排序</span>
        <el-select v-model="store.sortBy" size="small" style="width: 120px">
          <el-option value="relevance" label="相关度" />
          <el-option value="date_desc" label="最新优先" />
          <el-option value="date_asc" label="最早优先" />
        </el-select>
        <span class="opt-label" style="margin-left: 20px">输出语言</span>
        <el-radio-group v-model="store.language" size="small">
          <el-radio-button value="en">English</el-radio-button>
          <el-radio-button value="zh">中文</el-radio-button>
        </el-radio-group>
        <span class="opt-label" style="margin-left: 20px">Top N</span>
        <el-select v-model="store.maxResults" size="small" style="width: 100px">
          <el-option v-for="n in [5, 10, 20, 30]" :key="n" :value="n" :label="`${n} 篇`" />
        </el-select>
      </div>

      <div class="options-row">
        <span class="opt-label">筛选</span>
        <span class="opt-label">年份</span>
        <el-input-number
          v-model="store.minYear"
          :min="1900"
          :max="2100"
          :controls="false"
          size="small"
          placeholder="起始"
          style="width: 90px"
        />
        <span class="opt-label" style="margin: 0 6px">—</span>
        <el-input-number
          v-model="store.maxYear"
          :min="1900"
          :max="2100"
          :controls="false"
          size="small"
          placeholder="结束"
          style="width: 90px"
        />
        <span class="opt-label" style="margin-left: 16px">影响因子 ≥</span>
        <el-input-number
          v-model="store.minImpactFactor"
          :min="0"
          :max="100"
          :step="0.5"
          :controls="false"
          size="small"
          placeholder="如 5.0"
          style="width: 100px"
        />
        <el-button size="small" text type="primary" @click="clearFilters">清除筛选</el-button>
        <span class="hint-text">中文输入会自动翻译为英文检索；影响因子基于内置期刊表</span>
      </div>
    </el-card>

    <template v-if="store.result">
      <el-card shadow="never" class="result-card">
        <template #header>
          <div class="result-head">
            <span class="result-title">检索结果</span>
                        <span class="result-meta">
              状态：{{ store.result.status }} ｜命中：{{ store.result.total_found }} 篇 ｜
              方式：{{ store.result.search_mode === 'keyword' ? '关键词检索' : '高级检索' }} ｜
              排序：{{ sortLabel }} ｜
              检索式：<code>{{ store.result.pubmed_query || '-' }}</code>
            </span>
          </div>
        </template>
        <ArticleList :articles="store.result.articles" />
      </el-card>

      <SummaryReport :result="store.result" />
    </template>

    <el-empty
      v-else-if="!store.loading"
      description="输入研究问题并点击「开始检索」"
      class="welcome-empty"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSearchStore } from '@/stores/search'
import ArticleList from '@/components/ArticleList.vue'
import SummaryReport from '@/components/SummaryReport.vue'

const store = useSearchStore()

const sortLabel = computed(() => {
  const map: Record<string, string> = {
    relevance: '相关度',
    date_desc: '最新优先',
    date_asc: '最早优先'
  }
  return map[store.result?.sort_by || 'relevance'] || '相关度'
})

function clearFilters(): void {
  store.minYear = null
  store.maxYear = null
  store.minImpactFactor = null
}

onMounted(() => {
  store.refreshHistory()
})
</script>

<style scoped>
.query-card {
  margin-bottom: 16px;
}
.query-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.query-title {
  font-size: 18px;
  font-weight: 700;
}
.query-sub {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.query-row {
  display: flex;
  gap: 12px;
}
.options-row {
  display: flex;
  align-items: center;
  margin-top: 12px;
}
.opt-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-right: 8px;
}
.result-card {
  margin-bottom: 16px;
}
.result-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.result-title {
  font-weight: 600;
}
.result-meta {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.welcome-empty {
  padding-top: 40px;
}
.hint-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 12px;
}
</style>
