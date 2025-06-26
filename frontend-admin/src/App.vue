<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { marked } from 'marked';
import { v4 as uuidv4 } from 'uuid';

// --- 响应式状态 ---
const messages = ref([
  { id: uuidv4(), role: 'assistant', content: '您好！我是您的AI知识库助手，有什么可以帮助您的吗？' }
]);
const userInput = ref('');
const isConnected = ref(false);
const isGenerating = ref(false);
const chatWindow = ref(null);
let socket = null;
let isFirstToken = false;

// --- WebSocket 逻辑 ---
const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsURL = `${wsProtocol}//${window.location.host}/api/chat/ws`;
  
  socket = new WebSocket(wsURL);

  socket.onopen = () => {
    console.log("WebSocket 连接已建立。");
    isConnected.value = true;
  };

  socket.onmessage = (event) => {
    const receivedData = event.data;
    const lastMessage = messages.value[messages.value.length - 1];

    // 1. 优先处理流结束信号
    if (receivedData === '[DONE]') {
      if (isFirstToken && lastMessage && lastMessage.role === 'assistant') {
        messages.value.pop();
      }
      isGenerating.value = false;
      isFirstToken = false;
      console.log("AI 回复流已结束。");
      return;
    }

    // 2. 如果不是结束信号，且我们正期待回复，则处理为内容
    // （极限情况防御：isGenerating.value || (lastMessage && lastMessage.role === 'assistant')）
    if (isGenerating.value && lastMessage && lastMessage.role === 'assistant') {
      if (isFirstToken) {
        lastMessage.content = receivedData;
        isFirstToken = false;
      } else {
        lastMessage.content += receivedData;
      }
      scrollToBottom();
    }
  };

  socket.onclose = () => {
    console.log("WebSocket 连接已关闭。");
    isConnected.value = false;
    isGenerating.value = false;
  };

  socket.onerror = (error) => {
    console.error("WebSocket 错误:", error);
    isConnected.value = false;
    isGenerating.value = false;
    messages.value.push({
      id: uuidv4(),
      role: 'assistant',
      content: '抱歉，连接出现问题，请刷新页面重试。'
    });
  };
};

// --- 消息处理 ---
const sendMessage = () => {
  if (!userInput.value.trim() || !isConnected.value || isGenerating.value) return;

  messages.value.push({
    id: uuidv4(),
    role: 'user',
    content: userInput.value,
  });

  socket.send(userInput.value);
  userInput.value = '';
  
  isGenerating.value = true;
  isFirstToken = true;

  messages.value.push({
    id: uuidv4(),
    role: 'assistant',
    content: '🤔 思考中...',
  });
  
  scrollToBottom();
};

const renderMarkdown = (content) => marked.parse(content);

// --- UI 工具 ---
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

// --- 生命周期钩子 ---
onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
  }
});
</script>
