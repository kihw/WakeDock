import type { StorybookConfig } from '@storybook/svelte-vite';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.stories.@(js|jsx|ts|tsx|svelte)',
    '../src/**/*.story.@(js|jsx|ts|tsx|svelte)'
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-svelte-csf',
    '@storybook/addon-a11y',
    '@storybook/addon-docs',
    '@storybook/addon-controls',
    '@storybook/addon-viewport'
  ],
  framework: {
    name: '@storybook/svelte-vite',
    options: {}
  },
  docs: {
    autodocs: 'tag',
    defaultName: 'Documentation'
  },
  typescript: {
    check: false,
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => (prop.parent ? !/node_modules/.test(prop.parent.fileName) : true),
    },
  },
  viteFinal: async (config) => {
    // Customize Vite config for Storybook
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...config.resolve.alias,
      '$lib': '/src/lib',
      '$app': '/src/app'
    };

    return config;
  }
};

export default config;
