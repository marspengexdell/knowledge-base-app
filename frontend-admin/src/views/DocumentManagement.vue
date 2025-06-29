<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">文档管理</h1>
    <p class="mb-6 text-gray-600">在这里管理所有已上传到知识库的文档。</p>

    <div v-if="loading" class="text-center">
      <p>正在加载文档列表...</p>
    </div>

    <div v-else-if="error" class="text-center text-red-500">
      <p>加载失败: {{ error }}</p>
    </div>

    <div v-else class="bg-white shadow rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              文件名 (Source)
            </th>
            <th scope="col" class="relative px-6 py-3">
              <span class="sr-only">操作</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="documents.length === 0">
            <td colspan="2" class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">
              知识库中暂无文档
            </td>
          </tr>
          <tr v-for="doc in documents" :key="doc.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ doc.source }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button
                @click="confirmDelete(doc)"
                class="text-red-600 hover:text-red-900"
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
  if (window.confirm(`确定要删除文档 "${doc.source}" 吗？此操作不可逆，将删除该文件对应的所有知识库片段。`)) {
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
