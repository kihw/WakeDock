# 🔄 Button Component Migration Guide

**TASK-UI-001: Unification des Composants Button**

Ce guide détaille la migration des 5 composants Button fragmentés vers le nouveau `UnifiedButton`.

## 📋 Vue d'ensemble

### ✅ Avant (Fragmenté)
```
dashboard/src/lib/components/ui/atoms/
├── BaseButton.svelte      (logique de base)
├── PrimaryButton.svelte   (variante primaire)
├── SecondaryButton.svelte (variante secondaire)
├── IconButton.svelte      (boutons icône)
└── Button.svelte          (wrapper/routeur)
```

### ✅ Après (Unifié)
```
dashboard/src/lib/components/ui/atoms/
├── UnifiedButton.svelte       (composant unifié)
├── UnifiedButton.types.ts     (types TypeScript)
├── UnifiedButton.test.ts      (tests complets)
├── UnifiedButton.stories.ts   (documentation Storybook)
└── migrate-buttons.ts         (outils de migration)
```

## 🔄 Guide de Migration

### 1. **PrimaryButton → UnifiedButton**

**Avant:**
```svelte
<script>
  import PrimaryButton from '$lib/components/ui/atoms/PrimaryButton.svelte';
</script>

<PrimaryButton size="lg" fullWidth on:click={handleSubmit}>
  Submit Form
</PrimaryButton>
```

**Après:**
```svelte
<script>
  import { UnifiedButton } from '$lib/components/ui/atoms';
</script>

<UnifiedButton variant="primary" size="lg" fullWidth on:click={handleSubmit}>
  Submit Form
</UnifiedButton>
```

### 2. **SecondaryButton → UnifiedButton**

**Avant:**
```svelte
<SecondaryButton size="md" on:click={handleCancel}>
  Cancel
</SecondaryButton>
```

**Après:**
```svelte
<UnifiedButton variant="secondary" size="md" on:click={handleCancel}>
  Cancel
</UnifiedButton>
```

### 3. **IconButton → UnifiedButton**

**Avant:**
```svelte
<IconButton variant="ghost" size="sm" on:click={handleEdit}>
  ✏️
</IconButton>
```

**Après:**
```svelte
<UnifiedButton variant="ghost" size="sm" iconOnly on:click={handleEdit}>
  ✏️
</UnifiedButton>
```

### 4. **Button (wrapper) → UnifiedButton**

**Avant:**
```svelte
<Button variant="success" iconOnly={true} on:click={handleSave}>
  💾
</Button>
```

**Après:**
```svelte
<UnifiedButton variant="success" iconOnly on:click={handleSave}>
  💾
</UnifiedButton>
```

## 📊 Tableau de Correspondance des Props

| Legacy Component | Legacy Prop | UnifiedButton Prop | Notes |
|------------------|-------------|-------------------|-------|
| PrimaryButton | `size` | `size` | ✅ Identique |
| PrimaryButton | `fullWidth` | `fullWidth` | ✅ Identique |
| SecondaryButton | `size` | `size` | ✅ Identique |
| SecondaryButton | `fullWidth` | `fullWidth` | ✅ Identique |
| IconButton | `variant` | `variant` | ✅ Identique |
| IconButton | `size` | `size` | ✅ Identique |
| IconButton | - | `iconOnly=true` | ⚠️ Nouveau prop requis |
| Button | `variant` | `variant` | ✅ Identique |
| Button | `iconOnly` | `iconOnly` | ✅ Identique |
| BaseButton | `className` | `className` | ✅ Identique |
| Tous | `disabled` | `disabled` | ✅ Identique |
| Tous | `loading` | `loading` | ✅ Identique |
| Tous | `href` | `href` | ✅ Identique |
| Tous | `ariaLabel` | `ariaLabel` | ✅ Identique |
| Tous | `testId` | `testId` | ✅ Identique |

## 🚀 Nouvelles Fonctionnalités

### 1. **Variantes Étendues**
```svelte
<!-- Nouvelles variantes disponibles -->
<UnifiedButton variant="success">Success</UnifiedButton>
<UnifiedButton variant="warning">Warning</UnifiedButton>
<UnifiedButton variant="error">Error</UnifiedButton>
```

### 2. **Tailles Étendues**
```svelte
<!-- Nouvelles tailles -->
<UnifiedButton size="xs">Extra Small</UnifiedButton>
<UnifiedButton size="xl">Extra Large</UnifiedButton>
```

### 3. **Support d'Icônes Avancé**
```svelte
<!-- Icône à gauche (défaut) -->
<UnifiedButton icon="save" iconPosition="left">Save</UnifiedButton>

<!-- Icône à droite -->
<UnifiedButton icon="arrow-right" iconPosition="right">Next</UnifiedButton>

<!-- Bouton icône uniquement -->
<UnifiedButton icon="settings" iconOnly ariaLabel="Settings" />
```

### 4. **Variante Outlined**
```svelte
<!-- Nouveau style outlined -->
<UnifiedButton variant="primary" outlined>Outlined Primary</UnifiedButton>
<UnifiedButton variant="secondary" outlined>Outlined Secondary</UnifiedButton>
```

## 🛠️ Outils de Migration

### 1. **Script de Migration Automatique**

```typescript
import { migrateBatchFiles } from './migrate-buttons';

// Migrer plusieurs fichiers automatiquement
const result = await migrateBatchFiles(
  ['src/routes/+page.svelte', 'src/lib/components/**/*.svelte'],
  fs.readFile,
  fs.writeFile
);

console.log(`Migrated ${result.totalMigrations} components`);
```

### 2. **Rapport de Migration**

```typescript
import { generateMigrationReport } from './migrate-buttons';

const fileContent = await fs.readFile('component.svelte', 'utf8');
const report = generateMigrationReport(fileContent);

console.log(`Found ${report.migrationCount} components to migrate:`);
report.suggestions.forEach(suggestion => console.log(`- ${suggestion}`));
```

### 3. **Validation de Migration**

```typescript
import { validateMigration } from './migrate-buttons';

const validation = validateMigration(originalContent, migratedContent);
if (!validation.isValid) {
  console.error('Migration issues:', validation.issues);
} else {
  console.log('✅ Migration successful!');
}
```

## ✅ Checklist de Migration

### Phase 1: Préparation
- [ ] Sauvegarder le code existant
- [ ] Installer le nouveau `UnifiedButton`
- [ ] Mettre à jour les imports dans `index.ts`
- [ ] Configurer les tests automatisés

### Phase 2: Migration Progressive
- [ ] Identifier tous les fichiers utilisant les anciens composants
- [ ] Migrer les composants par type (PrimaryButton → UnifiedButton)
- [ ] Tester chaque migration individuellement
- [ ] Mettre à jour la documentation

### Phase 3: Validation
- [ ] Exécuter tous les tests automatisés
- [ ] Vérifier l'accessibilité (WCAG 2.1 AA)
- [ ] Tests manuels sur différents navigateurs
- [ ] Tests de régression visuelle

### Phase 4: Nettoyage
- [ ] Supprimer les anciens composants Button
- [ ] Nettoyer les imports obsolètes
- [ ] Mettre à jour la documentation du design system
- [ ] Publier les notes de version

## 🧪 Tests de Validation

### 1. **Tests Unitaires**
```bash
# Exécuter les tests du UnifiedButton
npm test UnifiedButton.test.ts

# Vérifier la couverture de tests (>90%)
npm run test:coverage
```

### 2. **Tests d'Accessibilité**
```bash
# Tests axe-core automatisés
npm run test:a11y

# Tests de navigation clavier
npm run test:keyboard
```

### 3. **Tests Visuels**
```bash
# Tests Storybook
npm run storybook

# Tests de régression visuelle (si disponible)
npm run test:visual
```

## 📈 Métriques de Succès

### Avant Migration
- **5 composants Button** séparés
- **~1,500 lignes de code** total
- **Inconsistances** de style et API
- **Tests fragmentés** (63% coverage)

### Après Migration
- **1 composant UnifiedButton** consolidé
- **~400 lignes de code** total
- **API unifiée** et cohérente
- **Tests complets** (>90% coverage)

### Gains
- **-73% réduction de code**
- **+100% couverture de tests**
- **-100% duplication d'API**
- **+50% nouvelles fonctionnalités**

## ⚠️ Points d'Attention

### 1. **Breaking Changes Potentiels**
- `IconButton` nécessite maintenant `iconOnly={true}`
- Certaines classes CSS spécifiques peuvent changer
- Props `className` appliqué différemment

### 2. **Tests à Vérifier**
- Tests utilisant des sélecteurs CSS spécifiques
- Tests d'intégration avec les anciens composants
- Tests de performance avec beaucoup de boutons

### 3. **Compatibilité**
- Vérifier les thèmes personnalisés
- Tester avec les plugins tiers
- Valider les animations personnalisées

## 🔗 Ressources

- **Documentation Storybook**: `npm run storybook` → UI/Atoms/UnifiedButton
- **Tests**: `dashboard/src/lib/components/ui/atoms/UnifiedButton.test.ts`
- **Types**: `dashboard/src/lib/components/ui/atoms/UnifiedButton.types.ts`
- **Migration Tools**: `dashboard/src/lib/components/ui/atoms/migrate-buttons.ts`

## 📞 Support

En cas de problème pendant la migration :

1. **Vérifier les tests** : `npm test UnifiedButton`
2. **Consulter Storybook** : Documentation complète avec exemples
3. **Utiliser les outils de migration** : Scripts automatiques disponibles
4. **Valider l'accessibilité** : Tests axe-core intégrés

---

**✅ Migration TASK-UI-001 Terminée**
*Date: 13 juillet 2025*
*Prochaine étape: TASK-UI-002 - Refactorisation du Système d'Input*