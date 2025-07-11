<template>
  <div>
    <h2 class="text-2xl font-semibold mb-6 text-gray-800">模型管理</h2>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 上传模型卡片 -->
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

      <!-- 模型列表卡片 -->
      <div class="lg:col-span-2">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-semibold">已上传模型</span>
              <el-button type="primary" :icon="Refresh" circle @click="fetchModels" />
            </div>
          </template>
          <el-table :data="models" v-loading="loading" style="width: 100%">
            <el-table-column prop="model_name" label="模型文件名">
              <template #default="scope">
                <div class="flex items-center">
                  <el-icon class="mr-2 text-gray-400"><Tickets /></el-icon>
                  <span>{{ scope.row.model_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="model_path" label="路径" width="350">
              <template #default="scope">
                <span class="text-xs text-gray-500">{{ scope.row.model_path }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="scope">
                <el-button
                  size="small"
                  type="primary"
                  :disabled="scope.row.active"
                  @click="switchModel(scope.row.model_name)"
                >
                  {{ scope.row.active ? '已激活' : '切换' }}
                </el-button>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { UploadFilled, Refresh, Tickets } from '@element-plus/icons-vue'

const models = ref([])
const loading = ref(false)

const fetchModels = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/admin/models')
    const data = response.data

    models.value = data.generation_models.map(model => ({
      model_name: model,
      model_path: `/models/${model}`,
      active: model === data.current_generation_model
    }))
  } catch (error) {
    ElMessage.error('获取模型列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const switchModel = async (modelName) => {
  try {
    const res = await axios.post(`/api/admin/models/load/${modelName}`)
    if (res.data.success) {
      ElMessage.success(res.data.message || '切换成功')
      fetchModels()
    } else {
      ElMessage.error(res.data.message || '切换失败')
    }
  } catch (e) {
    if (e?.response?.status === 202) {
      ElMessage.info(e?.response?.data?.detail || '模型正在加载，请稍后刷新')
    } else {
      ElMessage.error(e?.response?.data?.detail || '切换失败')
    }
  }
}

const handleSuccess = (response, file) => {
  if (response.success) {
    ElMessage.success(`模型 "${file.name}" 上传成功！`)
    fetchModels()
  } else {
    ElMessage.error(response.message || `模型 "${file.name}" 上传失败。`)
  }
}

const handleError = (error, file) => {
  ElMessage.error(`模型 "${file.name}" 上传失败，请检查网络或联系管理员。`)
  console.error(error)
}

const beforeUpload = (file) => {
  const isValid = file.name.endsWith('.gguf') || file.name.endsWith('.safetensors')
  if (!isValid) {
    ElMessage.error('只能上传 .gguf 或 .safetensors 格式的文件！')
  }
  return isValid
}

onMounted(() => {
  fetchModels()
})
</script>
