# Scripts de Surveillance et Performance

> **⚠️ Scripts Supprimés** : `health-check.sh` et `status.sh` ont été supprimés car entièrement remplacés par l'API et le dashboard intégré.

## 📁 Contenu

- **`performance_benchmark.py`** - Tests de performance spécialisés
- **`analyze-docker-compose.sh`** - Analyse et optimisation Docker Compose

## � Migration vers l'Application

Les fonctionnalités de monitoring sont maintenant intégrées dans :

- **API Health** : `/api/v1/health`, `/api/v1/system/health`
- **Dashboard** : Interface de monitoring temps réel
- **Backend** : `src/wakedock/core/health.py` (HealthMonitor)
- **Frontend** : `dashboard/src/lib/api/system-api.ts`

## 🚀 Usage

```bash
# Tests de performance spécialisés
python performance_benchmark.py --full

# Analyse Docker Compose
./analyze-docker-compose.sh

# Analyse Docker
./analyze-docker-compose.sh --optimize
```
