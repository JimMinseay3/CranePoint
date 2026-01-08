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
            <button 
              @click="exportData"
              class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-foreground/5 hover:bg-foreground/10 border border-thin rounded-lg transition-all active:scale-95 shadow-sm text-sm font-medium whitespace-nowrap"
            >
              <Save class="w-4 h-4" />
              <span>另存为</span>
            </button>
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
            <label class="flex items-center gap-2 px-3 py-1.5 bg-background border border-thin rounded-md cursor-pointer hover:bg-foreground/[0.02] transition-colors group">
              <input 
                type="checkbox" 
                v-model="filters.onlyIndividualStocks"
                class="w-4 h-4 rounded border-thin text-primary focus:ring-primary"
              />
              <span class="text-sm font-medium text-foreground/70 group-hover:text-foreground">仅看个股 (排除北交所/转债/退市)</span>
            </label>
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
      <div class="overflow-auto flex-1 custom-scrollbar">
        <table class="w-full min-w-[2000px] border-collapse text-left text-sm table-fixed">
          <thead class="sticky top-0 bg-background/95 backdrop-blur-md z-30 border-b border-thin">
            <tr>
              <th 
                v-for="header in headers" 
                :key="header.key" 
                @click="toggleSort(header.key)"
                class="px-4 py-3.5 font-semibold text-foreground/60 border-r border-thin last:border-r-0 whitespace-nowrap bg-background cursor-pointer hover:bg-foreground/[0.05] transition-colors group/th"
                :class="{ 
                  'sticky left-0 z-50': header.key === 'code',
                  'sticky left-[100px] z-50': header.key === 'name',
                  'sticky left-[220px] z-50': header.key === 'price',
                  'sticky left-[320px] z-50': header.key === 'change',
                  'shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]': header.key === 'change'
                }"
                :style="{ width: header.width }"
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
            <tr 
              v-for="(row, index) in filteredStocks" 
              :key="row.code" 
              class="hover:bg-foreground/[0.03] transition-colors group"
              :class="{ 'bg-foreground/[0.01]': index % 2 === 0 }"
            >
              <!-- 代码列 - 固定 (强制实色背景) -->
              <td class="px-4 py-3 border-r border-thin font-mono text-primary/80 sticky left-0 z-10 bg-background group-hover:bg-muted/50">{{ row.code }}</td>
              
              <!-- 名称列 - 固定 (强制实色背景) -->
              <td class="px-4 py-3 border-r border-thin font-medium sticky left-[100px] z-10 bg-background group-hover:bg-muted/50">{{ row.name }}</td>
              
              <!-- 最新价列 - 固定 (强制实色背景) -->
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums sticky left-[220px] z-10 bg-background group-hover:bg-muted/50" :class="getPriceColor(row.change)">{{ row.price.toFixed(2) }}</td>
              
              <!-- 涨跌幅列 - 固定 (强制实色背景) -->
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums sticky left-[320px] z-10 bg-background group-hover:bg-muted/50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]" :class="getPriceColor(row.change)">{{ (row.change > 0 ? '+' : '') + row.change.toFixed(2) }}%</td>
              
              <!-- 动态指标列 -->
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.speed)">{{ (row.speed > 0 ? '+' : '') + row.speed.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.volume_ratio.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.turnover.toFixed(2) }}%</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.pe_dynamic === 0 ? '--' : row.pe_dynamic.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.pe_static === 0 ? '--' : row.pe_static.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.pb.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.market_cap) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.circulating_market_cap) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.main_inflow)">{{ formatNumber(row.main_inflow) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.main_inflow_ratio)">{{ row.main_inflow_ratio.toFixed(2) }}%</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.change_60d)">{{ (row.change_60d > 0 ? '+' : '') + row.change_60d.toFixed(2) }}%</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.change_ytd)">{{ (row.change_ytd > 0 ? '+' : '') + row.change_ytd.toFixed(2) }}%</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.amplitude.toFixed(2) }}%</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.volume) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ formatNumber(row.amount) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.price - row.open)">{{ row.high.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums" :class="getPriceColor(row.price - row.open)">{{ row.low.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70">{{ row.open.toFixed(2) }}</td>
              <td class="px-4 py-3 border-r border-thin text-right font-mono tabular-nums text-foreground/70 border-r-0">{{ row.prevClose.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, RotateCw, Save, AlertCircle, X, ChevronUp, ChevronDown, ListFilter, LineChart, Clock } from 'lucide-vue-next'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { marketStore } from '../store/market'

const searchQuery = ref('')
const isRefreshing = ref(false)
const progress = ref(0)
const errorMessage = ref('')
const showFilters = ref(false)

const stocks = ref<any[]>([])

// 筛选状态
const filters = ref({
  minPrice: null as number | null,
  maxPrice: null as number | null,
  minChange: null as number | null,
  maxChange: null as number | null,
  onlyIndividualStocks: true // 默认开启“仅看个股”
})

// 定义表格列
const headers = [
  { key: 'code', label: '代码', width: '100px' },
  { key: 'name', label: '名称', width: '120px' },
  { key: 'price', label: '最新价', width: '100px' },
  { key: 'change', label: '涨跌幅', width: '100px' },
  { key: 'speed', label: '涨速', width: '80px' },
  { key: 'volume_ratio', label: '量比', width: '80px' },
  { key: 'turnover', label: '换手率', width: '100px' },
  { key: 'pe_dynamic', label: '市盈率(动)', width: '110px' },
  { key: 'pe_static', label: '市盈率(静)', width: '110px' },
  { key: 'pb', label: '市净率', width: '90px' },
  { key: 'market_cap', label: '总市值', width: '120px' },
  { key: 'circulating_market_cap', label: '流通市值', width: '120px' },
  { key: 'main_inflow', label: '主力净流入', width: '130px' },
  { key: 'main_inflow_ratio', label: '主力占比', width: '100px' },
  { key: 'change_60d', label: '60日涨跌', width: '100px' },
  { key: 'change_ytd', label: '今年涨跌', width: '100px' },
  { key: 'amplitude', label: '振幅', width: '90px' },
  { key: 'volume', label: '成交量', width: '110px' },
  { key: 'amount', label: '成交额', width: '110px' },
  { key: 'high', label: '最高', width: '90px' },
  { key: 'low', label: '最低', width: '90px' },
  { key: 'open', label: '今开', width: '90px' },
  { key: 'prevClose', label: '昨收', width: '90px' },
]

// 排序状态
const sortConfig = ref({
  key: '',
  order: 'none' as 'asc' | 'desc' | 'none'
})

const toggleSort = (key: string) => {
  if (sortConfig.value.key !== key) {
    sortConfig.value.key = key
    sortConfig.value.order = 'desc'
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

const filteredStocks = computed(() => {
  let result = [...stocks.value]

  // 1. 基础个股筛选 (排除北交所、转债、退市)
  if (filters.value.onlyIndividualStocks) {
    result = result.filter(stock => {
      const code = stock.code
      const name = stock.name
      
      // 排除北交所 (4或8开头)
      if (code.startsWith('4') || code.startsWith('8')) return false
      
      // 排除转债 (11或12开头，或者名字带"转")
      if (code.startsWith('11') || code.startsWith('12') || name.includes('转')) return false
      
      // 排除退市 (名字带"退")
      if (name.includes('退')) return false
      
      return true
    })
  }

  // 2. 搜索过滤
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
    maxChange: null,
    onlyIndividualStocks: true
  }
  searchQuery.value = ''
  sortConfig.value = { key: '', order: 'none' }
}

let unlisten: (() => void) | null = null

const fetchData = async () => {
  if (isRefreshing.value) return
  
  isRefreshing.value = true
  errorMessage.value = ''
  progress.value = 0
  
  try {
    const data = await invoke<any[]>('get_stock_data')
    stocks.value = data
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

onMounted(async () => {
  unlisten = await listen<number>('refresh-progress', (event) => {
    progress.value = event.payload
  })

  // 同步 store 中的数据到本地响应式变量
  if (marketStore.stocks.length > 0) {
    stocks.value = marketStore.stocks
  }
  // fetchData() 
})

onUnmounted(() => {
  if (unlisten) unlisten()
})

const refreshData = () => {
  fetchData()
}

const exportData = () => {
  // TODO: 实现导出功能
  alert('导出功能开发中...')
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
</script>

<style scoped>
@reference "../styles.css";

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
