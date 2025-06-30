<template>
  <div class="flex flex-col h-screen w-screen bg-background-primary font-sans">

    <header class="flex-shrink-0 flex items-center justify-between px-6 h-16 border-b border-border-color">
      <h1 class="text-xl font-medium text-text-primary tracking-wide">企业智能知识库</h1>
      </header>

    <main class="flex-1 relative overflow-hidden">
      <div id="chat-container" ref="chatContainer" class="h-full overflow-y-auto p-6 space-y-8 pb-48">
        <div v-for="msg in messages" :key="msg.id">
          <div v-if="msg.role === 'assistant'" class="flex items-start gap-4">
            <div class="flex-shrink-0 h-8 w-8 rounded-full bg-background-tertiary flex items-center justify-center text-primary-blue shadow-md">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <div class="bg-transparent rounded-lg max-w-3xl">
              <div v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none prose-invert prose-p:my-2"></div>
            </div>
          </div>

          <div v-if="msg.role === 'user'" class="flex items-start gap-4 flex-row-reverse">
             <div class="flex-shrink-0 h-8 w-8 rounded-full bg-background-tertiary flex items-center justify-center text-text-secondary shadow-md">
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-8a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 10c-3.86 0-7 1.498-7 3.335V20h14v-2.665c0-1.837-3.14-3.335-7-3.335Z"></path></svg>
            </div>
            <div class="bg-background-tertiary p-3 rounded-xl max-w-3xl shadow-md">
              <p class="text-sm text-text-primary">{{ msg.content }}</p>
            </div>
          </div>
        </div>
        <div v-if="isGenerating" class="flex items-start gap-4">
          <div class="flex-shrink-0 h-8 w-8 rounded-full bg-background-tertiary flex items-center justify-center text-primary-blue shadow-md">
             <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <div class="pt-1">
             <div class="h-6 w-1 bg-primary-blue rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>

      <footer class="absolute bottom-0 left-0 right-0 p-6 flex justify-center">
          <div 
            class="transition-all duration-300 ease-in-out" 
            :class="isInputFocused ? 'animate-expand' : 'animate-shrink'"
            style="max-width: 56rem;"
          >
            <div class="relative w-full">
              <textarea
                ref="inputRef"
                v-model="userInput"
                @keydown.enter.exact.prevent="sendMessage"
                @focus="isInputFocused = true"
                @blur="isInputFocused = false"
                placeholder="请输入您的问题..."
                class="w-full pl-5 pr-14 py-3 bg-background-secondary border border-border-color rounded-full focus:ring-2 focus:ring-primary-blue/50 focus:outline-none text-sm resize-none shadow-2xl transition-all duration-300 ease-in-out"
                rows="1"
                style="padding-top: 0.8rem; padding-bottom: 0.8rem;"
              ></textarea>
              <button
                @click="sendMessage"
                class="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 flex items-center justify-center bg-background-tertiary rounded-full hover:bg-primary-blue/20 disabled:bg-transparent disabled:cursor-not-allowed"
                :disabled="!userInput.trim() || isGenerating"
              >
                <svg class="h-5 w-5" :class="userInput.trim() ? 'text-text-primary' : 'text-text-secondary'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h11.232a4.5 4.5 0 0 1 0 2H3a1 1 0 1 1 0-2Zm19.92-9.434a1 1 0 0 0-1.07-.15L3.302 9.176a1 1 0 0 0 .15 1.92l7.375-2.313 7.91 7.233-2.62 2.05a1 1 0 0 0 .61 1.9L21.8 14.5a1 1 0 0 0 .54-1.391L15.39 3.86a1 1 0 0 0-1.47-.294l-1.35 1.057 9.35 3.821Z"></path></svg>
              </button>
            </div>
          </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import MarkdownIt from 'markdown-it';

const messages = ref([]);
const socket = ref(null);
const userInput = ref('');
const isGenerating = ref(false);
const sessionId = ref('');
const chatContainer = ref(null);
const isInputFocused = ref(false);
const inputRef = ref(null);
const md = new MarkdownIt();

// 自动调整输入框高度
watch(userInput, (newVal) => {
  nextTick(() => {
    const el = inputRef.value;
    if (el) {
      el.style.height = 'auto';
      const scrollHeight = el.scrollHeight;
      el.style.height = `${scrollHeight}px`;
    }
  });
});

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

<style>
/* prose-invert 会自动处理好暗黑模式下的文字、链接、代码块颜色 */
.prose {
  --tw-prose-body: var(--text-primary);
  --tw-prose-headings: var(--text-primary);
  --tw-prose-links: var(--primary-blue);
  --tw-prose-code: var(--text-primary);
  --tw-prose-pre-bg: var(--background-secondary);
}
</style>