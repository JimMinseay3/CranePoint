<script setup lang="ts">
import { ref } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import { 
  Filter, 
  Search, 
  Zap, 
  Target,
  History
} from 'lucide-vue-next'

const activeCategory = ref('strategy')

const menuItems = [
  { id: 'strategy', name: '策略选股', icon: Target },
  { id: 'realtime', name: '实时监控', icon: Zap },
  { id: 'search', name: '条件搜索', icon: Search },
  { id: 'history', name: '筛选记录', icon: History }
]
</script>

<template>
  <SidebarLayout
    title="股票筛选"
    subtitle="多维因子选股，锁定核心标的"
    :icon="Filter"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <template #default="{ activeId }">
      <div v-if="activeId === 'strategy'" class="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto">
        <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary">
          <Target class="w-10 h-10" />
        </div>
        <h2 class="text-2xl font-semibold mb-2">策略选股</h2>
        <p class="text-foreground/50">
          内置经典价值投资、动能策略、技术指标等多种选股方案，支持自定义因子权重。
        </p>
      </div>
      <div v-else class="flex flex-col items-center justify-center h-full text-foreground/20">
        <Filter class="w-16 h-16 mb-4 opacity-10" />
        <p>筛选模块准备中...</p>
      </div>
    </template>
  </SidebarLayout>
</template>
