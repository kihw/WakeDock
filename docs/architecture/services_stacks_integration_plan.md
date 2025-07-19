# Plan de fusion des services et des stacks

Ce document décrit les étapes nécessaires pour fusionner la gestion des **services** et des **stacks** au sein de WakeDock. L'objectif est d'unifier l'affichage et la création de ces éléments afin de simplifier l'expérience utilisateur.

## Objectifs

1. **Affichage unifié** :
   - La section *Stacks* doit pouvoir afficher :
     - Les conteneurs individuels
     - Les stacks Docker Compose
     - Les projets locaux
     - Les projets GitHub (dockerisés ou non)
2. **Création de service améliorée** :
   - Le formulaire *New Service* propose le type de ressource à créer (conteneur, stack, projet local, projet GitHub).
   - Les paramètres affichés s'adaptent automatiquement selon le type choisi.

## Étapes de restructuration

1. ### Analyse de l'existant
   - Recenser les vues et API actuelles dédiées aux services et aux stacks.
   - Identifier les duplications de logique et les différences de données entre les deux modules.

2. ### Unification du modèle de données
   - Définir un modèle commun `StackItem` capable de représenter :
     - Un conteneur simple
     - Un service issu d'un `docker-compose.yml`
     - Un projet local
     - Un projet GitHub
   - Ajouter des champs optionnels pour stocker l'origine (local, GitHub) et le type (conteneur, stack, projet).

3. ### Mise à jour de l'API
   - Fusionner les routes REST liées aux services et aux stacks sous un même prefixe (`/api/v1/stacks`).
   - Prévoir des filtres permettant d'afficher uniquement certains types (`type=container`, `type=github`, etc.).
   - Adapter la documentation OpenAPI en conséquence.

4. ### Refactorisation du frontend
   - Remplacer les pages séparées *Services* et *Stacks* par une vue unique listant tous les `StackItem`.
   - Ajouter des options de filtrage et de recherche par type et par source.
   - Mettre à jour le store Svelte/React pour gérer le nouveau modèle de données.

5. ### Formulaire de création dynamique
   - Réaliser un composant *New Service* proposant un sélecteur de type.
   - Afficher ou masquer les champs (image Docker, dépôt GitHub, chemin local…) selon la sélection.
   - Prévoir la validation spécifique pour chaque type (ex : vérification du `docker-compose.yml`).

6. ### Migration des données existantes
   - Écrire des scripts de migration pour convertir les services et stacks actuels vers le nouveau modèle `StackItem`.
   - Tester la migration sur un environnement de staging avant déploiement.

7. ### Tests et validation
   - Mettre à jour ou créer des tests unitaires et d’intégration pour couvrir les nouveaux comportements.
   - Vérifier le bon fonctionnement de l'affichage unifié et du formulaire dynamique.

8. ### Documentation
   - Mettre à jour la documentation utilisateur afin d’expliquer la nouvelle gestion des stacks et services.
   - Ajouter des exemples d’utilisation pour chaque type de ressource supporté.

## Prochaines étapes

- Planifier un sprint dédié à la mise en place du nouveau modèle de données.
- Définir les priorités pour l'implémentation frontend et backend.
- Prévoir une phase de tests utilisateurs pour valider l’ergonomie de la nouvelle interface.

