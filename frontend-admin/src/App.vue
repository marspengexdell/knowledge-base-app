<template>
  <div class="h-screen w-screen flex flex-col font-sans antialiased">
    
    <header class="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm flex items-center justify-between px-6 h-16 z-10">
      <div class="flex items-center space-x-3">
        <svg class="h-7 w-7 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
        </svg>
        <h1 class="text-lg font-semibold text-gray-800">知识库管理后台</h1>
      </div>
      </header>

    <div class="flex flex-1 overflow-hidden">
      <aside class="w-60 bg-white border-r border-gray-200 flex flex-col">
        <nav class="flex-1 px-3 py-4 space-y-1">
          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.path"
            class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150"
            active-class="bg-blue-50 text-blue-600 font-semibold"
            exact-active-class="bg-blue-50 text-blue-600 font-semibold"
            :class="[
              $route.path !== item.path ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900' : ''
            ]"
          >
            <span>{{ item.name }}</span>
          </router-link>
        </nav>
      </aside>

      <main class="flex-1 bg-gray-50 overflow-y-auto">
        <div class="mx-auto max-w-7xl py-6 px-4 sm:px-6 lg:px-8">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const navItems = ref([
  { name: '仪表盘', path: '/admin' }, // 将路径修改为 /admin
  { name: '模型管理', path: '/admin/model-management' },
  { name: '知识库上传', path: '/admin/knowledge-base' },
  { name: '文档管理', path: '/admin/document-management' },
]);
</script>

<style>
/* 添加一个全局样式，确保页面在所有情况下都撑满 */
html, body, #app {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  background-color: #f9fafb; /* 对应 bg-gray-50 */
}
</style>