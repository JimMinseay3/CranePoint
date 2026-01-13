<script setup lang="ts">
import { ref } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

defineProps<{
  title: string
  subtitle?: string
  icon?: any
  menuItems: Array<{
    id: string
    name: string
    icon: any
    disabled?: boolean
  }>
  activeId: string
}>()

const emit = defineEmits(['update:activeId'])
const isCollapsed = ref(false)
</script>

<template>
  <div class="h-full flex flex-col p-6 overflow-hidden bg-background">
    <!-- 顶部标题栏 -->
    <div class="flex-none mb-6 flex items-start">
      <div :class="[
        'flex-none transition-all duration-300 ease-in-out overflow-hidden',
        isCollapsed ? 'w-16' : 'w-64'
      ]">
        <div class="flex items-center gap-3 mb-1">
          <component :is="icon" v-if="icon" class="w-8 h-8 text-primary flex-none" />
          <h1 class="text-3xl font-semibold tracking-tight text-foreground truncate">{{ title }}</h1>
        </div>
        <p v-if="subtitle" class="text-sm text-foreground/50 ml-11 truncate transition-opacity duration-300" :class="isCollapsed ? 'opacity-0' : 'opacity-100'">
          {{ subtitle }}
        </p>
      </div>
      
      <!-- 标题栏右侧额外插槽 - 与主内容区对齐 -->
      <div v-if="$slots['header-extra']" class="flex-1 flex items-center ml-6">
        <slot name="header-extra"></slot>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="flex-1 flex gap-6 min-h-0 relative">
      <!-- 左侧目录栏 -->
      <aside 
        :class="[
          'relative flex flex-col bg-card border border-thin rounded-2xl transition-all duration-300 ease-in-out shadow-sm',
          isCollapsed ? 'w-16' : 'w-64'
        ]"
      >
        <button 
          @click="isCollapsed = !isCollapsed"
          class="absolute -right-3 top-6 w-6 h-6 bg-background border border-thin rounded-full flex items-center justify-center hover:bg-foreground/5 transition-colors z-10 shadow-sm"
        >
          <ChevronLeft v-if="!isCollapsed" class="w-3.5 h-3.5" />
          <ChevronRight v-else class="w-3.5 h-3.5" />
        </button>

        <div class="flex-1 flex flex-col p-3 overflow-hidden">
          <div class="mb-4 px-2" v-if="!isCollapsed">
            <h2 class="text-xs font-semibold text-foreground/40 uppercase tracking-widest">功能分类</h2>
          </div>

          <nav class="space-y-1">
            <button
              v-for="item in menuItems"
              :key="item.id"
              @click="!item.disabled && emit('update:activeId', item.id)"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative',
                activeId === item.id 
                  ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20' 
                  : 'text-foreground/60 hover:bg-foreground/5 hover:text-foreground',
                item.disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'
              ]"
              :title="isCollapsed ? item.name : ''"
            >
              <component :is="item.icon" class="w-5 h-5 flex-none" />
              <div v-if="!isCollapsed" class="flex flex-col items-start overflow-hidden text-left">
                <span class="text-sm font-medium truncate w-full">{{ item.name }}</span>
              </div>
              <div 
                v-if="activeId === item.id && isCollapsed" 
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary-foreground rounded-r-full"
              ></div>
            </button>
          </nav>
        </div>
      </aside>

      <!-- 右侧展示空间 -->
      <main class="flex-1 bg-card border border-thin rounded-2xl shadow-sm overflow-hidden flex flex-col relative">
        <div class="absolute inset-0 bg-grid-slate-200/[0.05] [mask-image:linear-gradient(to_bottom,white,transparent)] pointer-events-none"></div>
        <div class="relative flex-1 flex flex-col p-8 overflow-auto custom-scrollbar">
          <slot :activeId="activeId"></slot>
        </div>
      </main>
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
