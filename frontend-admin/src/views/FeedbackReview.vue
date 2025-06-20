<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户反馈审查</span>
        </div>
      </template>

      <el-table :data="feedbackList" style="width: 100%" border>
        <el-table-column type="expand">
          <template #default="props">
            <div class="feedback-detail">
              <p><strong>用户问题:</strong> {{ props.row.query }}</p>
              <p><strong>AI 回答:</strong> {{ props.row.answer }}</p>
              <p><strong>用户评价:</strong> {{ props.row.rating }}</p>
              <p v-if="props.row.comment"><strong>用户评论:</strong> {{ props.row.comment }}</p>
              <el-divider />
              <p><strong>回答时引用的上下文:</strong></p>
              <div v-for="(doc, index) in props.row.context" :key="index" class="context-doc">
                <pre>{{ doc }}</pre>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="日期" prop="date" width="180" />
        <el-table-column label="用户问题" prop="query" show-overflow-tooltip />
        <el-table-column label="评价" prop="rating" width="120">
            <template #default="scope">
                <el-tag :type="scope.row.rating === '👍' ? 'success' : 'danger'">
                    {{ scope.row.rating }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
            <template #default="scope">
                <el-button size="small" @click="handleMarkAsReviewed(scope.$index)">标记为已读</el-button>
            </template>
        </el-table-column>
      </el-table>

    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';

const feedbackList = ref([]);

// Mock data to simulate fetching from the backend
const mockData = [
  {
    id: 1,
    date: '2025-06-20 10:30:00',
    query: '如何切换AI模型？',
    answer: '您好，切换AI模型请在模型管理页面选择对应的模型并点击加载。',
    context: [
        "文档片段A: 模型管理页面提供了切换生成模型和嵌入模型的功能...",
        "文档片段B: 点击加载按钮后，系统会从后台加载新模型到GPU..."
    ],
    rating: '👍',
    comment: '回答很准确！'
  },
  {
    id: 2,
    date: '2025-06-20 11:45:12',
    query: '这个系统能处理PDF文件吗？',
    answer: '非常抱歉，我目前只能处理文本和.txt文件。',
     context: [
        "文档片段C: 系统支持.txt文件上传和纯文本粘贴...",
    ],
    rating: '👎',
    comment: '回答不正确，实际上已经支持PDF了（假设）。'
  },
];

const fetchFeedback = () => {
  // In a real application, this would be an API call:
  // axios.get('/api/admin/feedback').then(response => {
  //   feedbackList.value = response.data;
  // });
  feedbackList.value = mockData;
};

const handleMarkAsReviewed = (index) => {
    // In a real app, you would send a request to the backend to update the status.
    feedbackList.value.splice(index, 1);
    ElMessage.success('已标记为已读');
};

onMounted(() => {
  fetchFeedback();
});
</script>

<style scoped>
.card-header {
  font-weight: bold;
  font-size: 1.2em;
}
.feedback-detail {
    padding: 20px;
    background-color: #fafafa;
}
.context-doc {
    background-color: #f0f0f0;
    padding: 10px;
    margin-top: 10px;
    border-radius: 4px;
    white-space: pre-wrap; /* Ensures long lines wrap */
    word-break: break-all;
}
</style>