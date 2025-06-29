<template>
  <div class="flex flex-col h-screen w-screen bg-neutral-95 font-sans">
    
    <header class="flex-shrink-0 bg-neutral-100 border-b border-neutral-80 flex items-center px-6 h-16 shadow-sm">
      <h1 class="text-xl font-semibold text-neutral-10">企业智能知识库</h1>
    </header>

    <main class="flex-1 flex flex-col overflow-hidden">
      <div id="chat-container" ref="chatContainer" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        
        <div class="flex items-start space-x-3">
          <div class="flex-shrink-0 h-10 w-10 rounded-full bg-salesforce-blue flex items-center justify-center text-white">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div class="bg-neutral-100 p-4 rounded-lg rounded-tl-none max-w-xl shadow-sm border border-neutral-80">
            <p class="text-sm text-neutral-10">您好！我是您的智能售后助手，请问有什么可以帮您？</p>
          </div>
        </div>

        <div v-for="msg in messages" :key="msg.id" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'items-start'">
          
          <div v-if="msg.role === 'assistant'" class="flex items-start space-x-3">
            <div class="flex-shrink-0 h-10 w-10 rounded-full bg-salesforce-blue flex items-center justify-center text-white">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <div class="bg-neutral-100 p-4 rounded-lg rounded-tl-none max-w-xl shadow-sm border border-neutral-80">
              <div v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none"></div>
              
              <div v-if="msg.sources && msg.sources.length > 0" class="mt-4 border-t border-neutral-80 pt-3">
                <h4 class="text-xs font-semibold text-neutral-50 mb-2">引用来源:</h4>
                <div class="space-y-2">
                  <div v-for="(source, index) in msg.sources" :key="index" class="bg-neutral-95/50 p-3 rounded-md text-xs text-neutral-10">
                    <p class="font-medium truncate"><strong>{{ source.metadata.source }}</strong></p>
                    <p class="mt-1 text-neutral-50">{{ source.page_content }}</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
          
          <div v-if="msg.role === 'user'" class="bg-salesforce-blue text-white p-4 rounded-lg rounded-br-none max-w-xl shadow-sm">
            <p class="text-sm">{{ msg.content }}</p>
          </div>

        </div>

        <div v-if="isGenerating" class="flex items-start space-x-3">
          <div class="flex-shrink-0 h-10 w-10 rounded-full bg-salesforce-blue flex items-center justify-center text-white">
             <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div class="bg-neutral-100 p-4 rounded-lg rounded-tl-none max-w-xl shadow-sm border border-neutral-80 flex items-center space-x-2">
            <span class="h-2 w-2 bg-salesforce-blue rounded-full animate-bounce delay-75"></span>
            <span class="h-2 w-2 bg-salesforce-blue rounded-full animate-bounce delay-150"></span>
            <span class="h-2 w-2 bg-salesforce-blue rounded-full animate-bounce delay-300"></span>
          </div>
        </div>

      </div>

      <footer class="flex-shrink-0 bg-neutral-100 border-t border-neutral-80 p-4">
        <div class="flex items-center space-x-2">
          <input
            type="text"
            v-model="userInput"
            @keyup.enter="sendMessage"
            placeholder="请输入您的问题..."
            class="flex-1 w-full px-4 py-2 bg-white border border-neutral-80 rounded-md focus:ring-2 focus:ring-salesforce-blue focus:outline-none text-sm"
            :disabled="isGenerating"
          />
          <button
            @click="sendMessage"
            class="bg-salesforce-blue text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-salesforce-blue-dark disabled:bg-neutral-50 disabled:cursor-not-allowed"
            :disabled="!userInput.trim() || isGenerating"
          >
            发送
          </button>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import MarkdownIt from 'markdown-it';

// --- WebSocket 和数据状态管理 ---
const socket = ref(null);
const messages = ref([]);
const userInput = ref('');
const isGenerating = ref(false);
const sessionId = ref('');
const chatContainer = ref(null);

const md = new MarkdownIt(); // 初始化 Markdown 渲染器

// --- WebSocket 连接 ---
onMounted(() => {
  // 注意：这里的 URL 可能需要根据你的反向代理配置进行调整
  const wsUrl = `ws://${window.location.host}/api/chat/ws`;
  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => console.log("WebSocket 连接成功");
  socket.value.onerror = (error) => console.error("WebSocket 错误: ", error);
  socket.value.onclose = () => console.log("WebSocket 连接已关闭");
  
  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.session_id) sessionId.value = data.session_id;

    if (data.token) {
      handleToken(data.token);
    }
    
    if (data.sources) {
      handleSources(data.sources);
    }

    if (data.event === '[DONE]') {
      isGenerating.value = false;
    }
  };
});

// --- 核心方法 ---

const sendMessage = () => {
  if (!userInput.value.trim() || isGenerating.value) return;

  // 1. 将用户消息添加到列表
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userInput.value,
  });

  // 2. 准备发送的数据
  const payload = {
    query: userInput.value,
    session_id: sessionId.value,
  };

  // 3. 发送数据并清空输入框
  socket.value.send(JSON.stringify(payload));
  userInput.value = '';
  isGenerating.value = true;

  // 4. 创建一个空的 AI 消息占位符
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    sources: []
  });

  scrollToBottom();
};

const handleToken = (token) => {
  const lastMessage = messages.value[messages.value.length - 1];
  if (lastMessage && lastMessage.role === 'assistant') {
    lastMessage.content += token;
    scrollToBottom();
  }
};

const handleSources = (sources) => {
  const lastMessage = messages.value[messages.value.length - 1];
   if (lastMessage && lastMessage.role === 'assistant') {
    lastMessage.sources = sources;
    scrollToBottom();
  }
}

const renderMarkdown = (content) => {
  return md.render(content);
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
};

</script>

