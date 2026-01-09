<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
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
  XCircle
} from 'lucide-vue-next'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'

const activeCategory = ref('finance')
const isDownloading = ref(false)
const progress = ref(0)
const statusMessage = ref('')
const downloadWarnings = ref<string[]>([])
const showWarningDialog = ref(false)

// 财报下载配置
const financeConfig = ref({
  symbol: '',
  selectedYears: [] as string[],
  selectedTypes: ['年报'] as string[]
})

// 下载设置
const downloadSettings = ref({
  financePath: ''
})

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

// 监听下载成功事件，自动刷新列表
watch(() => progress.value, (newVal) => {
  if (newVal === 100) {
    setTimeout(scanDownloaded, 1000)
  }
})

const menuItems = [
  { id: 'finance', name: '财报下载', icon: FileText },
  { id: 'market', name: '行情历史', icon: Database },
  { id: 'settings', name: '下载设置', icon: Settings },
]

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

let unlistenProgress: any
let unlistenStatus: any

onMounted(async () => {
  // 初始化路径：优先从 localStorage 获取，如果没有则使用 dataPath + \Finance
  const savedPath = localStorage.getItem('financePath')
  if (savedPath) {
    downloadSettings.value.financePath = savedPath
  } else {
    const baseDataPath = localStorage.getItem('dataPath') || 'D:\\CranePoint_Data'
    downloadSettings.value.financePath = `${baseDataPath}\\Finance`
  }

  scanDownloaded()
  
  unlistenProgress = await listen('download-progress', (event: any) => {
    progress.value = event.payload
  })

  unlistenStatus = await listen('download-status', (event: any) => {
    const msg = event.payload as string
    if (msg.startsWith('INFO:')) {
      statusMessage.value = msg.replace('INFO:', '').trim()
    } else if (msg.startsWith('ERROR:')) {
      statusMessage.value = `错误: ${msg.replace('ERROR:', '').trim()}`
    } else if (msg.startsWith('WARNING:')) {
      downloadWarnings.value.push(msg.replace('WARNING:', '').trim())
    }
  })
})

onUnmounted(() => {
  if (unlistenProgress) unlistenProgress()
  if (unlistenStatus) unlistenStatus()
})
</script>

<template>
  <SidebarLayout
    title="数据下载"
    subtitle="构建您的本地量化数据库"
    :icon="Download"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <template #default="{ activeId }">
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
            <!-- 标的选择 -->
            <div class="space-y-3">
              <label class="text-sm font-semibold text-foreground/70 flex items-center gap-2">
                <Search class="w-4 h-4" /> 标的选择
              </label>
              <div class="relative">
                <input 
                  v-model="financeConfig.symbol"
                  type="text" 
                  placeholder="输入股票代码或名称 (如: 000001 或 平安银行)"
                  class="w-full bg-background border border-thin rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
              <p class="text-[11px] text-foreground/40 px-1">支持代码和名称模糊搜索匹配</p>
            </div>

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
                      @click="financeConfig.symbol = item.name.split('_')[0]"
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

        <!-- 下载异常提醒弹窗 -->
        <div v-if="showWarningDialog" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div class="bg-background border border-thin rounded-3xl shadow-2xl max-w-md w-full overflow-hidden animate-in zoom-in duration-200">
            <div class="p-6">
              <div class="flex items-center gap-3 mb-4 text-orange-500">
                <AlertCircle class="w-6 h-6" />
                <h3 class="text-lg font-bold">下载完成，但有部分提醒</h3>
              </div>
              <div class="bg-orange-500/5 rounded-2xl p-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                <ul class="space-y-2.5">
                  <li v-for="(warn, index) in downloadWarnings" :key="index" class="text-xs text-foreground/70 flex gap-2">
                    <span class="text-orange-500 font-bold">•</span>
                    {{ warn }}
                  </li>
                </ul>
              </div>
              <div class="mt-6 flex justify-end">
                <button 
                  @click="showWarningDialog = false"
                  class="px-6 py-2.5 bg-foreground/5 hover:bg-foreground/10 rounded-xl text-sm font-semibold transition-all"
                >
                  我知道了
                </button>
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

      <!-- 行情历史 -->
      <div v-else-if="activeId === 'market'" class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-2xl font-semibold mb-1">行情历史下载</h2>
            <p class="text-sm text-foreground/50">获取全量股票的历史 K 线、分钟线数据</p>
          </div>
        </div>
        <div class="flex flex-col items-center justify-center h-full text-foreground/20">
          <Database class="w-16 h-16 mb-4 opacity-10" />
          <p>行情历史模块配置中...</p>
        </div>
      </div>

      <!-- 下载设置 -->
      <div v-else-if="activeId === 'settings'" class="flex flex-col h-full">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-2xl font-semibold mb-1">下载参数设置</h2>
            <p class="text-sm text-foreground/50">配置本地数据库的存储路径与下载规则</p>
          </div>
        </div>

        <div class="space-y-6 max-w-2xl">
          <div class="p-6 bg-background border border-thin rounded-2xl space-y-4 shadow-sm">
            <div class="flex items-center gap-3 mb-2">
              <div class="p-2.5 bg-primary/10 rounded-xl text-primary">
                <FolderOpen class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">财报数据保存路径</span>
                <span class="text-xs text-foreground/40">下载的财报文件将按股票分类存储在此目录下</span>
              </div>
            </div>
            
            <div class="flex gap-2">
              <input 
                v-model="downloadSettings.financePath"
                type="text" 
                class="flex-1 bg-foreground/5 border border-thin rounded-xl px-4 py-3 text-sm text-foreground/70 outline-none focus:ring-2 focus:ring-primary/20 transition-all" 
              />
              <button 
                @click="setFinancePath"
                class="px-6 py-2 bg-background border border-thin rounded-xl text-sm font-medium hover:bg-foreground/5 transition-all"
              >
                浏览...
              </button>
            </div>
          </div>

          <div class="p-6 bg-background border border-thin rounded-2xl space-y-4 shadow-sm opacity-50">
            <div class="flex items-center gap-3 mb-2">
              <div class="p-2.5 bg-primary/10 rounded-xl text-primary">
                <Database class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">行情数据保存路径</span>
                <span class="text-xs text-foreground/40">本地 HDF5/CSV 历史数据库存储位置</span>
              </div>
            </div>
            <div class="flex gap-2">
              <input type="text" readonly value="D:\CranePoint_Data\Market" class="flex-1 bg-foreground/5 border border-thin rounded-xl px-4 py-3 text-sm text-foreground/40 outline-none" />
              <button disabled class="px-6 py-2 bg-background border border-thin rounded-xl text-sm font-medium cursor-not-allowed">浏览...</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SidebarLayout>
</template>

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
  background: color-mix(in srgb, var(--color-foreground) 10%, transparent);
  border-radius: 10px;
}
</style>
