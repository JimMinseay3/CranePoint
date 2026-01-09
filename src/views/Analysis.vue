<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import SidebarLayout from '../components/SidebarLayout.vue'
import * as echarts from 'echarts'
import { 
  LineChart, 
  TrendingUp, 
  ShieldAlert,
  Droplets,
  Activity,
  FileText,
  Network,
  History,
  Search,
  Loader2,
  AlertCircle,
  ChevronRight,
  Download,
  FolderOpen
} from 'lucide-vue-next'

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

const activeCategory = ref('dashboard')
const symbol = ref('')
const isLoading = ref(false)
const statusMessage = ref('')
const analysisResult = ref<AnalysisResult | null>(null)
const archives = ref<ArchiveItem[]>([])

const menuItems = [
  { id: 'dashboard', name: '分析概览', icon: Activity },
  { id: 'fund_flow', name: '资金流向', icon: TrendingUp },
  { id: 'risk', name: '风险波动', icon: ShieldAlert },
  { id: 'liquidity', name: '流动性深度', icon: Droplets },
  { id: 'fundamentals', name: '财务基本面', icon: FileText },
  { id: 'industry', name: '行业相关性', icon: Network },
  { id: 'archives', name: '历史归档', icon: History }
]

const fundFlowChartRef = ref<HTMLElement | null>(null)
let fundFlowChart: echarts.ECharts | null = null

const initFundFlowChart = () => {
  if (!fundFlowChartRef.value || !analysisResult.value) return
  
  if (!fundFlowChart) {
    fundFlowChart = echarts.init(fundFlowChartRef.value)
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

  fundFlowChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        name: '资金流向',
        type: 'pie',
        radius: [20, 100],
        center: ['50%', '50%'],
        roseType: 'radius',
        itemStyle: {
          borderRadius: 8
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data
      }
    ]
  })
}

const startAnalysis = async () => {
  if (!symbol.value) return
  
  console.log(`[Analysis] 开始分析股票: ${symbol.value}`)
  isLoading.value = true
  statusMessage.value = '正在初始化分析模块...'
  analysisResult.value = null
  
  try {
    console.log('[Analysis] 准备进入 invoke, 参数:', { symbol: symbol.value, path: 'data' })
    console.log('[Analysis] 正在调用 Tauri 命令: run_stock_analysis')
    const res = await invoke<string>('run_stock_analysis', {
      symbol: symbol.value,
      path: 'data'
    })
    
    console.log('[Analysis] 收到原始响应数据长度:', res ? res.length : 0)
    
    if (res) {
      try {
        const parsedData = JSON.parse(res)
        console.log('[Analysis] JSON 解析成功:', parsedData)
        analysisResult.value = parsedData
        activeCategory.value = 'dashboard'
        await nextTick()
        if (activeCategory.value === 'fund_flow' || activeCategory.value === 'dashboard') {
          initFundFlowChart()
        }
        loadArchives()
      } catch (parseErr) {
        console.error('[Analysis] JSON 解析失败:', parseErr, '原始数据:', res)
        statusMessage.value = `解析数据失败: ${parseErr}`
      }
    } else {
      console.warn('[Analysis] 收到空响应')
      statusMessage.value = '分析结束，但未收到有效数据'
    }
  } catch (err: any) {
    console.error('[Analysis] 命令调用捕获到异常:', err)
    statusMessage.value = `分析失败: ${err}`
  } finally {
    isLoading.value = false
    console.log('[Analysis] 分析流程结束')
  }
}

const loadArchives = async () => {
  try {
    const items = await invoke<ArchiveItem[]>('list_downloaded_finance', {
      path: 'data'
    })
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

onMounted(() => {
  loadArchives()
  listen('analysis-status', (event) => {
    statusMessage.value = (event.payload as string).replace('INFO: ', '').replace('ERROR: ', '')
  })
})

watch(activeCategory, (newVal) => {
  if ((newVal === 'fund_flow' || newVal === 'dashboard') && analysisResult.value) {
    nextTick(() => initFundFlowChart())
  }
})

const formatCurrency = (val: number) => {
  if (Math.abs(val) >= 100000000) {
    return (val / 100000000).toFixed(2) + ' 亿'
  }
  return (val / 10000).toFixed(2) + ' 万'
}
</script>

<template>
  <SidebarLayout
    title="量化分析"
    subtitle="多维度数据洞察与策略评估"
    :icon="LineChart"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <!-- 顶部搜索栏 -->
    <template #header-extra>
      <div class="flex items-center gap-2">
        <div class="relative group">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/30 group-focus-within:text-primary transition-colors" />
          <input 
            v-model="symbol"
            @keyup.enter="startAnalysis"
            type="text" 
            placeholder="输入股票代码 (如 000001)"
            class="pl-9 pr-4 py-2 bg-foreground/5 border border-foreground/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64"
          />
        </div>
        <button 
          @click="startAnalysis"
          :disabled="isLoading || !symbol"
          class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:active:scale-100 transition-all shadow-sm"
        >
          <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
          <TrendingUp v-else class="w-4 h-4" />
          开始分析
        </button>
      </div>
    </template>

    <template #default="{ activeId }">
      <!-- 空状态 -->
      <div v-if="!analysisResult && activeId !== 'archives'" class="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto">
        <div class="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mb-6 text-primary">
          <Activity class="w-10 h-10" v-if="!isLoading" />
          <Loader2 class="w-10 h-10 animate-spin" v-else />
        </div>
        <h2 class="text-2xl font-semibold mb-2">
          {{ isLoading ? '深度分析中' : '量化分析引擎' }}
        </h2>
        <p class="text-foreground/50 mb-8">
          {{ isLoading ? statusMessage : '请输入股票代码并点击开始分析，系统将从波动率、流动性、资金流、基本面、行业相关性及历史数据六大维度进行深度扫描。' }}
        </p>
      </div>

      <!-- 分析结果展示 -->
      <div v-else-if="analysisResult" class="p-6 h-full overflow-y-auto space-y-6">
        <!-- 概览 Dashboard -->
        <div v-if="activeId === 'dashboard'" class="grid grid-cols-3 gap-4">
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

          <!-- 快速指标卡片 -->
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

          <!-- 资金流向预览 -->
          <div class="col-span-2 bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
            <h3 class="font-medium mb-4 flex items-center gap-2">
              <TrendingUp class="w-4 h-4" /> 资金博弈分布
            </h3>
            <div class="h-64" ref="fundFlowChartRef"></div>
          </div>

          <!-- 历史行情预览 -->
          <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
            <h3 class="font-medium mb-4 flex items-center gap-2">
              <History class="w-4 h-4" /> 近期行情
            </h3>
            <div class="space-y-3">
              <div v-for="(item, idx) in analysisResult.history.slice(0, 5)" :key="idx" class="flex items-center justify-between text-sm">
                <span class="text-foreground/50">{{ item.日期 }}</span>
                <span :class="item.涨跌幅 >= 0 ? 'text-red-500' : 'text-green-500'">{{ item.收盘 }}</span>
              </div>
              <button @click="activeCategory = 'archives'" class="w-full mt-4 py-2 text-xs text-primary hover:underline">查看完整历史行情</button>
            </div>
          </div>
        </div>

        <!-- 资金流向模块 -->
        <div v-if="activeId === 'fund_flow'" class="space-y-6">
          <div class="grid grid-cols-2 gap-6">
            <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-6">
              <h3 class="font-medium mb-6">主力资金分布 (极坐标)</h3>
              <div class="h-80" ref="fundFlowChartRef"></div>
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
        <div v-if="activeId === 'risk'" class="space-y-6">
          <div class="grid grid-cols-2 gap-6">
            <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
              <div class="text-sm text-foreground/50 mb-2">20日历史波动率 (HV20)</div>
              <div class="text-5xl font-mono font-bold text-primary">{{ analysisResult.risk.hv20 }}%</div>
              <div class="mt-4 text-xs text-foreground/30">反映近一个月股价运行的剧烈程度</div>
            </div>
            <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
              <div class="text-sm text-foreground/50 mb-2">60日历史波动率 (HV60)</div>
              <div class="text-5xl font-mono font-bold text-foreground/70">{{ analysisResult.risk.hv60 }}%</div>
              <div class="mt-4 text-xs text-foreground/30">反映中长期股价波动的中枢水平</div>
            </div>
          </div>
          <div class="bg-primary/5 border border-primary/10 rounded-2xl p-6">
            <h4 class="font-medium mb-2 flex items-center gap-2 text-primary">
              <AlertCircle class="w-4 h-4" /> 风险评估建议
            </h4>
            <p class="text-sm text-foreground/70">
              当前 HV20 {{ analysisResult.risk.hv20 > 40 ? '处于高位，说明近期市场分歧较大，建议控制仓位。' : '处于平稳区间，市场情绪较为稳定。' }}
            </p>
          </div>
        </div>

        <!-- 流动性深度 -->
        <div v-if="activeId === 'liquidity'" class="space-y-6">
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
            <div class="mt-8 pt-6 border-t border-foreground/5 flex items-center justify-between">
              <div class="text-sm text-foreground/50">流动性评分: <span class="font-bold text-foreground">{{ analysisResult.liquidity.score }}</span></div>
              <div class="text-xs text-foreground/30">评分基于买卖盘口厚度与成交量综合评估</div>
            </div>
          </div>
        </div>

        <!-- 财务基本面 -->
        <div v-if="activeId === 'fundamentals'" class="space-y-6">
          <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8">
            <div class="flex items-center justify-between mb-8">
              <h3 class="text-xl font-bold">最新财务摘要</h3>
              <span class="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full">{{ analysisResult.fundamentals.report_period }} 报告期</span>
            </div>
            <div class="grid grid-cols-2 gap-8">
              <div class="p-6 bg-foreground/5 rounded-2xl border border-foreground/5">
                <div class="text-sm text-foreground/50 mb-2">扣除非经常性损益后的净利润</div>
                <div class="text-3xl font-mono font-bold">{{ analysisResult.fundamentals.deduct_net_profit }}</div>
                <div class="mt-4 text-xs text-foreground/30">反映排除政府补贴、资产变卖后的真实经营盈利能力</div>
              </div>
              <div class="p-6 bg-foreground/5 rounded-2xl border border-foreground/5 flex items-center justify-center text-foreground/20 italic">
                更多财务指标持续接入中...
              </div>
            </div>
          </div>
        </div>

        <!-- 行业相关性 -->
        <div v-if="activeId === 'industry'" class="space-y-6">
          <div class="bg-foreground/5 border border-foreground/10 rounded-2xl p-8 text-center">
            <div class="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4 text-primary">
              <Network class="w-8 h-8" />
            </div>
            <h3 class="text-lg font-medium mb-1">{{ analysisResult.industry.name }}</h3>
            <div class="text-sm text-foreground/50 mb-8">所属行业板块</div>
            
            <div class="max-w-md mx-auto">
              <div class="flex justify-between text-sm mb-2">
                <span class="text-foreground/50">行业走势相关度 (Pearson)</span>
                <span class="font-bold">{{ (analysisResult.industry.correlation * 100).toFixed(1) }}%</span>
              </div>
              <div class="h-3 bg-foreground/5 rounded-full overflow-hidden">
                <div class="h-full bg-primary transition-all duration-1000" :style="{ width: (analysisResult.industry.correlation * 100) + '%' }"></div>
              </div>
              <div class="mt-4 text-xs text-foreground/30">
                基于过去 150 个交易日个股与行业指数的收盘价走势计算。
                <br/>
                {{ analysisResult.industry.correlation > 0.8 ? '高相关性：股价走势基本随大流。' : '低相关性：个股具有独立行情特征。' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史归档列表 -->
      <div v-if="activeId === 'archives'" class="p-6 h-full overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-medium flex items-center gap-2">
            <History class="w-5 h-5" /> 历史分析记录
          </h3>
          <span class="text-xs text-foreground/30">共 {{ archives.length }} 条记录</span>
        </div>
        
        <div v-if="archives.length === 0" class="flex flex-col items-center justify-center py-20 text-foreground/20">
          <History class="w-12 h-12 mb-4 opacity-10" />
          <p>暂无分析记录</p>
        </div>
        
        <div v-else class="grid grid-cols-1 gap-3">
          <div 
            v-for="archive in archives" 
            :key="archive.name"
            class="group bg-foreground/5 border border-foreground/10 rounded-2xl p-4 flex items-center justify-between hover:bg-foreground/[0.08] transition-colors"
          >
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <FileText class="w-5 h-5" />
              </div>
              <div>
                <div class="font-medium">{{ archive.name }}</div>
                <div class="text-xs text-foreground/30 flex items-center gap-3">
                  <span>分析日期: {{ new Date(archive.updated_at * 1000).toLocaleString() }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="openArchiveFolder(archive.name)"
                class="p-2 text-foreground/30 hover:text-primary hover:bg-primary/10 rounded-lg transition-all"
                title="打开文件夹"
              >
                <FolderOpen class="w-5 h-5" />
              </button>
              <button 
                @click="symbol = archive.name.split('_')[0]; startAnalysis()"
                class="p-2 text-foreground/30 hover:text-primary hover:bg-primary/10 rounded-lg transition-all"
                title="重新分析"
              >
                <ChevronRight class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SidebarLayout>
</template>

<style scoped>
/* 隐藏滚动条但保留功能 */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(var(--foreground-rgb), 0.1);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--foreground-rgb), 0.2);
}
</style>
