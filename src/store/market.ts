import { reactive, watch } from 'vue'

interface Stock {
  code: string
  name: string
  price: number
  change: number
  volume: number
  amount: number
  turnover: number
  turnover_actual: number
  limit_up: number
  limit_down: number
  high: number
  low: number
  open: number
  prevClose: number
  amplitude: number
  pe_dynamic: number
  pe_static: number
  pe_ttm: number
  pb: number
  volume_ratio: number
  market_cap: number
  circulating_market_cap: number
  total_shares: number
  circulating_shares: number
  speed: number
  change_60d: number
  change_ytd: number
  main_inflow: number
  main_inflow_ratio: number
  [key: string]: any // 添加索引签名以支持动态排序
}

// 定义 Store 状态接口
interface MarketState {
  stocks: Stock[]
  lastUpdated: number | null
}

// 初始化数据：优先从 localStorage 加载
const STORAGE_KEY = 'cranepoint_market_data'
let initialState: MarketState = {
  stocks: [],
  lastUpdated: null
}

try {
  const savedData = localStorage.getItem(STORAGE_KEY)
  if (savedData) {
    initialState = JSON.parse(savedData)
  }
} catch (e) {
  console.error('Failed to load market data from localStorage:', e)
}

// 创建全局响应式状态
export const marketStore = reactive<MarketState>(initialState)

// 监听状态变化并自动保存到 localStorage (添加简单的防抖)
let saveTimer: any = null
watch(
  () => marketStore,
  (state) => {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      } catch (e) {
        console.error('Failed to save market data to localStorage:', e)
      }
    }, 1000)
  },
  { deep: true }
)

// 提供更新数据的方法
export const updateMarketData = (newStocks: Stock[]) => {
  marketStore.stocks = newStocks
  marketStore.lastUpdated = Date.now()
}
