<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SidebarLayout from '../components/SidebarLayout.vue'
import { marketStore } from '../store/market'
import { 
  Filter, 
  Search, 
  Target,
  History,
  TrendingUp,
  Award,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
  Info,
  X,
  Play,
  RotateCcw,
  Clock,
  Trash2,
  Loader2,
  AlertCircle
} from 'lucide-vue-next'

const router = useRouter()
const activeCategory = ref('strategy')
const selectedStrategy = ref<string | null>(null)
const isScreening = ref(false)

// 策略诊断逻辑
const strategyDiagnostics = computed(() => {
  if (!selectedStrategy.value || activeCategory.value !== 'results') return null
  
  const allStocks = marketStore.stocks
  if (!allStocks || allStocks.length === 0) return null
  const stats = {
    total: allStocks.length,
    conditions: [] as { label: string, count: number, pass: boolean }[]
  }

  if (selectedStrategy.value === 'buffett') {
    stats.conditions = [
      { label: 'PE(TTM) 5-20', count: allStocks.filter(s => { const v = Number(s.pe_ttm) || 0; return v > 5 && v < 20 }).length, pass: false },
      { label: 'PB 0-3', count: allStocks.filter(s => { const v = Number(s.pb) || 0; return v > 0 && v < 3 }).length, pass: false },
      { label: '市值 > 500亿', count: allStocks.filter(s => (Number(s.market_cap) || 0) > 50000000000).length, pass: false },
      { label: '今日主力净流入', count: allStocks.filter(s => (Number(s.main_inflow) || 0) > 0).length, pass: false }
    ]
  } else if (selectedStrategy.value === 'growth') {
    stats.conditions = [
      { label: '年内涨幅 > 20%', count: allStocks.filter(s => (Number(s.change_ytd) || 0) > 20).length, pass: false },
      { label: '换手率 > 3%', count: allStocks.filter(s => (Number(s.turnover) || 0) > 3).length, pass: false },
      { label: '今日涨幅 > 2%', count: allStocks.filter(s => (Number(s.change) || 0) > 2).length, pass: false },
      { label: '主力流入占比 > 5%', count: allStocks.filter(s => (Number(s.main_inflow_ratio) || 0) > 5).length, pass: false }
    ]
  } else if (selectedStrategy.value === 'safe') {
    stats.conditions = [
      { label: 'PE(TTM) < 12', count: allStocks.filter(s => { const v = Number(s.pe_ttm) || 0; return v > 0 && v < 12 }).length, pass: false },
      { label: '振幅 < 3%', count: allStocks.filter(s => (Number(s.amplitude) || 0) < 3).length, pass: false },
      { label: '市值 > 200亿', count: allStocks.filter(s => (Number(s.market_cap) || 0) > 20000000000).length, pass: false },
      { label: 'PB < 1.2', count: allStocks.filter(s => { const v = Number(s.pb) || 0; return v > 0 && v < 1.2 }).length, pass: false }
    ]
  }

  return stats
})

// 条件搜索状态
const searchFilters = ref({
  price: { min: '', max: '' },
  change: { min: '', max: '' },
  pe_ttm: { min: '', max: '' },
  pb: { min: '', max: '' },
  market_cap: { min: '', max: '' }, // 单位：亿
  turnover: { min: '', max: '' },
  main_inflow: { min: '', max: '' } // 单位：万
})

const isSearching = ref(false)
const showSearchResults = ref(false)

// 搜索记录状态
const searchHistory = ref<any[]>([])
const HISTORY_KEY = 'cranepoint_search_history'

onMounted(() => {
  const savedHistory = localStorage.getItem(HISTORY_KEY)
  if (savedHistory) {
    try {
      searchHistory.value = JSON.parse(savedHistory)
    } catch (e) {
      console.error('Failed to parse search history:', e)
    }
  }
})

const saveToHistory = (filters: any) => {
  const filtersStr = JSON.stringify(filters)
  
  // 检查是否已存在相同条件的记录
  const existingIndex = searchHistory.value.findIndex(item => 
    JSON.stringify(item.filters) === filtersStr
  )
  
  if (existingIndex !== -1) {
    // 如果存在相同记录，则将其移至最前并更新时间
    const existing = searchHistory.value.splice(existingIndex, 1)[0]
    existing.timestamp = new Date().toLocaleString()
    searchHistory.value.unshift(existing)
  } else {
    // 否则创建新记录
    const newEntry = {
      id: Date.now(),
      timestamp: new Date().toLocaleString(),
      filters: JSON.parse(filtersStr),
      count: customSearchResults.value.length
    }
    searchHistory.value.unshift(newEntry)
    if (searchHistory.value.length > 20) searchHistory.value.pop()
  }
  
  localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
}

const clearHistory = () => {
  searchHistory.value = []
  localStorage.removeItem(HISTORY_KEY)
}

const deleteHistoryItem = (id: number) => {
  searchHistory.value = searchHistory.value.filter(item => item.id !== id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
}

const applyHistory = (historyItem: any) => {
  searchFilters.value = JSON.parse(JSON.stringify(historyItem.filters))
  activeCategory.value = 'search'
  executeSearch()
}

const filterLabels: Record<string, string> = {
  price: '现价',
  change: '涨跌',
  pe_ttm: 'PE',
  pb: 'PB',
  market_cap: '市值',
  turnover: '换手',
  main_inflow: '流向'
}

const menuItems = [
  { id: 'strategy', name: '策略选股', icon: Target },
  { id: 'search', name: '条件搜索', icon: Search },
  { id: 'history', name: '筛选记录', icon: History }
]

// 策略定义
const strategies = [
  {
    id: 'buffett',
    name: '巴菲特价值投资策略',
    description: '寻找具有持续竞争优势、低估值且财务稳健的行业龙头。',
    icon: Award,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    criteria: [
      '估值合理：PE(TTM) 介于 5 - 20 之间',
      '资产溢价低：PB 介于 0 - 3 之间',
      '行业龙头：总市值 > 500 亿',
      '市场认可：今日主力资金净流入'
    ]
  },
  {
    id: 'growth',
    name: '高成长动能策略',
    description: '筛选本年度表现强劲且近期有大资金持续介入的成长股。',
    icon: TrendingUp,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    criteria: [
      '动能强劲：今年以来涨幅 > 20%',
      '活跃度高：换手率 > 3%',
      '趋势向上：今日涨幅 > 2%',
      '主力抢筹：主力流入比例 > 5%'
    ]
  },
  {
    id: 'safe',
    name: '稳健防御策略',
    description: '寻找低波动、高股息潜力且处于安全边际内的避险标的。',
    icon: ShieldCheck,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    criteria: [
      '极低估值：PE(TTM) < 12',
      '股价稳定：振幅 < 3%',
      '中大型市值：总市值 > 200 亿',
      '破净边际：PB < 1.2'
    ]
  }
]

// 自定义搜索筛选逻辑
const customSearchResults = computed(() => {
  const allStocks = marketStore.stocks
  return allStocks.filter(s => {
    const checkRange = (val: number, range: { min: string, max: string }, factor = 1) => {
      const min = range.min === '' ? -Infinity : parseFloat(range.min) * factor
      const max = range.max === '' ? Infinity : parseFloat(range.max) * factor
      return val >= min && val <= max
    }

    return (
      checkRange(s.price, searchFilters.value.price) &&
      checkRange(s.change, searchFilters.value.change) &&
      checkRange(s.pe_ttm, searchFilters.value.pe_ttm) &&
      checkRange(s.pb, searchFilters.value.pb) &&
      checkRange(s.market_cap, searchFilters.value.market_cap, 100000000) &&
      checkRange(s.turnover, searchFilters.value.turnover) &&
      checkRange(s.main_inflow, searchFilters.value.main_inflow, 10000)
    )
  })
})

const executeSearch = () => {
  isSearching.value = true
  setTimeout(() => {
    showSearchResults.value = true
    isSearching.value = false
    saveToHistory(searchFilters.value)
  }, 600)
}

const resetFilters = () => {
  searchFilters.value = {
    price: { min: '', max: '' },
    change: { min: '', max: '' },
    pe_ttm: { min: '', max: '' },
    pb: { min: '', max: '' },
    market_cap: { min: '', max: '' },
    turnover: { min: '', max: '' },
    main_inflow: { min: '', max: '' }
  }
  showSearchResults.value = false
}

// 策略筛选结果
const screeningResults = computed(() => {
  if (!selectedStrategy.value) return []
  
  const allStocks = marketStore.stocks
  
  if (selectedStrategy.value === 'buffett') {
    return allStocks.filter(s => {
      const pe = Number(s.pe_ttm) || 0
      const pb = Number(s.pb) || 0
      const mc = Number(s.market_cap) || 0
      const flow = Number(s.main_inflow) || 0
      
      return pe > 5 && pe < 20 &&
             pb > 0 && pb < 3 &&
             mc > 50000000000 && // 500亿
             flow > 0
    })
  }

  if (selectedStrategy.value === 'growth') {
    return allStocks.filter(s => {
      const ytd = Number(s.change_ytd) || 0
      const turn = Number(s.turnover) || 0
      const chg = Number(s.change) || 0
      const ratio = Number(s.main_inflow_ratio) || 0
      
      return ytd > 20 &&
             turn > 3 &&
             chg > 2 &&
             ratio > 5
    })
  }

  if (selectedStrategy.value === 'safe') {
    return allStocks.filter(s => {
      const pe = Number(s.pe_ttm) || 0
      const amp = Number(s.amplitude) || 0
      const mc = Number(s.market_cap) || 0
      const pb = Number(s.pb) || 0
      
      return pe > 0 && pe < 12 &&
             amp < 3 &&
             mc > 20000000000 && // 200亿
             pb > 0 && pb < 1.2
    })
  }
  
  return []
})

const selectStrategy = (id: string) => {
  isScreening.value = true
  selectedStrategy.value = null // 先清空，为了触发动画
  
  setTimeout(() => {
    selectedStrategy.value = id
    isScreening.value = false
  }, 800)
}

const goToAnalysis = (code: string) => {
  router.push({
    path: '/download',
    query: { symbol: code, mode: 'analysis' }
  })
}

const goToMarket = (code: string) => {
  router.push({
    path: '/market',
    query: { search: code }
  })
}

const formatAmount = (val: number | undefined | null) => {
  if (val === undefined || val === null || isNaN(Number(val))) return '--'
  const num = Number(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + ' 亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + ' 万'
  return num.toFixed(2)
}

const formatNumber = (val: number | undefined | null, decimals: number = 2) => {
  if (val === undefined || val === null || isNaN(Number(val))) return '--'
  return Number(val).toFixed(decimals)
}
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
      <!-- 策略选股主视图 -->
      <div v-if="activeId === 'strategy'" class="h-full flex flex-col p-8 overflow-hidden relative">
        <!-- 加载蒙层 -->
        <div v-if="isScreening" class="absolute inset-0 z-50 bg-background/60 backdrop-blur-sm flex flex-col items-center justify-center animate-in fade-in duration-300">
          <div class="w-16 h-16 bg-primary/10 rounded-3xl flex items-center justify-center mb-4 text-primary">
            <Loader2 class="w-8 h-8 animate-spin" />
          </div>
          <p class="text-sm font-medium text-foreground/60">正在基于实时行情快照进行多维筛选...</p>
        </div>

        <div v-if="!selectedStrategy && !isScreening" class="flex-none mb-12 text-center max-w-2xl mx-auto pt-10">
          <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary mx-auto">
            <Target class="w-10 h-10" />
          </div>
          <h2 class="text-3xl font-bold mb-4">策略选股中心</h2>
          <p class="text-foreground/50 text-lg">
            基于多维量化因子库，我们为您预设了以下经典投资策略。点击下方卡片即可开始在当前市场快照中进行实时筛选。
          </p>
        </div>

        <div v-if="!selectedStrategy && !isScreening" class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto w-full">
          <div 
            v-for="s in strategies" 
            :key="s.id"
            @click="selectStrategy(s.id)"
            class="group bg-card border border-thin rounded-3xl p-8 hover:border-primary/50 hover:shadow-xl hover:shadow-primary/5 transition-all cursor-pointer flex flex-col relative overflow-hidden"
          >
            <div :class="['absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-5 transition-transform group-hover:scale-150', s.bgColor]"></div>
            <div :class="['w-14 h-14 rounded-2xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110 shadow-sm', s.bgColor, s.color]">
              <component :is="s.icon" class="w-7 h-7" />
            </div>
            <h3 class="text-xl font-bold mb-3 group-hover:text-primary transition-colors">{{ s.name }}</h3>
            <p class="text-sm text-foreground/50 leading-relaxed mb-8 flex-1">{{ s.description }}</p>
            <div class="space-y-3 mb-8">
              <div v-for="(c, idx) in s.criteria" :key="idx" class="flex items-center gap-2 text-[13px] text-foreground/60 font-medium">
                <div class="w-1.5 h-1.5 rounded-full bg-primary/30"></div>
                {{ c }}
              </div>
            </div>
            <button class="w-full py-3 bg-foreground/[0.03] border border-thin rounded-xl text-sm font-bold group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary transition-all flex items-center justify-center gap-2 shadow-sm">
              开始筛选 <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div v-else-if="selectedStrategy && !isScreening" class="flex-1 flex flex-col min-h-0 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="flex-none flex items-center justify-between mb-6">
            <div class="flex items-center gap-4">
              <button @click="selectedStrategy = null" class="p-2 hover:bg-foreground/5 rounded-xl transition-colors text-foreground/40 hover:text-foreground">
                <ChevronRight class="w-6 h-6 rotate-180" />
              </button>
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <h3 class="text-2xl font-bold">{{ strategies.find(s => s.id === selectedStrategy)?.name }}</h3>
                  <span class="px-2.5 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded-full uppercase tracking-wider">筛选结果: {{ screeningResults.length }} 只</span>
                </div>
                <p class="text-sm text-foreground/40">基于当前市场快照数据，为您匹配符合策略条件的优质标的</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="px-4 py-2 bg-amber-500/10 text-amber-600 rounded-xl flex items-center gap-2 text-xs font-medium border border-amber-500/20">
                <Info class="w-4 h-4" />
                所有计算基于 <b>{{ marketStore.stocks.length }}</b> 只全量 A 股
              </div>
            </div>
          </div>

          <!-- 结果表格 -->
          <div class="flex-1 bg-card border border-thin rounded-3xl overflow-hidden shadow-sm flex flex-col">
            <div class="flex-1 overflow-auto custom-scrollbar">
              <table class="w-full border-collapse text-left">
                <thead class="sticky top-0 z-10 bg-card/80 backdrop-blur-md border-b border-thin">
                  <tr>
                    <th class="px-6 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider">股票名称</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">现价</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">涨跌幅</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">PE(TTM)</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">PB</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">总市值</th>
                    <th class="px-4 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-right">主力净流</th>
                    <th class="px-6 py-4 text-[11px] font-bold text-foreground/40 uppercase tracking-wider text-center">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-thin">
                  <tr v-for="stock in screeningResults" :key="stock.code" class="group hover:bg-foreground/[0.02] transition-colors">
                    <td class="px-6 py-4">
                      <div class="flex flex-col">
                        <span class="font-bold text-sm">{{ stock.name }}</span>
                        <span class="text-[10px] font-mono text-foreground/30 group-hover:text-primary/50 transition-colors">{{ stock.code }}</span>
                      </div>
                    </td>
                    <td class="px-4 py-4 text-right font-mono text-sm">{{ formatNumber(stock.price) }}</td>
                    <td class="px-4 py-4 text-right font-mono text-sm">
                      <span :class="stock.change > 0 ? 'text-red-500' : stock.change < 0 ? 'text-green-500' : ''">
                        {{ stock.change > 0 ? '+' : '' }}{{ formatNumber(stock.change) }}%
                      </span>
                    </td>
                    <td class="px-4 py-4 text-right font-mono text-sm text-foreground/60">{{ formatNumber(stock.pe_ttm) }}</td>
                    <td class="px-4 py-4 text-right font-mono text-sm text-foreground/60">{{ formatNumber(stock.pb) }}</td>
                    <td class="px-4 py-4 text-right font-mono text-sm text-foreground/60">{{ formatAmount(stock.market_cap) }}</td>
                    <td class="px-4 py-4 text-right font-mono text-sm">
                      <span :class="stock.main_inflow > 0 ? 'text-red-500' : 'text-green-500'">{{ formatAmount(stock.main_inflow) }}</span>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex items-center justify-center gap-2">
                        <button 
                          @click="goToAnalysis(stock.code)"
                          class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20" 
                          title="个股分析"
                        >
                          <TrendingUp class="w-4 h-4" />
                        </button>
                        <button 
                          @click="goToMarket(stock.code)"
                          class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20" 
                          title="查看行情"
                        >
                          <ExternalLink class="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="screeningResults.length === 0" class="py-24 flex flex-col items-center justify-center">
                <div class="w-16 h-16 bg-foreground/5 rounded-full flex items-center justify-center mb-6">
                  <ShieldCheck class="w-8 h-8 text-foreground/10" />
                </div>
                <h3 class="text-lg font-medium text-foreground/40 mb-2">在当前市场快照中未找到符合该策略的标的</h3>
                <p class="text-sm text-foreground/20 mb-8">请尝试更新市场快照或选择其他策略</p>
                
                <!-- 筛选诊断 -->
                <div v-if="strategyDiagnostics" class="w-full max-w-md bg-foreground/[0.02] rounded-2xl p-6 border border-thin">
                  <div class="flex items-center gap-2 mb-4">
                    <AlertCircle class="w-4 h-4 text-primary" />
                    <span class="text-sm font-medium">策略条件诊断 (通过数量 / 总数 {{ strategyDiagnostics.total }})</span>
                  </div>
                  <div class="space-y-3">
                    <div v-for="cond in strategyDiagnostics.conditions" :key="cond.label" class="flex items-center justify-between">
                      <span class="text-xs text-foreground/60">{{ cond.label }}</span>
                      <div class="flex items-center gap-3">
                        <div class="w-32 h-1.5 bg-foreground/5 rounded-full overflow-hidden">
                          <div 
                            class="h-full bg-primary transition-all duration-500"
                            :style="{ width: `${(cond.count / strategyDiagnostics.total) * 100}%` }"
                          ></div>
                        </div>
                        <span class="text-[11px] font-mono w-12 text-right" :class="cond.count === 0 ? 'text-red-500' : 'text-foreground/40'">
                          {{ cond.count }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-6 pt-4 border-t border-thin">
                    <p class="text-[11px] text-foreground/30 leading-relaxed">
                      提示：巴菲特策略对“大市值”和“资金流入”要求较高。若今日市场整体走势较弱，主力资金可能普遍呈现流出状态，导致无匹配项。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 条件搜索视图 -->
      <div v-else-if="activeId === 'search'" class="h-full flex flex-col p-8 overflow-hidden">
        <div class="flex-none mb-8 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-primary/10 rounded-2xl text-primary">
              <Search class="w-6 h-6" />
            </div>
            <div>
              <h2 class="text-2xl font-bold">多维条件搜索</h2>
              <p class="text-sm text-foreground/50">灵活配置多维量化指标，自定义您的选股方案</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button 
              @click="resetFilters"
              class="px-4 py-2 flex items-center gap-2 text-sm font-medium text-foreground/60 hover:text-foreground hover:bg-foreground/5 rounded-xl transition-all"
            >
              <RotateCcw class="w-4 h-4" /> 重置条件
            </button>
            <button 
              @click="executeSearch"
              :disabled="isSearching"
              class="px-6 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2 disabled:opacity-50 disabled:scale-100"
            >
              <Play v-if="!isSearching" class="w-4 h-4 fill-current" />
              <div v-else class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
              执行筛选
            </button>
          </div>
        </div>

        <div class="flex-1 flex flex-col min-h-0 gap-8">
          <!-- 筛选配置区 -->
          <div class="flex-none bg-card border border-thin rounded-3xl p-8 shadow-sm">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-12 gap-y-8">
              <!-- 价格范围 -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 现价范围 (元)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.price.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.price.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- 涨跌幅 -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 今日涨跌 (%)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.change.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.change.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- PE(TTM) -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 市盈率 PE(TTM)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.pe_ttm.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.pe_ttm.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- PB -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 市净率 PB
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.pb.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.pb.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- 总市值 -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 总市值 (亿元)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.market_cap.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.market_cap.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- 换手率 -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 换手率 (%)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.turnover.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.turnover.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
              <!-- 主力净流 -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-foreground/40 uppercase tracking-wider flex items-center gap-2">
                  <div class="w-1 h-1 rounded-full bg-primary"></div> 主力净流入 (万元)
                </label>
                <div class="flex items-center gap-3">
                  <input v-model="searchFilters.main_inflow.min" type="number" placeholder="最小" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                  <div class="w-3 h-px bg-foreground/20"></div>
                  <input v-model="searchFilters.main_inflow.max" type="number" placeholder="最大" class="w-full px-4 py-2.5 bg-foreground/[0.03] border border-thin rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" />
                </div>
              </div>
            </div>
          </div>

          <!-- 搜索结果区 -->
          <div v-if="showSearchResults" class="flex-1 flex flex-col min-h-0 animate-in fade-in slide-in-from-top-4 duration-500">
            <div class="flex-none mb-4 flex items-center justify-between">
              <span class="text-sm font-bold text-foreground/40 uppercase tracking-widest">搜索结果 ({{ customSearchResults.length }} 只)</span>
            </div>
            <div class="flex-1 bg-card border border-thin rounded-3xl overflow-hidden shadow-sm flex flex-col">
              <div class="flex-1 overflow-auto custom-scrollbar">
                <table class="w-full border-collapse text-left text-sm">
                  <thead class="sticky top-0 z-10 bg-card/80 backdrop-blur-md border-b border-thin">
                    <tr>
                      <th class="px-6 py-4 font-bold text-foreground/40 uppercase tracking-wider">股票名称</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">现价</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">涨跌幅</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">PE(TTM)</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">PB</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">总市值</th>
                      <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">主力净流</th>
                      <th class="px-6 py-4 font-bold text-foreground/40 uppercase tracking-wider text-center">操作</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-thin">
                    <tr v-for="stock in customSearchResults" :key="stock.code" class="group hover:bg-foreground/[0.02] transition-colors">
                      <td class="px-6 py-4">
                        <div class="flex flex-col">
                          <span class="font-bold">{{ stock.name }}</span>
                          <span class="text-[10px] font-mono text-foreground/30 group-hover:text-primary/50 transition-colors">{{ stock.code }}</span>
                        </div>
                      </td>
                      <td class="px-4 py-4 text-right font-mono">{{ formatNumber(stock.price) }}</td>
                      <td class="px-4 py-4 text-right font-mono">
                        <span :class="stock.change > 0 ? 'text-red-500' : stock.change < 0 ? 'text-green-500' : ''">
                          {{ stock.change > 0 ? '+' : '' }}{{ formatNumber(stock.change) }}%
                        </span>
                      </td>
                      <td class="px-4 py-4 text-right font-mono text-foreground/60">{{ formatNumber(stock.pe_ttm) }}</td>
                      <td class="px-4 py-4 text-right font-mono text-foreground/60">{{ formatNumber(stock.pb) }}</td>
                      <td class="px-4 py-4 text-right font-mono text-foreground/60">{{ formatAmount(stock.market_cap) }}</td>
                      <td class="px-4 py-4 text-right font-mono">
                        <span :class="stock.main_inflow > 0 ? 'text-red-500' : 'text-green-500'">{{ formatAmount(stock.main_inflow) }}</span>
                      </td>
                      <td class="px-6 py-4 text-center">
                        <div class="flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20"><TrendingUp class="w-4 h-4" /></button>
                          <button class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20"><ExternalLink class="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="customSearchResults.length === 0" class="flex flex-col items-center justify-center py-20 text-foreground/20">
                  <Search class="w-16 h-16 mb-4 opacity-10" />
                  <p class="text-lg">未找到符合条件的股票</p>
                  <p class="text-xs mt-2">请调整筛选范围后重试</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 初始引导状态 -->
          <div v-else class="flex-1 flex flex-col items-center justify-center text-foreground/20 space-y-4">
            <div class="w-20 h-20 bg-foreground/[0.03] border border-dashed border-thin rounded-3xl flex items-center justify-center">
              <Search class="w-10 h-10 opacity-20" />
            </div>
            <div class="text-center">
              <p class="text-lg font-medium">配置筛选条件并点击“执行筛选”</p>
              <p class="text-sm opacity-50">系统将从 {{ marketStore.stocks.length }} 只 A 股中为您快速匹配</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选记录视图 -->
      <div v-else-if="activeId === 'history'" class="h-full flex flex-col p-8 overflow-hidden">
        <div class="flex-none mb-8 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-primary/10 rounded-2xl text-primary">
              <History class="w-6 h-6" />
            </div>
            <div>
              <h2 class="text-2xl font-bold">筛选记录</h2>
              <p class="text-sm text-foreground/50">回顾并快速重新执行您之前的选股方案</p>
            </div>
          </div>
          <button 
            v-if="searchHistory.length > 0"
            @click="clearHistory"
            class="px-4 py-2 flex items-center gap-2 text-sm font-medium text-red-500 hover:bg-red-500/10 rounded-xl transition-all"
          >
            <Trash2 class="w-4 h-4" /> 清空记录
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="searchHistory.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div 
              v-for="item in searchHistory" 
              :key="item.id"
              class="group bg-card border border-thin rounded-3xl p-6 hover:border-primary/30 transition-all flex flex-col"
            >
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2 text-[10px] font-bold text-foreground/30 uppercase tracking-widest">
                  <Clock class="w-3 h-3" /> {{ item.timestamp }}
                </div>
                <button @click="deleteHistoryItem(item.id)" class="p-2 hover:bg-red-500/10 text-foreground/20 hover:text-red-500 rounded-lg transition-colors">
                  <X class="w-4 h-4" />
                </button>
              </div>

              <div class="flex-1 space-y-4 mb-6">
                <div class="flex flex-wrap gap-2">
                  <div v-for="(val, key) in item.filters" :key="key">
                    <div v-if="val.min !== '' || val.max !== ''" class="px-2 py-1 bg-foreground/[0.03] border border-thin rounded-lg text-[10px] text-foreground/60 flex items-center gap-1.5">
                      <span class="font-bold opacity-40">{{ filterLabels[key] || key }}</span>
                      <span>{{ val.min || '∞' }} - {{ val.max || '∞' }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2 text-xs font-bold text-primary">
                  <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                  命中结果: {{ item.count }} 只
                </div>
              </div>

              <button 
                @click="applyHistory(item)"
                class="w-full py-3 bg-primary/5 text-primary rounded-xl text-sm font-bold hover:bg-primary hover:text-primary-foreground transition-all flex items-center justify-center gap-2"
              >
                <Play class="w-4 h-4 fill-current" /> 重新执行
              </button>
            </div>
          </div>
          <div v-else class="h-full flex flex-col items-center justify-center text-foreground/20 space-y-4 py-20">
            <History class="w-16 h-16 opacity-10" />
            <p class="text-lg">暂无筛选记录</p>
          </div>
        </div>
      </div>
    </template>
  </SidebarLayout>
</template>
