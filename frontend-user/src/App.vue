<template>
  <div id="chat-container">
    <div class="header">
      <h1>AI 知识库</h1>
      <div class="status">
        <span :class="['status-light', connectionStatus.class]"></span>
        <span>{{ connectionStatus.text }}</span>
      </div>
    </div>

    <!-- Chat Message Display Area -->
    <div id="chat-window" ref="chatWindow">
      <div v-for="message in messages" :key="message.id" :class="['message-row', message.role]">
        <div class="message-bubble">
          <div class="content" v-html="renderMarkdown(message.content)"></div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div id="chat-input-area">
      <textarea
        v-model="userInput"
        @keydown.enter.prevent="sendMessage"
        placeholder="请输入您的问题..."
        :disabled="isGenerating"
      ></textarea>
      <button @click="sendMessage" :disabled="!userInput.trim() || isGenerating">
        {{ isGenerating ? '思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { marked } from 'marked';
import { v4 as uuidv4 } from 'uuid';

// --- Reactive State ---
const messages = ref([
  { id: uuidv4(), role: 'assistant', content: '您好！我是您的AI知识库助手，有什么可以帮助您的吗？' }
]);
const userInput = ref('');
const isConnected = ref(false);
const isGenerating = ref(false);
const chatWindow = ref(null); // Ref for the chat window DOM element
let socket = null;

// --- WebSocket Logic ---
const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // In production, this would point to the same host. For dev, Vite proxy handles it.
  const wsURL = `${wsProtocol}//${window.location.host}/api/chat/ws`;
  
  socket = new WebSocket(wsURL);

  socket.onopen = () => {
    console.log("WebSocket connection established.");
    isConnected.value = true;
  };

  socket.onmessage = (event) => {
    // Append the received token to the last assistant message
    const lastMessage = messages.value[messages.value.length - 1];
    if (lastMessage && lastMessage.role === 'assistant') {
      if (isGenerating.value) {
        // First token received, replace "Thinking..."
        lastMessage.content = event.data;
        isGenerating.value = false; // Allow user to send new message if they want
      } else {
        lastMessage.content += event.data;
      }
      scrollToBottom();
    }
  };

  socket.onclose = () => {
    console.log("WebSocket connection closed.");
    isConnected.value = false;
    isGenerating.value = false;
  };

  socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
    isConnected.value = false;
    isGenerating.value = false;
    messages.value.push({
      id: uuidv4(),
      role: 'assistant',
      content: '抱歉，连接出现问题，请刷新页面重试。'
    });
  };
};

// --- Message Handling ---
const sendMessage = () => {
  if (!userInput.value.trim() || !isConnected.value) return;

  // 1. Add user message to the list
  messages.value.push({
    id: uuidv4(),
    role: 'user',
    content: userInput.value,
  });

  // 2. Send message via WebSocket
  socket.send(userInput.value);
  userInput.value = ''; // Clear input
  isGenerating.value = true;

  // 3. Add a placeholder for the AI's response
  messages.value.push({
    id: uuidv4(),
    role: 'assistant',
    content: '🤔 思考中...',
  });
  
  scrollToBottom();
};

const renderMarkdown = (content) => {
  return marked.parse(content);
};

// --- UI Utility ---
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight;
    }
  });
};

const connectionStatus = computed(() => {
  if (isConnected.value) {
    return { text: '已连接', class: 'connected' };
  }
  return { text: '未连接', class: 'disconnected' };
});


// --- Lifecycle Hooks ---
onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
  }
});
</script>

<style>
/* Using global styles from style.css but adding component-specific styles here */
#chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #2d2d2d;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.header {
  padding: 10px 20px;
  background-color: #333;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h1 {
  font-size: 1.2em;
  margin: 0;
}
.status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
}
.status-light {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  transition: background-color 0.3s;
}
.status-light.connected { background-color: #4caf50; }
.status-light.disconnected { background-color: #f44336; }

#chat-window {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-row {
  display: flex;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 18px;
  line-height: 1.6;
}
.message-row.user .message-bubble {
  background-color: #007bff;
  color: white;
  border-top-right-radius: 4px;
}
.message-row.assistant .message-bubble {
  background-color: #444;
  color: #f1f1f1;
  border-top-left-radius: 4px;
}

/* Markdown rendering styles */
.content p:first-child { margin-top: 0; }
.content p:last-child { margin-bottom: 0; }
.content pre {
  background-color: #1e1e1e;
  padding: 10px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.content code {
  font-family: 'Courier New', Courier, monospace;
}


#chat-input-area {
  display: flex;
  padding: 15px;
  border-top: 1px solid #444;
  background-color: #333;
}
#chat-input-area textarea {
  flex-grow: 1;
  border-radius: 6px;
  border: 1px solid #555;
  background-color: #252525;
  color: #f1f1f1;
  padding: 10px;
  resize: none;
  font-family: inherit;
  font-size: 1em;
  margin-right: 10px;
}
#chat-input-area button {
  background-color: #007bff;
  color: white;
  border: none;
}
#chat-input-area button:disabled {
  background-color: #555;
  cursor: not-allowed;
}
</style>