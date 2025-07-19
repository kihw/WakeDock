# Plan de Page Unique : Monitoring, Analytics et Logs

Ce document propose une organisation regroupant les informations de **monitoring**, d'**analytics** et de **logs** dans une même page. Il servira de base pour la future mise à jour de la documentation de WakeDock.

## 1. Analyse du Projet

WakeDock se compose principalement :

- **Backend** : API FastAPI.
- **Frontend** : tableau de bord SvelteKit.
- **Reverse Proxy** : Caddy.
- **Base de données** : SQLite ou PostgreSQL.
- **Scripts** : outils de maintenance et de benchmark (ex. `scripts/monitoring/performance_benchmark.py`).
- **Configuration** : fichiers YAML (ex. `config/logging.yml`) et variables d'environnement (`.env.example`).

Le dépôt actuel met l'accent sur la gestion Docker et la mise en place d'un pipeline complet (CI/CD, déploiement, scripts de debug). La partie monitoring est évoquée à travers l'exposition de métriques Prometheus et des configurations de log, mais il n'existe pas encore de page dédiée regroupant ces aspects.

## 2. Objectif de la Nouvelle Page

Créer une page unique permettant de :

1. Détailler la configuration **Monitoring** (Prometheus, health checks, alertes).
2. Présenter les outils d'**Analytics** (Grafana, tableaux de bord de performance).
3. Expliquer la stratégie de **Logs** (format, stockage, rotation, consultation).
4. Proposer un exemple d'intégration complète dans l'environnement WakeDock.

## 3. Structure Proposée

1. **Introduction**
   - Rôle du monitoring, des analytics et des logs.
   - Bénéfices de les regrouper pour une vue unifiée.

2. **Métriques et Monitoring**
   - Endpoints disponibles (`/health`, `/metrics`).
   - Exemple de configuration Prometheus.
   - Références aux alertes et sondes de disponibilité.

3. **Analytics**
   - Utilisation de Grafana ou d'outils similaires.
   - Exemple de tableau de bord : temps de réponse API, charge CPU, etc.
   - Possibilité d'exporter des statistiques via les scripts de benchmark.

4. **Gestion des Logs**
   - Emplacement et format (cf. `config/logging.yml`).
   - Rotation et niveaux de log.
   - Accès via l'API (`/api/containers/{id}/logs`).

5. **Centralisation et Outils Complémentaires**
   - Suggestions : stack Loki ou EFK pour centraliser logs et métriques.
   - Intégration possible avec Sentry pour le suivi des erreurs.

6. **Mise en Place Pas à Pas**
   - Activer Prometheus et Grafana via `docker-compose`.
   - Exemple de configuration d'environnement (variables `.env`).
   - Liaison avec le dashboard SvelteKit pour afficher les données.

7. **Aller Plus Loin**
   - Liens vers les scripts de benchmark.
   - Idées d'amélioration pour la version future (alerting avancé, analytics personnalisées).

## 4. Étapes Suivantes

1. **Créer** la page de documentation complète en suivant cette structure.
2. **Mettre à jour** `docs/index.md` et `docs/operations/index.md` pour y ajouter un lien vers cette nouvelle section.
3. **Vérifier** la cohérence avec les fichiers de configuration existants et mettre à jour les exemples si nécessaire.

Ce plan servira de référence pour centraliser la documentation sur la surveillance, l'analyse et la gestion des logs de WakeDock.
