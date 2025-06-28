/**
 * Storage Utility
 * Abstraction layer for browser storage with error handling and serialization
 */

export interface StorageOptions {
    expiry?: number; // Expiration en millisecondes
    encrypt?: boolean; // Chiffrement des données (simple)
    compress?: boolean; // Compression des données
}

export interface StorageItem<T = any> {
    data: T;
    timestamp: number;
    expiry?: number;
    version?: string;
}

class StorageManager {
    private readonly storagePrefix = 'wakedock_';
    private readonly version = '1.0.0';

    /**
     * Vérifie si le localStorage est disponible
     */
    private isLocalStorageAvailable(): boolean {
        try {
            const test = '__localStorage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Vérifie si le sessionStorage est disponible
     */
    private isSessionStorageAvailable(): boolean {
        try {
            const test = '__sessionStorage_test__';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Génère une clé avec préfixe
     */
    private getKey(key: string): string {
        return `${this.storagePrefix}${key}`;
    }

    /**
     * Sérialise les données
     */
    private serialize<T>(data: T, options: StorageOptions = {}): string {
        const item: StorageItem<T> = {
            data,
            timestamp: Date.now(),
            version: this.version
        };

        if (options.expiry) {
            item.expiry = Date.now() + options.expiry;
        }

        let serialized = JSON.stringify(item);

        // Simple "chiffrement" (base64)
        if (options.encrypt) {
            serialized = btoa(serialized);
        }

        // Simple compression (non implémentée, placeholder)
        if (options.compress) {
            // TODO: Implémenter une vraie compression
            serialized = serialized;
        }

        return serialized;
    }

    /**
     * Désérialise les données
     */
    private deserialize<T>(serialized: string, options: StorageOptions = {}): T | null {
        try {
            let data = serialized;

            // Déchiffrement
            if (options.encrypt) {
                data = atob(data);
            }

            // Décompression
            if (options.compress) {
                // TODO: Implémenter une vraie décompression
                data = data;
            }

            const item: StorageItem<T> = JSON.parse(data);

            // Vérifier l'expiration
            if (item.expiry && Date.now() > item.expiry) {
                return null;
            }

            return item.data;
        } catch {
            return null;
        }
    }

    /**
     * Stocke une valeur dans le localStorage
     */
    setLocal<T>(key: string, value: T, options: StorageOptions = {}): boolean {
        if (!this.isLocalStorageAvailable()) {
            console.warn('localStorage is not available');
            return false;
        }

        try {
            const serialized = this.serialize(value, options);
            localStorage.setItem(this.getKey(key), serialized);
            return true;
        } catch (error) {
            console.error('Error setting localStorage item:', error);
            return false;
        }
    }

    /**
     * Récupère une valeur du localStorage
     */
    getLocal<T>(key: string, options: StorageOptions = {}): T | null {
        if (!this.isLocalStorageAvailable()) {
            return null;
        }

        try {
            const serialized = localStorage.getItem(this.getKey(key));
            if (!serialized) return null;

            const data = this.deserialize<T>(serialized, options);

            // Si les données ont expiré, les supprimer
            if (data === null) {
                this.removeLocal(key);
            }

            return data;
        } catch (error) {
            console.error('Error getting localStorage item:', error);
            return null;
        }
    }

    /**
     * Supprime une valeur du localStorage
     */
    removeLocal(key: string): boolean {
        if (!this.isLocalStorageAvailable()) {
            return false;
        }

        try {
            localStorage.removeItem(this.getKey(key));
            return true;
        } catch (error) {
            console.error('Error removing localStorage item:', error);
            return false;
        }
    }

    /**
     * Stocke une valeur dans le sessionStorage
     */
    setSession<T>(key: string, value: T, options: StorageOptions = {}): boolean {
        if (!this.isSessionStorageAvailable()) {
            console.warn('sessionStorage is not available');
            return false;
        }

        try {
            const serialized = this.serialize(value, options);
            sessionStorage.setItem(this.getKey(key), serialized);
            return true;
        } catch (error) {
            console.error('Error setting sessionStorage item:', error);
            return false;
        }
    }

    /**
     * Récupère une valeur du sessionStorage
     */
    getSession<T>(key: string, options: StorageOptions = {}): T | null {
        if (!this.isSessionStorageAvailable()) {
            return null;
        }

        try {
            const serialized = sessionStorage.getItem(this.getKey(key));
            if (!serialized) return null;

            const data = this.deserialize<T>(serialized, options);

            // Si les données ont expiré, les supprimer
            if (data === null) {
                this.removeSession(key);
            }

            return data;
        } catch (error) {
            console.error('Error getting sessionStorage item:', error);
            return null;
        }
    }

    /**
     * Supprime une valeur du sessionStorage
     */
    removeSession(key: string): boolean {
        if (!this.isSessionStorageAvailable()) {
            return false;
        }

        try {
            sessionStorage.removeItem(this.getKey(key));
            return true;
        } catch (error) {
            console.error('Error removing sessionStorage item:', error);
            return false;
        }
    }

    /**
     * Vide tout le localStorage de l'application
     */
    clearLocal(): boolean {
        if (!this.isLocalStorageAvailable()) {
            return false;
        }

        try {
            const keys = Object.keys(localStorage).filter(key =>
                key.startsWith(this.storagePrefix)
            );

            keys.forEach(key => localStorage.removeItem(key));
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }

    /**
     * Vide tout le sessionStorage de l'application
     */
    clearSession(): boolean {
        if (!this.isSessionStorageAvailable()) {
            return false;
        }

        try {
            const keys = Object.keys(sessionStorage).filter(key =>
                key.startsWith(this.storagePrefix)
            );

            keys.forEach(key => sessionStorage.removeItem(key));
            return true;
        } catch (error) {
            console.error('Error clearing sessionStorage:', error);
            return false;
        }
    }

    /**
     * Obtient la taille utilisée du localStorage
     */
    getLocalStorageSize(): number {
        if (!this.isLocalStorageAvailable()) {
            return 0;
        }

        let size = 0;
        for (const key in localStorage) {
            if (key.startsWith(this.storagePrefix)) {
                size += localStorage[key].length + key.length;
            }
        }
        return size;
    }

    /**
     * Vérifie si une clé existe dans le localStorage
     */
    hasLocal(key: string): boolean {
        if (!this.isLocalStorageAvailable()) {
            return false;
        }

        return localStorage.getItem(this.getKey(key)) !== null;
    }

    /**
     * Vérifie si une clé existe dans le sessionStorage
     */
    hasSession(key: string): boolean {
        if (!this.isSessionStorageAvailable()) {
            return false;
        }

        return sessionStorage.getItem(this.getKey(key)) !== null;
    }

    /**
     * Liste toutes les clés de l'application dans le localStorage
     */
    getLocalKeys(): string[] {
        if (!this.isLocalStorageAvailable()) {
            return [];
        }

        return Object.keys(localStorage)
            .filter(key => key.startsWith(this.storagePrefix))
            .map(key => key.replace(this.storagePrefix, ''));
    }

    /**
     * Liste toutes les clés de l'application dans le sessionStorage
     */
    getSessionKeys(): string[] {
        if (!this.isSessionStorageAvailable()) {
            return [];
        }

        return Object.keys(sessionStorage)
            .filter(key => key.startsWith(this.storagePrefix))
            .map(key => key.replace(this.storagePrefix, ''));
    }
}

// Instance singleton
export const storage = new StorageManager();

// Raccourcis pour des utilisations courantes
export const storageHelpers = {
    // Authentification
    setAuthToken: (token: string) => storage.setLocal('auth_token', token),
    getAuthToken: () => storage.getLocal<string>('auth_token'),
    removeAuthToken: () => storage.removeLocal('auth_token'),

    // Utilisateur
    setUser: (user: any) => storage.setLocal('user', user),
    getUser: () => storage.getLocal('user'),
    removeUser: () => storage.removeLocal('user'),

    // Préférences UI
    setTheme: (theme: string) => storage.setLocal('theme', theme),
    getTheme: () => storage.getLocal<string>('theme') || 'light',

    // Cache temporaire
    setCacheItem: <T>(key: string, data: T, expiry = 300000) => // 5 minutes par défaut
        storage.setLocal(key, data, { expiry }),
    getCacheItem: <T>(key: string) => storage.getLocal<T>(key),

    // Configuration
    setSetting: (key: string, value: any) => storage.setLocal(`setting_${key}`, value),
    getSetting: <T>(key: string, defaultValue?: T) =>
        storage.getLocal<T>(`setting_${key}`) ?? defaultValue
};

// Types déjà exportés au-dessus, pas besoin de les ré-exporter
