import { defineConfig } from 'vite';
import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const frontendRoot = resolve(import.meta.dirname, 'frontend');

function htmlPages(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? htmlPages(path) : entry.name.endsWith('.html') ? [path] : [];
  });
}

export default defineConfig({
  root: frontendRoot,
  appType: 'mpa',
  build: {
    outDir: resolve(import.meta.dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: htmlPages(frontendRoot),
    },
  },
});