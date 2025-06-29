<template>
  <div id="app-container">
    <aside class="sidebar">
      <div class="logo">
        <h2>AI Admin</h2>
      </div>
      <nav class="navigation">
        <router-link to="/knowledge-base" class="nav-item">知识库管理</router-link>
        <router-link to="/model-management" class="nav-item">模型管理</router-link>
        <router-link to="/document-management" class="nav-item">文档管理</router-link>
      </nav>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// 这个主 App.vue 组件只负责提供整体布局和导航。
</script>

<style>
/* 重置和全局样式 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f0f2f5;
  color: #333;
}

#app-container {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 240px;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}

.logo {
  padding: 24px 20px;
  text-align: center;
  font-size: 1.6rem;
  font-weight: bold;
  color: #fff;
  background-color: #3498db;
}

.navigation {
  flex-grow: 1;
  padding-top: 20px;
}

.nav-item {
  display: block;
  padding: 16px 24px;
  color: #ecf0f1;
  text-decoration: none;
  transition: background-color 0.2s, border-left-color 0.2s;
  border-left: 4px solid transparent;
  font-size: 1rem;
}

.nav-item:hover {
  background-color: #34495e;
}

/* 当链接被激活时（即当前页面），显示高亮效果 */
.router-link-active, .router-link-exact-active {
  background-color: #34495e;
  border-left-color: #3498db;
  font-weight: 600;
}

.main-content {
  flex-grow: 1;
  padding: 30px;
  overflow-y: auto;
}
</style>