export default {
    plugins: {
        tailwindcss: {},
        autoprefixer: {},
        // CSS optimization for production
        ...(process.env.NODE_ENV === 'production' ? {
            'cssnano': {
                preset: ['default', {
                    discardComments: {
                        removeAll: true,
                    },
                    normalizeWhitespace: true,
                    colormin: true,
                    reduceIdents: false, // Keep CSS custom properties intact
                    zindex: false, // Keep z-index values intact
                    mergeLonghand: true,
                    mergeRules: true,
                    minifyFontValues: true,
                    minifyGradients: true,
                    minifyParams: true,
                    minifySelectors: true,
                    normalizeCharset: true,
                    normalizeDisplayValues: true,
                    normalizePositions: true,
                    normalizeRepeatStyle: true,
                    normalizeString: true,
                    normalizeTimingFunctions: true,
                    normalizeUnicode: true,
                    normalizeUrl: true,
                    orderedValues: true,
                    reduceTransforms: true,
                    convertValues: {
                        length: false, // Keep rem/px units intact for design system
                    },
                }],
            },
            '@fullhuman/postcss-purgecss': {
                content: [
                    './src/**/*.{html,js,svelte,ts}',
                    './src/**/*.md'
                ],
                defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
                safelist: [
                    // Preserve design system classes
                    /^variant-/,
                    /^theme-/,
                    /^dark:/,
                    /^hover:/,
                    /^focus:/,
                    /^active:/,
                    // Preserve dynamic classes
                    'animate-pulse',
                    'animate-spin',
                    'animate-fade',
                    // Preserve glassmorphism classes
                    'backdrop-blur',
                    'bg-opacity',
                    // Preserve responsive classes that might be dynamically applied
                    /^sm:/,
                    /^md:/,
                    /^lg:/,
                    /^xl:/,
                    /^2xl:/,
                ],
                blocklist: [
                    // Remove unused Tailwind utilities
                    /^backdrop-brightness/,
                    /^backdrop-contrast/,
                    /^backdrop-grayscale/,
                    /^backdrop-hue/,
                    /^backdrop-invert/,
                    /^backdrop-saturate/,
                    /^backdrop-sepia/,
                    /^bg-attachment/,
                    /^bg-clip/,
                    /^bg-origin/,
                    /^bg-position/,
                    /^bg-repeat/,
                    /^bg-size/,
                ]
            }
        } : {})
    },
}
