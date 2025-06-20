<template>
  <el-container class="main-layout">
    <!-- Sidebar Navigation Menu -->
    <el-aside width="220px">
      <div class="logo-container">
        <h3>知识库管理后台</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical-demo"
        router
      >
        <el-menu-item index="/knowledge-base">
          <el-icon><icon-document /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/model-management">
          <el-icon><icon-setting /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
        <el-menu-item index="/feedback-review">
           <el-icon><icon-message /></el-icon>
          <span>用户反馈审查</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content Area -->
    <el-main>
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  Document as IconDocument,
  Setting as IconSetting,
  Message as IconMessage,
} from '@element-plus/icons-vue';

// Get the current route to dynamically set the active menu item
const route = useRoute();
const activeMenu = computed(() => route.path);
</script>

<style>
/* Basic styling for the layout */
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.main-layout {
  height: 100%;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  background-color: #f4f4f5;
}

.el-menu {
  border-right: none !important;
}

.el-aside {
  border-right: 1px solid #e6e6e6;
}

.el-main {
  padding: 20px;
  background-color: #fcfcfc;
}
</style>
