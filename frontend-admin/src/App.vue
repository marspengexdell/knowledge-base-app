<template>
  <div class="h-screen w-screen flex flex-col font-sans">
    <header class="flex-shrink-0 bg-neutral-100 border-b border-neutral-80 shadow-sm flex items-center justify-between px-6 h-16">
      <div class="flex items-center space-x-4">
        <svg class="h-8 w-8 text-salesforce-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h1 class="text-xl font-semibold text-neutral-10">知识库管理后台</h1>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <aside class="w-64 bg-neutral-100 border-r border-neutral-80 p-2">
        <nav class="flex flex-col space-y-1">
          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.path"
            class="px-4 py-2.5 text-sm font-medium rounded-md transition-colors hover:bg-salesforce-blue/5"
            active-class="bg-salesforce-blue/10 text-salesforce-blue font-semibold"
            exact-active-class="bg-salesforce-blue/10 text-salesforce-blue font-semibold"
          >
            {{ item.name }}
          </router-link>
        </nav>
      </aside>

      <main class="flex-1 bg-neutral-95 overflow-y-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const navItems = ref([
  { name: '仪表盘', path: '/admin/' }, // 路径修改为/admin/
  { name: '模型管理', path: '/admin/model-management' },
  { name: '知识库上传', path: '/admin/knowledge-base' },
  { name: '文档管理', path: '/admin/document-management' },
]);
</script>
