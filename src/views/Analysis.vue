<script setup lang="ts">
import { ref } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import { 
  LineChart, 
  Layers,
  Info
} from 'lucide-vue-next'

const activeCategory = ref('placeholder')

const menuItems = [
  { id: 'placeholder', name: '更多分析模块', icon: Layers }
]
</script>

<template>
  <SidebarLayout
    title="数据分析"
    subtitle="深度量化分析与多维数据洞察"
    :icon="LineChart"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <template #default="{ activeId }">
      <div v-if="activeId === 'placeholder'" class="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto p-8">
        <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary">
          <Info class="w-10 h-10" />
        </div>
        <h2 class="text-2xl font-semibold mb-2">深度分析模块升级中</h2>
        <p class="text-foreground/50 mb-8">
          为了提供更流畅的使用体验，原有的个股分析功能已整合至「个股数据」栏目。
          此处将用于承载未来的进阶量化策略分析、行业对比及宏观数据洞察模块。
        </p>
        <div class="grid grid-cols-2 gap-4 w-full">
          <div class="p-4 bg-foreground/5 border border-foreground/10 rounded-2xl text-left">
            <div class="font-medium mb-1">多因子回测</div>
            <div class="text-xs text-foreground/30">自定义选股策略回测引擎</div>
          </div>
          <div class="p-4 bg-foreground/5 border border-foreground/10 rounded-2xl text-left">
            <div class="font-medium mb-1">行业图谱</div>
            <div class="text-xs text-foreground/30">产业链上下游关联度分析</div>
          </div>
        </div>
      </div>
    </template>
  </SidebarLayout>
</template>
