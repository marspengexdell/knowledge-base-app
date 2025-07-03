<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
        </div>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="文件上传" name="file">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            :action="uploadUrl"
            name="file"
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
import { ref } from 'vue';
import { ElMessage, genFileId } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const activeTab = ref('file');
const uploadRef = ref();
// ✅ 改为 /api/admin/kb/upload
const uploadUrl = '/api/admin/kb/upload';

const submitUpload = () => {
  uploadRef.value?.submit();
};

const handleExceed = (files) => {
  uploadRef.value?.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value?.handleStart(file);
};

const handleSuccess = (response) => {
  ElMessage.success(response.message || '文件上传成功！');
  uploadRef.value?.clearFiles();
};

const handleError = (error) => {
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
