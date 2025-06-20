import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Configure the development server
    port: 8080, // Specify the port for the user UI dev server
    host: true, // This allows the server to be accessible from outside the container
    proxy: {
      // Proxy for standard API requests (e.g., submitting feedback)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy for the WebSocket chat connection
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true, // Enable WebSocket proxying
      },
    }
  },
  build: {
    outDir: 'dist',
  }
})
