<template>
  <div class="graph-view">
    <el-card shadow="never" class="stats-card">
      <template #header>
        <div class="head">
          <span class="page-title">知识图谱</span>
          <el-tag v-if="stats" :type="stats.ready ? 'success' : 'danger'" size="small">
            {{ stats.ready ? 'Neo4j 已连接' : 'Neo4j 未连接' }}
          </el-tag>
        </div>
      </template>

      <div class="stat-grid">
        <div class="stat-item">
          <div class="num">{{ stats ? stats.papers : '-' }}</div>
          <div class="label">文献节点</div>
        </div>
        <div class="stat-item">
          <div class="num">{{ stats ? stats.authors : '-' }}</div>
          <div class="label">作者节点</div>
        </div>
        <div class="stat-item">
          <div class="num">{{ stats ? stats.journals : '-' }}</div>
          <div class="label">期刊节点</div>
        </div>
      </div>

      <el-alert
        v-if="stats && !stats.ready"
        type="warning"
        :closable="false"
        :title="stats.error || 'Neo4j 不可用'"
        class="error-alert"
      />
      <p class="hint">
        图谱由已检索的文献自动构建：节点代表文献 / 作者 / 期刊，边代表作者关系（AUTHORED）与期刊归属（PUBLISHED_IN）。
      </p>
    </el-card>

    <el-card shadow="never" class="explore-card">
      <template #header><span class="page-title">关联文献探索</span></template>
      <div class="explore-row">
        <el-input
          v-model="pmid"
          placeholder="输入 PMID，例如 39990664"
          clearable
          size="large"
          style="max-width: 320px"
          @keyup.enter="explore()"
        />
        <el-button type="primary" size="large" :loading="loading" @click="explore()">查询关联</el-button>
      </div>
      <el-alert v-if="error" type="error" :closable="false" :title="error" class="error-alert" />

      <template v-if="subgraph && subgraph.nodes.length">
        <GraphCanvas
          :nodes="subgraph.nodes"
          :links="subgraph.links"
          :center-id="`paper:${subgraph.pmid}`"
          @select="explore"
        />
        <h4 class="sub-title">关联文献列表（{{ related.length }}）</h4>
        <el-table v-if="related.length" :data="related" stripe class="related-table">
          <el-table-column label="PMID" width="120">
            <template #default="{ row }">
              <el-link type="primary" @click="jump(row.pmid)">{{ row.pmid }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="320" show-overflow-tooltip />
          <el-table-column prop="overlap" label="共现数" width="100" align="center" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-link type="primary" @click="jump(row.pmid)">继续延伸</el-link>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无关联文献（该文献尚未与其他文献共享作者/期刊）" />
      </template>
      <el-empty
        v-else-if="!loading && explored"
        description="该 PMID 暂无图谱数据（请先完成一次检索并确认 Neo4j 已连接）"
      />
      <el-empty v-else-if="!loading" description="输入 PMID 查询共享作者 / 期刊的关联文献" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getGraphStats, getRelatedPapers, getSubgraph } from '@/api/graph'
import { notifyError } from '@/api/http'
import GraphCanvas from '@/components/GraphCanvas.vue'
import type { GraphStats, GraphSubgraph, RelatedPaper } from '@/types'

const stats = ref<GraphStats | null>(null)
const pmid = ref('')
const subgraph = ref<GraphSubgraph | null>(null)
const related = ref<RelatedPaper[]>([])
const loading = ref(false)
const explored = ref(false)
const error = ref('')

async function loadStats(): Promise<void> {
  try {
    stats.value = await getGraphStats()
  } catch (err) {
    notifyError(err)
  }
}

async function explore(target?: string): Promise<void> {
  const id = (target ?? pmid.value).trim()
  if (!id || loading.value) return
  if (target) pmid.value = id
  loading.value = true
  explored.value = true
  error.value = ''
  subgraph.value = null
  related.value = []
  try {
    const [sg, rel] = await Promise.all([getSubgraph(id, 20), getRelatedPapers(id, 20)])
    subgraph.value = sg
    related.value = rel.related
  } catch (err) {
    error.value = err instanceof Error ? err.message : '关联文献查询失败'
    notifyError(err)
  } finally {
    loading.value = false
  }
}

function jump(id: string): void {
  void explore(id)
}

onMounted(loadStats)
</script>

<style scoped>
.stats-card {
  margin-bottom: 16px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-title {
  font-weight: 600;
}
.stat-grid {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}
.stat-item {
  flex: 1;
  text-align: center;
  padding: 16px 0;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}
.num {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary);
}
.label {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.hint {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.7;
}
.error-alert {
  margin-bottom: 12px;
}
.explore-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.sub-title {
  margin: 18px 0 10px;
  font-weight: 600;
}
.related-table {
  margin-top: 4px;
}
</style>
