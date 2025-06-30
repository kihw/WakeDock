/**
 * Performance Optimization Configuration
 * Bundle analysis and code splitting configuration
 */

import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    sveltekit(),
    
    // Bundle analyzer for production builds
    ...(process.env.ANALYZE === 'true' ? [
      visualizer({
        filename: 'dist/bundle-analysis.html',
        open: true,
        gzipSize: true,
        brotliSize: true,
        template: 'treemap'
      })
    ] : [])
  ],

  build: {
    // Performance optimizations
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
    
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    
    rollupOptions: {
      output: {
        // Manual chunking for better caching
        manualChunks: {
          // Vendor chunks
          'vendor-svelte': ['svelte', 'svelte/store'],
          'vendor-utils': ['lodash-es', 'date-fns'],
          
          // Feature chunks
          'services': [
            'src/routes/services/+page.svelte',
            'src/routes/services/[id]/+page.svelte',
            'src/routes/services/new/+page.svelte'
          ],
          'analytics': [
            'src/routes/analytics/+page.svelte'
          ],
          'security': [
            'src/routes/security/+page.svelte'
          ],
          
          // Component chunks
          'charts': [
            'src/lib/components/charts/ResourceChart.svelte'
          ],
          'forms': [
            'src/lib/components/forms/ServiceForm.svelte'
          ]
        },
        
        // Ensure dynamic imports are properly chunked
        dynamicImportFunction: 'import'
      }
    },
    
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console statements in production
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.debug']
      },
      mangle: {
        safari10: true
      }
    }
  },

  // Performance optimizations for development
  server: {
    fs: {
      // Allow serving files from one level up
      allow: ['..']
    }
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'svelte/store',
      'svelte/animate',
      'svelte/easing',
      'svelte/motion',
      'svelte/transition'
    ],
    exclude: [
      // Exclude large libraries that should be loaded on demand
      'three',
      'chart.js'
    ]
  },

  // Experimental features for better performance
  experimental: {
    renderBuiltUrl(filename, { hostType }) {
      if (hostType === 'js') {
        return { js: `/${filename}` };
      }
      return { relative: true };
    }
  }
});
