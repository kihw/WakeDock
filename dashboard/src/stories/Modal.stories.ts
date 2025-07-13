/**
 * Modal Component Stories - WakeDock Design System
 * Documentation des composants de modale
 */

export const modalStories = {
  title: 'Design System/Organisms/Modal',
  component: 'Modal',

  stories: [
    {
      name: 'Default',
      description: 'Modale par défaut',
      template: `
        <Modal open={true}>
          <h2 slot="title">Titre de la modale</h2>
          <p>Contenu de la modale avec du texte explicatif.</p>
          <div slot="actions">
            <Button variant="outline">Annuler</Button>
            <Button variant="primary">Confirmer</Button>
          </div>
        </Modal>
      `
    },

    {
      name: 'Sizes',
      description: 'Différentes tailles de modales',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <Button on:click={() => openModal('sm')}>Petite modale</Button>
          <Button on:click={() => openModal('md')}>Modale moyenne</Button>
          <Button on:click={() => openModal('lg')}>Grande modale</Button>
          <Button on:click={() => openModal('xl')}>Très grande modale</Button>
        </div>
      `
    },

    {
      name: 'Types',
      description: 'Types de modales spécialisées',
      template: `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <!-- Modale de confirmation -->
          <Modal type="confirm">
            <h2 slot="title">Confirmer la suppression</h2>
            <p>Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.</p>
            <div slot="actions">
              <Button variant="outline">Annuler</Button>
              <Button variant="danger">Supprimer</Button>
            </div>
          </Modal>
          
          <!-- Modale d'alerte -->
          <Modal type="alert">
            <h2 slot="title">⚠️ Attention</h2>
            <p>Une erreur s'est produite lors de l'opération. Veuillez réessayer.</p>
            <div slot="actions">
              <Button variant="primary">OK</Button>
            </div>
          </Modal>
          
          <!-- Modale de formulaire -->
          <Modal type="form" size="lg">
            <h2 slot="title">Ajouter un utilisateur</h2>
            <form style="display: flex; flex-direction: column; gap: 1rem;">
              <Input placeholder="Nom complet" required />
              <Input type="email" placeholder="Email" required />
              <Input type="password" placeholder="Mot de passe" required />
              <select>
                <option>Utilisateur</option>
                <option>Administrateur</option>
              </select>
            </form>
            <div slot="actions">
              <Button variant="outline">Annuler</Button>
              <Button variant="primary">Créer</Button>
            </div>
          </Modal>
        </div>
      `
    },

    {
      name: 'Accessibility',
      description: 'Fonctionnalités d\'accessibilité',
      template: `
        <Modal 
          open={true}
          aria-labelledby="modal-title"
          aria-describedby="modal-description"
        >
          <h2 id="modal-title" slot="title">Modale accessible</h2>
          <div id="modal-description">
            <p>Cette modale démontre les bonnes pratiques d'accessibilité :</p>
            <ul>
              <li>Focus automatique sur la modale</li>
              <li>Piégeage du focus (Tab cycling)</li>
              <li>Fermeture avec Escape</li>
              <li>ARIA labels appropriés</li>
              <li>Gestion du focus de retour</li>
            </ul>
          </div>
          <div slot="actions">
            <Button variant="outline" aria-label="Fermer sans sauvegarder">
              Annuler
            </Button>
            <Button variant="primary" aria-label="Sauvegarder et fermer">
              Valider
            </Button>
          </div>
        </Modal>
      `
    },

    {
      name: 'Complex Content',
      description: 'Modale avec contenu complexe',
      template: `
        <Modal size="xl">
          <h2 slot="title">Paramètres avancés</h2>
          
          <div style="display: flex; flex-direction: column; gap: 2rem;">
            <!-- Onglets dans la modale -->
            <div>
              <nav style="display: flex; gap: 1rem; border-bottom: 1px solid #eee;">
                <button class="tab active">Général</button>
                <button class="tab">Sécurité</button>
                <button class="tab">Notifications</button>
              </nav>
            </div>
            
            <!-- Contenu de l'onglet -->
            <div style="min-height: 300px;">
              <h3>Configuration générale</h3>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                  <label>Nom du service</label>
                  <Input value="wakedock-api" />
                </div>
                <div>
                  <label>Port</label>
                  <Input type="number" value="3000" />
                </div>
                <div>
                  <label>Environnement</label>
                  <select>
                    <option>Production</option>
                    <option>Staging</option>
                    <option>Development</option>
                  </select>
                </div>
                <div>
                  <label>SSL/TLS</label>
                  <input type="checkbox" checked /> Activé
                </div>
              </div>
            </div>
          </div>
          
          <div slot="actions">
            <Button variant="outline">Reset</Button>
            <Button variant="outline">Annuler</Button>
            <Button variant="primary">Sauvegarder</Button>
          </div>
        </Modal>
      `
    }
  ],

  documentation: {
    description: `
# Modal Component - WakeDock Design System

Composant de modale flexible et accessible pour les interactions utilisateur.

## Caractéristiques

- **Sizes**: Small (sm), Medium (md), Large (lg), Extra Large (xl)
- **Types**: Default, Confirm, Alert, Form
- **Accessibility**: Focus management, ARIA compliance, keyboard navigation
- **Responsive**: Adaptation mobile avec full-screen sur petits écrans
- **Customizable**: Slots pour title, content, et actions

## Usage

\`\`\`svelte
<Modal bind:open={showModal} size="md">
  <h2 slot="title">Titre</h2>
  <p>Contenu de la modale...</p>
  <div slot="actions">
    <Button on:click={() => showModal = false}>Fermer</Button>
  </div>
</Modal>
\`\`\`

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| open | boolean | false | État d'ouverture |
| size | string | 'md' | Taille de la modale |
| type | string | 'default' | Type spécialisé |
| closeOnEscape | boolean | true | Fermeture avec Escape |
| closeOnBackdrop | boolean | true | Fermeture clic backdrop |

## Slots

- **title**: Titre de la modale
- **default**: Contenu principal
- **actions**: Boutons d'action (footer)

## Accessibility

- Focus automatique et piégeage
- Navigation clavier (Tab, Escape)
- ARIA labels et roles appropriés
- Gestion du focus de retour
- Support des lecteurs d'écran

## Best Practices

- Toujours fournir un titre explicite
- Limiter le contenu pour éviter le scroll
- Actions claires (Annuler/Confirmer)
- Éviter les modales imbriquées
- Considérer les alternatives (drawer, popover)
    `
  }
};

export default modalStories;
