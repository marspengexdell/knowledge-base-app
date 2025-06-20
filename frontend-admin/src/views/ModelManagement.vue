<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>模型管理</span>
        </div>
      </template>
      
      <!-- Display Current Models -->
      <el-descriptions title="当前加载模型" :column="2" border>
        <el-descriptions-item label="生成模型">
          <el-tag v-if="modelsInfo.current_generation_model" type="success">{{ modelsInfo.current_generation_model }}</el-tag>
          <span v-else>未加载</span>
        </el-descriptions-item>
        <el-descriptions-item label="嵌入模型">
          <el-tag v-if="modelsInfo.current_embedding_model" type="success">{{ modelsInfo.current_embedding_model }}</el-tag>
          <span v-else>未加载</span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- Switch Models Form -->
      <el-divider content-position="left">切换模型</el-divider>
      
      <el-form :model="selection" label-width="120px" class="model-form">
        <el-form-item label="选择生成模型">
          <el-select v-model="selection.generationModel" placeholder="请选择可用的生成模型" class="model-select">
            <el-option
              v-for="model in modelsInfo.generation_models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-button @click="handleSwitchModel('generation')" :loading="loading.generation" type="primary" class="switch-button">加载</el-button>
        </el-form-item>

        <el-form-item label="选择嵌入模型">
          <el-select v-model="selection.embeddingModel" placeholder="请选择可用的嵌入模型" class="model-select">
            <el-option
              v-for="model in modelsInfo.embedding_models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-button @click="handleSwitchModel('embedding')" :loading="loading.embedding" type="primary" class="switch-button">加载</el-button>
        </el-form-item>
      </el-form>

    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

// --- Reactive State ---
const modelsInfo = ref({
  generation_models: [],
  embedding_models: [],
  current_generation_model: '',
  current_embedding_model: ''
});

const selection = reactive({
  generationModel: '',
  embeddingModel: ''
});

const loading = reactive({
  generation: false,
  embedding: false
});

// --- API Functions ---
const fetchModels = async () => {
  try {
    const response = await axios.get('/api/admin/models');
    modelsInfo.value = response.data;
    // Set initial selection to the currently loaded model
    selection.generationModel = response.data.current_generation_model;
    selection.embeddingModel = response.data.current_embedding_model;
  } catch (error) {
    ElMessage.error('获取模型列表失败！');
    console.error(error);
  }
};

const handleSwitchModel = async (modelType) => {
  const modelName = modelType === 'generation' ? selection.generationModel : selection.embeddingModel;

  if (!modelName) {
    ElMessage.warning('请先选择一个模型！');
    return;
  }

  loading[modelType] = true;
  try {
    const params = new URLSearchParams();
    params.append('model_name', modelName);
    params.append('model_type', modelType);
    
    const response = await axios.post('/api/admin/models/switch', params);

    ElMessage.success(response.data.message || '模型切换成功！');
    await fetchModels(); // Refresh the model list after switching
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '模型切换失败！');
    console.error(error);
  } finally {
    loading[modelType] = false;
  }
};


// --- Lifecycle Hooks ---
onMounted(() => {
  fetchModels();
});
</script>

<style scoped>
.card-header {
  font-weight: bold;
  font-size: 1.2em;
}

.model-form {
  margin-top: 20px;
}

.model-select {
  width: 400px;
}

.switch-button {
  margin-left: 10px;
}
</style>
