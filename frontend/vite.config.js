import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: './src/Certs/localhost+2-key.pem',
      cert: './src/Certs/localhost+2.pem',
    },
    host: 'localhost',
    port: 5173,
  },
})
