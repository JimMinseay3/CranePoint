<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { 
  Minus, 
  Square, 
  X, 
  Pin, 
  PinOff 
} from 'lucide-vue-next'

const appWindow = ref<any>(null)
const isPinned = ref(false)
const isMaximized = ref(false)

const togglePin = async () => {
  if (!appWindow.value) return
  isPinned.value = !isPinned.value
  await appWindow.value.setAlwaysOnTop(isPinned.value)
}

const minimize = () => appWindow.value?.minimize()
const toggleMaximize = async () => {
  if (!appWindow.value) return
  await appWindow.value.toggleMaximize()
  isMaximized.value = await appWindow.value.isMaximized()
}
const close = () => appWindow.value?.close()

onMounted(async () => {
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    appWindow.value = getCurrentWindow()
    
    // 监听窗口最大化状态变化
    appWindow.value.onResized(async () => {
      isMaximized.value = await appWindow.value.isMaximized()
    })
  } catch (e) {
    console.warn('Running in non-Tauri environment, window controls disabled.')
  }
})
</script>

<template>
  <div 
    class="h-10 flex items-center justify-between bg-background/40 backdrop-blur-md border-b border-thin select-none z-[100] relative"
  >
    <!-- 拖拽区域覆盖层 -->
    <div 
      data-tauri-drag-region 
      class="absolute inset-0 z-[-1] cursor-default"
    ></div>

    <div class="flex items-center px-4 gap-2 pointer-events-none">
      <span class="text-xs font-medium text-foreground/40 tracking-widest uppercase">CranePoint</span>
    </div>

    <div class="flex items-center h-full relative z-10">
      <!-- Pin Button -->
      <button 
        @click.stop="togglePin"
        :class="[
          'h-full px-3 flex items-center justify-center transition-colors duration-200 no-drag',
          isPinned ? 'text-primary bg-foreground/5' : 'text-foreground/60 hover:bg-foreground/5'
        ]"
        :title="isPinned ? '取消置顶' : '固定窗口'"
      >
        <component :is="isPinned ? Pin : PinOff" :size="14" :stroke-width="2" />
      </button>

      <!-- Minimize -->
      <button 
        @click.stop="minimize"
        class="h-full px-3 flex items-center justify-center text-foreground/60 hover:bg-foreground/5 transition-colors duration-200 no-drag"
      >
        <Minus :size="14" :stroke-width="2" />
      </button>

      <!-- Maximize -->
      <button 
        @click.stop="toggleMaximize"
        class="h-full px-3 flex items-center justify-center text-foreground/60 hover:bg-foreground/5 transition-colors duration-200 no-drag"
      >
        <Square :size="12" :stroke-width="2" />
      </button>

      <!-- Close -->
      <button 
        @click.stop="close"
        class="h-full px-4 flex items-center justify-center text-foreground/60 hover:bg-red-500 hover:text-white transition-colors duration-200 no-drag"
      >
        <X :size="16" :stroke-width="2" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.no-drag {
  -webkit-app-region: no-drag;
}
</style>
