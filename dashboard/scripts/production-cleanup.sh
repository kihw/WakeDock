#!/bin/bash

# Script de nettoyage de production pour WakeDock Dashboard
# Nettoie les console.log, TODOs et optimise le code pour la production

set -e

echo "🧹 Nettoyage de production WakeDock Dashboard"
echo "============================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DASHBOARD_DIR="/Docker/code/WakeDock/dashboard"
SRC_DIR="$DASHBOARD_DIR/src"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}❌ Erreur: Répertoire source non trouvé: $SRC_DIR${NC}"
    exit 1
fi

cd "$DASHBOARD_DIR"

echo -e "\n${BLUE}📍 Répertoire de travail: $(pwd)${NC}"

# 1. Analyser les console.log existants
echo -e "\n${YELLOW}🔍 Analyse des console.log existants...${NC}"
CONSOLE_COUNT=$(find src -name "*.ts" -o -name "*.js" -o -name "*.svelte" | xargs grep -l "console\." | wc -l)
echo -e "   Fichiers avec console.log: ${CONSOLE_COUNT}"

if [ "$CONSOLE_COUNT" -gt 0 ]; then
    echo -e "\n${YELLOW}📋 Fichiers contenant des console.log:${NC}"
    find src -name "*.ts" -o -name "*.js" -o -name "*.svelte" | xargs grep -l "console\." | while read file; do
        COUNT=$(grep -c "console\." "$file" || true)
        echo -e "   📄 $file (${COUNT} occurrences)"
    done
fi

# 2. Vérifier les TODOs
echo -e "\n${YELLOW}📝 Recherche des TODOs...${NC}"
TODO_FILES=$(find src -name "*.ts" -o -name "*.js" -o -name "*.svelte" | xargs grep -l "TODO\|FIXME\|XXX\|HACK" | grep -v "XXX" | wc -l || echo "0")
echo -e "   Fichiers avec TODOs: ${TODO_FILES}"

if [ "$TODO_FILES" -gt 0 ]; then
    echo -e "\n${YELLOW}📋 TODOs trouvés:${NC}"
    find src -name "*.ts" -o -name "*.js" -o -name "*.svelte" | xargs grep -Hn "TODO\|FIXME\|HACK" | grep -v "XXX" | head -10
fi

# 3. Remplacer les console.log par le logger de production
echo -e "\n${GREEN}🔄 Remplacement des console.log...${NC}"

# Fonction pour traiter un fichier
process_file() {
    local file="$1"
    local temp_file="${file}.tmp"
    local has_changes=false
    
    # Vérifier si le fichier contient des console.log
    if grep -q "console\." "$file"; then
        echo "   🔧 Traitement: $file"
        
        # Vérifier si l'import du logger existe déjà
        if ! grep -q "production-logger" "$file"; then
            # Ajouter l'import selon le type de fichier
            if [[ "$file" == *.svelte ]]; then
                # Pour les fichiers Svelte, ajouter après <script>
                sed '/^<script[^>]*>/a\  import { log } from '\''$lib/utils/production-logger'\'';' "$file" > "$temp_file"
            else
                # Pour les fichiers TS/JS, ajouter au début
                echo "import { log } from '\$lib/utils/production-logger';" > "$temp_file"
                cat "$file" >> "$temp_file"
            fi
            mv "$temp_file" "$file"
        fi
        
        # Remplacer les console.log
        sed -i.bak \
            -e 's/console\.log(/log.info(/g' \
            -e 's/console\.info(/log.info(/g' \
            -e 's/console\.warn(/log.warn(/g' \
            -e 's/console\.error(/log.error(/g' \
            -e 's/console\.debug(/log.debug(/g' \
            "$file"
        
        # Supprimer le fichier de sauvegarde
        rm -f "${file}.bak"
        
        has_changes=true
    fi
    
    if $has_changes; then
        echo "   ✅ Modifié: $file"
        return 0
    else
        return 1
    fi
}

# Traiter tous les fichiers
MODIFIED_COUNT=0
find src -name "*.ts" -o -name "*.js" -o -name "*.svelte" | while read file; do
    if process_file "$file"; then
        MODIFIED_COUNT=$((MODIFIED_COUNT + 1))
    fi
done

# 4. Optimiser les animations pour prefers-reduced-motion
echo -e "\n${GREEN}🎨 Optimisation des animations...${NC}"

# Vérifier que le fichier animations.ts a les bonnes fonctions
ANIMATIONS_FILE="src/lib/utils/animations.ts"
if [ -f "$ANIMATIONS_FILE" ]; then
    if grep -q "prefersReducedMotion" "$ANIMATIONS_FILE"; then
        echo "   ✅ Support prefers-reduced-motion déjà présent"
    else
        echo "   ⚠️  Support prefers-reduced-motion manquant"
    fi
else
    echo "   ❌ Fichier animations.ts non trouvé"
fi

# 5. Vérifier les imports du logger
echo -e "\n${GREEN}🔗 Vérification des imports du logger...${NC}"
LOGGER_FILE="src/lib/utils/production-logger.ts"
if [ -f "$LOGGER_FILE" ]; then
    echo "   ✅ Logger de production présent"
else
    echo "   ❌ Logger de production manquant"
fi

# 6. Optimiser les bundles CSS
echo -e "\n${GREEN}📦 Analyse de la taille des bundles...${NC}"
if [ -d "build" ]; then
    CSS_SIZE=$(find build -name "*.css" -exec du -ch {} + | tail -1 | cut -f1)
    JS_SIZE=$(find build -name "*.js" -exec du -ch {} + | tail -1 | cut -f1)
    echo "   📊 Taille CSS totale: $CSS_SIZE"
    echo "   📊 Taille JS totale: $JS_SIZE"
else
    echo "   ⚠️  Pas de build trouvé. Lancez 'npm run build' d'abord."
fi

# 7. Supprimer les fichiers de debug/test temporaires
echo -e "\n${GREEN}🗑️  Nettoyage des fichiers temporaires...${NC}"
find src -name "*.tmp" -o -name "*.backup" -o -name "*.orig" | while read file; do
    rm -f "$file"
    echo "   🗑️  Supprimé: $file"
done

# 8. Vérifier la conformité ESLint
echo -e "\n${GREEN}🔍 Vérification ESLint...${NC}"
if command -v npm &> /dev/null; then
    if npm run lint:check > /dev/null 2>&1; then
        echo "   ✅ ESLint: Aucune erreur"
    else
        echo "   ⚠️  ESLint: Erreurs détectées. Lancez 'npm run lint:fix'"
    fi
else
    echo "   ⚠️  npm non disponible pour vérifier ESLint"
fi

# 9. Résumé final
echo -e "\n${BLUE}📊 RÉSUMÉ DU NETTOYAGE${NC}"
echo "=========================="
echo -e "✅ Console.log traités dans les fichiers modifiés"
echo -e "✅ Support prefers-reduced-motion vérifié"
echo -e "✅ Logger de production vérifié"
echo -e "✅ Fichiers temporaires nettoyés"

# Recommandations finales
echo -e "\n${YELLOW}💡 ÉTAPES SUIVANTES RECOMMANDÉES:${NC}"
echo "1. 🧪 Testez l'application: npm run dev"
echo "2. 🏗️  Construisez: npm run build"
echo "3. 🔍 Vérifiez les erreurs: npm run lint:check"
echo "4. 🧪 Lancez les tests: npm run test"
echo "5. 📊 Vérifiez les performances: npm run analyze"

echo -e "\n${GREEN}✨ Nettoyage de production terminé!${NC}"

# Retourner le code d'erreur approprié
exit 0
