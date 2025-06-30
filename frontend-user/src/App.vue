<template>
  <div class="flex flex-col h-screen w-screen bg-neutral-95 font-sans">
    <header class="flex-shrink-0 bg-neutral-100 border-b border-neutral-80 flex items-center px-6 h-16 shadow-sm">
      <h1 class="text-xl font-semibold text-neutral-10">企业智能知识库</h1>
    </header>

    <main class="flex-1 flex flex-col overflow-hidden">
      <div id="chat-container" ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-for="msg in messages" :key="msg.id">
          <div v-if="msg.role === 'assistant'" class="flex items-start gap-3">
            <div class="flex-shrink-0 h-9 w-9 rounded-full bg-salesforce-blue flex items-center justify-center text-white shadow-sm">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <div class="bg-neutral-100 p-3 rounded-xl rounded-tl-none max-w-2xl shadow-sm border border-neutral-80">
              <div v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none prose-p:my-2 prose-ol:my-2 prose-ul:my-2"></div>
            </div>
          </div>
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-salesforce-blue text-white p-3 rounded-xl rounded-br-none max-w-2xl shadow-sm">
              <p class="text-sm">{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <div v-if="isGenerating" class="flex items-start gap-3">
          <div class="flex-shrink-0 h-9 w-9 rounded-full bg-salesforce-blue flex items-center justify-center text-white shadow-sm">
             <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div class="bg-neutral-100 p-4 rounded-xl rounded-tl-none shadow-sm border border-neutral-80 flex items-center space-x-2">
            <span class="h-2 w-2 bg-neutral-50 rounded-full animate-bounce" style="animation-delay: -0.3s;"></span>
            <span class="h-2 w-2 bg-neutral-50 rounded-full animate-bounce" style="animation-delay: -0.15s;"></span>
            <span class="h-2 w-2 bg-neutral-50 rounded-full animate-bounce"></span>
          </div>
        </div>
      </div>

      <footer class="flex-shrink-0 bg-neutral-100/70 border-t border-neutral-80 p-4">
        <div class="flex items-center space-x-3 max-w-4xl mx-auto">
          <input
            type="text"
            v-model="userInput"
            @keyup.enter="sendMessage"
            placeholder="请输入您的问题..."
            class="flex-1 w-full px-4 py-2 bg-white border border-gray-300 rounded-full focus:ring-2 focus:ring-salesforce-blue focus:outline-none text-sm shadow-sm"
            :disabled="isGenerating"
          />
          <button
            @click="sendMessage"
            class="bg-salesforce-blue text-white px-5 py-2 rounded-full text-sm font-medium hover:bg-salesforce-blue-dark disabled:bg-neutral-50 disabled:cursor-not-allowed transition-colors shadow-sm"
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
import { ref, onMounted, nextTick } from 'vue';
import MarkdownIt from 'markdown-it';

const messages = ref([
  { id: 'welcome', role: 'assistant', content: '您好！我是您的智能售后助手，请问有什么可以帮您？' }
]);
const socket = ref(null);
const userInput = ref('');
const isGenerating = ref(false);
const sessionId = ref('');
const chatContainer = ref(null);
const md = new MarkdownIt();

onMounted(() => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/api/chat/ws`;
  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => console.log("WebSocket 连接成功");
  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.session_id) sessionId.value = data.session_id;

    if (data.event === '[DONE]') {
      isGenerating.value = false;
      return;
    }

    const lastMessage = messages.value[messages.value.length - 1];
    if (lastMessage && lastMessage.role === 'assistant') {
      if (data.token) {
        lastMessage.content += data.token;
      }
      if (data.sources) {
        lastMessage.sources = data.sources;
      }
      scrollToBottom();
    }
  };
});

const sendMessage = () => {
  if (!userInput.value.trim() || isGenerating.value) return;

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userInput.value,
  });

  const payload = { query: userInput.value, session_id: sessionId.value };
  socket.value.send(JSON.stringify(payload));
  userInput.value = '';
  isGenerating.value = true;
  
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    sources: []
  });

  scrollToBottom();
};

const renderMarkdown = (content) => md.render(content);

const scrollToBottom = () => {
  nextTick(() => {
    chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' });
  });
};
</script>

