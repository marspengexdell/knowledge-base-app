<template>
  <div class="chat-window">
    <div ref="msgList" class="messages">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['msg-row', msg.role]"
      >
        <div class="msg-bubble">
          <span v-if="msg.role === 'user'" class="msg-username">我：</span>
          <span v-if="msg.role === 'ai'" class="msg-username">AI：</span>
          <span class="msg-text">{{ msg.content }}</span>
        </div>
      </div>
      <div v-if="loading && partialAIMessage" class="msg-row ai">
        <div class="msg-bubble">
          <span class="msg-username">AI：</span>
          <span class="msg-text">{{ partialAIMessage }}</span>
        </div>
      </div>
    </div>
    <div class="input-row">
      <el-input
        v-model="input"
        placeholder="请输入您的问题…"
        @keyup.enter="handleSend"
        :disabled="loading"
        clearable
        class="chat-input"
      />
      <el-button
        type="primary"
        :loading="loading"
        @click="handleSend"
        :disabled="loading"
        class="send-btn"
      >
        发送
      </el-button>
    </div>
    <el-alert v-if="wsError" :title="wsError" type="error" show-icon style="margin-top:10px" />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const msgList = ref(null)
const ws = ref(null)
const wsError = ref('')
const partialAIMessage = ref('')

function scrollToBottom() {
  nextTick(() => {
    if (msgList.value) {
      msgList.value.scrollTop = msgList.value.scrollHeight
    }
  })
}

function connectWS() {
  if (ws.value) ws.value.close()
  ws.value = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/chat/ws`)
  ws.value.onopen = () => {
    wsError.value = ''
  }
  ws.value.onerror = () => {
    wsError.value = '无法连接到AI服务，请稍后重试。'
  }
  ws.value.onclose = () => {
    if (!wsError.value) wsError.value = 'AI连接已断开。正在重连...'
    setTimeout(connectWS, 2000) // 自动重连
  }
  ws.value.onmessage = (event) => {
    // AI回复的每个片段
    if (loading.value) {
      if (event.data === '[DONE]') {
        if (partialAIMessage.value) {
          messages.value.push({ role: 'ai', content: partialAIMessage.value })
        }
        loading.value = false
        partialAIMessage.value = ''
      } else {
        partialAIMessage.value += event.data
      }
      scrollToBottom()
    }
  }
}

onMounted(() => {
  connectWS()
})

onUnmounted(() => {
  if (ws.value) ws.value.close()
})

async function handleSend() {
  if (!input.value.trim() || loading.value || !ws.value || ws.value.readyState !== 1) {
    if (!ws.value || ws.value.readyState !== 1) {
      wsError.value = 'AI服务未连接，无法发送。'
    }
    return
  }
  const userMsg = input.value
  messages.value.push({ role: 'user', content: userMsg })
  input.value = ''
  loading.value = true
  partialAIMessage.value = ''
  scrollToBottom()
  // 通过ws发送
  try {
    ws.value.send(userMsg)
  } catch (e) {
    loading.value = false
    wsError.value = 'AI服务通信异常'
    ElMessage.error(wsError.value)
  }
}
</script>

<style scoped>
/* ...你原来的样式...（完全兼容，无需改） */
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 12px 12px 12px;
  background: #f7f7fa;
  min-height: 350px;
}
.msg-row {
  display: flex;
  margin-bottom: 10px;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.ai {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 70%;
  padding: 10px 16px;
  border-radius: 16px;
  word-break: break-word;
  font-size: 1em;
  background: #f0f4fb;
  color: #222;
}
.msg-row.user .msg-bubble {
  background: #d3e6fd;
  color: #124e94;
  border-bottom-right-radius: 4px;
}
.msg-row.ai .msg-bubble {
  background: #eef1f5;
  color: #333;
  border-bottom-left-radius: 4px;
}
.msg-username {
  font-weight: bold;
  margin-right: 4px;
  color: #888;
}
.input-row {
  display: flex;
  padding: 16px 8px 8px 8px;
  background: #fff;
  border-top: 1px solid #eee;
}
.chat-input {
  flex: 1;
  margin-right: 8px;
}
.send-btn {
  width: 80px;
}
</style>
