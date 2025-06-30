<template>
  <div class="flex flex-col h-full w-full bg-light-secondary">
    <header class="flex-shrink-0 bg-light border-b border-border flex items-center h-16 shadow-sm">
      <div class="w-full max-w-3xl mx-auto px-4">
        <h1 class="text-lg font-semibold text-dark">企业智能知识库</h1>
      </div>
    </header>

    <main class="flex-1 overflow-hidden">
      <div class="h-full w-full max-w-3xl mx-auto flex flex-col" id="chat-wrapper">
        <transition-group tag="div" name="message" class="flex-1 overflow-y-auto p-4 space-y-6" ref="chatContainer">
          <div key="welcome-message" class="flex items-start gap-4">
            <div class="flex-shrink-0 h-9 w-9 rounded-full bg-brand-blue flex items-center justify-center text-white shadow-sm">
              <el-icon :size="20"><ChatDotRound /></el-icon>
            </div>
            <div class="bg-light p-4 rounded-xl rounded-tl-none max-w-xl shadow-sm border border-border">
              <p class="text-sm text-dark-secondary">您好！我是您的智能售后助手，请问有什么可以帮您？</p>
            </div>
          </div>
          
          <div v-for="msg in messages" :key="msg.id" :class="msg.role === 'user' ? 'flex justify-end' : 'flex items-start gap-4'">
            <template v-if="msg.role === 'assistant'">
              <div class="flex-shrink-0 h-9 w-9 rounded-full bg-brand-blue flex items-center justify-center text-white shadow-sm">
                <el-icon :size="20"><ChatDotRound /></el-icon>
              </div>
              <div class="bg-light p-3.5 rounded-xl rounded-tl-none max-w-xl shadow-sm border border-border">
                <div v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none text-dark-secondary prose-p:my-2 prose-ol:my-2 prose-ul:my-2"></div>
              </div>
            </template>
            
            <template v-if="msg.role === 'user'">
              <div class="bg-brand-blue text-white p-3.5 rounded-xl rounded-br-none max-w-xl shadow-sm">
                <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
              </div>
            </template>
          </div>

          <div v-if="isGenerating" key="thinking-indicator" class="flex items-start gap-4">
             <div class="flex-shrink-0 h-9 w-9 rounded-full bg-brand-blue flex items-center justify-center text-white shadow-sm animate-pulse">
               <el-icon :size="20"><ChatDotRound /></el-icon>
             </div>
             <div class="bg-light p-4 rounded-xl rounded-tl-none shadow-sm border border-border flex items-center space-x-2">
                <span class="h-1.5 w-1.5 bg-dark-secondary rounded-full animate-pulse" style="animation-delay: -0.2s;"></span>
                <span class="h-1.5 w-1.5 bg-dark-secondary rounded-full animate-pulse" style="animation-delay: -0.1s;"></span>
                <span class="h-1.5 w-1.5 bg-dark-secondary rounded-full animate-pulse"></span>
             </div>
          </div>
        </transition-group>

        <footer class="flex-shrink-0 p-4 pb-6">
           <div 
             class="relative transition-all duration-300 ease-in-out"
             :class="{ 'shadow-glow': isInputFocused }"
           >
            <textarea
              ref="textareaRef"
              v-model="userInput"
              @keydown.enter.exact.prevent="sendMessage"
              @focus="isInputFocused = true"
              @blur="isInputFocused = false"
              placeholder="请输入您的问题..."
              class="w-full pl-4 pr-12 py-3.5 bg-light border border-border rounded-2xl focus:ring-0 focus:outline-none text-sm text-dark-secondary shadow-sm transition-all duration-300 ease-in-out resize-none"
              :style="{ height: textareaHeight + 'px' }"
            ></textarea>
            <button
              @click="sendMessage"
              class="absolute right-3 bottom-3 flex items-center justify-center h-8 w-8 rounded-full transition-colors"
              :class="userInput.trim() ? 'bg-brand-blue text-white' : 'bg-gray-200 text-gray-400'"
              :disabled="!userInput.trim() || isGenerating"
            >
              <el-icon :size="18"><Promotion /></el-icon>
            </button>
           </div>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue';
import MarkdownIt from 'markdown-it';
import { ElIcon } from 'element-plus';
import { ChatDotRound, Promotion } from '@element-plus/icons-vue';

const messages = ref([]);
const socket = ref(null);
const userInput = ref('');
const isGenerating = ref(false);
const sessionId = ref('');
const chatContainer = ref(null);
const md = new MarkdownIt();
const isInputFocused = ref(false);
const textareaRef = ref(null);
const baseHeight = 52; 
const maxHeight = 200; 

const textareaHeight = computed(() => {
    const lines = userInput.value.split('\n').length;
    const newHeight = baseHeight + (lines - 1) * 20;
    return Math.min(Math.max(newHeight, baseHeight), maxHeight);
});

onMounted(() => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/api/chat/ws`;
  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => console.log("WebSocket 连接成功");

  socket.value.onmessage = (event) => {
    if (isGenerating.value && !messages.value.some(m => m.id === 'generating')) {
      isGenerating.value = false;
    }
    
    const data = JSON.parse(event.data);
    if (data.session_id) sessionId.value = data.session_id;

    if (data.event === '[DONE]') {
      isGenerating.value = false;
      return;
    }

    let lastMessage = messages.value[messages.value.length - 1];
    
    if (!lastMessage || lastMessage.role !== 'assistant' || lastMessage.content.endsWith('[DONE]')) {
       messages.value.push({
          id: Date.now() + Math.random(),
          role: 'assistant',
          content: ''
       });
       lastMessage = messages.value[messages.value.length - 1];
    }
    
    if (data.token) {
      lastMessage.content += data.token;
      scrollToBottom();
    }
  };
  
  textareaRef.value?.focus();
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
  
  scrollToBottom();

  nextTick(() => {
    textareaRef.value?.focus();
  });
};

const renderMarkdown = (content) => md.render(content);

const scrollToBottom = () => {
  nextTick(() => {
    const el = chatContainer.value?.$el;
    if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  });
};
</script>

<style>
.message-enter-active {
  transition: all 0.4s ease-out;
}
.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.message-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.message-leave-active {
  transition: all 0.3s ease-in;
  position: absolute;
}
#chat-wrapper {
  height: 100%;
}
</style>