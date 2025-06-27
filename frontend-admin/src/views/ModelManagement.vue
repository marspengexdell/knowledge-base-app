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
