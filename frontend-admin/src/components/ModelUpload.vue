<template>
  <el-upload
    class="upload-demo"
    action="/api/admin/models/upload"
    :headers="headers"
    :show-file-list="true"
    :before-upload="beforeUpload"
    :on-success="handleSuccess"
    :on-error="handleError"
    :auto-upload="true"
    drag
    multiple>
    <i class="el-icon-upload"></i>
    <div class="el-upload__text">将模型文件拖到此处，或 <em>点击上传</em></div>
    <div class="el-upload__tip" slot="tip">只支持 .gguf 和 .safetensors 格式</div>
  </el-upload>
</template>

<script setup>
import { ElMessage } from 'element-plus';
import { ref } from 'vue';

const headers = ref({});

const emit = defineEmits(['upload-success']);

const beforeUpload = (file) => {
  const allowed = ['.gguf', '.safetensors'];
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!allowed.includes(ext)) {
    ElMessage.error('只允许上传 .gguf 或 .safetensors 文件');
    return false;
  }
  return true;
};

const handleSuccess = (response, file, fileList) => {
  ElMessage.success('模型上传成功');
  emit('upload-success'); // 通知父组件刷新列表
};

const handleError = (err, file, fileList) => {
  ElMessage.error('模型上传失败');
};
</script>

<style scoped>
.upload-demo {
  margin-bottom: 20px;
}
</style>
