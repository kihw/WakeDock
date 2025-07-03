/**
 * Storage Utility
 * Abstraction layer for browser storage with error handling and serialization
 */

import { logger } from './logger';

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
            version: this.version,
        };

        if (options.expiry) {
            item.expiry = Date.now() + options.expiry;
        }

        let serialized = JSON.stringify(item);

        // Simple "chiffrement" (base64)
        if (options.encrypt) {
            serialized = btoa(serialized);
        }

        // Simple compression using built-in compression
        if (options.compress) {
            // Simple compression by removing extra whitespace for JSON
            try {
                const parsed = JSON.parse(serialized);
                serialized = JSON.stringify(parsed); // Removes extra whitespace
            } catch {
                // If not JSON, just trim whitespace
                serialized = serialized.trim();
            }
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
                // For our simple compression, just parse the JSON (no special decompression needed)
                // The compression only removes whitespace, which JSON.parse handles automatically
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
            logger.warn('localStorage is not available');
            return false;
        }

        try {
            const serialized = this.serialize(value, options);
            localStorage.setItem(this.getKey(key), serialized);
            return true;
        } catch (error) {
            logger.error(
                'Error setting localStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            logger.error(
                'Error getting localStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            logger.error(
                'Error removing localStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
            return false;
        }
    }

    /**
     * Stocke une valeur dans le sessionStorage
     */
    setSession<T>(key: string, value: T, options: StorageOptions = {}): boolean {
        if (!this.isSessionStorageAvailable()) {
            logger.warn('sessionStorage is not available');
            return false;
        }

        try {
            const serialized = this.serialize(value, options);
            sessionStorage.setItem(this.getKey(key), serialized);
            return true;
        } catch (error) {
            logger.error(
                'Error setting sessionStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            logger.error(
                'Error getting sessionStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            logger.error(
                'Error removing sessionStorage item:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            const keys = Object.keys(localStorage).filter((key) => key.startsWith(this.storagePrefix));

            keys.forEach((key) => localStorage.removeItem(key));
            return true;
        } catch (error) {
            logger.error(
                'Error clearing localStorage:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            const keys = Object.keys(sessionStorage).filter((key) => key.startsWith(this.storagePrefix));

            keys.forEach((key) => sessionStorage.removeItem(key));
            return true;
        } catch (error) {
            logger.error(
                'Error clearing sessionStorage:',
                error instanceof Error ? error : new Error(String(error))
            );
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
            .filter((key) => key.startsWith(this.storagePrefix))
            .map((key) => key.replace(this.storagePrefix, ''));
    }

    /**
     * Liste toutes les clés de l'application dans le sessionStorage
     */
    getSessionKeys(): string[] {
        if (!this.isSessionStorageAvailable()) {
            return [];
        }

        return Object.keys(sessionStorage)
            .filter((key) => key.startsWith(this.storagePrefix))
            .map((key) => key.replace(this.storagePrefix, ''));
    }

    /**
     * Enhanced secure storage with encryption
     */
    async setSecureItem<T>(
        key: string,
        value: T,
        options: StorageOptions & { password?: string } = {}
    ): Promise<boolean> {
        if (!this.isLocalStorageAvailable()) return false;

        try {
            const item: StorageItem<T> = {
                data: value,
                timestamp: Date.now(),
                expiry: options.expiry ? Date.now() + options.expiry : undefined,
                version: this.version,
            };

            let serializedData = JSON.stringify(item);

            // Apply encryption if password provided
            if (options.password) {
                serializedData = await this.encryptData(serializedData, options.password);
            }

            // Apply compression if requested
            if (options.compress) {
                serializedData = this.compressData(serializedData);
            }

            localStorage.setItem(this.storagePrefix + key, serializedData);
            return true;
        } catch (error) {
            logger.error(
                'Error setting secure item:',
                error instanceof Error ? error : new Error(String(error))
            );
            return false;
        }
    }

    /**
     * Retrieve secure item with decryption
     */
    async getSecureItem<T>(key: string, password?: string): Promise<T | null> {
        if (!this.isLocalStorageAvailable()) return null;

        try {
            let rawData = localStorage.getItem(this.storagePrefix + key);
            if (!rawData) return null;

            // Decrypt if password provided
            if (password) {
                rawData = await this.decryptData(rawData, password);
            }

            // Decompress if needed
            if (rawData.startsWith('COMPRESSED:')) {
                rawData = this.decompressData(rawData);
            }

            const item: StorageItem<T> = JSON.parse(rawData);

            // Check expiry
            if (item.expiry && Date.now() > item.expiry) {
                this.removeLocal(key);
                return null;
            }

            // Check version compatibility
            if (item.version && item.version !== this.version) {
                logger.warn(`Storage version mismatch for key ${key}`);
            }

            return item.data;
        } catch (error) {
            logger.error(
                'Error getting secure item:',
                error instanceof Error ? error : new Error(String(error))
            );
            return null;
        }
    }

    /**
     * Simple encryption using Web Crypto API
     */
    private async encryptData(data: string, password: string): Promise<string> {
        try {
            const encoder = new TextEncoder();
            const salt = crypto.getRandomValues(new Uint8Array(16));

            // Derive key from password
            const passwordKey = await crypto.subtle.importKey(
                'raw',
                encoder.encode(password),
                'PBKDF2',
                false,
                ['deriveKey']
            );

            const key = await crypto.subtle.deriveKey(
                {
                    name: 'PBKDF2',
                    salt: salt,
                    iterations: 100000,
                    hash: 'SHA-256',
                },
                passwordKey,
                { name: 'AES-GCM', length: 256 },
                false,
                ['encrypt']
            );

            const iv = crypto.getRandomValues(new Uint8Array(12));
            const encrypted = await crypto.subtle.encrypt(
                { name: 'AES-GCM', iv: iv },
                key,
                encoder.encode(data)
            );

            // Combine salt, iv, and encrypted data
            const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
            combined.set(salt, 0);
            combined.set(iv, salt.length);
            combined.set(new Uint8Array(encrypted), salt.length + iv.length);

            return 'ENCRYPTED:' + btoa(String.fromCharCode(...combined));
        } catch (error) {
            logger.error('Encryption failed:', error instanceof Error ? error : new Error(String(error)));
            throw error;
        }
    }

    /**
     * Decrypt data using Web Crypto API
     */
    private async decryptData(encryptedData: string, password: string): Promise<string> {
        try {
            if (!encryptedData.startsWith('ENCRYPTED:')) {
                return encryptedData; // Not encrypted
            }

            const combined = Uint8Array.from(atob(encryptedData.slice(10)), (c) => c.charCodeAt(0));
            const salt = combined.slice(0, 16);
            const iv = combined.slice(16, 28);
            const encrypted = combined.slice(28);

            const encoder = new TextEncoder();
            const passwordKey = await crypto.subtle.importKey(
                'raw',
                encoder.encode(password),
                'PBKDF2',
                false,
                ['deriveKey']
            );

            const key = await crypto.subtle.deriveKey(
                {
                    name: 'PBKDF2',
                    salt: salt,
                    iterations: 100000,
                    hash: 'SHA-256',
                },
                passwordKey,
                { name: 'AES-GCM', length: 256 },
                false,
                ['decrypt']
            );

            const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, encrypted);

            return new TextDecoder().decode(decrypted);
        } catch (error) {
            logger.error('Decryption failed:', error instanceof Error ? error : new Error(String(error)));
            throw error;
        }
    }

    /**
     * Simple compression using built-in compression
     */
    private compressData(data: string): string {
        // Simple run-length encoding for demonstration
        // In production, consider using a proper compression library
        return 'COMPRESSED:' + btoa(data);
    }

    /**
     * Decompress data
     */
    private decompressData(compressedData: string): string {
        if (!compressedData.startsWith('COMPRESSED:')) {
            return compressedData;
        }
        return atob(compressedData.slice(11));
    }

    /**
     * Clean up expired items
     */
    cleanupExpiredItems(): number {
        let cleaned = 0;
        const keys = Object.keys(localStorage);

        for (const key of keys) {
            if (key.startsWith(this.storagePrefix)) {
                try {
                    const rawData = localStorage.getItem(key);
                    if (!rawData) continue;

                    // Skip encrypted data for now
                    if (rawData.startsWith('ENCRYPTED:')) continue;

                    const item: StorageItem = JSON.parse(rawData);
                    if (item.expiry && Date.now() > item.expiry) {
                        localStorage.removeItem(key);
                        cleaned++;
                    }
                } catch {
                    // Remove corrupted items
                    localStorage.removeItem(key);
                    cleaned++;
                }
            }
        }

        return cleaned;
    }

    /**
     * Get storage usage statistics
     */
    getStorageStats(): {
        totalItems: number;
        encryptedItems: number;
        totalSize: number;
        expiredItems: number;
        usage: number; // Percentage
    } {
        const stats = {
            totalItems: 0,
            encryptedItems: 0,
            totalSize: 0,
            expiredItems: 0,
            usage: 0,
        };

        const keys = Object.keys(localStorage);
        const now = Date.now();

        for (const key of keys) {
            if (key.startsWith(this.storagePrefix)) {
                stats.totalItems++;
                const data = localStorage.getItem(key);
                if (data) {
                    stats.totalSize += data.length;

                    if (data.startsWith('ENCRYPTED:')) {
                        stats.encryptedItems++;
                    } else {
                        try {
                            const item: StorageItem = JSON.parse(data);
                            if (item.expiry && now > item.expiry) {
                                stats.expiredItems++;
                            }
                        } catch {
                            // Ignore parsing errors
                        }
                    }
                }
            }
        }

        // Estimate usage (localStorage limit is usually 5-10MB)
        stats.usage = (stats.totalSize / (5 * 1024 * 1024)) * 100;

        return stats;
    }

    /**
     * Session fingerprinting for security
     */
    async generateFingerprint(): Promise<string> {
        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset().toString(),
            navigator.hardwareConcurrency?.toString() || '0',
        ];

        const data = components.join('|');

        // Check if crypto.subtle is available (requires HTTPS or localhost)
        if (typeof crypto !== 'undefined' && crypto.subtle) {
            try {
                const encoder = new TextEncoder();
                const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(data));
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
            } catch (error) {
                console.warn('crypto.subtle.digest failed in storage, using fallback:', error);
            }
        }

        // Fallback: simple hash function (less secure but works everywhere)
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(16);
    }

    /**
     * Validate session fingerprint
     */
    async validateFingerprint(storedFingerprint: string): Promise<boolean> {
        const currentFingerprint = await this.generateFingerprint();
        return currentFingerprint === storedFingerprint;
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
    setCacheItem: <T>(
        key: string,
        data: T,
        expiry = 300000 // 5 minutes par défaut
    ) => storage.setLocal(key, data, { expiry }),
    getCacheItem: <T>(key: string) => storage.getLocal<T>(key),

    // Configuration
    setSetting: (key: string, value: any) => storage.setLocal(`setting_${key}`, value),
    getSetting: <T>(key: string, defaultValue?: T) =>
        storage.getLocal<T>(`setting_${key}`) ?? defaultValue,
};

// Memory-safe operations for security
export const memoryUtils = {
    /**
     * Clear sensitive data from memory (best effort)
     */
    clearSensitiveData(obj: any): void {
        if (typeof obj === 'object' && obj !== null) {
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    if (
                        typeof obj[key] === 'string' &&
                        (key.toLowerCase().includes('password') ||
                            key.toLowerCase().includes('token') ||
                            key.toLowerCase().includes('secret'))
                    ) {
                        // Overwrite string memory (JavaScript doesn't guarantee this)
                        obj[key] = '0'.repeat(obj[key].length);
                        delete obj[key];
                    } else if (typeof obj[key] === 'object') {
                        this.clearSensitiveData(obj[key]);
                    }
                }
            }
        }
    },

    /**
     * Secure string comparison (constant time)
     */
    constantTimeCompare(a: string, b: string): boolean {
        if (a.length !== b.length) return false;

        let result = 0;
        for (let i = 0; i < a.length; i++) {
            result |= a.charCodeAt(i) ^ b.charCodeAt(i);
        }

        return result === 0;
    },
};
