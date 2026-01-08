<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import TitleBar from './components/TitleBar.vue'

const applyTheme = () => {
  const currentTheme = localStorage.getItem('theme') || 'system'
  const isDark = 
    currentTheme === 'dark' || 
    (currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

onMounted(() => {
  applyTheme()
  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (localStorage.getItem('theme') === 'system') {
      applyTheme()
    }
  })
})
</script>

<template>
  <div class="flex flex-col h-screen bg-background/80 text-foreground transition-colors duration-300 overflow-hidden rounded-lg border border-thin shadow-2xl">
    <TitleBar />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <main class="flex-1 overflow-y-auto relative">
        <router-view v-slot="{ Component }">
          <transition 
            name="fade" 
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 隐藏滚动条但保持可滚动 */
::-webkit-scrollbar {
  width: 0px;
  background: transparent;
}
</style>
