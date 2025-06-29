import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../backend/static'),
    emptyOutDir: false,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './setupTests.js',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,jsx}'],
    exclude: ['tests/**'],
  },
});
