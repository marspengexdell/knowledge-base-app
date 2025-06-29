<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-neutral-10">文档管理</h1>
        <p class="mt-1 text-sm text-neutral-50">在这里管理所有已上传到知识库的文档。</p>
      </div>
      <div>
        </div>
    </div>

    <div class="bg-neutral-100 shadow-sm border border-neutral-80 rounded-lg overflow-hidden">
      <div v-if="loading" class="p-12 text-center text-neutral-50">
        <p>正在加载文档列表...</p>
      </div>
      <div v-else-if="error" class="p-12 text-center text-destructive">
        <p>加载失败: {{ error }}</p>
      </div>
      
      <table v-else class="min-w-full">
        <thead class="border-b border-neutral-80 bg-neutral-95/50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-neutral-10 uppercase tracking-wider">
              文件名 (Source)
            </th>
            <th scope="col" class="relative px-6 py-3">
              <span class="sr-only">操作</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="documents.length === 0">
            <td colspan="2" class="py-12 text-center text-sm text-neutral-50">
              知识库中暂无文档
            </td>
          </tr>
          <tr v-for="(doc, index) in documents" :key="doc.id" :class="index % 2 === 0 ? 'bg-neutral-100' : 'bg-neutral-95/30'">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-10">
              {{ doc.source }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button
                @click="confirmDelete(doc)"
                class="text-destructive font-medium rounded-md px-3 py-1 hover:bg-destructive/10 transition-colors"
                :disabled="deleting[doc.id]"
              >
                {{ deleting[doc.id] ? '删除中...' : '删除' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
// Script 部分保持不变
import { ref, onMounted } from 'vue';
import axios from 'axios';

const documents = ref([]);
const loading = ref(true);
const error = ref(null);
const deleting = ref({});

const fetchDocuments = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get('/api/admin/kb/documents'); 
    documents.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.detail || err.message;
  } finally {
    loading.value = false;
  }
};

const confirmDelete = (doc) => {
  if (window.confirm(`确定要删除文档 "${doc.source}" 吗？此操作不可逆。`)) {
    deleteDocument(doc);
  }
};

const deleteDocument = async (doc) => {
  deleting.value[doc.id] = true;
  try {
    await axios.delete(`/api/admin/kb/documents/${encodeURIComponent(doc.source)}`);
    documents.value = documents.value.filter(d => d.id !== doc.id);
  } catch (err) {
    alert(`删除失败: ${err.response?.data?.detail || err.message}`);
  } finally {
    deleting.value[doc.id] = false;
  }
};

onMounted(() => {
  fetchDocuments();
});
</script>
