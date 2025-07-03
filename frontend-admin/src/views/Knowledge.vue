<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识文档管理</span>
        </div>
      </template>

      <!-- 文档上传 -->
      <el-upload
        class="upload-demo"
        action="/api/admin/kb/upload"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :with-credentials="false"
        drag>
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将知识文档拖到此处，或 <em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">支持 .txt/.md/.pdf 文件，上传后自动入库</div>
      </el-upload>

      <el-divider content-position="left">已上传文档</el-divider>

      <!-- 文档列表 -->
      <el-table :data="docList" border style="width: 100%">
        <el-table-column prop="source" label="文档名称" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <!-- 如需下载，后端需实现该接口 -->
            <!-- <el-button
              type="primary"
              size="small"
              @click="handleDownload(scope.row.source)">
              下载
            </el-button> -->
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(scope.row.source)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!docList.length" description="暂无文档" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const docList = ref([]);

const fetchDocList = async () => {
  try {
    const { data } = await axios.get('/api/admin/kb/documents');
    // 返回的是数组[{source:xxx}], 直接赋值
    docList.value = data || [];
  } catch (err) {
    ElMessage.error('获取文档列表失败！');
  }
};

const beforeUpload = (file) => {
  const allowed = ['.txt', '.md', '.pdf'];
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!allowed.includes(ext)) {
    ElMessage.error('仅允许上传 .txt、.md 或 .pdf 文件');
    return false;
  }
  return true;
};

const handleUploadSuccess = (res) => {
  ElMessage.success(res.message || '文档上传成功！');
  fetchDocList();
};

const handleUploadError = () => {
  ElMessage.error('文档上传失败！');
};

const handleDelete = (fileName) => {
  ElMessageBox.confirm(
    `确定要删除文档 "${fileName}" 吗？`,
    '删除确认',
    { type: 'warning' }
  ).then(async () => {
    try {
      await axios.delete(`/api/admin/kb/documents/${encodeURIComponent(fileName)}`);
      ElMessage.success('删除成功！');
      fetchDocList();
    } catch (err) {
      ElMessage.error('删除失败！');
    }
  });
};

// 如需下载功能，需要后端实现 /api/admin/kb/download
// const handleDownload = (fileName) => {
//   window.open(`/api/admin/kb/download?file=${encodeURIComponent(fileName)}`);
// };

onMounted(fetchDocList);
</script>

<style scoped>
.card-header {
  font-weight: bold;
  font-size: 1.2em;
}
.upload-demo {
  margin: 18px 0;
}
</style>
