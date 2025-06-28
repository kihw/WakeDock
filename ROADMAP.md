# 🗺️ WakeDock Roadmap

## ✅ 1. Internationalisation (i18n)
**Objectif** : Rendre l’interface accessible en anglais 🇬🇧 et français 🇫🇷.
- Intégration d’un système multilingue (ex: i18next, react-intl)
- Traduction des composants et textes clés
- Détection automatique de la langue navigateur
- Sélecteur manuel de langue

---

## ⚙️ 2. Setup automatique des services + configuration Caddy
**Objectif** : Déployer les services automatiquement et configurer Caddy sans intervention manuelle.
- Détection des conteneurs actifs et ports exposés
- Génération automatique de la config Caddy correspondante
- Reload automatique de Caddy (via script ou API)
- Association nom de domaine ↔ conteneur

---

## 🔐 3. Authentification centralisée + Reverse Proxy sécurisé
**Objectif** : Protéger tous les services derrière une authentification WakeDock.
- Page de login centralisée (avec session persistante ou JWT)
- Reverse proxy via Caddy vers les services protégés
- Redirection automatique si non authentifié
- Intégration possible avec OAuth2 (GitHub, Google, etc.)

---

## 🚀 4. Wake-on-demand + écran de chargement
**Objectif** : Démarrer les conteneurs à la demande avec une UX fluide.
- Interception des requêtes si container éteint
- Affichage d’un écran de chargement personnalisé
- Démarrage automatique du conteneur cible
- Timeout + message d’échec si le service ne démarre pas

---

## 📊 5. Interface de gestion avancée
**Objectif** : Offrir plus de contrôle et de visibilité aux utilisateurs.
- Vue d’ensemble : mémoire, CPU, statut par conteneur
- Système de logs/événements : start/stop/errors
- Favoris, filtres, regroupement par projet/service
- Gestion manuelle des règles d’arrêt (par inactivité, durée, etc.)

---

