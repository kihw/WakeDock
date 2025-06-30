/**
 * Asset Optimization Utilities
 * Utilities for optimizing images, icons, and other static assets
 */

/**
 * WebP image with fallback support
 */
export function createWebPWithFallback(src: string, alt: string, className?: string): string {
    const webpSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    
    return `
        <picture ${className ? `class="${className}"` : ''}>
            <source srcset="${webpSrc}" type="image/webp">
            <img src="${src}" alt="${alt}" loading="lazy" decoding="async">
        </picture>
    `;
}

/**
 * Optimized SVG loading
 */
export function loadOptimizedSVG(iconName: string): Promise<string> {
    return import(`../assets/icons/${iconName}.svg?raw`).then(module => {
        // Remove unnecessary attributes and optimize
        return module.default
            .replace(/\s*fill="[^"]*"/g, '')
            .replace(/\s*stroke="[^"]*"/g, '')
            .replace(/\s*id="[^"]*"/g, '')
            .replace(/\s*class="[^"]*"/g, '');
    });
}

/**
 * Lazy loading for images
 */
export function setupLazyLoading(): void {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target as HTMLImageElement;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

/**
 * Preload critical assets
 */
export function preloadCriticalAssets(): void {
    // Preload critical fonts
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = '/fonts/inter-var.woff2';
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);

    // Preload critical images
    const criticalImages = [
        '/images/logo.webp',
        '/images/hero-bg.webp'
    ];

    criticalImages.forEach(src => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = src;
        link.as = 'image';
        document.head.appendChild(link);
    });
}

/**
 * Optimize icon loading
 */
export class IconOptimizer {
    private static cache = new Map<string, string>();
    
    static async getIcon(name: string): Promise<string> {
        if (this.cache.has(name)) {
            return this.cache.get(name)!;
        }
        
        try {
            const svgContent = await loadOptimizedSVG(name);
            this.cache.set(name, svgContent);
            return svgContent;
        } catch (error) {
            console.warn(`Failed to load icon: ${name}`, error);
            return `<svg><use xlink:href="#fallback-icon"></use></svg>`;
        }
    }
    
    static preloadIcons(iconNames: string[]): void {
        iconNames.forEach(name => {
            this.getIcon(name).catch(() => {
                // Silently handle preload failures
            });
        });
    }
}
