<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- Text Input Tab -->
        <el-tab-pane label="文本入库" name="text">
          <el-form :model="textInput" label-position="top">
            <el-form-item label="源名称 (可选)">
              <el-input v-model="textInput.sourceName" placeholder="例如：产品A说明文档 v1.2"></el-input>
            </el-form-item>
            <el-form-item label="文本内容">
              <el-input
                v-model="textInput.content"
                :rows="15"
                type="textarea"
                placeholder="请在此处粘贴要入库的文本内容..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleTextUpload" :loading="loading.text">提交入库</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- File Upload Tab -->
        <el-tab-pane label="文件上传" name="file">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            action="/api/admin/documents/upload/file"
            :limit="1"
            :on-exceed="handleExceed"
            :auto-upload="false"
            :on-success="handleSuccess"
            :on-error="handleError"
            accept=".txt"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将.txt文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传.txt文件，且一次只能上传一个文件
              </div>
            </template>
          </el-upload>
          <br>
          <el-button type="primary" @click="submitUpload">上传到服务器</el-button>
        </el-tab-pane>
      </el-tabs>

    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';
import { ElMessage, genFileId } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

// --- Refs and Reactive State ---
const activeTab = ref('text');
const uploadRef = ref(); // Ref for the el-upload component
const loading = reactive({
  text: false,
  file: false
});
const textInput = reactive({
  sourceName: '',
  content: ''
});

// --- Text Upload Logic ---
const handleTextUpload = async () => {
  if (!textInput.content.trim()) {
    ElMessage.warning('文本内容不能为空！');
    return;
  }
  loading.text = true;
  try {
    const formData = new FormData();
    formData.append('text_content', textInput.content);
    if (textInput.sourceName) {
      formData.append('source_name', textInput.sourceName);
    }
    
    const response = await axios.post('/api/admin/documents/upload/text', formData);
    ElMessage.success(response.data.message || '文本入库成功！');
    textInput.content = '';
    textInput.sourceName = '';
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '文本入库失败！');
    console.error(error);
  } finally {
    loading.text = false;
  }
};

// --- File Upload Logic ---
const submitUpload = () => {
  uploadRef.value?.submit();
};

const handleExceed = (files) => {
  uploadRef.value?.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value?.handleStart(file);
};

const handleSuccess = (response, file, fileList) => {
  ElMessage.success(response.message || '文件上传成功！');
  uploadRef.value?.clearFiles();
};

const handleError = (error, file, fileList) => {
  try {
    const errorData = JSON.parse(error.message);
    ElMessage.error(errorData.detail || '文件上传失败！');
  } catch(e) {
    ElMessage.error('文件上传失败！');
  }
  console.error(error);
};
</script>

<style scoped>
.card-header {
  font-weight: bold;
  font-size: 1.2em;
}
.upload-demo {
  width: 100%;
}
</style>