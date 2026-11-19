import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The browser talks only to its own origin. In development Vite forwards API
// paths to the local FastAPI server; in production a reverse proxy does the same.
const backend = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/health': { target: backend, changeOrigin: true },
    },
  },
})
