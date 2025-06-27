<template>
  <div class="model-management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>生成模型 (Generation Model)</span>
          <el-tag v-if="modelsInfo.device" type="info">运行设备: {{ modelsInfo.device }}</el-tag>
        </div>
      </template>
      <div class="model-selector">
        <el-select
          v-model="selection.generationModel"
          placeholder="请选择生成模型"
          size="large"
          style="width: 100%;"
        >
          <el-option
            v-for="model in modelsInfo.generation_models"
            :key="model"
            :label="model"
            :value="model"
          >
            <span style="float: left">{{ model }}</span>
            <span
              v-if="model === modelsInfo.current_generation_model"
              style="float: right; color: var(--el-text-color-secondary); font-size: 13px;"
            >
              当前
            </span>
          </el-option>
        </el-select>
        <el-button
          type="primary"
          @click="handleSwitchModel('generation')"
          :loading="loading.generation"
          class="switch-button"
        >
          {{ loading.generation ? '切换中...' : '切换模型' }}
        </el-button>
      </div>
    </el-card>

    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>嵌入模型 (Embedding Model)</span>
        </div>
      </template>
      <div class="model-selector">
        <el-select
          v-model="selection.embeddingModel"
          placeholder="请选择嵌入模型"
          size="large"
          style="width: 100%;"
        >
          <el-option
            v-for="model in modelsInfo.embedding_models"
            :key="model"
            :label="model"
            :value="model"
          >
            <span style="float: left">{{ model }}</span>
            <span
              v-if="model === modelsInfo.current_embedding_model"
              style="float: right; color: var(--el-text-color-secondary); font-size: 13px;"
            >
              当前
            </span>
          </el-option>
        </el-select>
        <el-button
          type="primary"
          @click="handleSwitchModel('embedding')"
          :loading="loading.embedding"
          class="switch-button"
        >
          {{ loading.embedding ? '切换中...' : '切换模型' }}
        </el-button>
      </div>
    </el-card>

    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>上传新模型</span>
        </div>
      </template>
      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :headers="uploadHeaders"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            仅支持 .gguf 或 .safetensors 格式的模型文件。
          </div>
        </template>
      </el-upload>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const modelsInfo = ref({
  generation_models: [],
  embedding_models: [],
  current_generation_model: '',
  current_embedding_model: '',
  device: ''
});
const selection = reactive({
  generationModel: '',
  embeddingModel: ''
});
const loading = reactive({
  generation: false,
  embedding: false
});
const uploadUrl = '/api/admin/models/upload';
const uploadHeaders = {};

const fetchModels = async () => {
  try {
    const { data } = await axios.get('/api/admin/models');
    modelsInfo.value = data;
    selection.generationModel = data.current_generation_model || '';
    selection.embeddingModel = data.current_embedding_model || '';
  } catch (error) {
    ElMessage.error('获取模型列表失败！');
    console.error(error);
  }
};

const beforeUpload = (file) => {
  const isValid = file.name.endsWith('.gguf') || file.name.endsWith('.safetensors');
  if (!isValid) {
    ElMessage.error('仅支持 .gguf 或 .safetensors 格式的模型文件！');
  }
  return isValid;
};

const handleUploadSuccess = (res) => {
  ElMessage.success(res.message || '模型上传成功！');
  fetchModels();
};

const handleUploadError = (err) => {
  ElMessage.error('模型上传失败！');
  console.error(err);
};

const handleSwitchModel = async (modelType) => {
  const modelName = modelType === 'generation' ? selection.generationModel : selection.embeddingModel;
  if (!modelName) {
    ElMessage.warning('请先选择一个模型！');
    return;
  }
  loading[modelType] = true;
  try {
    await axios.post('/api/admin/models/switch', {
      model_name: modelName,
      model_type: modelType.toUpperCase()    // ★ 关键修正点：转大写
    });
    ElMessage.success('模型切换请求已发送！');
    setTimeout(fetchModels, 2000);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '模型切换失败！');
    console.error(error);
  } finally {
    loading[modelType] = false;
  }
};

onMounted(fetchModels);
</script>

<style scoped>
.model-management-container {
  padding: 20px;
}
.box-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.model-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}
.switch-button {
  margin-left: auto;
}
.el-upload__tip {
  margin-top: 10px;
}
</style>
