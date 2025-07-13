# Scripts de Base de Données

## 📁 Contenu

- **`init-db.sh`** - Initialisation de la base de données
- **`init-db.sql`** - Script SQL d'initialisation
- **`migrate.sh`** - Gestion des migrations de schéma

## 🚀 Usage

```bash
# Initialisation complète
./init-db.sh --create-admin

# Migrations
./migrate.sh --upgrade

# Migrations avec rollback
./migrate.sh --downgrade
```
