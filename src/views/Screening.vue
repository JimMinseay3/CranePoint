<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import SidebarLayout from '../components/SidebarLayout.vue'
import { marketStore } from '../store/market'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
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
  AlertCircle,
  Zap,
  Activity,
  Plus,
  ArrowUp
} from 'lucide-vue-next'

const router = useRouter()
const activeCategory = ref('strategy')
const selectedStrategy = ref<string | null>(null)
const isScreening = ref(false)
const screeningProgress = ref(0)
const sidecarResults = ref<any[]>([])
let unlistenScreening: any = null

const searchScrollContainer = ref<HTMLElement | null>(null)
const showBackTop = ref(false)
const resultsHeaderRef = ref<HTMLElement | null>(null)

// 监听滚动显示回到顶部按钮
const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement
  showBackTop.value = target.scrollTop > 400
}

onMounted(async () => {
  // 查找 SidebarLayout 中的滚动容器
  const scrollContainer = document.querySelector('main .custom-scrollbar')
  if (scrollContainer) {
    scrollContainer.addEventListener('scroll', handleScroll)
    searchScrollContainer.value = scrollContainer as HTMLElement
  }
})

// 配置常量
const availableFilterOptions = [
  // 动能指标
  { key: 'price', label: '最新价', unit: '元', group: 'momentum' },
  { key: 'change', label: '今日涨跌', unit: '%', group: 'momentum' },
  { key: 'speed', label: '涨速', unit: '', group: 'momentum' },
  { key: 'volume_ratio', label: '量比', unit: '', group: 'momentum' },
  
  // 量能分析
  { key: 'volume', label: '成交量', unit: '', group: 'volume' },
  { key: 'amount', label: '成交额', unit: '', group: 'volume' },
  { key: 'turnover_actual', label: '换手(实)', unit: '%', group: 'volume' },
  { key: 'turnover', label: '换手率', unit: '%', group: 'volume' },
  { key: 'limit_up', label: '涨停', unit: '元', group: 'volume' },
  { key: 'limit_down', label: '跌停', unit: '元', group: 'volume' },
  
  // 空间位置
  { key: 'amplitude', label: '振幅', unit: '%', group: 'space' },
  { key: 'high', label: '最高', unit: '元', group: 'space' },
  { key: 'low', label: '最低', unit: '元', group: 'space' },
  { key: 'open', label: '今开', unit: '元', group: 'space' },
  { key: 'prevClose', label: '昨收', unit: '元', group: 'space' },
  
  // 资金流向
  { key: 'main_inflow', label: '主力净流', unit: '万元', group: 'flow', factor: 10000 },
  { key: 'main_inflow_ratio', label: '主力占比', unit: '%', group: 'flow' },
  { key: 'change_ytd', label: '年内涨跌', unit: '%', group: 'flow' },
  
  // 基本面
  { key: 'market_cap', label: '总市值', unit: '亿元', group: 'fundamental', factor: 100000000 },
  { key: 'circulating_market_cap', label: '流通市值', unit: '亿元', group: 'fundamental', factor: 100000000 },
  { key: 'total_shares', label: '总股本', unit: '', group: 'fundamental' },
  { key: 'circulating_shares', label: '流通股', unit: '', group: 'fundamental' },
  { key: 'pe_static', label: '市盈(静)', unit: '', group: 'fundamental' },
  { key: 'pe_ttm', label: '市盈(TTM)', unit: '', group: 'fundamental' },
  { key: 'pb', label: '市净率', unit: '', group: 'fundamental' }
]

const groupMetadata: Record<string, { label: string, color: string, borderColor: string, bgColor: string }> = {
  'momentum': { label: '动能指标', color: 'text-orange-600', borderColor: 'border-orange-500/30', bgColor: 'bg-orange-500/5' },
  'volume': { label: '量能分析', color: 'text-blue-600', borderColor: 'border-blue-500/30', bgColor: 'bg-blue-500/5' },
  'space': { label: '空间位置', color: 'text-purple-600', borderColor: 'border-purple-500/30', bgColor: 'bg-purple-500/5' },
  'flow': { label: '资金流向', color: 'text-cyan-600', borderColor: 'border-cyan-500/30', bgColor: 'bg-cyan-500/5' },
  'fundamental': { label: '基本面', color: 'text-emerald-600', borderColor: 'border-emerald-500/30', bgColor: 'bg-emerald-500/5' }
}

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
const searchFilters = ref(
  availableFilterOptions.reduce((acc, opt) => {
    acc[opt.key] = { min: '', max: '' }
    return acc
  }, {} as any)
)

const isSearching = ref(false)
const showSearchResults = ref(false)

// 搜索记录状态
const searchHistory = ref<any[]>([])
const HISTORY_KEY = 'cranepoint_search_history'

onMounted(async () => {
  const savedHistory = localStorage.getItem(HISTORY_KEY)
  if (savedHistory) {
    try {
      searchHistory.value = JSON.parse(savedHistory)
    } catch (e) {
      console.error('Failed to parse search history:', e)
    }
  }

  // 监听筛选进度
  try {
    unlistenScreening = await listen('screening-progress', (event: any) => {
      // 逻辑保护：进度条只增不减，防止多个后台进程（如果意外存在）干扰
      if (event.payload > screeningProgress.value) {
        screeningProgress.value = event.payload
      }
    })
  } catch (e) {
    console.warn('Tauri events not available')
  }
})

onUnmounted(() => {
  if (unlistenScreening) unlistenScreening()
  if (searchScrollContainer.value) {
    searchScrollContainer.value.removeEventListener('scroll', handleScroll)
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

const executeSearch = () => {
  isSearching.value = true
  setTimeout(() => {
    showSearchResults.value = true
    isSearching.value = false
    saveToHistory(searchFilters.value)
    
    // 自动滑动到结果区
    setTimeout(() => {
      if (resultsHeaderRef.value && searchScrollContainer.value) {
        resultsHeaderRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }, 600)
}

const scrollToTop = () => {
  if (searchScrollContainer.value) {
    searchScrollContainer.value.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const applyHistory = (historyItem: any) => {
  searchFilters.value = JSON.parse(JSON.stringify(historyItem.filters))
  activeCategory.value = 'search'
  executeSearch()
}

const resetFilters = () => {
  availableFilterOptions.forEach(opt => {
    if (searchFilters.value[opt.key as keyof typeof searchFilters.value]) {
      searchFilters.value[opt.key as keyof typeof searchFilters.value] = { min: '', max: '' }
    }
  })
  showSearchResults.value = false
}

const getFilterLabel = (key: string) => {
  return availableFilterOptions.find(o => o.key === key)?.label || key
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
  },
  {
    id: 'macd_cross',
    name: 'MACD 零下金叉 (全市场)',
    description: '寻找处于零轴下方的 MACD 金叉，捕捉超跌反弹或波段起涨点。',
    icon: Zap,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    criteria: [
      '核心信号：零下金叉 (DIFF/DEA < 0)',
      '判定条件：昨日 DIFF <= DEA 且今日 DIFF > DEA',
      '范围限制：排除今日跌幅超过 5% 的标的'
    ]
  }
]

// 自定义搜索筛选逻辑
const columnFilters = computed(() => {
  const total = availableFilterOptions.length
  
  // 尽量均匀分布到 3 列
  const perCol = Math.ceil(total / 3)
  const cols: any[][] = [[], [], []]
  
  availableFilterOptions.forEach((opt, index) => {
    const colIndex = Math.min(Math.floor(index / perCol), 2)
    cols[colIndex].push(opt)
  })
  
  // 在每一列内按连续的分组进行包装
  return cols.map(col => {
    const groupedInCol: { group: string, items: any[] }[] = []
    col.forEach(item => {
      const lastGroup = groupedInCol[groupedInCol.length - 1]
      if (lastGroup && lastGroup.group === item.group) {
        lastGroup.items.push(item)
      } else {
        groupedInCol.push({ group: item.group, items: [item] })
      }
    })
    return groupedInCol
  })
})

const customSearchResults = computed(() => {
  const allStocks = marketStore.stocks
  return allStocks.filter(s => {
    const checkRange = (val: number, range: { min: string, max: string }, factor = 1) => {
      const min = range.min === '' ? -Infinity : parseFloat(range.min) * factor
      const max = range.max === '' ? Infinity : parseFloat(range.max) * factor
      return val >= min && val <= max
    }

    // 仅对填了数值的项进行过滤
    return availableFilterOptions.every(opt => {
      const range = searchFilters.value[opt.key as keyof typeof searchFilters.value]
      if (range.min === '' && range.max === '') return true // 未填写的项跳过过滤
      
      const factor = opt.factor || 1
      const val = s[opt.key as keyof typeof s]
      return checkRange(Number(val), range, factor)
    })
  })
})

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

  if (selectedStrategy.value === 'macd_cross') {
    return sidecarResults.value
  }
  
  return []
})

const selectStrategy = async (id: string) => {
  if (isScreening.value) return // 并发保护：如果正在筛选，拒绝新的请求
  
  isScreening.value = true
  selectedStrategy.value = null // 先清空，为了触发动画
  screeningProgress.value = 0
  sidecarResults.value = []
  
  if (id === 'macd_cross') {
    // 数据完整性检查
    if (!marketStore.stocks || marketStore.stocks.length === 0) {
      alert('请先在“行情中心”刷新并获取市场实时数据')
      isScreening.value = false
      return
    }

    try {
      selectedStrategy.value = id // 立即切换，即使还在加载
      // 如果是 MACD 策略，调用 Sidecar
      const results = await invoke('run_strategy_screening', {
        stocks: marketStore.stocks
      })
      const parsedResults = JSON.parse(results as string)
      sidecarResults.value = parsedResults

      if (parsedResults.length === 0) {
        // 可以选择提示用户没有符合条件的股票
        console.log('No stocks met the criteria.')
      }
    } catch (e) {
      console.error('Screening failed:', e)
      alert(`筛选失败: ${e}`)
    } finally {
      isScreening.value = false
    }
  } else {
    // 其他本地策略
    setTimeout(() => {
      selectedStrategy.value = id
      isScreening.value = false
    }, 800)
  }
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
  <div class="h-full">
    <SidebarLayout
      title="股票筛选"
      subtitle="多维因子选股，锁定核心标的"
      :icon="Filter"
      :menuItems="menuItems"
      v-model:activeId="activeCategory"
    >
      <template #default="{ activeId }">
        <!-- 策略选股主视图 -->
        <div v-if="activeId === 'strategy'" class="h-full flex flex-col p-6 overflow-hidden">
          <div class="flex-1 flex gap-6 min-h-0">
            <!-- 左侧策略列表 -->
            <div class="w-80 flex-none flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2">
              <div class="flex-none px-2 py-4">
                <h2 class="text-xl font-bold flex items-center gap-2">
                  <Target class="w-5 h-5 text-primary" />
                  策略中心
                </h2>
                <p class="text-xs text-foreground/40 mt-1">点击切换量化投资策略</p>
              </div>
              
              <div class="flex flex-col gap-2">
                <button 
                  v-for="s in strategies" 
                  :key="s.id"
                  @click="selectStrategy(s.id)"
                  class="group w-full text-left p-4 rounded-2xl border border-thin transition-all relative overflow-hidden"
                  :class="[
                    selectedStrategy === s.id 
                      ? 'bg-primary/5 border-primary/30 shadow-sm' 
                      : 'bg-card hover:bg-foreground/[0.02] hover:border-foreground/10'
                  ]"
                >
                  <!-- 激活状态指示条 -->
                  <div 
                    v-if="selectedStrategy === s.id" 
                    class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full"
                  ></div>

                  <div class="flex items-start gap-3">
                    <div :class="['w-10 h-10 rounded-xl flex items-center justify-center flex-none shadow-sm', s.bgColor, s.color]">
                      <component :is="s.icon" class="w-5 h-5" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="font-bold text-sm mb-1 truncate" :class="{ 'text-primary': selectedStrategy === s.id }">{{ s.name }}</h3>
                      <p class="text-[11px] text-foreground/40 leading-relaxed line-clamp-2">{{ s.description }}</p>
                    </div>
                  </div>

                  <!-- 策略条件简述 - 仅在选中时显示更多细节 -->
                  <div v-if="selectedStrategy === s.id" class="mt-4 pt-4 border-t border-primary/10 space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div v-for="(c, idx) in s.criteria" :key="idx" class="flex items-center gap-2 text-[10px] text-foreground/60 font-medium">
                      <div class="w-1 h-1 rounded-full bg-primary/30"></div>
                      {{ c }}
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <!-- 右侧显示框 -->
            <div class="flex-1 bg-card border border-thin rounded-[2rem] shadow-sm flex flex-col overflow-hidden relative">
              <!-- 加载蒙层 -->
              <div v-if="isScreening" class="absolute inset-0 z-50 bg-background/60 backdrop-blur-sm flex flex-col items-center justify-center animate-in fade-in duration-300">
                <div class="w-16 h-16 bg-primary/10 rounded-3xl flex items-center justify-center mb-4 text-primary relative overflow-hidden">
                  <Loader2 class="w-8 h-8 animate-spin z-10" />
                  <!-- 进度条背景 -->
                  <div v-if="screeningProgress > 0" class="absolute inset-0 bg-primary/20 transition-all duration-300" :style="{ height: screeningProgress + '%' }"></div>
                </div>
                <p class="text-sm font-medium text-foreground/60">{{ screeningProgress < 10 ? '正在初始化并发引擎...' : '正在进行全市场实时扫描...' }}</p>
                <div class="flex flex-col items-center gap-1 mt-2">
                  <p v-if="screeningProgress > 0" class="text-[10px] text-primary font-mono font-bold">{{ screeningProgress }}%</p>
                  <p class="text-[10px] text-foreground/30">已开启 30 线程并发加速</p>
                </div>
              </div>

              <div v-if="selectedStrategy" class="flex-1 flex flex-col min-h-0">
                <!-- 顶部统计栏 -->
                <div class="flex-none px-8 py-6 border-b border-thin bg-foreground/[0.01] flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', strategies.find(s => s.id === selectedStrategy)?.bgColor, strategies.find(s => s.id === selectedStrategy)?.color]">
                      <component :is="strategies.find(s => s.id === selectedStrategy)?.icon" class="w-4 h-4" />
                    </div>
                    <div>
                      <h3 class="font-bold text-lg">{{ strategies.find(s => s.id === selectedStrategy)?.name }}</h3>
                      <p class="text-xs text-foreground/40">筛选结果: <span class="text-primary font-bold">{{ screeningResults.length }}</span> 只</p>
                    </div>
                  </div>
                  <div class="px-4 py-2 bg-amber-500/5 text-amber-600 rounded-xl flex items-center gap-2 text-xs font-medium border border-amber-500/10">
                    <Info class="w-3.5 h-3.5" />
                    基于 <b>{{ marketStore.stocks.length }}</b> 基于实时行情快照
                  </div>
                </div>

              <!-- 结果表格 -->
              <div class="flex-1 overflow-auto custom-scrollbar">
                <table class="w-full border-collapse text-left">
                  <thead class="sticky top-0 z-10 bg-card/80 backdrop-blur-md border-b border-thin">
                    <tr>
                      <th class="px-8 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest">股票名称</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-right">最新价</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-right">涨跌幅</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-right">PE(TTM)</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-right">量比/换手</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-right">总市值</th>
                      <th class="px-4 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-center">信号状态</th>
                      <th class="px-8 py-4 text-[10px] font-bold text-foreground/30 uppercase tracking-widest text-center">操作</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-thin">
                    <tr v-for="stock in screeningResults" :key="stock.code" class="group hover:bg-foreground/[0.02] transition-colors">
                      <td class="px-8 py-4">
                        <div class="flex flex-col">
                          <span class="font-bold text-sm">{{ stock.name }}</span>
                          <span class="text-[10px] font-mono text-foreground/20 group-hover:text-primary/50 transition-colors">{{ stock.code }}</span>
                        </div>
                      </td>
                      <td class="px-4 py-4 text-right font-mono text-sm">{{ formatNumber(stock.price) }}</td>
                      <td class="px-4 py-4 text-right font-mono text-sm">
                        <span :class="stock.change > 0 ? 'text-red-500' : stock.change < 0 ? 'text-green-500' : ''">
                          {{ stock.change > 0 ? '+' : '' }}{{ formatNumber(stock.change) }}%
                        </span>
                      </td>
                      <td class="px-4 py-4 text-right font-mono text-sm text-foreground/50">{{ formatNumber(stock.pe_ttm) }}</td>
                      <td class="px-4 py-4 text-right font-mono text-sm text-foreground/50">
                        <div class="flex flex-col items-end">
                          <span>{{ formatNumber(stock.volume_ratio) }}</span>
                          <span class="text-[10px] text-foreground/30">{{ formatNumber(stock.turnover) }}%</span>
                        </div>
                      </td>
                      <td class="px-4 py-4 text-right font-mono text-sm text-foreground/50">{{ formatAmount(stock.market_cap) }}</td>
                      <td class="px-4 py-4 text-center">
                        <div class="flex flex-col items-center gap-1">
                          <span v-if="stock.macd_status" class="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500 text-[10px] font-bold">
                            零下金叉
                          </span>
                          <span v-if="stock.has_divergence" class="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 text-[10px] font-bold">
                            底背离
                          </span>
                          <span v-if="!stock.macd_status && !stock.has_divergence" class="text-foreground/20 text-[10px]">-</span>
                        </div>
                      </td>
                      <td class="px-8 py-4">
                        <div class="flex items-center justify-center gap-2">
                          <button @click="goToAnalysis(stock.code)" class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20" title="个股分析"><TrendingUp class="w-4 h-4" /></button>
                          <button @click="goToMarket(stock.code)" class="p-2 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-foreground/20" title="查看行情"><ExternalLink class="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="screeningResults.length === 0" class="py-32 flex flex-col items-center justify-center">
                  <div class="w-20 h-20 bg-foreground/[0.03] rounded-full flex items-center justify-center mb-6">
                    <ShieldCheck class="w-10 h-10 text-foreground/10" />
                  </div>
                  <h3 class="text-lg font-medium text-foreground/40 mb-2">未找到符合该策略的标的</h3>
                  <p class="text-sm text-foreground/20">请尝试更新市场快照或选择其他策略</p>
                </div>
              </div>
            </div>

            <!-- 未选择策略时的空状态 -->
            <div v-else class="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <div class="w-24 h-24 bg-primary/5 rounded-[2.5rem] flex items-center justify-center mb-8 text-primary/20">
                <Target class="w-12 h-12" />
              </div>
              <h3 class="text-2xl font-bold mb-4 text-foreground/80">欢迎来到策略选股中心</h3>
              <p class="text-foreground/40 max-w-md mx-auto leading-relaxed">
                请从左侧列表中选择一个量化投资策略，系统将立即基于全量实时 A 股行情为您进行多维因子筛选。
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 条件搜索视图 -->
      <div v-else-if="activeId === 'search'" class="flex flex-col gap-8">
        <!-- 顶部标题与操作栏 -->
        <div class="flex items-center justify-between">
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

        <!-- 筛选配置区 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div v-for="(colGroups, colIdx) in columnFilters" :key="colIdx" class="space-y-6">
            <div 
              v-for="groupData in colGroups" 
              :key="groupData.group + colIdx"
              class="relative border-2 border-dashed rounded-2xl p-4 transition-all duration-300"
              :class="groupMetadata[groupData.group].borderColor + ' ' + groupMetadata[groupData.group].bgColor"
            >
              <!-- 组名标签 -->
              <div 
                class="absolute -top-3 left-4 px-2 bg-background text-[10px] font-bold uppercase tracking-widest"
                :class="groupMetadata[groupData.group].color"
              >
                {{ groupMetadata[groupData.group].label }}
              </div>

              <div class="space-y-5">
                <div v-for="item in groupData.items" :key="item.key" class="space-y-2 relative group/item">
                  <label class="text-[11px] font-bold text-foreground/50 uppercase tracking-wider flex items-center gap-2">
                    <div class="w-1 h-1 rounded-full" :class="'bg-' + groupMetadata[groupData.group].color.split('-')[1] + '-500'"></div> 
                    {{ item.label }} 
                    <span v-if="item.unit" class="opacity-40 font-normal">({{ item.unit }})</span>
                  </label>
                  <div class="flex items-center gap-2">
                    <input 
                      v-model="searchFilters[item.key as keyof typeof searchFilters].min" 
                      type="number" 
                      placeholder="最小" 
                      class="w-full px-3 py-2 bg-background/50 border border-thin rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" 
                    />
                    <div class="w-2 h-px bg-foreground/10"></div>
                    <input 
                      v-model="searchFilters[item.key as keyof typeof searchFilters].max" 
                      type="number" 
                      placeholder="最大" 
                      class="w-full px-3 py-2 bg-background/50 border border-thin rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm" 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分割线 -->
        <div v-if="showSearchResults" class="h-px bg-foreground/5 -mx-8"></div>

        <!-- 搜索结果区 -->
        <div v-if="showSearchResults" class="flex flex-col animate-in fade-in slide-in-from-top-4 duration-500">
          <div ref="resultsHeaderRef" class="mb-6 flex items-center justify-between scroll-mt-8">
            <span class="text-sm font-bold text-foreground/40 uppercase tracking-widest">搜索结果 ({{ customSearchResults.length }} 只)</span>
          </div>
          <div class="bg-card border border-thin rounded-3xl overflow-hidden shadow-sm">
            <div class="overflow-x-auto">
              <table class="w-full border-collapse text-left text-sm">
                <thead class="bg-card/80 backdrop-blur-md border-b border-thin">
                  <tr>
                    <th class="px-6 py-4 font-bold text-foreground/40 uppercase tracking-wider">股票名称</th>
                    <th class="px-4 py-4 font-bold text-foreground/40 uppercase tracking-wider text-right">最新价</th>
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
            </div>
            <div v-if="customSearchResults.length === 0" class="flex flex-col items-center justify-center py-20 text-foreground/20">
              <Search class="w-16 h-16 mb-4 opacity-10" />
              <p class="text-lg">未找到符合条件的股票</p>
              <p class="text-xs mt-2">请调整筛选范围后重试</p>
            </div>
          </div>
        </div>
        
        <!-- 初始引导状态 -->
        <div v-else class="flex flex-col items-center justify-center text-foreground/20 space-y-4 py-20">
          <div class="w-20 h-20 bg-foreground/[0.03] border border-dashed border-thin rounded-3xl flex items-center justify-center">
            <Search class="w-10 h-10 opacity-20" />
          </div>
          <div class="text-center">
            <p class="text-lg font-medium">配置筛选条件并点击“执行筛选”</p>
            <p class="text-sm opacity-50">系统将从 {{ marketStore.stocks.length }} 只 A 股中为您快速匹配</p>
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
                      <span class="font-bold opacity-40">{{ getFilterLabel(key) }}</span>
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

  <!-- 回到顶部悬浮按钮 -->
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="translate-y-10 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-10 opacity-0"
  >
    <button 
      v-show="showBackTop"
      @click="scrollToTop"
      class="fixed bottom-8 right-8 w-12 h-12 bg-primary text-primary-foreground rounded-2xl shadow-xl shadow-primary/20 flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-[100]"
      title="回到顶部"
    >
      <ArrowUp class="w-6 h-6" />
    </button>
  </Transition>
  </div>
</template>
