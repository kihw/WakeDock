import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter({
            // Explicitly set the output directory
            out: 'build',
            // Precompress files for better performance
            precompress: false,
            // Environment variables prefix
            envPrefix: ''
        })
    }
};

export default config;
