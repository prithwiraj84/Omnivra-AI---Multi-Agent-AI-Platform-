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
      // The backend serves /health at the ROOT (not under /api); proxy it so the
      // Settings page's liveness check reaches the backend instead of Vite's SPA fallback.
      '/health': {
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
          // Swallow socket-level write aborts on the upgraded WS connection
          // (ECONNABORTED/ECONNRESET on reconnect) so they don't spam the dev console.
          proxy.on('proxyReqWs', (_proxyReq, _req, socket) => {
            socket.on('error', () => {})
          })
          proxy.on('open', (socket) => {
            socket.on('error', () => {})
          })
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
