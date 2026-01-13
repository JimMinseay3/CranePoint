<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import SidebarLayout from '../components/SidebarLayout.vue'
import * as echarts from 'echarts'
import { 
  FileText, 
  Download,
  Database,
  Search,
  Calendar,
  Layers,
  Settings,
  FolderOpen,
  RefreshCw,
  Clock,
  ExternalLink,
  AlertCircle,
  XCircle,
  Activity,
  TrendingUp,
  ShieldAlert,
  Droplets,
  Network,
  History,
  ChevronRight,
  Loader2
} from 'lucide-vue-next'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { marketStore } from '../store/market'

const activeCategory = ref('finance')

// --- 状态定义开始 ---

// 全局标的选择相关
const globalSearchQuery = ref('')
const selectedStock = ref<any>(null)
const showSearchDropdown = ref(false)

// 下载相关状态
const isDownloading = ref(false)
const progress = ref(0)
const statusMessage = ref('')
const downloadStatusMessage = ref('')
const downloadWarnings = ref<string[]>([])
const showWarningDialog = ref(false)

const financeConfig = ref({
  symbol: '',
  selectedYears: [] as string[],
  selectedTypes: ['年报'] as string[]
})

const downloadSettings = ref({
  financePath: ''
})

// 分析相关状态
interface AnalysisResult {
  symbol: string
  name: string
  updated_at: string
  risk: {
    hv20: number
    hv60: number
  }
  liquidity: {
    bid_depth: number
    ask_depth: number
    score: string
  }
  fund_flow: {
    details: any[]
    rose_chart: Array<{
      name: string
      value: number
      raw: number
      type: string
    }>
    weekly_main_net: number
  }
  fundamentals: {
    deduct_net_profit: string | number
    report_period: string
  }
  industry: {
    name: string
    correlation: number
  }
  history: any[]
}

interface ArchiveItem {
  name: string
  updated_at: number
}

const analysisSymbol = ref('')
const isAnalyzing = ref(false)
const analysisStatus = ref('')
const analysisError = ref('')
const analysisResult = ref<AnalysisResult | null>(null)
const archives = ref<ArchiveItem[]>([])

// 行情历史相关状态
const marketHistoryConfig = ref({
  symbol: '',
  rangeType: 'month', // 'week', 'month', 'quarter', 'custom'
  startDate: '',
  endDate: '',
  dataLevel: 'standard', // 'lite', 'standard', 'research'
  includeIndex: true
})
const isDownloadingHistory = ref(false)
const historyStatus = ref('')
const historyProgress = ref(0)

// --- 状态定义结束 ---

// 搜索匹配逻辑
const searchResults = computed(() => {
  if (!globalSearchQuery.value) return []
  const query = globalSearchQuery.value.toLowerCase()
  return marketStore.stocks.filter(s => 
    s.code.toLowerCase().includes(query) || 
    s.name.toLowerCase().includes(query)
  ).slice(0, 10)
})

// 选择标的
const selectStock = (stock: any) => {
  selectedStock.value = stock
  globalSearchQuery.value = ''
  showSearchDropdown.value = false
  
  // 同步到各个配置中
  financeConfig.value.symbol = stock.code
  analysisSymbol.value = stock.code
  marketHistoryConfig.value.symbol = stock.code
}

// 监听配置中的 symbol 变化，反向更新全局标的 (用于点击侧边栏“本地已下载”等场景)
watch(() => financeConfig.value.symbol, (newVal) => {
  if (newVal && (!selectedStock.value || selectedStock.value.code !== newVal)) {
    const stock = marketStore.stocks.find(s => s.code === newVal)
    if (stock) selectedStock.value = stock
  }
})

const startHistoryDownload = async () => {
  if (!marketHistoryConfig.value.symbol) return
  
  isDownloadingHistory.value = true
  historyProgress.value = 0
  historyStatus.value = '准备导出任务...'
  
  let start = marketHistoryConfig.value.startDate
  let end = marketHistoryConfig.value.endDate
  
  // 如果不是自定义，则根据 rangeType 计算时间
  if (marketHistoryConfig.value.rangeType !== 'custom') {
    const now = new Date()
    end = now.toISOString().split('T')[0].replace(/-/g, '')
    
    let days = 7
    if (marketHistoryConfig.value.rangeType === 'month') days = 30
    else if (marketHistoryConfig.value.rangeType === 'quarter') days = 90
    
    const startDateObj = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)
    start = startDateObj.toISOString().split('T')[0].replace(/-/g, '')
    end = now.toISOString().split('T')[0].replace(/-/g, '')
  } else {
    // 处理自定义日期的格式 YYYYMMDD
    start = start.replace(/-/g, '')
    end = end.replace(/-/g, '')
  }

  try {
    historyStatus.value = `正在获取 ${marketHistoryConfig.value.symbol} 从 ${start} 到 ${end} 的数据...`
    historyProgress.value = 20
    
    const res = await invoke<string>('download_market_history', {
      symbol: marketHistoryConfig.value.symbol,
      startDate: start,
      endDate: end,
      path: downloadSettings.value.financePath || 'data/history',
      level: marketHistoryConfig.value.dataLevel,
      includeIndex: marketHistoryConfig.value.includeIndex
    })
    
    if (res) {
      historyStatus.value = `导出成功！文件已保存至本地目录。`
      historyProgress.value = 100
    }
  } catch (err: any) {
    historyStatus.value = `导出失败: ${err}`
    historyProgress.value = 0
  } finally {
    isDownloadingHistory.value = false
  }
}

const fundFlowChartRef = ref<HTMLElement | null>(null)
const fundFlowDetailChartRef = ref<HTMLElement | null>(null)
let fundFlowChart: echarts.ECharts | null = null
let fundFlowDetailChart: echarts.ECharts | null = null

const menuItems = [
  { id: 'market', name: '行情历史', icon: Database },
  { id: 'finance', name: '财报下载', icon: FileText },
  { id: 'dashboard', name: '分析概览', icon: Activity },
  { id: 'archives', name: '分析归档', icon: History },
  { id: 'settings', name: '设置选项', icon: Settings },
]

const analysisSubTab = ref('overview')
const analysisTabs = [
  { id: 'overview', name: '概览', icon: Activity },
  { id: 'fund_flow', name: '资金流向', icon: TrendingUp },
  { id: 'risk', name: '风险波动', icon: ShieldAlert },
  { id: 'liquidity', name: '流动性深度', icon: Droplets },
  { id: 'fundamentals', name: '财务基本面', icon: FileText },
  { id: 'industry', name: '行业相关性', icon: Network },
]

// 下载相关方法
const setFinancePath = async () => {
  try {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const selected = await open({
      directory: true,
      multiple: false,
      defaultPath: downloadSettings.value.financePath || undefined
    })
    if (selected) {
      downloadSettings.value.financePath = selected as string
      localStorage.setItem('financePath', selected as string)
    }
  } catch (err) {
    console.error('Failed to open directory dialog:', err)
  }
}

interface DownloadedItem {
  name: String;
  updated_at: number;
}

const downloadedList = ref<DownloadedItem[]>([])
const isScanning = ref(false)

const scanDownloaded = async () => {
  isScanning.value = true
  try {
    const list = await invoke<DownloadedItem[]>('list_downloaded_finance', { path: downloadSettings.value.financePath })
    downloadedList.value = list
  } catch (e) {
    console.error('扫描本地财报失败:', e)
  } finally {
    isScanning.value = false
  }
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getItemStatus = (timestamp: number) => {
  const now = Math.floor(Date.now() / 1000)
  const diff = now - timestamp
  if (diff < 3600) return { label: '刚刚更新', color: 'text-green-500 bg-green-500/10' }
  if (diff < 86400) return { label: '今日更新', color: 'text-blue-500 bg-blue-500/10' }
  return { label: '已同步', color: 'text-foreground/30 bg-foreground/5' }
}

const openDownloadFolder = async () => {
  try {
    await invoke('open_folder', { path: downloadSettings.value.financePath })
  } catch (e) {
    console.error('无法打开文件夹:', e)
  }
}

// 分析相关方法
const initFundFlowChart = (targetRef: HTMLElement | null, chartInstance: 'main' | 'detail') => {
  if (!targetRef || !analysisResult.value) return
  
  try {
    let chart = chartInstance === 'main' ? fundFlowChart : fundFlowDetailChart
    
    // 如果实例已经存在但绑定的 DOM 不同，先销毁
    if (chart) {
      if (chart.getDom() !== targetRef) {
        chart.dispose()
        chart = null
      }
    }
    
    if (!chart) {
      chart = echarts.init(targetRef)
      if (chartInstance === 'main') fundFlowChart = chart
      else fundFlowDetailChart = chart
    }

    const roseData = analysisResult.value.fund_flow.rose_chart
    const data = roseData.map(item => ({
      value: item.value,
      name: item.name,
      itemStyle: {
        color: item.type === 'inflow' 
          ? (item.name.includes('超大') ? '#ef4444' : item.name.includes('大单') ? '#f87171' : item.name.includes('中单') ? '#fca5a5' : '#fee2e2')
          : (item.name.includes('超大') ? '#22c55e' : item.name.includes('大单') ? '#4ade80' : item.name.includes('中单') ? '#86efac' : '#dcfce7')
      }
    }))
    
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        name: '资金流向', type: 'pie', radius: [20, 100], center: ['50%', '50%'],
        roseType: 'radius', itemStyle: { borderRadius: 8 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false }, data: data
      }]
    })
  } catch (err) {
    console.error('ECharts init error:', err)
  }
}

const startAnalysis = async () => {
  if (!analysisSymbol.value) return
  isAnalyzing.value = true
  analysisStatus.value = '正在初始化分析模块...'
  analysisError.value = ''
  analysisResult.value = null
  
  // 销毁旧图表
  if (fundFlowChart) { fundFlowChart.dispose(); fundFlowChart = null; }
  if (fundFlowDetailChart) { fundFlowDetailChart.dispose(); fundFlowDetailChart = null; }

  try {
    const res = await invoke<string>('run_stock_analysis', {
      symbol: analysisSymbol.value,
      path: 'data'
    })
    if (res) {
      try {
        const parsed = JSON.parse(res)
        if (parsed && parsed.symbol && parsed.fund_flow) {
          analysisResult.value = parsed
          activeCategory.value = 'dashboard'
        } else {
          throw new Error('分析结果数据格式不完整')
        }
      } catch (parseErr) {
        console.error('Failed to parse analysis result:', parseErr)
        analysisError.value = `解析结果失败: ${parseErr}`
      }
    }
  } catch (err: any) {
    analysisError.value = `分析失败: ${err}`
  } finally {
    isAnalyzing.value = false
  }
}

const loadArchives = async () => {
  try {
    const items = await invoke<ArchiveItem[]>('list_analysis_archives', { path: 'data' })
    archives.value = items
  } catch (err) {
    console.error('Failed to load archives:', err)
  }
}

const openArchiveFolder = async (name: string) => {
  try {
    await invoke('open_folder', { path: `data/${name}` })
  } catch (err) {
    console.error('Failed to open folder:', err)
  }
}

// 通用监听和钩子
watch([activeCategory, analysisSubTab], ([newCat, newSub]) => {
  if (newCat === 'dashboard') {
    if (newSub === 'overview' && analysisResult.value) {
      nextTick(() => initFundFlowChart(fundFlowChartRef.value, 'main'))
    } else if (newSub === 'fund_flow' && analysisResult.value) {
      nextTick(() => initFundFlowChart(fundFlowDetailChartRef.value, 'detail'))
    }
  }
})

watch(() => progress.value, (newVal) => {
  if (newVal === 100) {
    setTimeout(scanDownloaded, 1000)
  }
})

// 生成年份列表 (从当前年份到 1990 年)
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let y = currentYear; y >= 1990; y--) {
    years.push(y.toString())
  }
  return years
})

const reportTypes = ['一季报', '半年报', '三季报', '年报']

// 切换年份选择
const toggleYear = (year: string) => {
  const index = financeConfig.value.selectedYears.indexOf(year)
  if (index === -1) {
    financeConfig.value.selectedYears.push(year)
  } else {
    financeConfig.value.selectedYears.splice(index, 1)
  }
}

// 切换报表类型选择
const toggleType = (type: string) => {
  const index = financeConfig.value.selectedTypes.indexOf(type)
  if (index === -1) {
    financeConfig.value.selectedTypes.push(type)
  } else {
    financeConfig.value.selectedTypes.splice(index, 1)
  }
}

// 快捷选择年份
const quickSelectYears = (type: 'recent3' | 'recent5' | 'all') => {
  const currentYear = new Date().getFullYear()
  if (type === 'recent3') {
    financeConfig.value.selectedYears = [currentYear, currentYear - 1, currentYear - 2].map(String)
  } else if (type === 'recent5') {
    financeConfig.value.selectedYears = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4].map(String)
  }
}

// 开始下载财报
const startFinanceDownload = async () => {
  if (!financeConfig.value.symbol) {
    alert('请输入股票代码或名称')
    return
  }
  if (financeConfig.value.selectedYears.length === 0) {
    alert('请选择至少一个年份')
    return
  }
  if (financeConfig.value.selectedTypes.length === 0) {
    alert('请选择至少一种报表类型')
    return
  }

  isDownloading.value = true
  progress.value = 0
  statusMessage.value = '准备下载...'
  downloadWarnings.value = [] // 重置警告

  try {
    const result = await invoke('download_finance_data', {
      symbol: financeConfig.value.symbol,
      years: financeConfig.value.selectedYears.join(','),
      types: financeConfig.value.selectedTypes.join(','),
      path: downloadSettings.value.financePath
    })
    console.log('Download complete:', result)
    statusMessage.value = '同步完成'
    await scanDownloaded() // 刷新列表

    // 如果有警告，显示对话框
    if (downloadWarnings.value.length > 0) {
      showWarningDialog.value = true
    }
  } catch (error) {
    console.error('Download failed:', error)
    statusMessage.value = `下载失败: ${error}`
  } finally {
    isDownloading.value = false
  }
}

// 监听下载进度
let unlisten: any = null
let unlistenAnalysis: any = null
let unlistenHistory: any = null

const route = useRoute()

onMounted(async () => {
  // 如果全局 store 没数据，尝试从后端拉取一次基础数据
  if (marketStore.stocks.length === 0) {
    try {
      const res = await invoke<any[]>('get_stock_data')
      if (res && res.length > 0) {
        marketStore.stocks = res
        marketStore.lastUpdated = Date.now()
      }
    } catch (err) {
      console.error('Failed to init market data in Download view:', err)
    }
  }

  // 处理路由参数
  if (route.query.symbol) {
    const symbol = route.query.symbol as string
    // 尝试在现有列表中查找标的
    const stock = marketStore.stocks.find(s => s.code === symbol)
    if (stock) {
      selectStock(stock)
    } else {
      // 如果没找到（可能 marketStore 还没完全加载或 localStorage 为空），至少同步 symbol
      financeConfig.value.symbol = symbol
      analysisSymbol.value = symbol
    }

    if (route.query.mode === 'analysis') {
      activeCategory.value = 'dashboard'
      startAnalysis()
    }
  }

  // 1. 初始化路径：优先从 localStorage 获取，如果没有则使用 dataPath + \Finance
  const savedPath = localStorage.getItem('financePath')
  if (savedPath) {
    downloadSettings.value.financePath = savedPath
  } else {
    const baseDataPath = localStorage.getItem('dataPath') || 'D:\\CranePoint_Data'
    downloadSettings.value.financePath = `${baseDataPath}\\Finance`
  }
  
  // 2. 加载基础数据
  await Promise.all([
    scanDownloaded(),
    loadArchives()
  ])

  // 3. 注册 Tauri 事件监听
  try {
    unlisten = await listen('download-progress', (event: any) => {
      progress.value = event.payload.progress
      downloadStatusMessage.value = event.payload.message
      if (event.payload.warning) {
        downloadWarnings.value.push(event.payload.warning)
      }
    })
    
    unlistenAnalysis = await listen('analysis-status', (event: any) => {
      analysisStatus.value = event.payload
    })

    unlistenHistory = await listen('history-status', (event: any) => {
      historyStatus.value = event.payload
    })
  } catch (e) {
    console.warn('Tauri event listeners not available')
  }
})

onUnmounted(() => {
  if (unlisten) unlisten()
  if (unlistenAnalysis) unlistenAnalysis()
  if (unlistenHistory) unlistenHistory()
  if (fundFlowChart) {
    fundFlowChart.dispose()
    fundFlowChart = null
  }
  if (fundFlowDetailChart) {
    fundFlowDetailChart.dispose()
    fundFlowDetailChart = null
  }
})
</script>

<template>
  <div class="h-full relative">
    <SidebarLayout
    title="个股数据"
    subtitle="财报下载、行情同步与量化分析"
    :icon="Database"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <!-- 顶部操作栏 -->
    <template #header-extra>
      <div class="flex-1 flex items-center justify-between">
        <!-- 左侧：全局标的选择器 -->
        <div class="flex items-center gap-3">
          <div class="relative group">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/30 group-focus-within:text-primary transition-colors" />
            <input 
              v-model="globalSearchQuery"
              @focus="showSearchDropdown = true"
              @input="showSearchDropdown = true"
              type="text" 
              placeholder="输入代码或名称"
              class="pl-9 pr-4 py-2 bg-foreground/5 border border-foreground/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-80"
            />
            
            <!-- 搜索下拉列表 -->
            <div v-if="showSearchDropdown && searchResults.length > 0" 
                 class="absolute top-full left-0 right-0 mt-2 bg-background border border-foreground/10 rounded-xl shadow-xl overflow-hidden z-50">
              <div 
                v-for="stock in searchResults" 
                :key="stock.code"
                @click="selectStock(stock)"
                class="px-4 py-2.5 hover:bg-foreground/5 cursor-pointer flex items-center justify-between group/item transition-colors"
              >
                <div class="flex flex-col">
                  <span class="text-sm font-medium group-hover/item:text-primary transition-colors">{{ stock.name }}</span>
                  <span class="text-xs text-foreground/40">{{ stock.code }}</span>
                </div>
                <ChevronRight class="w-4 h-4 text-foreground/20 group-hover/item:text-primary transition-all transform translate-x-0 group-hover/item:translate-x-1" />
              </div>
            </div>
            
            <!-- 点击外部关闭下拉框 -->
            <div v-if="showSearchDropdown" @click="showSearchDropdown = false" class="fixed inset-0 z-40"></div>
          </div>

          <!-- 选中标的信息展示 -->
          <div v-if="selectedStock" class="flex items-center gap-2 px-3 py-1.5 bg-primary/10 rounded-lg border border-primary/20 animate-in fade-in slide-in-from-left-2 duration-300">
            <div class="flex flex-col">
              <span class="text-sm font-bold text-primary leading-none">{{ selectedStock.name }}</span>
              <span class="text-[10px] text-primary/60 font-mono mt-0.5">{{ selectedStock.code }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧：功能按钮 -->
        <div class="flex items-center gap-2 border-l border-foreground/10 pl-4">
          <!-- 分析按钮 -->
          <button 
            v-if="['dashboard', 'finance', 'market'].includes(activeCategory)"
            @click="startAnalysis"
            :disabled="isAnalyzing || !selectedStock"
            class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:active:scale-100 transition-all shadow-sm"
          >
            <Loader2 v-if="isAnalyzing" class="w-4 h-4 animate-spin" />
            <TrendingUp v-else class="w-4 h-4" />
            开始分析
          </button>

          <!-- 财报下载按钮 -->
          <button 
            v-if="activeCategory === 'finance'"
            @click="startFinanceDownload"
            :disabled="isDownloading || !selectedStock"
            class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:active:scale-100 transition-all shadow-sm"
          >
            <Download v-if="!isDownloading" class="w-4 h-4" />
            <RefreshCw v-else class="w-4 h-4 animate-spin" />
            {{ isDownloading ? '下载中...' : '下载财报' }}
          </button>

          <!-- 行情导出按钮 -->
          <button 
            v-if="activeCategory === 'market'"
            @click="startHistoryDownload"
            :disabled="isDownloadingHistory || !selectedStock"
            class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:active:scale-100 transition-all shadow-sm"
          >
            <Database v-if="!isDownloadingHistory" class="w-4 h-4" />
            <RefreshCw v-else class="w-4 h-4 animate-spin" />
            {{ isDownloadingHistory ? '导出中...' : '导出行情' }}
          </button>
        </div>
      </div>
    </template>

    <template #default="{ activeId }">
      <!-- 量化分析概览 -->
      <div v-if="activeId === 'dashboard'" class="h-full flex flex-col">
        <!-- 空状态 -->
        <div v-if="!analysisResult" class="flex-1 flex flex-col items-center justify-center text-center max-w-2xl mx-auto">
          <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary">
            <Activity class="w-10 h-10" v-if="!isAnalyzing && !analysisError" />
            <Loader2 class="w-10 h-10 animate-spin" v-else-if="isAnalyzing" />
            <AlertCircle class="w-10 h-10 text-red-500" v-else />
          </div>
          <h2 class="text-2xl font-semibold mb-2">
            {{ isAnalyzing ? '深度分析中' : (analysisError ? '分析失败' : '量化分析引擎') }}
          </h2>
          <p class="text-foreground/50 mb-8">
            <template v-if="isAnalyzing">
              {{ analysisStatus }}
            </template>
            <template v-else-if="analysisError">
              <span class="text-red-500">{{ analysisError }}</span>
            </template>
            <template v-else>
              请在顶部搜索框选择标的并点击开始分析，系统将从波动率、流动性、资金流、基本面及行业相关性维度进行深度扫描。
            </template>
          </p>
        </div>

        <!-- 分析结果展示 -->
        <div v-else class="flex-1 flex flex-col min-h-0">
          <!-- 子标签导航 -->
          <div class="flex-none px-6 py-2 border-b border-foreground/5 flex items-center gap-1 overflow-x-auto no-scrollbar">
            <button 
              v-for="tab in analysisTabs" 
              :key="tab.id"
              @click="analysisSubTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all whitespace-nowrap',
                analysisSubTab === tab.id 
                  ? 'bg-primary text-primary-foreground shadow-sm' 
                  : 'text-foreground/50 hover:bg-foreground/5 hover:text-foreground'
              ]"
            >
              <component :is="tab.icon" class="w-4 h-4" />
              {{ tab.name }}
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            <!-- 概览 Overview -->
            <div v-if="analysisSubTab === 'overview'" class="grid grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="col-span-3 bg-foreground/5 border border-foreground/10 rounded-2xl p-6 flex items-center justify-between">
                <div>
                  <div class="text-foreground/50 text-sm mb-1">正在分析</div>
                  <div class="text-2xl font-bold flex items-center gap-2">
                    {{ analysisResult.name }}
                    <span class="text-sm font-normal text-foreground/30">{{ analysisResult.symbol }}</span>
                  </div>
                </div>
                <div class="flex gap-4">
                  <div class="text-right">
                    <div class="text-foreground/50 text-xs mb-1">HV20 波动率</div>
                    <div class="text-lg font-mono">{{ analysisResult.risk.hv20 }}%</div>
                  </div>
                  <div class="w-px h-10 bg-foreground/10"></div>
                  <div class="text-right">
                    <div class="text-foreground/50 text-xs mb-1">一周主力净额</div>
                    <div :class="['text-lg font-mono', analysisResult.fund_flow.weekly_main_net >= 0 ? 'text-red-500' : 'text-green-500']">
                      {{ analysisResult.fund_flow.weekly_main_net.toFixed(2) }} 万
                    </div>
                  </div>
                </div>
              </div>

              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-4">
                <div class="flex items-center gap-2 text-foreground/50 text-sm mb-3">
                  <Droplets class="w-4 h-4" /> 流动性评估
                </div>
                <div class="text-xl font-bold mb-1">{{ analysisResult.liquidity.score }}</div>
                <div class="text-xs text-foreground/30">基于五档挂单深度与成交量</div>
              </div>

              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-4">
                <div class="flex items-center gap-2 text-foreground/50 text-sm mb-3">
                  <FileText class="w-4 h-4" /> 盈利能力
                </div>
                <div class="text-xl font-bold mb-1">{{ analysisResult.fundamentals.deduct_net_profit }}</div>
                <div class="text-xs text-foreground/30">{{ analysisResult.fundamentals.report_period }} 扣非净利润</div>
              </div>

              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-4">
                <div class="flex items-center gap-2 text-foreground/50 text-sm mb-3">
                  <Network class="w-4 h-4" /> 行业相关性
                </div>
                <div class="text-xl font-bold mb-1">{{ (analysisResult.industry.correlation * 100).toFixed(1) }}%</div>
                <div class="text-xs text-foreground/30">Pearson 相关系数</div>
              </div>

              <div class="col-span-2 bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
                <h3 class="font-medium mb-4 flex items-center gap-2">
                  <TrendingUp class="w-4 h-4" /> 资金博弈分布
                </h3>
                <div class="h-64" ref="fundFlowChartRef"></div>
              </div>

              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
                <h3 class="font-medium mb-4 flex items-center gap-2">
                  <History class="w-4 h-4" /> 近期行情
                </h3>
                <div class="space-y-3">
                  <div v-for="(item, idx) in analysisResult.history.slice(0, 5)" :key="idx" class="flex items-center justify-between text-sm">
                    <span class="text-foreground/50">{{ item.日期 }}</span>
                    <span :class="item.涨跌幅 >= 0 ? 'text-red-500' : 'text-green-500'">{{ item.收盘 }}</span>
                  </div>
                  <button @click="activeCategory = 'archives'" class="w-full mt-4 py-2 text-xs text-primary hover:underline">查看分析归档</button>
                </div>
              </div>
            </div>

            <!-- 资金流向模块 -->
            <div v-if="analysisSubTab === 'fund_flow'" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="grid grid-cols-2 gap-6">
                <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
                  <h3 class="font-medium mb-6">主力资金分布 (极坐标)</h3>
                  <div class="h-80" ref="fundFlowDetailChartRef"></div>
                </div>
                <div class="space-y-4">
                  <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
                    <h3 class="font-medium mb-4">资金流向统计</h3>
                    <div class="space-y-4">
                      <div class="flex justify-between items-center">
                        <span class="text-sm text-foreground/50">当日主力净额</span>
                        <span :class="['font-mono font-bold', (analysisResult.fund_flow.details[0]?.主力 || 0) >= 0 ? 'text-red-500' : 'text-green-500']">
                          {{ (analysisResult.fund_flow.details[0]?.主力 || 0).toFixed(2) }} 万
                        </span>
                      </div>
                      <div class="flex justify-between items-center">
                        <span class="text-sm text-foreground/50">近一周累计净额</span>
                        <span :class="['font-mono font-bold', analysisResult.fund_flow.weekly_main_net >= 0 ? 'text-red-500' : 'text-green-500']">
                          {{ analysisResult.fund_flow.weekly_main_net.toFixed(2) }} 万
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="bg-red-500/5 border border-red-500/10 rounded-2xl p-4">
                    <div class="text-xs text-red-500/50 mb-1 font-medium">最新资金流入构成</div>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                      <div v-for="item in analysisResult.fund_flow.rose_chart.filter(i => i.type === 'inflow')" :key="item.name" class="p-2 bg-red-500/10 rounded-lg">
                        {{ item.name.split('(')[0] }}: {{ item.raw.toFixed(1) }} 万
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 风险与波动模块 -->
            <div v-if="analysisSubTab === 'risk'" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="grid grid-cols-2 gap-6">
                <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
                  <div class="text-sm text-foreground/50 mb-2">20日历史波动率 (HV20)</div>
                  <div class="text-5xl font-mono font-bold text-primary">{{ analysisResult.risk.hv20 }}%</div>
                </div>
                <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
                  <div class="text-sm text-foreground/50 mb-2">60日历史波动率 (HV60)</div>
                  <div class="text-5xl font-mono font-bold text-foreground/70">{{ analysisResult.risk.hv60 }}%</div>
                </div>
              </div>
            </div>

            <!-- 流动性深度 -->
            <div v-if="analysisSubTab === 'liquidity'" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
                <h3 class="font-medium mb-6">盘口深度评估</h3>
                <div class="grid grid-cols-2 gap-12">
                  <div class="bg-red-500/5 p-8 rounded-2xl text-center border border-red-500/10">
                    <div class="text-sm text-red-500/50 mb-2">买盘五档总深度</div>
                    <div class="text-4xl font-mono font-bold">{{ analysisResult.liquidity.bid_depth }} <span class="text-sm font-normal">手</span></div>
                  </div>
                  <div class="bg-green-500/5 p-8 rounded-2xl text-center border border-green-500/10">
                    <div class="text-sm text-green-500/50 mb-2">卖盘五档总深度</div>
                    <div class="text-4xl font-mono font-bold">{{ analysisResult.liquidity.ask_depth }} <span class="text-sm font-normal">手</span></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 财务基本面 -->
            <div v-if="analysisSubTab === 'fundamentals'" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8">
                <div class="flex items-center justify-between mb-8">
                  <h3 class="text-xl font-bold">最新财务摘要</h3>
                  <span class="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">{{ analysisResult.fundamentals.report_period }} 报告期</span>
                </div>
                <div class="p-6 bg-foreground/5 rounded-2xl border border-foreground/5">
                  <div class="text-sm text-foreground/50 mb-2">扣除非经常性损益后的净利润</div>
                  <div class="text-3xl font-mono font-bold">{{ analysisResult.fundamentals.deduct_net_profit }}</div>
                </div>
              </div>
            </div>

            <!-- 行业相关性 -->
            <div v-if="analysisSubTab === 'industry'" class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
                <div class="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 text-primary">
                  <Network class="w-8 h-8" />
                </div>
                <h3 class="text-lg font-medium mb-1">{{ analysisResult.industry.name }}</h3>
                <div class="max-w-md mx-auto">
                  <div class="flex justify-between text-sm mb-2">
                    <span class="text-foreground/50">行业走势相关度</span>
                    <span class="font-bold">{{ (analysisResult.industry.correlation * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="h-3 bg-foreground/5 rounded-full overflow-hidden">
                    <div class="h-full bg-primary transition-all duration-1000" :style="{ width: (analysisResult.industry.correlation * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分析归档列表 -->
      <div v-if="activeId === 'archives'" class="p-6 h-full overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-medium flex items-center gap-2">
            <History class="w-5 h-5" /> 历史分析记录
          </h3>
          <button @click="loadArchives" class="p-2 hover:bg-foreground/5 rounded-lg transition-colors">
            <RefreshCw class="w-4 h-4" />
          </button>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div 
            v-for="item in archives" 
            :key="item.name"
            class="group bg-foreground/5 border border-foreground/10 rounded-2xl p-4 hover:border-primary/50 transition-all cursor-pointer"
            @click="openArchiveFolder(item.name)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                  <FolderOpen class="w-5 h-5" />
                </div>
                <div>
                  <div class="font-medium group-hover:text-primary transition-colors">{{ item.name }}</div>
                  <div class="text-xs text-foreground/30">{{ formatTime(item.updated_at) }}</div>
                </div>
              </div>
              <ChevronRight class="w-4 h-4 text-foreground/20 group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        </div>
      </div>

      <!-- 财报下载 -->
      <div v-if="activeId === 'finance'" class="flex flex-col h-full overflow-y-auto pr-4 custom-scrollbar">
        <div class="flex items-center justify-between mb-6 shrink-0">
          <div>
            <h2 class="text-2xl font-semibold mb-1">财报数据下载</h2>
            <p class="text-sm text-foreground/50">获取 A 股上市公司的标准化财务报表数据</p>
          </div>
          <div v-if="isDownloading" class="flex items-center gap-3 bg-primary/10 px-4 py-2 rounded-full">
            <div class="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            <span class="text-xs font-bold text-primary">{{ statusMessage }}</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
          <!-- 左侧配置区 -->
          <div class="flex flex-col gap-6">
            <!-- 报表类型 -->
            <div class="space-y-3">
              <label class="text-sm font-semibold text-foreground/70 flex items-center gap-2">
                <Layers class="w-4 h-4" /> 报表类型 (多选)
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button 
                  v-for="type in reportTypes"
                  :key="type"
                  @click="toggleType(type)"
                  :class="[
                    'px-4 py-2.5 text-sm rounded-xl border transition-all flex items-center justify-between group',
                    financeConfig.selectedTypes.includes(type)
                      ? 'bg-primary/5 border-primary text-primary font-medium'
                      : 'bg-background border-thin text-foreground/60 hover:border-primary/30'
                  ]"
                >
                  {{ type }}
                  <div :class="[
                    'w-4 h-4 rounded-full border flex items-center justify-center transition-colors',
                    financeConfig.selectedTypes.includes(type) ? 'bg-primary border-primary' : 'border-thin group-hover:border-primary/50'
                  ]">
                    <div v-if="financeConfig.selectedTypes.includes(type)" class="w-1.5 h-1.5 bg-white rounded-full"></div>
                  </div>
                </button>
              </div>
            </div>

            <!-- 披露年份 -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-sm font-semibold text-foreground/70 flex items-center gap-2">
                  <Calendar class="w-4 h-4" /> 披露年份 (多选)
                </label>
                <div class="flex gap-2">
                  <button @click="quickSelectYears('recent3')" class="text-[10px] px-2 py-1 bg-foreground/5 rounded-md hover:bg-foreground/10 transition-colors">近3年</button>
                  <button @click="quickSelectYears('recent5')" class="text-[10px] px-2 py-1 bg-foreground/5 rounded-md hover:bg-foreground/10 transition-colors">近5年</button>
                </div>
              </div>
              <div class="bg-background border border-thin rounded-xl p-3">
                <div class="grid grid-cols-4 gap-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                  <button 
                    v-for="year in availableYears"
                    :key="year"
                    @click="toggleYear(year)"
                    :class="[
                      'py-2 text-xs rounded-lg border transition-all',
                      financeConfig.selectedYears.includes(year)
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background border-thin text-foreground/60 hover:bg-foreground/5'
                    ]"
                  >
                    {{ year }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 选中的标的信息提示 -->
            <div v-if="!selectedStock" class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
              <AlertCircle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <div class="text-sm font-bold text-amber-600 mb-0.5">未选择标的</div>
                <div class="text-xs text-amber-600/70">请在顶部搜索框输入并选择一个股票标的以开始下载任务。</div>
              </div>
            </div>
          </div>

          <!-- 右侧：本地已下载栏目 -->
        <div class="flex flex-col bg-foreground/[0.02] border border-thin rounded-2xl overflow-hidden min-h-[500px]">
            <div class="p-4 border-b border-thin flex items-center justify-between shrink-0 bg-background/50 backdrop-blur-sm">
              <div class="flex items-center gap-2">
                <Database class="w-4 h-4 text-primary" />
                <span class="text-sm font-semibold">本地已下载标的</span>
                <span class="px-1.5 py-0.5 bg-foreground/10 rounded text-[10px] text-foreground/50 font-mono">{{ downloadedList.length }}</span>
              </div>
              <div class="flex items-center gap-1">
                <button 
                  @click="scanDownloaded"
                  class="p-2 hover:bg-foreground/10 rounded-lg transition-colors group"
                  title="刷新列表"
                >
                  <RefreshCw :class="['w-4 h-4 text-foreground/50 group-hover:text-primary', isScanning ? 'animate-spin' : '']" />
                </button>
                <button 
                  @click="openDownloadFolder"
                  class="p-2 hover:bg-foreground/10 rounded-lg transition-colors group"
                  title="打开保存目录"
                >
                  <FolderOpen class="w-4 h-4 text-foreground/50 group-hover:text-primary" />
                </button>
              </div>
            </div>
            
            <div class="flex-1 overflow-y-auto custom-scrollbar p-2">
              <div v-if="downloadedList.length > 0" class="grid grid-cols-1 gap-1">
                <div 
                  v-for="item in downloadedList" 
                  :key="item.name.toString()"
                  class="flex items-center justify-between p-3 rounded-xl hover:bg-background border border-transparent hover:border-thin transition-all group"
                >
                  <div class="flex items-center gap-3 overflow-hidden">
                    <div class="p-2 bg-primary/5 rounded-lg text-primary shrink-0">
                      <FileText class="w-4 h-4" />
                    </div>
                    <div class="overflow-hidden">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-medium truncate">{{ item.name.split('_')[1] || item.name }}</span>
                        <span 
                          :class="[
                            'px-1.5 py-0.5 rounded text-[9px] font-bold whitespace-nowrap',
                            getItemStatus(item.updated_at).color
                          ]"
                        >
                          {{ getItemStatus(item.updated_at).label }}
                        </span>
                      </div>
                      <div class="flex items-center gap-2 mt-0.5">
                        <span class="text-[10px] text-foreground/40 font-mono">{{ item.name.split('_')[0] }}</span>
                        <span class="text-[9px] text-foreground/30 flex items-center gap-1">
                          <Clock class="w-2.5 h-2.5" /> {{ formatTime(item.updated_at) }} 导入
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-1 shrink-0">
                    <button 
                      @click="() => {
                        const code = item.name.split('_')[0];
                        const stock = marketStore.stocks.find(s => s.code === code);
                        if (stock) selectStock(stock);
                        else financeConfig.symbol = code; // Fallback
                      }"
                      class="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-primary/10 rounded-md text-primary transition-all"
                      title="快速选择"
                    >
                      <ExternalLink class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="h-full flex flex-col items-center justify-center text-foreground/20 py-12">
                <Clock class="w-12 h-12 mb-3 opacity-10" />
                <p class="text-sm">暂无本地下载记录</p>
                <p class="text-[11px] mt-1">开始下载后将自动同步至此处</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作区 -->
        <div class="shrink-0 flex flex-col items-center pb-10">
          <div v-if="isDownloading" class="w-full max-w-2xl mb-4">
            <div class="flex justify-between text-xs font-medium mb-1.5">
              <span class="text-foreground/60">正在为您同步数据...</span>
              <span class="text-primary font-mono">{{ progress }}%</span>
            </div>
            <div class="w-full h-1.5 bg-foreground/5 rounded-full overflow-hidden">
              <div 
                class="h-full bg-primary transition-all duration-300 ease-out shadow-[0_0_8px_rgba(var(--color-primary),0.3)]"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
          </div>

          <button 
            @click="startFinanceDownload"
            :disabled="isDownloading"
            class="px-20 py-4 bg-primary text-primary-foreground rounded-2xl font-bold shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100 transition-all flex items-center gap-3"
          >
            <Download v-if="!isDownloading" class="w-5 h-5" />
            <div v-else class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            {{ isDownloading ? '同步中...' : '开始同步财报数据' }}
          </button>
        </div>
      </div>

      <!-- 下载进度浮窗 -->
      <div v-if="isDownloading" class="fixed bottom-8 right-8 w-80 bg-background border border-foreground/10 rounded-2xl shadow-2xl p-4 animate-in slide-in-from-bottom-4">
        <div class="flex items-center justify-between mb-3">
          <div class="text-sm font-medium flex items-center gap-2">
            <RefreshCw class="w-4 h-4 animate-spin text-primary" />
            正在同步数据...
          </div>
          <span class="text-xs font-mono text-primary">{{ progress }}%</span>
        </div>
        <div class="h-2 bg-foreground/5 rounded-full overflow-hidden mb-2">
          <div class="h-full bg-primary transition-all duration-300" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="text-[10px] text-foreground/40 truncate">{{ downloadStatusMessage }}</div>
      </div>

      <!-- 行情历史 -->
      <div v-if="activeId === 'market'" class="h-full flex flex-col p-8 overflow-hidden">
        <div class="flex-none mb-8">
          <div class="flex items-center gap-4 mb-2">
            <div class="p-3 bg-primary/10 rounded-2xl text-primary">
              <Database class="w-6 h-6" />
            </div>
            <div>
              <h2 class="text-2xl font-bold">行情历史导出</h2>
              <p class="text-sm text-foreground/50">支持 A 股历史 K 线数据的自定义范围导出</p>
            </div>
          </div>
        </div>

        <div class="flex-1 flex gap-8 min-h-0">
          <!-- 左侧：导出配置 -->
          <div class="w-96 flex flex-col gap-6">
            <div class="bg-card border border-thin rounded-3xl p-6 space-y-6 shadow-sm">
              <!-- 时间范围预设 -->
              <div class="space-y-3">
                <label class="text-sm font-semibold text-foreground/70 flex items-center gap-2 px-1">
                  <Calendar class="w-4 h-4" /> 时间范围
                </label>
                <div class="grid grid-cols-2 gap-2">
                  <button 
                    v-for="range in [
                      { id: 'week', name: '最近一周' },
                      { id: 'month', name: '最近一月' },
                      { id: 'quarter', name: '最近一季' },
                      { id: 'custom', name: '自定义' }
                    ]"
                    :key="range.id"
                    @click="marketHistoryConfig.rangeType = range.id"
                    :class="[
                      'px-4 py-2.5 rounded-xl text-sm font-medium transition-all border',
                      marketHistoryConfig.rangeType === range.id
                        ? 'bg-primary text-primary-foreground border-primary shadow-sm shadow-primary/20'
                        : 'bg-foreground/5 border-transparent hover:bg-foreground/10 text-foreground/60'
                    ]"
                  >
                    {{ range.name }}
                  </button>
                </div>
              </div>

              <!-- 自定义时间 -->
              <div v-if="marketHistoryConfig.rangeType === 'custom'" class="space-y-4 animate-in slide-in-from-top-2 duration-200">
                <div class="grid grid-cols-2 gap-3">
                  <div class="space-y-1.5">
                    <span class="text-[10px] text-foreground/40 font-bold uppercase ml-1">开始日期</span>
                    <input 
                      v-model="marketHistoryConfig.startDate"
                      type="date" 
                      class="w-full px-3 py-2 bg-foreground/5 border border-thin rounded-xl text-xs outline-none focus:ring-1 focus:ring-primary/30"
                    />
                  </div>
                  <div class="space-y-1.5">
                    <span class="text-[10px] text-foreground/40 font-bold uppercase ml-1">结束日期</span>
                    <input 
                      v-model="marketHistoryConfig.endDate"
                      type="date" 
                      class="w-full px-3 py-2 bg-foreground/5 border border-thin rounded-xl text-xs outline-none focus:ring-1 focus:ring-primary/30"
                    />
                  </div>
                </div>
              </div>

              <!-- 数据粒度 -->
              <div class="space-y-3">
                <label class="text-sm font-semibold text-foreground/70 flex items-center gap-2 px-1">
                  <Layers class="w-4 h-4" /> 数据粒度
                </label>
                <div class="space-y-2">
                  <button 
                    v-for="level in [
                      { id: 'lite', name: '精简版', desc: '基础量价, 占用极小' },
                      { id: 'standard', name: '标准版', desc: '含复权因子, 适合回测' },
                      { id: 'research', name: '研究版', desc: '含市值/盘口, 深度量化' }
                    ]"
                    :key="level.id"
                    @click="marketHistoryConfig.dataLevel = level.id"
                    :class="[
                      'w-full flex items-center justify-between px-4 py-3 rounded-2xl transition-all border group',
                      marketHistoryConfig.dataLevel === level.id
                        ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10'
                        : 'bg-foreground/5 border-transparent hover:border-foreground/10'
                    ]"
                  >
                    <div class="flex flex-col items-start">
                      <span :class="['text-sm font-bold', marketHistoryConfig.dataLevel === level.id ? 'text-primary' : 'text-foreground/80']">{{ level.name }}</span>
                      <span class="text-[10px] text-foreground/40">{{ level.desc }}</span>
                    </div>
                    <div 
                      :class="[
                        'w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all',
                        marketHistoryConfig.dataLevel === level.id ? 'border-primary bg-primary' : 'border-foreground/20'
                      ]"
                    >
                      <div v-if="marketHistoryConfig.dataLevel === level.id" class="w-1.5 h-1.5 bg-white rounded-full"></div>
                    </div>
                  </button>
                </div>
              </div>

              <!-- 额外选项 -->
              <div class="pt-2">
                <label class="flex items-center gap-3 px-2 cursor-pointer group">
                  <div class="relative flex items-center">
                    <input 
                      type="checkbox" 
                      v-model="marketHistoryConfig.includeIndex"
                      class="peer sr-only"
                    />
                    <div class="w-9 h-5 bg-foreground/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                  </div>
                  <div class="flex flex-col">
                    <span class="text-xs font-semibold text-foreground/70">同步基准指数</span>
                    <span class="text-[10px] text-foreground/40">默认同步上证/沪深300用于对齐分析</span>
                  </div>
                </label>
              </div>

              <!-- 选中的标的信息提示 -->
              <div v-if="!selectedStock" class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
                <AlertCircle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <div class="text-sm font-bold text-amber-600 mb-0.5">未选择标的</div>
                  <div class="text-xs text-amber-600/70">请在顶部搜索框输入并选择一个股票标的以开始导出任务。</div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="pt-4">
                <button 
                  @click="startHistoryDownload"
                  :disabled="!selectedStock || isDownloadingHistory"
                  class="w-full py-4 bg-primary text-primary-foreground rounded-2xl font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100 transition-all flex items-center justify-center gap-3"
                >
                  <Download v-if="!isDownloadingHistory" class="w-5 h-5" />
                  <Loader2 v-else class="w-5 h-5 animate-spin" />
                  {{ isDownloadingHistory ? '正在同步数据...' : '开始导出历史行情' }}
                </button>
              </div>
            </div>

            <!-- 提示卡片 -->
            <div class="bg-primary/5 border border-primary/10 rounded-2xl p-4 flex gap-3">
              <AlertCircle class="w-5 h-5 text-primary shrink-0" />
              <p class="text-[11px] text-primary/70 leading-relaxed">
                历史行情数据包含：开盘价、收盘价、最高价、最低价、成交量、成交额、振幅、涨跌幅、涨跌额及换手率。导出文件将默认为 CSV 格式。
              </p>
            </div>
          </div>

          <!-- 右侧：导出日志/预览 -->
          <div class="flex-1 bg-card border border-thin rounded-3xl flex flex-col overflow-hidden shadow-sm relative">
            <div class="p-4 border-b border-thin flex items-center justify-between bg-foreground/[0.02]">
              <span class="text-xs font-bold text-foreground/40 uppercase tracking-wider">执行日志</span>
              <div v-if="isDownloadingHistory" class="flex items-center gap-2">
                <span class="text-[10px] text-primary font-mono animate-pulse">{{ historyProgress }}%</span>
                <div class="w-24 h-1 bg-primary/10 rounded-full overflow-hidden">
                  <div class="h-full bg-primary transition-all duration-300" :style="{ width: historyProgress + '%' }"></div>
                </div>
              </div>
            </div>
            
            <div class="flex-1 p-6 font-mono text-xs overflow-y-auto custom-scrollbar space-y-2 bg-black/[0.02]">
              <div v-if="!historyStatus && !isDownloadingHistory" class="h-full flex flex-col items-center justify-center text-foreground/20 space-y-3">
                <Activity class="w-8 h-8 opacity-20" />
                <p>等待任务启动...</p>
              </div>
              <div v-else class="space-y-1">
                <div class="flex gap-3 text-foreground/40">
                  <span class="shrink-0 text-primary/50">[{{ new Date().toLocaleTimeString() }}]</span>
                  <span class="text-foreground/80">{{ historyStatus }}</span>
                </div>
                <!-- 这里可以扩展更多日志行 -->
              </div>
            </div>

            <!-- 导出完成后的快速操作 -->
            <div v-if="!isDownloadingHistory && historyStatus.includes('成功')" class="p-4 border-t border-thin bg-green-500/5 flex items-center justify-between animate-in fade-in slide-in-from-bottom-2">
              <div class="flex items-center gap-2 text-green-600 text-xs font-medium">
                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                导出任务已完成
              </div>
              <button @click="openDownloadFolder" class="flex items-center gap-2 text-xs text-primary hover:underline">
                <FolderOpen class="w-4 h-4" /> 查看文件
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 设置 -->
      <div v-if="activeId === 'settings'" class="p-8 h-full overflow-y-auto max-w-2xl mx-auto space-y-8">
        <div class="bg-foreground/5 border border-foreground/10 rounded-3xl p-8">
          <h3 class="text-xl font-bold mb-6 flex items-center gap-2">
            <Settings class="w-6 h-6 text-primary" />
            数据存储配置
          </h3>
          
          <div class="space-y-6">
            <div>
              <label class="block text-sm font-medium text-foreground/50 mb-2">财报存储路径</label>
              <div class="flex gap-2">
                <input 
                  type="text" 
                  readonly
                  :value="downloadSettings.financePath"
                  class="flex-1 px-4 py-2 bg-foreground/5 border border-foreground/10 rounded-xl text-sm text-foreground/50 outline-none"
                />
                <button 
                  @click="setFinancePath"
                  class="px-4 py-2 bg-foreground/5 hover:bg-foreground/10 border border-foreground/10 rounded-xl text-sm transition-colors flex items-center gap-2"
                >
                  <FolderOpen class="w-4 h-4" />
                  浏览
                </button>
              </div>
              <p class="mt-2 text-[10px] text-foreground/30">财报 PDF 将保存至该目录下的具体年份子目录中</p>
            </div>

            <div class="pt-6 border-t border-foreground/5">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-sm font-medium">自动打开目录</div>
                  <div class="text-xs text-foreground/30">下载完成后自动在资源管理器中定位文件</div>
                </div>
                <div class="w-10 h-5 bg-primary/20 rounded-full relative cursor-not-allowed opacity-50">
                  <div class="absolute right-1 top-1 w-3 h-3 bg-primary rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SidebarLayout>

  <!-- 警告对话框 -->
  <div v-if="showWarningDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
    <div class="bg-background border border-foreground/10 rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-200">
      <div class="p-6 border-b border-foreground/5 flex items-center justify-between bg-yellow-500/5">
        <div class="flex items-center gap-3 text-yellow-600">
          <AlertCircle class="w-6 h-6" />
          <h3 class="text-lg font-bold">同步完成但存在部分异常</h3>
        </div>
        <button @click="showWarningDialog = false" class="p-2 hover:bg-foreground/5 rounded-xl transition-colors">
          <XCircle class="w-5 h-5 text-foreground/30" />
        </button>
      </div>
      
      <div class="p-6 max-h-[60vh] overflow-y-auto">
        <div class="space-y-3">
          <div v-for="(warn, idx) in downloadWarnings" :key="idx" class="flex gap-3 p-3 bg-yellow-500/5 border border-yellow-500/10 rounded-xl text-sm text-yellow-700/80">
            <span class="font-mono text-xs opacity-50 mt-0.5">{{ idx + 1 }}.</span>
            {{ warn }}
          </div>
        </div>
      </div>

      <div class="p-6 bg-foreground/5 border-t border-foreground/5 flex justify-end">
        <button 
          @click="showWarningDialog = false"
          class="px-6 py-2 bg-foreground/10 hover:bg-foreground/20 rounded-xl text-sm font-medium transition-all"
        >
          我知道了
        </button>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-foreground) 10%, transparent);
  border-radius: 10px;
}
</style>
