<script setup lang="ts">
import { 
  Home, 
  Camera, 
  Download, 
  BarChart2, 
  Filter, 
  Settings,
  Anchor
} from 'lucide-vue-next'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { name: '主页', path: '/', icon: Home },
  { name: '市场快照', path: '/market', icon: Camera },
  { name: '数据下载', path: '/download', icon: Download },
  { name: '数据分析', path: '/analysis', icon: BarChart2 },
  { name: '股票筛选', path: '/screening', icon: Filter },
]

const navigate = (path: string) => {
  router.push(path)
}
</script>

<template>
  <aside class="w-64 h-full border-r border-thin flex flex-col acrylic overflow-hidden transition-all duration-300">
    <!-- Header -->
    <div class="p-6 flex items-center gap-3">
      <div class="p-2 rounded-lg bg-foreground text-background">
        <Anchor :size="24" stroke-width="1.5" />
      </div>
      <h1 class="text-xl font-semibold tracking-tight text-foreground">CranePoint</h1>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-4 space-y-1">
      <button
        v-for="item in menuItems"
        :key="item.path"
        @click="navigate(item.path)"
        :class="[
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group',
          route.path === item.path 
            ? 'bg-foreground/5 text-foreground' 
            : 'text-foreground/60 hover:text-foreground hover:bg-foreground/5'
        ]"
      >
        <component 
          :is="item.icon" 
          :size="20" 
          :stroke-width="route.path === item.path ? 2 : 1.5"
          class="transition-transform duration-200 group-hover:scale-110"
        />
        <span class="text-sm font-medium">{{ item.name }}</span>
      </button>
    </nav>

    <!-- Bottom Settings -->
    <div class="p-3 border-t border-thin">
      <button
        @click="navigate('/settings')"
        :class="[
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group',
          route.path === '/settings' 
            ? 'bg-foreground/5 text-foreground' 
            : 'text-foreground/60 hover:text-foreground hover:bg-foreground/5'
        ]"
      >
        <Settings 
          :size="20" 
          :stroke-width="route.path === '/settings' ? 2 : 1.5"
          class="transition-transform duration-200 group-hover:rotate-45"
        />
        <span class="text-sm font-medium">设置</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.acrylic {
  backdrop-filter: blur(20px) saturate(180%);
}
</style>
