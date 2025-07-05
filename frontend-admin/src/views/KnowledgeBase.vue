<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">知识库管理</div>
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
            :auto-upload="false"
            :on-exceed="handleExceed"
            :on-success="handleSuccess"
            :on-error="handleError"
            accept=".txt"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将.txt文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">只能上传.txt文件，且一次只能上传一个文件</div>
            </template>
          </el-upload>
          <br />
          <el-button type="primary" @click="submitUpload">上传到服务器</el-button>
        </el-tab-pane>

        <el-tab-pane label="文档列表" name="list">
          <el-input
            v-model="search"
            placeholder="搜索标题/正文"
            style="width:300px"
            @keyup.enter="fetchDocs"
            clearable
            @clear="fetchDocs"
          >
            <template #append>
              <el-select v-model="searchBy" style="width:90px">
                <el-option label="全部" value="all" />
                <el-option label="标题" value="title" />
                <el-option label="正文" value="content" />
              </el-select>
            </template>
          </el-input>

          <el-table :data="docs" style="width: 100%">
            <el-table-column prop="title" label="文档名" />
            <el-table-column prop="content" label="预览" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDelete(scope.row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[20,30,40,50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="changePageSize"
            @current-change="changePage"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, genFileId } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const activeTab = ref('list')
const uploadRef = ref()
const uploadUrl = '/api/admin/kb/upload'

const submitUpload = () => {
  uploadRef.value?.submit()
}
const handleExceed = (files) => {
  uploadRef.value?.clearFiles()
  const file = files[0]
  file.uid = genFileId()
  uploadRef.value?.handleStart(file)
}
const handleSuccess = (res) => {
  ElMessage.success(res.message || '文件上传成功！')
  uploadRef.value?.clearFiles()
  fetchDocs()
}
const handleError = () => {
  ElMessage.error('上传失败！')
}

const docs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const search = ref('')
const searchBy = ref('all')

const fetchDocs = async () => {
  const { data } = await axios.get('/api/admin/kb/documents', {
    params: {
      page: page.value,
      page_size: pageSize.value,
      search: search.value,
      by: searchBy.value
    }
  })
  docs.value = data.docs
  total.value = data.total
}

const changePage = (p) => {
  page.value = p
  fetchDocs()
}
const changePageSize = (s) => {
  pageSize.value = s
  page.value = 1
  fetchDocs()
}
const handleDelete = (id) => {
  if (!id || id === 'undefined') {
    ElMessage.error('无效的文档 ID')
    return
  }
  ElMessageBox.confirm(`确定删除该文档？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`/api/admin/kb/documents/${encodeURIComponent(id)}`)
      ElMessage.success('删除成功')
      fetchDocs()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  })
}

onMounted(fetchDocs)
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
