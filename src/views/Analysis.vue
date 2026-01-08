<script setup lang="ts">
import { ref } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import { 
  LineChart, 
  PieChart, 
  TrendingUp, 
  BarChart2,
  BrainCircuit
} from 'lucide-vue-next'

const activeCategory = ref('trend')

const menuItems = [
  { id: 'trend', name: '趋势分析', icon: TrendingUp },
  { id: 'structure', name: '持仓结构', icon: PieChart },
  { id: 'compare', name: '对比工具', icon: BarChart2 },
  { id: 'ai', name: '智能诊断', icon: BrainCircuit, disabled: true }
]
</script>

<template>
  <SidebarLayout
    title="数据分析"
    subtitle="深度挖掘市场数据价值"
    :icon="LineChart"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <template #default="{ activeId }">
      <div v-if="activeId === 'trend'" class="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto">
        <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary">
          <TrendingUp class="w-10 h-10" />
        </div>
        <h2 class="text-2xl font-semibold mb-2">趋势分析</h2>
        <p class="text-foreground/50">
          基于历史 K 线与成交量数据，通过量化指标自动识别股价运行趋势。
        </p>
      </div>
      <div v-else class="flex flex-col items-center justify-center h-full text-foreground/20">
        <LineChart class="w-16 h-16 mb-4 opacity-10" />
        <p>分析模块准备中...</p>
      </div>
    </template>
  </SidebarLayout>
</template>
