import eslint from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import parser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import prettier from 'eslint-config-prettier';

export default [
    eslint.configs.recommended,
    {
        files: ['**/*.{js,ts,svelte}'],
        languageOptions: {
            parser: parser,
            parserOptions: {
                ecmaVersion: 2020,
                sourceType: 'module',
                extraFileExtensions: ['.svelte']
            },
            globals: {
                browser: true,
                es2017: true,
                node: true
            }
        },
        plugins: {
            '@typescript-eslint': typescript
        },
        rules: {
            ...typescript.configs.recommended.rules,
            // Custom rules
            '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/prefer-const': 'error',
            'no-console': 'warn'
        }
    },
    {
        files: ['**/*.svelte'],
        languageOptions: {
            parser: svelte.parser,
            parserOptions: {
                parser: parser
            }
        },
        plugins: {
            svelte
        },
        rules: {
            ...svelte.configs.recommended.rules,
            // Svelte-specific rules
            'svelte/no-at-html-tags': 'error',
            'svelte/no-unused-svelte-ignore': 'error'
        }
    },
    prettier
];
