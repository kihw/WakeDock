/**
 * Accessibility Utilities
 * Tools and helpers for accessibility compliance and improvement
 */

export interface A11yConfig {
    enableAnnouncements: boolean;
    enableFocusManagement: boolean;
    enableKeyboardNavigation: boolean;
    announceDelay: number;
}

/**
 * Gestionnaire d'accessibilité global
 */
class AccessibilityManager {
    private config: A11yConfig;
    private announcer?: HTMLElement;
    private focusStack: HTMLElement[] = [];

    constructor(config: Partial<A11yConfig> = {}) {
        this.config = {
            enableAnnouncements: true,
            enableFocusManagement: true,
            enableKeyboardNavigation: true,
            announceDelay: 100,
            ...config
        };

        if (typeof window !== 'undefined') {
            this.init();
        }
    }

    private init(): void {
        if (this.config.enableAnnouncements) {
            this.createAnnouncer();
        }

        if (this.config.enableKeyboardNavigation) {
            this.setupKeyboardNavigation();
        }
    }

    /**
     * Créer un élément pour les annonces screen reader
     */
    private createAnnouncer(): void {
        this.announcer = document.createElement('div');
        this.announcer.setAttribute('aria-live', 'polite');
        this.announcer.setAttribute('aria-atomic', 'true');
        this.announcer.style.position = 'absolute';
        this.announcer.style.left = '-10000px';
        this.announcer.style.width = '1px';
        this.announcer.style.height = '1px';
        this.announcer.style.overflow = 'hidden';
        document.body.appendChild(this.announcer);
    }

    /**
     * Configuration de la navigation clavier
     */
    private setupKeyboardNavigation(): void {
        document.addEventListener('keydown', (event) => {
            // Échap pour fermer les modales
            if (event.key === 'Escape') {
                const openModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
                if (openModal) {
                    this.closeModal(openModal as HTMLElement);
                }
            }

            // Tab piège pour les modales
            if (event.key === 'Tab') {
                const activeModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
                if (activeModal) {
                    this.trapFocus(event, activeModal as HTMLElement);
                }
            }
        });
    }

    /**
     * Piège le focus dans un élément
     */
    private trapFocus(event: KeyboardEvent, container: HTMLElement): void {
        const focusableElements = this.getFocusableElements(container);
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
            if (document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }

    /**
     * Annonce un message aux lecteurs d'écran
     */
    announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
        if (!this.config.enableAnnouncements || !this.announcer) return;

        this.announcer.setAttribute('aria-live', priority);

        // Délai pour s'assurer que le message est lu
        setTimeout(() => {
            if (this.announcer) {
                this.announcer.textContent = message;
            }
        }, this.config.announceDelay);

        // Nettoyer après un délai
        setTimeout(() => {
            if (this.announcer) {
                this.announcer.textContent = '';
            }
        }, this.config.announceDelay + 3000);
    }

    /**
     * Gère le focus lors de l'ouverture d'une modale
     */
    openModal(modal: HTMLElement): void {
        if (!this.config.enableFocusManagement) return;

        // Sauvegarder l'élément actuellement focusé
        const currentFocus = document.activeElement as HTMLElement;
        if (currentFocus) {
            this.focusStack.push(currentFocus);
        }

        // Configurer la modale
        modal.setAttribute('aria-hidden', 'false');
        modal.setAttribute('role', 'dialog');

        // Focuser le premier élément focusable ou la modale elle-même
        const focusableElements = this.getFocusableElements(modal);
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        } else if (modal.tabIndex >= 0) {
            modal.focus();
        }

        // Ajouter un backdrop si nécessaire
        this.addModalBackdrop(modal);
    }

    /**
     * Gère le focus lors de la fermeture d'une modale
     */
    closeModal(modal: HTMLElement): void {
        modal.setAttribute('aria-hidden', 'true');
        modal.removeAttribute('role');

        // Restaurer le focus précédent
        if (this.config.enableFocusManagement && this.focusStack.length > 0) {
            const previousFocus = this.focusStack.pop();
            if (previousFocus && document.contains(previousFocus)) {
                previousFocus.focus();
            }
        }

        // Supprimer le backdrop
        this.removeModalBackdrop();
    }

    /**
     * Ajoute un backdrop pour la modale
     */
    private addModalBackdrop(modal: HTMLElement): void {
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop';
        backdrop.style.position = 'fixed';
        backdrop.style.top = '0';
        backdrop.style.left = '0';
        backdrop.style.width = '100%';
        backdrop.style.height = '100%';
        backdrop.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        backdrop.style.zIndex = '999';
        backdrop.setAttribute('aria-hidden', 'true');

        backdrop.addEventListener('click', () => this.closeModal(modal));

        document.body.appendChild(backdrop);
    }

    /**
     * Supprime le backdrop de la modale
     */
    private removeModalBackdrop(): void {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    /**
     * Obtient tous les éléments focusables dans un conteneur
     */
    getFocusableElements(container: HTMLElement): HTMLElement[] {
        const focusableSelectors = [
            'button:not([disabled])',
            '[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable]'
        ].join(', ');

        const elements = container.querySelectorAll(focusableSelectors) as NodeListOf<HTMLElement>;
        return Array.from(elements).filter(el => {
            return !el.hidden &&
                el.offsetWidth > 0 &&
                el.offsetHeight > 0 &&
                window.getComputedStyle(el).visibility !== 'hidden';
        });
    }

    /**
     * Vérifie le contraste des couleurs
     */
    checkColorContrast(foreground: string, background: string): { ratio: number; passes: { aa: boolean; aaa: boolean } } {
        const getLuminance = (color: string): number => {
            // Conversion simplifiée - pour une implémentation complète, 
            // utiliser une bibliothèque comme chroma.js
            const rgb = this.hexToRgb(color);
            if (!rgb) return 0;

            const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
                c = c / 255;
                return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
            });

            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        };

        const l1 = getLuminance(foreground);
        const l2 = getLuminance(background);
        const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

        return {
            ratio,
            passes: {
                aa: ratio >= 4.5,
                aaa: ratio >= 7
            }
        };
    }

    /**
     * Convertit une couleur hex en RGB
     */
    private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    /**
     * Ajoute des propriétés ARIA à un élément
     */
    setAriaAttributes(element: HTMLElement, attributes: Record<string, string>): void {
        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key.startsWith('aria-') ? key : `aria-${key}`, value);
        });
    }

    /**
     * Génère un ID unique pour les éléments
     */
    generateId(prefix = 'a11y'): string {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Instance globale
export const a11y = new AccessibilityManager();

// Utilitaires d'accessibilité
export const a11yUtils = {
    /**
     * Vérifie si un élément est focusable
     */
    isFocusable: (element: HTMLElement): boolean => {
        return a11y.getFocusableElements(element.parentElement || document.body).includes(element);
    },

    /**
     * Crée un label invisible pour les lecteurs d'écran
     */
    createScreenReaderLabel: (text: string, id?: string): HTMLElement => {
        const label = document.createElement('span');
        if (id) label.id = id;
        label.textContent = text;
        label.className = 'sr-only';
        label.style.position = 'absolute';
        label.style.left = '-10000px';
        label.style.width = '1px';
        label.style.height = '1px';
        label.style.overflow = 'hidden';
        return label;
    },

    /**
     * Associe un label à un input
     */
    linkLabelToInput: (input: HTMLInputElement, labelText: string): void => {
        const labelId = a11y.generateId('label');
        const label = a11yUtils.createScreenReaderLabel(labelText, labelId);

        input.setAttribute('aria-labelledby', labelId);
        input.parentElement?.appendChild(label);
    },

    /**
     * Ajoute une description à un élément
     */
    addDescription: (element: HTMLElement, description: string): void => {
        const descId = a11y.generateId('desc');
        const descElement = a11yUtils.createScreenReaderLabel(description, descId);

        element.setAttribute('aria-describedby', descId);
        element.parentElement?.appendChild(descElement);
    },

    /**
     * Crée un bouton accessible
     */
    createAccessibleButton: (text: string, onClick?: () => void): HTMLButtonElement => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = text;
        button.setAttribute('aria-label', text);

        if (onClick) {
            button.addEventListener('click', onClick);
        }

        return button;
    },

    /**
     * Vérifie si les animations sont réduites
     */
    prefersReducedMotion: (): boolean => {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    /**
     * Vérifie le thème préféré
     */
    prefersColorScheme: (): 'light' | 'dark' => {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    /**
     * Ajoute un skip link
     */
    addSkipLink: (targetId: string, text = 'Aller au contenu principal'): void => {
        const skipLink = document.createElement('a');
        skipLink.href = `#${targetId}`;
        skipLink.textContent = text;
        skipLink.className = 'skip-link';
        skipLink.style.position = 'absolute';
        skipLink.style.top = '-40px';
        skipLink.style.left = '6px';
        skipLink.style.background = '#000';
        skipLink.style.color = '#fff';
        skipLink.style.padding = '8px';
        skipLink.style.textDecoration = 'none';
        skipLink.style.zIndex = '1000';

        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);
    },

    /**
     * Notifie un changement d'état
     */
    announceStateChange: (element: HTMLElement, newState: string): void => {
        element.setAttribute('aria-live', 'polite');
        a11y.announce(`État changé: ${newState}`);
    },

    /**
     * Crée une liste accessible
     */
    makeListAccessible: (list: HTMLElement, itemRole = 'listitem'): void => {
        list.setAttribute('role', 'list');
        const items = list.children;

        for (let i = 0; i < items.length; i++) {
            const item = items[i] as HTMLElement;
            item.setAttribute('role', itemRole);
            item.setAttribute('aria-setsize', items.length.toString());
            item.setAttribute('aria-posinset', (i + 1).toString());
        }
    },

    /**
     * Crée un group de boutons radio accessible
     */
    makeRadioGroupAccessible: (container: HTMLElement, groupLabel: string): void => {
        container.setAttribute('role', 'radiogroup');
        container.setAttribute('aria-labelledby', a11y.generateId('radio-label'));

        const label = a11yUtils.createScreenReaderLabel(groupLabel);
        container.appendChild(label);

        const radios = container.querySelectorAll('input[type="radio"]');
        radios.forEach((radio, index) => {
            radio.setAttribute('role', 'radio');
            if (index === 0) {
                radio.setAttribute('tabindex', '0');
            } else {
                radio.setAttribute('tabindex', '-1');
            }
        });
    }
};

// Configuration par défaut selon l'environnement
if (typeof window !== 'undefined') {
    // Ajouter les styles CSS de base pour l'accessibilité
    const style = document.createElement('style');
    style.textContent = `
		.sr-only {
			position: absolute !important;
			width: 1px !important;
			height: 1px !important;
			padding: 0 !important;
			margin: -1px !important;
			overflow: hidden !important;
			clip: rect(0, 0, 0, 0) !important;
			white-space: nowrap !important;
			border: 0 !important;
		}
		
		*:focus-visible {
			outline: 2px solid #4A90E2;
			outline-offset: 2px;
		}
		
		.skip-link:focus {
			position: absolute;
			top: 6px !important;
			left: 6px;
			background: #000;
			color: #fff;
			padding: 8px;
			text-decoration: none;
			z-index: 1000;
		}
	`;
    document.head.appendChild(style);
}
