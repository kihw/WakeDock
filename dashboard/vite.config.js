import { sveltekit } from '@sveltejs/kit/vite';
import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig } from 'vite';

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
                    // Disable manual chunks to prevent stack overflow in SvelteKit analyzer
                    manualChunks: undefined,
                    assetFileNames: (assetInfo) => {
                        const info = assetInfo.name.split('.');
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
            chunkSizeWarningLimit: 1000,
            minify: isProduction ? 'terser' : false,
            terserOptions: isProduction ? {
                compress: {
                    drop_console: true,
                    drop_debugger: true,
                    pure_funcs: ['console.log', 'console.debug', 'console.info'],
                    passes: 2
                },
                mangle: {
                    safari10: true
                },
                format: {
                    comments: false
                }
            } : undefined,
            reportCompressedSize: true,
            target: 'es2020',
        }
    };
});
