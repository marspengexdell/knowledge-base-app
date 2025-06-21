<template>
  <div class="chat-window">
    <el-card shadow="never" class="chat-card">
      <div class="chat-history" ref="historyRef">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['chat-msg', msg.role]">
          <div class="msg-bubble">
            <span v-if="msg.role === 'user'"><el-icon><UserFilled /></el-icon></span>
            <span v-if="msg.role === 'assistant'"><el-icon><Cpu /></el-icon></span>
            <span class="msg-text">{{ msg.content }}</span>
          </div>
        </div>
        <div v-if="loading" class="chat-msg assistant">
          <div class="msg-bubble">
            <el-icon><Cpu /></el-icon>
            <span class="msg-text">
              <el-icon><Loading /></el-icon>
              AI 正在输入...
            </span>
          </div>
        </div>
      </div>
      <el-form @submit.prevent="sendMsg" class="input-form">
        <el-input
          v-model="input"
          :disabled="loading"
          type="textarea"
          rows="2"
          placeholder="输入内容，回车发送"
          @keyup.enter.native="sendMsg"
          class="chat-input"
        />
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!input.trim() || loading"
          @click="sendMsg"
          class="send-btn"
        >发送</el-button>
      </el-form>
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        class="chat-error"
        @close="error = ''"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue';
import { ElMessage, ElNotification } from 'element-plus';
import { Loading, Cpu, UserFilled } from '@element-plus/icons-vue';

const input = ref('');
const loading = ref(false);
const error = ref('');
const messages = reactive([]);
const historyRef = ref(null);
let ws = null;
let sessionId = ''; // 可用uuid或后端返回

// 自动滚到底部
function scrollToBottom() {
  nextTick(() => {
    if (historyRef.value) {
      historyRef.value.scrollTop = historyRef.value.scrollHeight;
    }
  });
}

// 连接 WebSocket
function connectWs() {
  if (ws) ws.close();
  ws = new WebSocket('ws://localhost:8000/chat/ws'); // 按需修改地址
  ws.onopen = () => { /* 可提示连接成功 */ };
  ws.onerror = () => {
    error.value = '无法连接到AI服务，请稍后重试';
    loading.value = false;
  };
  ws.onclose = () => {
    if (loading.value) error.value = '连接已断开，AI回复失败';
    loading.value = false;
  };
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.error) {
        error.value = data.error;
        loading.value = false;
        return;
      }
      if (data.token || data.response_type === 'token') {
        if (!messages.length || messages[messages.length - 1].role !== 'assistant') {
          messages.push({ role: 'assistant', content: '' });
        }
        messages[messages.length - 1].content += data.token || '';
        scrollToBottom();
      }
      if (data.error_message || data.response_type === 'error_message') {
        error.value = data.error_message;
        loading.value = false;
      }
      // 源文档（如果有可追加）
      if (data.source_document) {
        messages.push({ role: 'assistant', content: '[引用]' + data.source_document });
      }
    } catch (e) {
      error.value = 'AI回复解析失败';
      loading.value = false;
    }
  };
}

// 发送消息
async function sendMsg() {
  if (!input.value.trim() || loading.value) return;
  error.value = '';
  messages.push({ role: 'user', content: input.value });
  loading.value = true;
  scrollToBottom();
  // 首次发消息需确保ws连接
  if (!ws || ws.readyState !== 1) connectWs();
  // 构造 payload
  const payload = {
    query: input.value,
    session_id: sessionId || '',
  };
  ws.send(JSON.stringify(payload));
  input.value = '';
}

onMounted(() => {
  connectWs();
});
</script>

<style scoped>
.chat-window {
  max-width: 800px;
  margin: 0 auto;
}
.chat-card {
  min-height: 520px;
}
.chat-history {
  height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  background: #fafbfc;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #eee;
}
.chat-msg {
  margin: 8px 0;
  display: flex;
}
.chat-msg.user .msg-bubble {
  margin-left: auto;
  background: #ecf5ff;
  color: #409eff;
}
.chat-msg.assistant .msg-bubble {
  margin-right: auto;
  background: #f2f2f2;
  color: #222;
}
.msg-bubble {
  padding: 8px 16px;
  border-radius: 16px;
  max-width: 70%;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px #eee;
  font-size: 1em;
  line-height: 1.6;
}
.msg-text {
  margin-left: 6px;
  word-break: break-all;
  white-space: pre-wrap;
}
.input-form {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.chat-input {
  flex: 1;
}
.send-btn {
  min-width: 88px;
}
.chat-error {
  margin-top: 10px;
}
</style>
