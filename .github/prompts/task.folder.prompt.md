---
mode: agent
---
# Analyse complète de projet et génération du plan de finalisation

## Instructions

1. **Analyse uniquement le contexte fourni** via le chat copilot (structure de fichiers et code partagé)
2. **Examine le contenu partagé** pour identifier toutes les tâches restantes
3. **Recherche spécifiquement les références au dossier "données"** dans le contexte fourni
4. **Génère un fichier `{NomDuDossier}.todo.md`** basé sur l'analyse du contexte

## Objectif

Déterminer toutes les tâches nécessaires pour finaliser le projet jusqu'à un état prêt pour production en analysant :
- Le contexte de code fourni dans la conversation
- Les références au dossier "données" mentionnées dans le contexte
- Tous les éléments incomplets ou manquants identifiables depuis le contexte partagé

## Format de sortie

Crée un fichier markdown avec un tableau exhaustif dans ce format :

```markdown
# Plan de finalisation - [Nom du Projet]

## Analyse du contexte fourni
*[Description des fichiers et code partagés dans la conversation, avec attention particulière aux mentions du dossier "données"]*

## Tâches de finalisation

| Status | Action | File | Type | Priority | Complexity | Current State | Target State | Tests to Update |
|--------|--------|------|------|----------|------------|---------------|--------------|-----------------|
| TODO | CREATE | path/to/file.js | New | CRITICAL | High | Missing implementation | Fully functional module | unit_tests/file.test.js |
```

## Critères d'analyse

Pour chaque élément du contexte fourni, identifie :

### 1. Fonctionnalités incomplètes
- Blocs TODO, FIXME, HACK, XXX
- Commentaires non suivis d'implémentation
- Fonctions vides ou avec `throw new Error("Not implemented")`
- Appels vers des fonctions/modules inexistants
- Logique métier manquante ou partielle

### 2. Structure et architecture
- Modules prévus mais non créés
- Interfaces sans implémentation
- Classes/composants incomplets
- Dépendances manquantes ou mal configurées

### 3. Données et traitement
- **Références au dossier "données" dans le contexte fourni**
- Scripts de migration manquants (identifiables depuis le contexte)
- Validation de données incomplète
- Formatage ou transformation requis

### 4. Tests et qualité
- Tests unitaires manquants
- Tests d'intégration absents
- Couverture de code insuffisante
- Tests de validation des données

### 5. Configuration et déploiement
- Variables d'environnement manquantes
- Configuration de production incomplète
- Scripts de build/déploiement absents
- Documentation technique manquante

### 6. Sécurité et performance
- Validation d'entrées manquante
- Gestion d'erreurs incomplète
- Optimisations performance requises
- Contrôles d'accès manquants

## Définitions des colonnes

- **Status** : TODO, IN PROGRESS, DONE, BLOCKED
- **Action** : CREATE, MODIFY, DELETE, REFACTOR, COMPLETE, MIGRATE
- **File** : Chemin exact relatif depuis la racine du projet
- **Type** : New, Fix, Update, Refactor, Migration, Documentation, Test
- **Priority** : CRITICAL, HIGH, MEDIUM, LOW
- **Complexity** : High (>1 jour), Medium (quelques heures), Low (<2h)
- **Current State** : Description précise de ce qui existe actuellement
- **Target State** : Description claire de l'état final attendu
- **Tests to Update** : Fichiers de tests à créer/modifier

## Méthodologie

1. **Analyse du contexte fourni** : Examine uniquement le code et la structure partagés dans la conversation
2. **Lecture détaillée** : Analyse le contenu fourni ligne par ligne, pas seulement les noms de fichiers
3. **Priorisation intelligente** : Les tâches bloquantes en CRITICAL, les améliorations en LOW
4. **Granularité appropriée** : Une tâche = une action atomique et testable
5. **Attention aux références "données"** : Identifier tous les besoins liés au dossier "données" mentionnés dans le contexte

## Livrable final

Un fichier `{NomDuDossier}.todo.md` contenant :
- Résumé exécutif des tâches par priorité
- Tableau détaillé de toutes les tâches
- Estimation du temps total par complexité
- Dépendances entre tâches identifiées