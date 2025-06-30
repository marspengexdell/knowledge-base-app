import './index.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Import the root Vue component
import App from './App.vue'

// --- Create and configure the Vue application instance ---
const app = createApp(App)

// Use Pinia for state management
app.use(createPinia())

// Mount the application to the DOM
app.mount('#app')
