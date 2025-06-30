<template>
  <div>
    <h2 class="text-2xl font-semibold mb-6 text-gray-800">模型管理</h2>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1">
        <el-card shadow="never" class="h-full">
          <template #header>
            <div class="font-semibold">上传新模型</div>
          </template>

          <el-upload
            drag
            action="/api/admin/models/upload"
            :on-success="handleSuccess"
            :on-error="handleError"
            :before-upload="beforeUpload"
            class="w-full"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将 GGUF 模型文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip mt-2">
                请上传 .gguf 格式的模型文件。
              </div>
            </template>
          </el-upload>
        </el-card>
      </div>

      <div class="lg:col-span-2">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-semibold">已上传模型</span>
              <el-button type="primary" :icon="Refresh" circle @click="fetchModels" />
            </div>
          </template>

          <el-table :data="models" v-loading="loading" style="width: 100%">
            <el-table-column prop="name" label="模型文件名">
               <template #default="scope">
                 <div class="flex items-center">
                    <el-icon class="mr-2 text-gray-400"><Tickets /></el-icon>
                    <span>{{ scope.row.name }}</span>
                 </div>
               </template>
            </el-table-column>

            <el-table-column label="状态" width="120" align="center">
              <template #default>
                <el-tag type="success">可用</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && models.length === 0" description="暂无已上传的模型" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { UploadFilled, Refresh, Tickets } from '@element-plus/icons-vue';

const models = ref([]);
const loading = ref(false);

// 获取模型列表
const fetchModels = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/admin/models/list');
    // 后端返回 { "models": ["model1.gguf", "model2.gguf"] }
    // 转换为 [{ name: 'model1.gguf' }, ...]
    models.value = response.data.models.map(modelName => ({ name: modelName }));
  } catch (error) {
    ElMessage.error('获取模型列表失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 上传成功回调
const handleSuccess = (response, file) => {
  if (response.success) {
    ElMessage.success(`模型 "${file.name}" 上传成功！`);
    fetchModels(); // 上传成功后刷新列表
  } else {
    ElMessage.error(response.message || `模型 "${file.name}" 上传失败。`);
  }
};

// 上传失败回调
const handleError = (error, file) => {
  ElMessage.error(`模型 "${file.name}" 上传失败，请检查网络或联系管理员。`);
  console.error(error);
};

// 上传前检查
const beforeUpload = (file) => {
  const isGGUF = file.name.endsWith('.gguf');
  if (!isGGUF) {
    ElMessage.error('只能上传 .gguf 格式的文件！');
  }
  return isGGUF;
};

// 组件加载时，自动获取一次列表
onMounted(() => {
  fetchModels();
});
</script>
