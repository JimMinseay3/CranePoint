<template>
  <div class="h-full flex flex-col p-6 overflow-hidden bg-background">
    <!-- 顶部标题栏 - 统一风格 -->
    <div class="flex-none mb-6">
      <div class="flex items-center gap-3 mb-1">
        <LineChart class="w-8 h-8 text-primary" />
        <h1 class="text-3xl font-semibold tracking-tight text-foreground">市场快照</h1>
      </div>
      <p class="text-sm text-foreground/50 ml-11 flex items-center gap-4">
        <span>沪深 A 股全量个股行情监控 (已过滤北交所/转债/退市)</span>
        <span v-if="marketStore.lastUpdated" class="flex items-center gap-1.5 text-xs bg-foreground/[0.03] px-2 py-0.5 rounded-full border border-thin">
          <Clock class="w-3 h-3" />
          上次更新: {{ new Date(marketStore.lastUpdated).toLocaleString() }}
        </span>
      </p>
    </div>

    <!-- 操作栏区域 -->
    <div class="flex-none flex flex-col gap-4 mb-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-1 w-full">
          <div class="relative flex-1 group min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40 group-focus-within:text-primary transition-colors" />
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索股票代码或名称..." 
              class="w-full bg-foreground/[0.03] border border-thin rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
            />
          </div>
          
          <!-- 筛选按钮 -->
          <button 
            @click="showFilters = !showFilters"
            class="flex items-center gap-2 px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-lg hover:bg-foreground/[0.06] transition-all text-sm font-medium"
            :class="{ 'bg-primary/10 border-primary/30 text-primary': showFilters }"
          >
            <ListFilter class="w-4 h-4" />
            <span>筛选</span>
          </button>
          
          <div class="flex items-center gap-2 sm:w-auto">
            <button 
              @click="refreshData"
              :disabled="isRefreshing"
              class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-primary/20 text-sm font-medium whitespace-nowrap"
            >
              <RotateCw class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" />
              <span>刷新</span>
            </button>
            <div class="relative">
              <button 
                @click="showExportMenu = !showExportMenu"
                class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-foreground/5 hover:bg-foreground/10 border border-thin rounded-lg transition-all active:scale-95 shadow-sm text-sm font-medium whitespace-nowrap"
              >
                <Save class="w-4 h-4" />
                <span>另存为</span>
              </button>
              
              <!-- 导出菜单 -->
              <div v-if="showExportMenu" class="absolute right-0 mt-2 w-48 bg-background border border-thin rounded-xl shadow-xl z-50 py-1 animate-in fade-in zoom-in-95 duration-200">
                <button @click="exportData('xlsx')" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors">
                  <FileSpreadsheet class="w-4 h-4 text-emerald-500" />
                  <span>Excel (.xlsx)</span>
                </button>
                <button @click="exportData('csv')" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors">
                  <FileTextIcon class="w-4 h-4 text-blue-500" />
                  <span>CSV (.csv)</span>
                </button>
                <button @click="exportData('pdf')" class="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors">
                  <FileJson class="w-4 h-4 text-red-500" />
                  <span>PDF (.pdf)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 高级筛选面板 -->
      <div v-if="showFilters" class="flex-none bg-foreground/[0.02] border border-thin rounded-xl p-4 mb-2 animate-in slide-in-from-top-2 duration-300">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="space-y-2">
            <label class="text-xs font-semibold text-foreground/50 uppercase tracking-wider">价格区间</label>
            <div class="flex items-center gap-2">
              <input v-model.number="filters.minPrice" type="number" placeholder="最小" class="w-full bg-background border border-thin rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              <span class="text-foreground/30">-</span>
              <input v-model.number="filters.maxPrice" type="number" placeholder="最大" class="w-full bg-background border border-thin rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-xs font-semibold text-foreground/50 uppercase tracking-wider">涨跌幅 (%)</label>
            <div class="flex items-center gap-2">
              <input v-model.number="filters.minChange" type="number" placeholder="最小" class="w-full bg-background border border-thin rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              <span class="text-foreground/30">-</span>
              <input v-model.number="filters.maxChange" type="number" placeholder="最大" class="w-full bg-background border border-thin rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
          </div>
          <div class="flex items-end gap-3 lg:col-span-2">
            <button @click="resetFilters" class="px-4 py-1.5 text-sm font-medium text-foreground/60 hover:text-foreground hover:bg-foreground/5 rounded-md transition-colors">
              重置全部
            </button>
          </div>
        </div>
      </div>

      <!-- 进度条 - 宽度跟随操作栏 -->
      <div v-if="isRefreshing" class="w-full animate-in fade-in slide-in-from-top-2 duration-300">
        <div class="flex items-center justify-between mb-1.5 px-1">
          <span class="text-xs font-medium text-primary flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
            正在同步 A 股实时行情...
          </span>
          <span class="text-xs font-bold text-primary font-mono">{{ progress }}%</span>
        </div>
        <div class="h-1 w-full bg-primary/10 rounded-full overflow-hidden border border-primary/5">
          <div 
            class="h-full bg-primary transition-all duration-300 ease-out shadow-[0_0_12px_rgba(var(--primary),0.3)]"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 错误信息提示 -->
    <div v-if="errorMessage" class="flex-none mb-4 animate-in slide-in-from-top-2 duration-300">
      <div class="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <AlertCircle class="w-5 h-5" />
          <p class="text-sm font-medium">{{ errorMessage }}</p>
        </div>
        <button @click="errorMessage = ''" class="hover:bg-destructive/10 p-1 rounded-md transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 数据展示区域 - 确保 flex-1 填满垂直剩余空间 -->
    <div class="flex-1 border border-thin rounded-xl overflow-hidden flex flex-col bg-card shadow-sm relative">
      <div 
        ref="scrollContainer"
        @scroll="onScroll"
        class="overflow-auto flex-1 custom-scrollbar"
      >
        <div :style="{ height: `${totalHeight}px`, position: 'relative' }">
          <table class="w-full min-w-max border-collapse text-left text-sm table-auto bg-background">
            <thead class="sticky top-0 bg-background/95 backdrop-blur-md z-40 border-b border-thin">
              <tr>
                <th 
                  v-for="header in headers" 
                  :key="header.key" 
                  @click="toggleSort(header.key)"
                  class="px-4 py-3.5 font-semibold border-r border-thin last:border-r-0 whitespace-nowrap bg-background cursor-pointer hover:bg-foreground/[0.05] transition-colors group/th"
                   :class="[
                     { 
                       'sticky left-0 z-50 shadow-[1px_0_0_0_rgba(var(--color-thin))]': header.key === 'code',
                       'sticky left-[100px] z-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]': header.key === 'name',
                     },
                     getGroupHeaderClass(header.group)
                   ]"
                  :style="{ minWidth: header.width }"
                >
                  <div class="flex items-center justify-between gap-2">
                    <span>{{ header.label }}</span>
                    <div class="flex flex-col opacity-0 group-hover/th:opacity-100 transition-opacity" :class="{ 'opacity-100': sortConfig.key === header.key }">
                      <ChevronUp class="w-3 h-3 -mb-1" :class="{ 'text-primary': sortConfig.key === header.key && sortConfig.order === 'asc' }" />
                      <ChevronDown class="w-3 h-3" :class="{ 'text-primary': sortConfig.key === header.key && sortConfig.order === 'desc' }" />
                    </div>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-thin">
              <!-- 顶部占位行 -->
              <tr :style="{ height: `${offsetY}px` }">
                <td :colspan="headers.length" class="p-0 border-0"></td>
              </tr>
              
              <!-- 实际数据行 -->
              <tr 
                v-for="(row, index) in visibleStocks" 
                :key="row.code" 
                class="hover:bg-foreground/[0.03] transition-colors group"
                :class="{ 'bg-foreground/[0.01]': (startIndex + index) % 2 === 0 }"
                :style="{ height: `${rowHeight}px` }"
              >
                <!-- 固定列：代码、名称 -->
                <td class="px-4 py-3 border-r border-thin text-blue-500 font-mono sticky left-0 z-10 bg-background group-hover:bg-foreground/[0.03] transition-colors shadow-[1px_0_0_0_rgba(var(--color-thin))]">{{ row.code }}</td>
                <td class="px-4 py-3 border-r border-thin font-medium sticky left-[100px] z-10 bg-background group-hover:bg-foreground/[0.03] transition-colors shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">{{ row.name }}</td>

                <!-- 动态指标列 -->
                <!-- 动能组 -->
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="[getPriceColor(row.price - row.prevClose), getPriceUnderlineClass(row)]">{{ row.price.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.change)">{{ (row.change > 0 ? '+' : '') + row.change.toFixed(2) }}%</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.speed)">{{ (row.speed > 0 ? '+' : '') + row.speed.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.volume_ratio.toFixed(2) }}</td>

                <!-- 量能组 -->
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.volume) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.amount) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.turnover_actual.toFixed(2) }}%</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.turnover.toFixed(2) }}%</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-[#EA4335] font-bold">{{ row.limit_up > 0 ? row.limit_up.toFixed(2) : '--' }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-emerald-500 font-bold">{{ row.limit_down > 0 ? row.limit_down.toFixed(2) : '--' }}</td>

                <!-- 空间组 -->
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.amplitude.toFixed(2) }}%</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.high - row.prevClose)">{{ row.high.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.low - row.prevClose)">{{ row.low.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.open.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.prevClose.toFixed(2) }}</td>

                <!-- 基本面组 -->
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.market_cap) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.circulating_market_cap) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.total_shares) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.circulating_shares) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.pe_static === 0 ? '--' : row.pe_static.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.pe_ttm === 0 ? '--' : row.pe_ttm.toFixed(2) }}</td>
                <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70 border-r-0">{{ row.pb.toFixed(2) }}</td>
              </tr>

              <!-- 底部占位行 -->
              <tr :style="{ height: `${Math.max(0, totalHeight - offsetY - (visibleStocks.length * rowHeight))}px` }">
                <td :colspan="headers.length" class="p-0 border-0"></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 无数据提示 -->
        <div v-if="filteredStocks.length === 0 && !isRefreshing" class="flex flex-col items-center justify-center py-20 text-foreground/30">
          <Search class="w-12 h-12 mb-4 opacity-20" />
          <p class="text-lg">未找到匹配的股票数据</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Search, RotateCw, Save, AlertCircle, X, ChevronUp, ChevronDown, ListFilter, Clock, FileSpreadsheet, FileText as FileTextIcon, FileJson, LineChart } from 'lucide-vue-next'
import { save } from '@tauri-apps/plugin-dialog'
import { writeFile } from '@tauri-apps/plugin-fs'
import { marketStore } from '../store/market'

const route = useRoute()
const searchQuery = ref('')
const isRefreshing = ref(false)
const progress = ref(0)
const errorMessage = ref('')
const showFilters = ref(false)
const showExportMenu = ref(false)

const stocks = computed(() => marketStore.stocks)

// --- 虚拟滚动逻辑开始 ---
const scrollContainer = ref<HTMLElement | null>(null)
const scrollTop = ref(0)
const containerHeight = ref(800) // 提高默认初始值，防止初次渲染空白
const rowHeight = 45
const bufferCount = 10

const onScroll = (e: Event) => {
  scrollTop.value = (e.target as HTMLElement).scrollTop
}

const totalHeight = computed(() => {
  return filteredStocks.value.length * rowHeight
})

const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / rowHeight) - bufferCount)
})

const endIndex = computed(() => {
  const count = Math.ceil(containerHeight.value / rowHeight) + bufferCount * 2
  return Math.min(
    filteredStocks.value.length,
    startIndex.value + count
  )
})

const visibleStocks = computed(() => {
  const result = filteredStocks.value.slice(startIndex.value, endIndex.value)
  // 安全保障：如果计算结果为空但实际有数据，返回首屏数据
  if (result.length === 0 && filteredStocks.value.length > 0) {
    return filteredStocks.value.slice(0, bufferCount * 2)
  }
  return result
})

const offsetY = computed(() => {
  return startIndex.value * rowHeight
})

// 监听容器高度变化
let resizeObserver: ResizeObserver | null = null
let unlisten: (() => void) | null = null

const updateContainerHeight = () => {
  if (scrollContainer.value) {
    const height = scrollContainer.value.clientHeight
    if (height > 0) {
      containerHeight.value = height
    }
  }
}

onMounted(async () => {
  if (route.query.search) {
    searchQuery.value = route.query.search as string
  }

  // 0. 重置滚动位置
  scrollTop.value = 0
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
  }
  
  // 1. 初始化虚拟滚动容器高度监听
  await nextTick()
  updateContainerHeight()
  
  // 即使 nextTick 没拿到，也要在短时间后再试一次
  setTimeout(updateContainerHeight, 100)
  setTimeout(updateContainerHeight, 500)
  
  if (scrollContainer.value) {
    resizeObserver = new ResizeObserver((entries) => {
      if (entries[0]) {
        const newHeight = entries[0].contentRect.height
        if (newHeight > 0) {
          containerHeight.value = newHeight
        }
      }
    })
    resizeObserver.observe(scrollContainer.value)
  }

  // 2. 监听 Tauri 后端进度事件
  try {
    const { listen } = await import('@tauri-apps/api/event')
    unlisten = await listen<number>('refresh-progress', (event) => {
      progress.value = event.payload
    })
  } catch (e) {
    console.warn('Tauri event listener not available')
  }

  // 3. 数据初始化：如果没有数据则自动刷新
  if (stocks.value.length === 0) {
    refreshData()
  }
})

onUnmounted(() => {
  if (unlisten) unlisten()
  if (resizeObserver) resizeObserver.disconnect()
})
// --- 虚拟滚动逻辑结束 ---

// 筛选状态
const filters = ref({
  minPrice: null as number | null,
  maxPrice: null as number | null,
  minChange: null as number | null,
  maxChange: null as number | null
})

// 定义表格列
const headers = [
  // 核心组
  { key: 'code', label: '代码', width: '100px', group: 'core' },
  { key: 'name', label: '名称', width: '120px', group: 'core' },
  // 动能组
  { key: 'price', label: '最新价', width: '100px', group: 'momentum' },
  { key: 'change', label: '涨跌幅', width: '100px', group: 'momentum' },
  { key: 'speed', label: '涨速', width: '80px', group: 'momentum' },
  { key: 'volume_ratio', label: '量比', width: '80px', group: 'momentum' },
  // 量能组
  { key: 'volume', label: '成交量', width: '110px', group: 'volume' },
  { key: 'amount', label: '成交额', width: '110px', group: 'volume' },
  { key: 'turnover_actual', label: '换手(实)', width: '100px', group: 'volume' },
  { key: 'turnover', label: '换手率', width: '100px', group: 'volume' },
  { key: 'limit_up', label: '涨停', width: '110px', group: 'volume' },
  { key: 'limit_down', label: '跌停', width: '110px', group: 'volume' },
  // 空间组
  { key: 'amplitude', label: '振幅', width: '90px', group: 'space' },
  { key: 'high', label: '最高', width: '90px', group: 'space' },
  { key: 'low', label: '最低', width: '90px', group: 'space' },
  { key: 'open', label: '今开', width: '90px', group: 'space' },
  { key: 'prevClose', label: '昨收', width: '90px', group: 'space' },
  // 基本面组
  { key: 'market_cap', label: '总市值', width: '120px', group: 'fundamental' },
  { key: 'circulating_market_cap', label: '流通市值', width: '120px', group: 'fundamental' },
  { key: 'total_shares', label: '总股本', width: '120px', group: 'fundamental' },
  { key: 'circulating_shares', label: '流通股', width: '120px', group: 'fundamental' },
  { key: 'pe_static', label: '市盈(静)', width: '110px', group: 'fundamental' },
  { key: 'pe_ttm', label: '市盈(TTM)', width: '110px', group: 'fundamental' },
  { key: 'pb', label: '市净率', width: '90px', group: 'fundamental' },
]

// 获取分组颜色的工具函数
const getGroupHeaderClass = (group: string) => {
  switch (group) {
    case 'core': return 'text-primary font-bold'
    case 'momentum': return 'text-orange-500/80'
    case 'volume': return 'text-blue-500/80'
    case 'space': return 'text-purple-500/80'
    case 'fundamental': return 'text-emerald-500/80'
    default: return 'text-foreground/40'
  }
}

// 排序状态
const sortConfig = ref({
  key: '',
  order: 'none' as 'asc' | 'desc' | 'none'
})

const toggleSort = (key: string) => {
  if (sortConfig.value.key !== key) {
    sortConfig.value.order = 'desc'
    sortConfig.value.key = key
  } else {
    if (sortConfig.value.order === 'desc') {
      sortConfig.value.order = 'asc'
    } else if (sortConfig.value.order === 'asc') {
      sortConfig.value.order = 'none'
      sortConfig.value.key = ''
    } else {
      sortConfig.value.order = 'desc'
    }
  }
}

// 当搜索或筛选条件变化时，重置滚动位置
watch([searchQuery, filters, () => sortConfig.value.key, () => sortConfig.value.order], () => {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0
    scrollTop.value = 0
  }
})

const filteredStocks = computed(() => {
  let result = [...stocks.value]

  // 1. 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.code.includes(query) || s.name.toLowerCase().includes(query)
    )
  }

  // 2. 多重区间过滤
  if (filters.value.minPrice !== null) result = result.filter(s => s.price >= (filters.value.minPrice || 0))
  if (filters.value.maxPrice !== null) result = result.filter(s => s.price <= (filters.value.maxPrice || Infinity))
  if (filters.value.minChange !== null) result = result.filter(s => s.change >= (filters.value.minChange || -100))
  if (filters.value.maxChange !== null) result = result.filter(s => s.change <= (filters.value.maxChange || 100))

  // 3. 排序逻辑
  if (sortConfig.value.key && sortConfig.value.order !== 'none') {
    const { key, order } = sortConfig.value
    result.sort((a, b) => {
      let valA = a[key]
      let valB = b[key]
      
      // 处理数值和字符串
      if (typeof valA === 'string') {
        return order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
      }
      
      return order === 'asc' ? valA - valB : valB - valA
    })
  }

  return result
})

const resetFilters = () => {
  filters.value = {
    minPrice: null,
    maxPrice: null,
    minChange: null,
    maxChange: null
  }
  searchQuery.value = ''
  sortConfig.value = { key: '', order: 'none' }
}

const fetchData = async () => {
  if (isRefreshing.value) return
  
  isRefreshing.value = true
  errorMessage.value = ''
  progress.value = 0
  
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const data = await invoke<any[]>('get_stock_data')
    // 更新全局 store
    marketStore.stocks = data
    marketStore.lastUpdated = Date.now()
  } catch (err: any) {
    console.error('获取数据失败:', err)
    errorMessage.value = err.toString()
  } finally {
    isRefreshing.value = false
    progress.value = 0
  }
}


const refreshData = () => {
  fetchData()
}

const exportData = async (format: string) => {
  showExportMenu.value = false
  
  if (filteredStocks.value.length === 0) {
    errorMessage.value = '没有可导出的数据'
    return
  }

  try {
    const defaultPath = localStorage.getItem('dataPath') || 'D:\\CranePoint_Data'
    const fileName = `市场快照_${new Date().toISOString().replace(/[:.]/g, '-')}.${format}`
    
    // 调用 Tauri 保存对话框
    const filePath = await save({
      defaultPath: `${defaultPath}\\${fileName}`,
      filters: [{
        name: format.toUpperCase(),
        extensions: [format]
      }]
    })

    if (!filePath) return

    isRefreshing.value = true
    progress.value = 10
    
    // 准备数据
    const exportHeaders = headers.map(h => h.label).join(',')
    const exportRows = filteredStocks.value.map(stock => {
      return headers.map(h => {
        const val = stock[h.key]
        return typeof val === 'number' ? val.toString() : `"${val}"`
      }).join(',')
    }).join('\n')
    
    const content = `${exportHeaders}\n${exportRows}`
    
    // 如果是 CSV，直接写入 UTF-8 with BOM 以支持 Excel 中文
    if (format === 'csv') {
      const encoder = new TextEncoder()
      const bom = new Uint8Array([0xEF, 0xBB, 0xBF])
      const data = encoder.encode(content)
      const fullData = new Uint8Array(bom.length + data.length)
      fullData.set(bom)
      fullData.set(data, bom.length)
      await writeFile(filePath, fullData)
    } else {
      // 其他格式暂时作为文本导出（PDF/XLSX 需要更复杂的库，此处先实装 CSV 的逻辑框架）
      // 在实际生产中，PDF 和 XLSX 通常通过后端生成或专门的 JS 库
      const encoder = new TextEncoder()
      await writeFile(filePath, encoder.encode(content))
    }
    
    progress.value = 100
    setTimeout(() => {
      isRefreshing.value = false
      progress.value = 0
    }, 1000)
    
    alert(`文件已成功保存至: ${filePath}`)
  } catch (err: any) {
    console.error('导出失败:', err)
    errorMessage.value = `导出失败: ${err.message}`
    isRefreshing.value = false
  }
}

// 数值格式化工具
const formatNumber = (val: any, decimals: number = 2, unit: string = '') => {
  if (val === undefined || val === null || val === '--' || isNaN(parseFloat(val))) return '--'
  const num = parseFloat(val)
  
  // 处理大数字单位
  if (Math.abs(num) >= 100000000) {
    return (num / 100000000).toFixed(decimals) + '亿'
  } else if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(decimals) + '万'
  }
  
  return num.toFixed(decimals) + unit
}

// 颜色工具
const getPriceColor = (val: any) => {
  const num = parseFloat(val)
  if (isNaN(num) || num === 0) return 'text-foreground/60'
  return num > 0 ? 'text-[#EA4335]' : 'text-[#34A853]' // 使用 Google 风格的红绿
}

const getPriceUnderlineClass = (row: any) => {
  if (row.limit_up > 0 && row.price >= row.limit_up) {
    return 'underline decoration-2 decoration-[#EA4335] underline-offset-4'
  }
  if (row.limit_down > 0 && row.price <= row.limit_down) {
    return 'underline decoration-2 decoration-[#34A853] underline-offset-4'
  }
  return ''
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: color-mix(in srgb, var(--color-foreground) 10%, transparent);
  border-radius: 9999px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: color-mix(in srgb, var(--color-foreground) 20%, transparent);
}
</style>
