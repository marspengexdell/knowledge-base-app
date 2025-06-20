import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Import the root Vue component
import App from './App.vue'

// Import a simple global stylesheet
import './style.css'

// --- Create and configure the Vue application instance ---
const app = createApp(App)

// Use Pinia for state management
app.use(createPinia())

// Mount the application to the DOM
app.mount('#app')
