/**
 * Input Component Stories - WakeDock Design System
 * Documentation des composants de saisie
 */

export const inputStories = {
  title: 'Design System/Atoms/Input',
  component: 'Input',

  stories: [
    {
      name: 'Default',
      description: 'Input par défaut',
      template: '<Input placeholder="Entrez votre texte..." />'
    },

    {
      name: 'Variants',
      description: 'Types d\'inputs disponibles',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
          <Input type="text" placeholder="Texte" />
          <Input type="email" placeholder="Email" />
          <Input type="password" placeholder="Mot de passe" />
          <Input type="number" placeholder="Nombre" />
          <Input type="search" placeholder="Recherche" />
        </div>
      `
    },

    {
      name: 'States',
      description: 'États de l\'input',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
          <Input placeholder="Normal" />
          <Input placeholder="Disabled" disabled />
          <Input placeholder="Error" error />
          <Input placeholder="Success" success />
          <Input placeholder="Required" required />
        </div>
      `
    },

    {
      name: 'With Labels',
      description: 'Inputs avec labels',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
          <div>
            <label for="name">Nom complet</label>
            <Input id="name" placeholder="John Doe" />
          </div>
          
          <div>
            <label for="email">Email *</label>
            <Input id="email" type="email" placeholder="john@example.com" required />
          </div>
          
          <div>
            <label for="phone">Téléphone</label>
            <Input id="phone" type="tel" placeholder="+33 1 23 45 67 89" />
            <small>Format: +33 X XX XX XX XX</small>
          </div>
        </div>
      `
    },

    {
      name: 'Accessibility',
      description: 'Fonctionnalités d\'accessibilité',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 400px;">
          <h3>Navigation clavier</h3>
          <div>
            <Input placeholder="Tab order 1" />
            <Input placeholder="Tab order 2" />
            <Input placeholder="Tab order 3" />
          </div>
          
          <h3>ARIA Labels</h3>
          <Input aria-label="Nom d'utilisateur" placeholder="Username" />
          <Input aria-describedby="pwd-help" type="password" placeholder="Password" />
          <small id="pwd-help">Minimum 8 caractères avec majuscules et chiffres</small>
          
          <h3>États pour lecteurs d'écran</h3>
          <Input aria-invalid="true" placeholder="Input avec erreur" />
          <Input aria-required="true" placeholder="Champ obligatoire" />
        </div>
      `
    }
  ],

  documentation: {
    description: `
# Input Component - WakeDock Design System

Composant de saisie polyvalent et accessible.

## Caractéristiques

- **Types**: Text, Email, Password, Number, Search, Tel, URL
- **States**: Normal, Disabled, Error, Success, Loading
- **Accessibility**: Support ARIA complet, navigation clavier
- **Validation**: Intégration avec validateurs de formulaire
- **Responsive**: Adaptation mobile/desktop

## Usage

\`\`\`svelte
<Input type="email" placeholder="votre@email.com" required />
<Input type="password" bind:value={password} />
<Input type="search" on:input={handleSearch} />
\`\`\`

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| type | string | 'text' | Type d'input HTML |
| placeholder | string | '' | Texte d'aide |
| disabled | boolean | false | Désactivé |
| required | boolean | false | Requis |
| error | boolean | false | État d'erreur |
| success | boolean | false | État de succès |

## Accessibility

- Labels appropriés (for/id ou aria-label)
- Navigation clavier complète
- États ARIA (invalid, required, describedby)
- Contraste conforme WCAG 2.1 AA
- Messages d'erreur accessibles
    `
  }
};

export default inputStories;
