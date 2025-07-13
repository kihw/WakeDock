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
                        // Vendor splitting - more granular
                        if (id.includes('node_modules')) {
                            if (id.includes('svelte')) return 'vendor-svelte';
                            if (id.includes('lucide')) return 'vendor-icons';
                            if (id.includes('chart') || id.includes('graph') || id.includes('plot')) return 'vendor-charts';
                            if (id.includes('@floating-ui') || id.includes('tippy')) return 'vendor-floating';
                            if (id.includes('date') || id.includes('time') || id.includes('moment')) return 'vendor-date';
                            return 'vendor-core';
                        }

                        // Route-based splitting
                        if (id.includes('/routes/services/')) return 'route-services';
                        if (id.includes('/routes/monitoring/')) return 'route-monitoring';
                        if (id.includes('/routes/analytics/')) return 'route-analytics';
                        if (id.includes('/routes/backup/')) return 'route-backup';
                        if (id.includes('/routes/users/')) return 'route-users';
                        if (id.includes('/routes/settings/')) return 'route-settings';

                        // Component-based splitting
                        if (id.includes('/lib/components/charts/')) return 'components-charts';
                        if (id.includes('/lib/components/ui/organisms/')) return 'components-organisms';
                        if (id.includes('/lib/components/ui/molecules/')) return 'components-molecules';
                        if (id.includes('/lib/components/auth/')) return 'components-auth';
                        if (id.includes('/lib/components/mobile/')) return 'components-mobile';
                        if (id.includes('/lib/components/')) return 'components-core';

                        // Feature splitting
                        if (id.includes('/lib/features/')) return 'features';
                        if (id.includes('/lib/stores/')) return 'stores';
                        if (id.includes('/lib/utils/')) return 'utils';
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
            chunkSizeWarningLimit: 1000,
            minify: 'terser',
            terserOptions: {
                compress: {
                    drop_console: isProduction,
                    drop_debugger: isProduction,
                    pure_funcs: isProduction ? ['console.log', 'console.debug', 'console.info'] : [],
                    passes: 2
                },
                mangle: {
                    safari10: true
                },
                format: {
                    comments: false
                }
            },
            reportCompressedSize: true,
            target: 'es2020',
        }
    };
});
