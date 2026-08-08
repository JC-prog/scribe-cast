import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Same relative /api/* calls work in `npm run dev` (proxied here) and in
      // the Dockerized build (proxied by nginx, see frontend/nginx.conf) —
      // no VITE_API_BASE_URL needed in either case.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
