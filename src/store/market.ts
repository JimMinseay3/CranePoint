import { reactive, watch } from 'vue'

interface Stock {
  code: string
  name: string
  price: number
  change: number
  volume: number
  amount: number
  turnover: number
  high: number
  low: number
  open: number
  prevClose: number
  amplitude: number
  pe_dynamic: number
  pe_static: number
  pb: number
  volume_ratio: number
  market_cap: number
  circulating_market_cap: number
  speed: number
  change_60d: number
  change_ytd: number
  main_inflow: number
  main_inflow_ratio: number
}

// 定义 Store 状态接口
interface MarketState {
  stocks: Stock[]
  lastUpdated: number | null
}

// 初始化数据：优先从 localStorage 加载
const STORAGE_KEY = 'cranepoint_market_data'
const savedData = localStorage.getItem(STORAGE_KEY)
const initialState: MarketState = savedData ? JSON.parse(savedData) : {
  stocks: [],
  lastUpdated: null
}

// 创建全局响应式状态
export const marketStore = reactive<MarketState>(initialState)

// 监听状态变化并自动保存到 localStorage
watch(
  () => marketStore,
  (state) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  },
  { deep: true }
)

// 提供更新数据的方法
export const updateMarketData = (newStocks: Stock[]) => {
  marketStore.stocks = newStocks
  marketStore.lastUpdated = Date.now()
}
