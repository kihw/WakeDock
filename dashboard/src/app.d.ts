// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        interface Locals {
            user: import('./lib/types/user').User | null;
            isAuthenticated: boolean;
            errorContext?: {
                request: any;
                userAgent?: string;
                timestamp: string;
                userId?: number;
            };
        }
        // interface PageData {}
        // interface PageState {}
        // interface Platform {}
    }
}

export { };
