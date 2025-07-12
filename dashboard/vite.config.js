import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => {
    const isProduction = mode === 'production';
    const apiBaseUrl = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const wsBaseUrl = process.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

    return {
        plugins: [
            sveltekit(),
            isProduction && visualizer({
                filename: './build/stats.html',
                open: false,
                gzipSize: true,
                brotliSize: true,
            }),
        ],
        server: {
            host: '0.0.0.0',
            port: 3000,
            proxy: {
                '/api': {
                    target: apiBaseUrl,
                    changeOrigin: true,
                    secure: false,
                },
                '/ws': {
                    target: wsBaseUrl,
                    ws: true,
                    changeOrigin: true,
                    secure: false,
                }
            }
        },
        css: {
            devSourcemap: true
        },
        build: {
            sourcemap: !isProduction,
            cssCodeSplit: true,
            rollupOptions: {
                output: {
                    manualChunks: (id) => {
                        if (id.includes('node_modules')) {
                            if (id.includes('svelte')) return 'vendor-svelte';
                            if (id.includes('lucide')) return 'vendor-icons';
                            return 'vendor';
                        }
                        if (id.includes('/lib/features/')) return 'features';
                        if (id.includes('/lib/components/')) return 'components';
                    },
                    assetFileNames: (assetInfo) => {
                        const info = assetInfo.name.split('.');
                        const extType = info[info.length - 1];
                        if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
                            return `assets/images/[name]-[hash][extname]`;
                        }
                        if (/\.(css)$/i.test(assetInfo.name)) {
                            return `assets/css/[name]-[hash][extname]`;
                        }
                        if (/\.(woff|woff2|eot|ttf|otf)$/i.test(assetInfo.name)) {
                            return `assets/fonts/[name]-[hash][extname]`;
                        }
                        return `assets/[name]-[hash][extname]`;
                    }
                }
            },
            assetsInlineLimit: 4096,
            chunkSizeWarningLimit: 500,
            minify: 'terser',
            terserOptions: {
                compress: {
                    drop_console: isProduction,
                    drop_debugger: isProduction,
                    pure_funcs: isProduction ? ['console.log', 'console.debug', 'console.info'] : []
                }
            },
            reportCompressedSize: true,
            target: 'es2020',
        }
    };
});
