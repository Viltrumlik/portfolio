/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url';
import preact from '@preact/preset-vite';
import { defineConfig } from 'vite';

// Django loads the dev client from http://localhost:5173/@vite/client and /src/main.ts,
// and the built files from STATIC_URL + "dist/" via static/dist/.vite/manifest.json.
const DEV_ORIGIN = 'http://localhost:5173';

export default defineConfig(({ command }) => ({
  root: fileURLToPath(new URL('.', import.meta.url)),
  base: command === 'build' ? '/static/dist/' : '/',
  plugins: [preact()],
  resolve: {
    alias: {
      react: 'preact/compat',
      'react-dom': 'preact/compat',
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    origin: DEV_ORIGIN,
    // Same-machine pages only (Django on localhost / 127.0.0.1 on any port).
    cors: { origin: /^https?:\/\/(?:(?:[^:]+\.)?localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/ },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: fileURLToPath(new URL('./src/main.ts', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'],
    restoreMocks: true,
  },
}));
