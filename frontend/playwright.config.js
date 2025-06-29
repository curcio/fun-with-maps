// @ts-check
import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const indexPath = join(__dirname, '..', 'backend', 'static', 'index.html');

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: `file://${indexPath}`,
  },
});
