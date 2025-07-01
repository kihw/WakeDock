# 🛠️ Scripts d'Optimisation WakeDock Dashboard

Ce dossier contient des scripts utilitaires pour optimiser le développement et la production du Dashboard WakeDock.

## 📋 Scripts Disponibles

### 🖼️ optimize-images.js

Script d'optimisation automatique des images pour le projet.

**Fonctionnalités:**
- Conversion automatique des images en format WebP pour une meilleure performance
- Optimisation des images existantes (PNG, JPG, JPEG, GIF)
- Recherche récursive dans les dossiers `static/` et `src/`
- Génération d'alternatives WebP tout en conservant les originaux

**Utilisation:**
```bash
npm run optimize:images
```

**Dépendances:**
- Nécessite la bibliothèque `sharp` (installée automatiquement si manquante)

**Conseils d'utilisation:**
- Exécuter ce script avant chaque build de production
- Les images WebP sont supportées par 95%+ des navigateurs modernes
- Pour les navigateurs plus anciens, utiliser l'élément `<picture>` avec fallback

## 🔄 Intégration avec Husky

Ces scripts peuvent être intégrés dans le workflow Git via Husky:

```json
// Exemple dans .husky/pre-commit
"scripts": {
  "npm run optimize:images"
}
```

## 🚀 Ajout de Nouveaux Scripts

Pour ajouter de nouveaux scripts:

1. Créer un fichier JavaScript/TypeScript dans ce dossier
2. Ajouter une entrée correspondante dans `package.json` sous `scripts`
3. Documenter le script dans ce README

## 📊 Bonnes Pratiques

- Tous les scripts doivent inclure une gestion d'erreurs appropriée
- Documenter clairement les options et paramètres
- Inclure des messages de progression/statut
- Prévoir une option pour l'exécution silencieuse (`--quiet`)
