import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5173,
    proxy: {
      // Swallow the noisy ECONNREFUSED/ECONNABORTED logs that appear when the backend
      // dev server (:8000) isn't running — the SPA degrades to fallback data on its own.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', () => {})
        },
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', () => {})
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          flow: ['reactflow'],
          motion: ['framer-motion'],
        },
      },
    },
  },
})
