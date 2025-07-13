/**
 * Button Component Stories - WakeDock Design System
 * Documentation des composants boutons
 * 
 * Note: Ce fichier sera compatible avec Storybook une fois les dépendances installées
 */

// Configuration temporaire en attendant Storybook
export const buttonStories = {
  title: 'Design System/Atoms/Button',
  component: 'Button',

  stories: [
    {
      name: 'Default',
      description: 'Bouton par défaut',
      props: {
        variant: 'primary',
        size: 'md'
      },
      template: '<Button variant="primary" size="md">Default Button</Button>'
    },

    {
      name: 'Variants',
      description: 'Tous les variants disponibles',
      template: `
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
      `
    },

    {
      name: 'Sizes',
      description: 'Différentes tailles',
      template: `
        <div style="display: flex; gap: 1rem; align-items: center;">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      `
    },

    {
      name: 'States',
      description: 'États du bouton',
      template: `
        <div style="display: flex; gap: 1rem; align-items: center;">
          <Button>Normal</Button>
          <Button disabled>Disabled</Button>
          <Button loading>Loading</Button>
        </div>
      `
    },

    {
      name: 'Accessibility',
      description: 'Fonctionnalités d\'accessibilité',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <h3>Navigation clavier (Tab, Enter, Space)</h3>
          <div style="display: flex; gap: 0.5rem;">
            <Button>Tab 1</Button>
            <Button>Tab 2</Button>
            <Button>Tab 3</Button>
          </div>
          
          <h3>ARIA Labels pour lecteurs d'écran</h3>
          <Button aria-label="Fermer la modale">×</Button>
          
          <h3>États ARIA</h3>
          <div style="display: flex; gap: 0.5rem;">
            <Button aria-pressed="false">Toggle Off</Button>
            <Button aria-pressed="true">Toggle On</Button>
          </div>
        </div>
      `
    }
  ],

  documentation: {
    description: `
# Button Component - WakeDock Design System

Composant bouton polyvalent et accessible.

## Caractéristiques

- **Variants**: Primary, Secondary, Outline, Ghost, Danger  
- **Sizes**: Small (sm), Medium (md), Large (lg)
- **States**: Normal, Disabled, Loading
- **Accessibility**: Support ARIA complet, navigation clavier
- **Responsive**: Adaptation automatique mobile/desktop
- **Dark Mode**: Thème adaptatif

## Usage

\`\`\`svelte
<Button variant="primary" size="md">Click me</Button>
<Button variant="outline" disabled>Disabled</Button>  
<Button variant="danger" loading>Loading...</Button>
\`\`\`

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | string | 'primary' | Style variant |
| size | string | 'md' | Taille du bouton |
| disabled | boolean | false | Désactivé |
| loading | boolean | false | État de chargement |
| fullWidth | boolean | false | Largeur complète |

## Accessibility

- Navigation au clavier (Tab, Enter, Space)
- Support des lecteurs d'écran
- Contraste conforme WCAG 2.1 AA
- États ARIA appropriés (pressed, expanded, etc.)

## Design Tokens

Utilise les tokens de couleur et d'espacement du système de design WakeDock.
    `,

    examples: [
      '<!-- Bouton principal -->',
      '<Button variant="primary">Submit</Button>',
      '',
      '<!-- Bouton avec icône -->',
      '<Button variant="outline">',
      '  <Icon name="download" />',
      '  Download',
      '</Button>',
      '',
      '<!-- Bouton d\'action dangereuse -->',
      '<Button variant="danger" on:click={deleteItem}>',
      '  Delete Item',
      '</Button>'
    ].join('\n')
  }
};

// Export par défaut pour compatibilité future avec Storybook
export default buttonStories;
