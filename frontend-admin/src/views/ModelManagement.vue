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
          <el-tag v-if="modelsInfo.current_generation_model" type="success">
            {{ modelsInfo.current_generation_model }}
          </el-tag>
          <span v-else>未加载</span>
        </el-descriptions-item>
        <el-descriptions-item label="嵌入模型">
          <el-tag v-if="modelsInfo.current_embedding_model" type="success">
            {{ modelsInfo.current_embedding_model }}
          </el-tag>
          <span v-else>未加载</span>
        </el-descriptions-item>
        <el-descriptions-item label="设备">
          <el-tag>{{ modelsInfo.device || '未知' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- Upload Models -->
      <el-divider content-position="left">上传模型文件</el-divider>
      <el-upload
        class="upload-demo"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :with-credentials="false"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将模型文件拖到此处，或 <em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">
          只支持 .gguf / .safetensors 文件，建议 Chrome/Edge 浏览器。
        </div>
      </el-upload>

      <!-- Switch Models Form -->
      <el-divider content-position="left">切换模型</el-divider>
      <el-form :model="selection" label-width="120px" class="model-form">
        <el-form-item label="选择生成模型">
          <el-select
            v-model="selection.generationModel"
            placeholder="请选择可用的生成模型"
            class="model-select"
            filterable
            clearable
          >
            <el-option
              v-for="model in modelsInfo.generation_models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-button
            @click="handleSwitchModel('generation')"
            :loading="loading.generation"
            type="primary"
            class="switch-button"
          >加载</el-button>
        </el-form-item>
        <el-form-item label="选择嵌入模型">
          <el-select
            v-model="selection.embeddingModel"
            placeholder="请选择可用的嵌入模型"
            class="model-select"
            filterable
            clearable
          >
            <el-option
              v-for="model in modelsInfo.embedding_models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-button
            @click="handleSwitchModel('embedding')"
            :loading="loading.embedding"
            type="primary"
            class="switch-button"
          >加载</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

// 状态
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
const uploadHeaders = {}; // 需要 token 可以设置

// 获取模型列表
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

// 上传前校验
const beforeUpload = (file) => {
  const isValid = file.name.endsWith('.gguf') || file.name.endsWith('.safetensors');
  if (!isValid) {
    ElMessage.error('仅支持 .gguf 或 .safetensors 格式的模型文件！');
  }
  return isValid;
};

const handleUploadSuccess = (res, file) => {
  ElMessage.success(res.message || '模型上传成功！');
  fetchModels();
};

const handleUploadError = (err) => {
  ElMessage.error('模型上传失败！');
  console.error(err);
};

// 切换模型
const handleSwitchModel = async (modelType) => {
  const modelName = modelType === 'generation' ? selection.generationModel : selection.embeddingModel;
  if (!modelName) {
    ElMessage.warning('请先选择一个模型！');
    return;
  }
  loading[modelType] = true;
  try {
    const payload = {
      model_name: modelName,
      model_type: modelType,
    };

    const { data } = await axios.post('/api/admin/models/switch', payload);
    ElMessage.success(data.message || '模型切换成功！');
    await fetchModels();
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
.upload-demo {
  margin: 20px 0;
}
</style>
