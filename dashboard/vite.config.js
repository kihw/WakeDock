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
            // Ajoute un rapport de bundle pour analyser les performances
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
                    configure: (proxy, _options) => {
                        proxy.on('error', (err, _req, _res) => {
                            console.log('proxy error', err);
                        });
                        proxy.on('proxyReq', (proxyReq, req, _res) => {
                            console.log('Sending Request to the Target:', req.method, req.url);
                        });
                        proxy.on('proxyRes', (proxyRes, req, _res) => {
                            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
                        });
                    },
                },
                '/ws': {
                    target: wsBaseUrl,
                    ws: true,
                    changeOrigin: true,
                    secure: false,
                    configure: (proxy, _options) => {
                        proxy.on('error', (err, _req, _res) => {
                            console.log('websocket proxy error', err);
                        });
                    },
                }
            }
        },
        css: {
            devSourcemap: true
        },
        build: {
            sourcemap: isProduction ? false : true, // Désactive en prod pour réduire la taille
            cssCodeSplit: true,
            rollupOptions: {
                output: {
                    manualChunks: (id) => {
                        // Chunking optimisé basé sur le chemin des modules
                        if (id.includes('node_modules')) {
                            if (id.includes('svelte')) return 'vendor-svelte';
                            if (id.includes('lucide')) return 'vendor-icons';
                            return 'vendor'; // autres dépendances
                        }
                        // Regrouper par features pour le code de l'application
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
            // Optimisation des assets
            assetsInlineLimit: 4096, // 4KB - inline plus petit assets
            chunkSizeWarningLimit: 500, // Warning pour chunks > 500KB
            minify: 'terser',
            terserOptions: {
                compress: {
                    drop_console: isProduction, // Supprime console.log en production
                    drop_debugger: isProduction, // Supprime debugger en production
                    pure_funcs: isProduction ? ['console.log', 'console.debug', 'console.info'] : []
                }
            },
            // Optimisations additionnelles
            reportCompressedSize: true,
            target: 'es2020', // Target moderne pour réduire la taille du code
        }
    };
});
