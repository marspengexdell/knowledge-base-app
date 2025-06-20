import { createApp } from 'vue'

// Import Element Plus UI Library and its base styles
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// Import the root Vue component
import App from './App.vue'

// Import the router instance we created
import router from './router'
// import { createPinia } from 'pinia' // Pinia setup is still pending


// --- Create and configure the Vue application instance ---

// 1. Create the application instance from the root component
const app = createApp(App)

// 2. Use plugins
// app.use(createPinia()) 
app.use(router)       // Use the Vue Router plugin
app.use(ElementPlus)  // Register the Element Plus component library

// 3. Mount the application to the DOM
// This targets the <div id="app"></div> in the public/index.html file
app.mount('#app')
