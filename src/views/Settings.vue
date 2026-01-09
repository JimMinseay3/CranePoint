<script setup lang="ts">
import { ref, onMounted } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import { 
  Settings, 
  Palette, 
  Database, 
  Info,
  Monitor,
  Moon,
  Sun,
  Globe,
  HardDrive,
  Chrome,
  Trees,
  Zap,
  Feather
} from 'lucide-vue-next'

const activeCategory = ref('appearance') // 为了演示，默认切到外观
const theme = ref('light')
const themeStyle = ref('default')
const dataPath = ref('D:\\CranePoint_Data')

const menuItems = [
  { id: 'general', name: '常规设置', icon: Settings },
  { id: 'appearance', name: '外观与主题', icon: Palette },
  { id: 'data', name: '数据与 API', icon: Database },
  { id: 'about', name: '关于软件', icon: Info },
]

const setTheme = (newTheme: string) => {
  theme.value = newTheme
  localStorage.setItem('theme', newTheme)
  applyTheme()
}

const setThemeStyle = (style: string) => {
  themeStyle.value = style
  localStorage.setItem('themeStyle', style)
  applyTheme()
}

const setDataPath = async () => {
  try {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const selected = await open({
      directory: true,
      multiple: false,
      defaultPath: dataPath.value
    })
    if (selected) {
      dataPath.value = selected as string
      localStorage.setItem('dataPath', selected as string)
    }
  } catch (err) {
    console.error('Failed to open directory dialog:', err)
  }
}

const applyTheme = () => {
  const currentTheme = localStorage.getItem('theme') || 'light'
  const currentStyle = localStorage.getItem('themeStyle') || 'default'
  
  const isDark = 
    currentTheme === 'dark' || 
    (currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  
  // 处理暗色模式
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }

  // 处理风格切换
  document.documentElement.classList.remove('theme-google', 'theme-nordic', 'theme-cyber', 'theme-ink')
  if (currentStyle === 'google') {
    document.documentElement.classList.add('theme-google')
  } else if (currentStyle === 'nordic') {
    document.documentElement.classList.add('theme-nordic')
  } else if (currentStyle === 'cyber') {
    document.documentElement.classList.add('theme-cyber')
  } else if (currentStyle === 'ink') {
    document.documentElement.classList.add('theme-ink')
  }
}

onMounted(() => {
  theme.value = localStorage.getItem('theme') || 'light'
  themeStyle.value = localStorage.getItem('themeStyle') || 'default'
  dataPath.value = localStorage.getItem('dataPath') || 'D:\\CranePoint_Data'
  applyTheme()
})
</script>

<template>
  <SidebarLayout
    title="设置中心"
    subtitle="管理应用程序的首选项、外观和数据配置"
    :icon="Settings"
    :menuItems="menuItems"
    v-model:activeId="activeCategory"
  >
    <!-- 外观与主题 -->
    <template v-if="activeCategory === 'appearance'">
      <div class="space-y-12">
        <!-- 颜色模式 -->
        <div class="space-y-4">
          <div>
            <h2 class="text-xl font-semibold mb-1">颜色模式</h2>
            <p class="text-sm text-foreground/50">选择您喜欢的亮度模式</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <button 
              @click="setTheme('light')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative overflow-hidden',
                theme === 'light' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                theme === 'light' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Sun class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">亮色模式</span>
                <span class="text-xs text-foreground/40">清晰明亮的视觉体验</span>
              </div>
              <!-- 预览色块 -->
              <div class="absolute top-0 right-0 w-16 h-16 opacity-10 translate-x-4 -translate-y-4">
                <div class="w-full h-full bg-foreground rounded-full"></div>
              </div>
            </button>
            
            <button 
              @click="setTheme('dark')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative overflow-hidden',
                theme === 'dark' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                theme === 'dark' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Moon class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">暗色模式</span>
                <span class="text-xs text-foreground/40">保护眼睛，降低功耗</span>
              </div>
              <!-- 预览色块 -->
              <div class="absolute top-0 right-0 w-16 h-16 opacity-10 translate-x-4 -translate-y-4">
                <div class="w-full h-full bg-black rounded-full border border-white/20"></div>
              </div>
            </button>
            
            <button 
              @click="setTheme('system')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative overflow-hidden',
                theme === 'system' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                theme === 'system' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Monitor class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">跟随系统</span>
                <span class="text-xs text-foreground/40">自动匹配系统主题设置</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 主题风格 -->
        <div class="space-y-4">
          <div>
            <h2 class="text-xl font-semibold mb-1">主题风格</h2>
            <p class="text-sm text-foreground/50">选择界面的色彩和品牌个性</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <button 
              @click="setThemeStyle('default')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative',
                themeStyle === 'default' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                themeStyle === 'default' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Palette class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">极简白 (默认)</span>
                <span class="text-xs text-foreground/40">干净、纯粹的界面风格</span>
              </div>
              <!-- 预览色块 -->
              <div class="flex gap-1.5 mt-2">
                <div class="w-4 h-4 rounded-full bg-blue-500 shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-slate-200 shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-slate-100 shadow-sm"></div>
              </div>
            </button>

            <button 
              @click="setThemeStyle('google')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative',
                themeStyle === 'google' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                themeStyle === 'google' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Chrome class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">Google 三原色</span>
                <span class="text-xs text-foreground/40">活泼、现代的多色系风格</span>
              </div>
              <!-- 预览色块 -->
              <div class="flex gap-1.5 mt-2">
                <div class="w-4 h-4 rounded-full bg-[#4285F4] shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-[#EA4335] shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-[#FBBC05] shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-[#34A853] shadow-sm"></div>
              </div>
            </button>

            <button 
              @click="setThemeStyle('nordic')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative',
                themeStyle === 'nordic' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                themeStyle === 'nordic' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Trees class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">北欧森林</span>
                <span class="text-xs text-foreground/40">低饱和绿调，专业且解压</span>
              </div>
              <!-- 预览色块 -->
              <div class="flex gap-1.5 mt-2">
                <div class="w-4 h-4 rounded-full bg-[#3d7a6a] shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-[#a1c6b3] shadow-sm"></div>
                <div class="w-4 h-4 rounded-full bg-[#728c7c] shadow-sm"></div>
              </div>
            </button>

            <button 
              @click="setThemeStyle('cyber')"
              :class="[
                'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative',
                themeStyle === 'cyber' 
                  ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                  : 'bg-background border-thin hover:border-primary/30'
              ]"
            >
              <div :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                themeStyle === 'cyber' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
              ]">
                <Zap class="w-5 h-5" />
              </div>
              <div>
                <span class="font-semibold block">赛博霓虹</span>
                <span class="text-xs text-foreground/40">极高对比度，科幻极客感</span>
              </div>
              <!-- 预览色块 -->
               <div class="flex gap-1.5 mt-2">
                 <div class="w-4 h-4 rounded-full bg-[#ff55cc] shadow-sm"></div>
                 <div class="w-4 h-4 rounded-full bg-[#00ffff] shadow-sm"></div>
                 <div class="w-4 h-4 rounded-full bg-[#ffff00] shadow-sm"></div>
               </div>
             </button>

             <button 
               @click="setThemeStyle('ink')"
               :class="[
                 'p-6 rounded-2xl border transition-all duration-300 flex flex-col items-start gap-4 text-left group relative',
                 themeStyle === 'ink' 
                   ? 'bg-primary/5 border-primary shadow-sm shadow-primary/10' 
                   : 'bg-background border-thin hover:border-primary/30'
               ]"
             >
               <div :class="[
                 'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                 themeStyle === 'ink' ? 'bg-primary text-primary-foreground' : 'bg-foreground/5 text-foreground/40 group-hover:text-primary group-hover:bg-primary/10'
               ]">
                 <Feather class="w-5 h-5" />
               </div>
               <div>
                 <span class="font-semibold block">中式水墨</span>
                 <span class="text-xs text-foreground/40">宣纸背景与黛墨色，禅意悠远</span>
               </div>
               <!-- 预览色块 -->
               <div class="flex gap-1.5 mt-2">
                 <div class="w-4 h-4 rounded-full bg-[#262626] shadow-sm"></div>
                 <div class="w-4 h-4 rounded-full bg-[#737373] shadow-sm"></div>
                 <div class="w-4 h-4 rounded-full bg-[#f4f1ea] border border-black/5 shadow-sm"></div>
               </div>
             </button>
           </div>
         </div>
      </div>
    </template>

    <!-- 常规设置 -->
    <template v-else-if="activeCategory === 'general'">
      <div class="space-y-8">
        <div>
          <h2 class="text-xl font-semibold mb-1">常规设置</h2>
          <p class="text-sm text-foreground/50">管理语言、启动和系统交互选项</p>
        </div>

        <div class="space-y-4 max-w-xl">
          <div class="p-4 bg-background border border-thin rounded-xl flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-foreground/5 rounded-lg text-foreground/60">
                <Globe class="w-4 h-4" />
              </div>
              <div>
                <span class="text-sm font-medium">界面语言</span>
                <p class="text-[11px] text-foreground/40">选择您偏好的显示语言</p>
              </div>
            </div>
            <select class="bg-background border border-thin rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>

          <label class="p-4 bg-background border border-thin rounded-xl flex items-center justify-between cursor-pointer hover:bg-foreground/[0.02] transition-colors">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-foreground/5 rounded-lg text-foreground/60">
                <Monitor class="w-4 h-4" />
              </div>
              <div>
                <span class="text-sm font-medium">开机自启动</span>
                <p class="text-[11px] text-foreground/40">在计算机启动时自动运行 CranePoint</p>
              </div>
            </div>
            <input type="checkbox" class="w-4 h-4 rounded text-primary border-thin focus:ring-primary/20" />
          </label>
        </div>
      </div>
    </template>

    <!-- 数据与 API -->
    <template v-else-if="activeCategory === 'data'">
      <div class="space-y-8">
        <div>
          <h2 class="text-xl font-semibold mb-1">数据与 API</h2>
          <p class="text-sm text-foreground/50">管理行情数据的存储位置及外部接口</p>
        </div>

        <div class="space-y-4 max-w-2xl">
          <div class="p-4 bg-background border border-thin rounded-xl space-y-3">
            <div class="flex items-center gap-3 mb-1">
              <div class="p-2 bg-foreground/5 rounded-lg text-foreground/60">
                <HardDrive class="w-4 h-4" />
              </div>
              <span class="text-sm font-medium">数据存储路径</span>
            </div>
            <div class="flex gap-2">
              <input 
                type="text" 
                readonly 
                :value="dataPath" 
                class="flex-1 bg-foreground/5 border border-thin rounded-lg px-3 py-2 text-sm text-foreground/60 outline-none" 
              />
              <button 
                @click="setDataPath"
                class="px-4 py-2 bg-background border border-thin rounded-lg text-sm font-medium hover:bg-foreground/5 transition-colors"
              >
                更改目录
              </button>
            </div>
            <p class="text-[11px] text-foreground/40">所有下载的行情数据、财报和日志将保存在此路径下。</p>
          </div>

          <div class="p-4 bg-background border border-thin rounded-xl space-y-3">
            <div class="flex items-center gap-3 mb-1">
              <div class="p-2 bg-foreground/5 rounded-lg text-foreground/60">
                <Database class="w-4 h-4" />
              </div>
              <span class="text-sm font-medium">API 令牌 (Token)</span>
            </div>
            <div class="space-y-2">
              <div class="flex flex-col gap-1">
                <span class="text-[10px] uppercase font-bold text-foreground/30 ml-1">Tushare Token</span>
                <input 
                  type="password" 
                  placeholder="请输入您的 Tushare Token" 
                  class="w-full bg-background border border-thin rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" 
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 关于 -->
    <template v-else-if="activeCategory === 'about'">
      <div class="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center space-y-6">
        <div class="w-24 h-24 bg-primary text-primary-foreground rounded-[2rem] flex items-center justify-center shadow-xl shadow-primary/20 transform rotate-12 mb-4">
          <Settings class="w-12 h-12 transform -rotate-12" />
        </div>
        <div>
          <h2 class="text-3xl font-bold tracking-tight">CranePoint</h2>
          <p class="text-sm text-foreground/40 font-medium">专业级量化投研工作站</p>
        </div>
        <div class="px-4 py-1.5 bg-foreground/5 rounded-full text-[11px] font-bold text-foreground/40 uppercase tracking-widest">
          Version 1.0.0 (Build 2026.01)
        </div>
        <p class="text-sm text-foreground/60 leading-relaxed">
          CranePoint 致力于为投资者提供极速的数据获取体验、强大的筛选分析工具以及直观的策略可视化能力。
        </p>
        <div class="pt-6 w-full border-t border-thin flex justify-center gap-8">
          <a href="#" class="text-xs text-primary hover:underline font-medium">检查更新</a>
          <a href="#" class="text-xs text-primary hover:underline font-medium">官方文档</a>
          <a href="#" class="text-xs text-primary hover:underline font-medium">问题反馈</a>
        </div>
        <p class="text-[10px] text-foreground/30">© 2026 CranePoint Studio. All rights reserved.</p>
      </div>
    </template>
  </SidebarLayout>
</template>

<style scoped>
</style>
