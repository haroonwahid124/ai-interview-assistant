import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// proxy /api to the backend in dev
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
