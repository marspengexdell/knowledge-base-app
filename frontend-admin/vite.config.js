import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Imports for Element Plus auto-importing
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Configure AutoImport to automatically import Element Plus functions
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    // Configure Components to automatically import Element Plus components
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  server: {
    // Configure the development server
    port: 8081, // Specify the port for the admin UI dev server
    proxy: {
      // Set up a proxy for API requests to the backend
      '/api': {
        // Requests to /api will be forwarded to the backend server
        target: 'http://localhost:8000',
        // Change the origin of the host header to the target URL
        changeOrigin: true,
        // The path will not be rewritten, so /api/admin/models remains /api/admin/models
        // rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  },
  // Base path for serving the admin front-end
  base: '/admin/',
  // Optional: Configure build options, like output directory
  build: {
    outDir: 'dist',
  }
})