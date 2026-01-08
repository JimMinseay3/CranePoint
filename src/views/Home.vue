<script setup lang="ts">
import { LayoutDashboard } from 'lucide-vue-next'
</script>

<template>
  <div class="h-full flex flex-col p-6 bg-background overflow-auto custom-scrollbar">
    <!-- 顶部标题栏 - 统一风格 -->
    <div class="flex-none mb-8">
      <div class="flex items-center gap-3 mb-1">
        <LayoutDashboard class="w-8 h-8 text-primary" />
        <h1 class="text-3xl font-semibold tracking-tight text-foreground">工作台</h1>
      </div>
      <p class="text-sm text-foreground/50 ml-11">欢迎回来，这是您的量化投资仪表盘</p>
    </div>

    <!-- 欢迎区域 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="p-6 bg-card border border-thin rounded-2xl shadow-sm">
        <h3 class="font-medium mb-2">系统状态</h3>
        <p class="text-sm text-foreground/50 leading-relaxed">行情引擎运行正常，已连接至 13 个数据节点。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-foreground) 10%, transparent);
  border-radius: 10px;
}
</style>
