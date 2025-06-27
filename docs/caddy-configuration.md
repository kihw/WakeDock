# WakeDock Caddy Configuration

## Vue d'ensemble

WakeDock utilise une approche dynamique pour configurer Caddy. Au lieu de monter des fichiers statiques Caddyfile, l'application gère sa propre configuration via l'API Admin de Caddy.

## Avantages

1. **Pas de problèmes de montage de fichiers** - Évite les erreurs Docker lors du déploiement
2. **Configuration dynamique** - WakeDock peut modifier la configuration en temps réel
3. **Portabilité** - Fonctionne sur tous les environnements (local, Dokploy, Kubernetes, etc.)
4. **Auto-configuration** - L'application configure automatiquement ses propres routes

## Comment ça fonctionne

### 1. Configuration initiale
Caddy démarre avec une configuration minimale qui :
- Active l'API Admin sur le port 2019
- Sert une page d'attente sur le port 80

### 2. Configuration dynamique par WakeDock
Au démarrage, WakeDock :
- Attend que Caddy soit disponible
- Configure automatiquement les routes vers le dashboard et l'API
- Met à jour la configuration selon les besoins

### 3. Gestion des services Docker
Quand WakeDock détecte de nouveaux services :
- Il peut automatiquement créer des routes Caddy
- Gère les certificats SSL automatiquement
- Configure les proxy reverses

## Configuration manuelle (optionnelle)

Si vous voulez configurer Caddy manuellement, vous pouvez utiliser l'API Admin :

```bash
# Voir la configuration actuelle
curl http://localhost:2019/config/

# Appliquer une nouvelle configuration
curl -X POST http://localhost:2019/config/ \
     -H "Content-Type: application/json" \
     -d @nouvelle-config.json
```

## Variables d'environnement

- `CADDY_AUTO_HTTPS` - Active/désactive HTTPS automatique (on/off)
- `CADDY_ADMIN_API_ENABLED` - Active/désactive l'API Admin
- `CADDY_ADMIN_PORT` - Port pour l'API Admin (défaut: 2019)

## Fichiers de configuration legacy

Les fichiers `Caddyfile*` dans le dossier `caddy/` sont conservés pour référence mais ne sont plus utilisés par défaut. Ils peuvent servir d'exemples pour configuration manuelle.
