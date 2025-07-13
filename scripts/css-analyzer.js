#!/usr/bin/env node

/**
 * CSS Bundle Optimization Analyzer
 * TASK-PERF-001: Analyze CSS bundles for optimization opportunities
 * 
 * Conformément aux règles strictes WakeDock:
 * - Analyse statique uniquement
 * - Pas d'exécution locale de serveurs
 * - Focus sur les métriques de production
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration pour l'analyse
const CONFIG = {
  buildDir: 'dashboard/.svelte-kit/output/client',
  reportFile: 'reports/css-optimization-report.json',
  thresholds: {
    maxBundleSize: 100 * 1024, // 100KB
    maxDuplication: 5, // 5%
    maxUnusedSelectors: 10, // 10%
    criticalCssSize: 14 * 1024 // 14KB (critical CSS)
  }
};

class CSSAnalyzer {
  constructor() {
    this.results = {
      timestamp: new Date().toISOString(),
      bundles: [],
      duplicatedRules: [],
      unusedSelectors: [],
      optimizations: [],
      metrics: {}
    };
  }

  async analyze() {
    console.log('🔍 CSS Bundle Optimization Analysis - WakeDock');
    console.log('================================================\n');

    try {
      // 1. Analyser les bundles CSS
      await this.analyzeBundles();

      // 2. Détecter les doublons
      await this.findDuplicatedRules();

      // 3. Identifier les sélecteurs inutilisés
      await this.findUnusedSelectors();

      // 4. Calculer les métriques
      this.calculateMetrics();

      // 5. Générer les recommandations
      this.generateOptimizations();

      // 6. Afficher le rapport
      this.displayReport();

      // 7. Sauvegarder le rapport
      this.saveReport();

    } catch (error) {
      console.error('❌ Erreur lors de l\'analyse CSS:', error.message);
      process.exit(1);
    }
  }

  async analyzeBundles() {
    const buildPath = path.join(process.cwd(), CONFIG.buildDir);

    if (!fs.existsSync(buildPath)) {
      throw new Error(`Build directory not found: ${buildPath}`);
    }

    console.log('📦 Analyse des bundles CSS...');

    // Trouver tous les fichiers CSS
    const cssFiles = this.findCSSFiles(buildPath);

    for (const file of cssFiles) {
      const bundle = await this.analyzeBundle(file);
      this.results.bundles.push(bundle);
    }

    console.log(`   ✓ ${cssFiles.length} bundles analysés\n`);
  }

  findCSSFiles(dir) {
    const cssFiles = [];

    const scanDir = (currentDir) => {
      const items = fs.readdirSync(currentDir);

      for (const item of items) {
        const itemPath = path.join(currentDir, item);
        const stat = fs.statSync(itemPath);

        if (stat.isDirectory()) {
          scanDir(itemPath);
        } else if (item.endsWith('.css') && !item.includes('.map')) {
          cssFiles.push(itemPath);
        }
      }
    };

    scanDir(dir);
    return cssFiles;
  }

  async analyzeBundle(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const stats = fs.statSync(filePath);

    // Analyse de base
    const analysis = {
      file: path.relative(process.cwd(), filePath),
      size: stats.size,
      gzipSize: this.estimateGzipSize(content),
      rules: this.countCSSRules(content),
      selectors: this.extractSelectors(content),
      properties: this.countProperties(content),
      mediaQueries: this.countMediaQueries(content),
      imports: this.countImports(content)
    };

    return analysis;
  }

  estimateGzipSize(content) {
    // Estimation approximative de la taille gzip
    // Ratio typique CSS: ~75% compression
    return Math.round(content.length * 0.25);
  }

  countCSSRules(content) {
    // Compter les règles CSS (approximatif)
    const rules = content.match(/[^}]*\{[^}]*\}/g) || [];
    return rules.length;
  }

  extractSelectors(content) {
    const selectors = [];
    const rules = content.match(/([^{}]+)\{[^}]*\}/g) || [];

    for (const rule of rules) {
      const selectorPart = rule.split('{')[0].trim();
      if (selectorPart) {
        selectors.push(selectorPart);
      }
    }

    return selectors;
  }

  countProperties(content) {
    const properties = content.match(/[a-z-]+\s*:/g) || [];
    return properties.length;
  }

  countMediaQueries(content) {
    const mediaQueries = content.match(/@media[^{]*\{/g) || [];
    return mediaQueries.length;
  }

  countImports(content) {
    const imports = content.match(/@import[^;]*;/g) || [];
    return imports.length;
  }

  async findDuplicatedRules() {
    console.log('🔍 Recherche de règles dupliquées...');

    const allSelectors = [];

    // Collecter tous les sélecteurs
    for (const bundle of this.results.bundles) {
      for (const selector of bundle.selectors) {
        allSelectors.push({
          selector: selector.trim(),
          bundle: bundle.file
        });
      }
    }

    // Trouver les doublons
    const selectorCounts = {};
    for (const item of allSelectors) {
      if (!selectorCounts[item.selector]) {
        selectorCounts[item.selector] = [];
      }
      selectorCounts[item.selector].push(item.bundle);
    }

    for (const [selector, bundles] of Object.entries(selectorCounts)) {
      if (bundles.length > 1) {
        this.results.duplicatedRules.push({
          selector,
          count: bundles.length,
          bundles: [...new Set(bundles)]
        });
      }
    }

    console.log(`   ✓ ${this.results.duplicatedRules.length} règles dupliquées trouvées\n`);
  }

  async findUnusedSelectors() {
    console.log('🔍 Recherche de sélecteurs inutilisés...');

    // Cette analyse nécessiterait une analyse statique plus poussée
    // Pour l'instant, on identifie les patterns suspects

    const suspiciousPatterns = [
      /^\.[a-z0-9-]+_[a-f0-9]{8}$/, // Classes générées avec hash
      /^\.unused-/,                   // Classes préfixées 'unused'
      /^\.test-/,                     // Classes de test
      /^\.debug-/                     // Classes de debug
    ];

    for (const bundle of this.results.bundles) {
      for (const selector of bundle.selectors) {
        const cleanSelector = selector.split(',')[0].trim();

        for (const pattern of suspiciousPatterns) {
          if (pattern.test(cleanSelector)) {
            this.results.unusedSelectors.push({
              selector: cleanSelector,
              bundle: bundle.file,
              reason: 'Potentially unused pattern'
            });
          }
        }
      }
    }

    console.log(`   ✓ ${this.results.unusedSelectors.length} sélecteurs potentiellement inutilisés\n`);
  }

  calculateMetrics() {
    console.log('📊 Calcul des métriques...');

    const totalSize = this.results.bundles.reduce((sum, bundle) => sum + bundle.size, 0);
    const totalGzipSize = this.results.bundles.reduce((sum, bundle) => sum + bundle.gzipSize, 0);
    const totalRules = this.results.bundles.reduce((sum, bundle) => sum + bundle.rules, 0);
    const totalSelectors = this.results.bundles.reduce((sum, bundle) => sum + bundle.selectors.length, 0);

    this.results.metrics = {
      totalBundles: this.results.bundles.length,
      totalSize,
      totalGzipSize,
      totalRules,
      totalSelectors,
      duplicatedRulesCount: this.results.duplicatedRules.length,
      unusedSelectorsCount: this.results.unusedSelectors.length,
      duplicationRate: totalSelectors > 0 ? (this.results.duplicatedRules.length / totalSelectors * 100).toFixed(2) : 0,
      compressionRatio: totalSize > 0 ? ((totalSize - totalGzipSize) / totalSize * 100).toFixed(2) : 0
    };

    console.log(`   ✓ Métriques calculées\n`);
  }

  generateOptimizations() {
    console.log('💡 Génération des optimisations...');

    const { metrics, bundles } = this.results;

    // Recommandations basées sur les seuils
    if (metrics.totalSize > CONFIG.thresholds.maxBundleSize) {
      this.results.optimizations.push({
        type: 'size',
        priority: 'high',
        title: 'Bundle CSS trop volumineux',
        description: `Taille totale: ${this.formatBytes(metrics.totalSize)} > ${this.formatBytes(CONFIG.thresholds.maxBundleSize)}`,
        recommendations: [
          'Diviser les bundles par route/composant',
          'Implémenter le code splitting CSS',
          'Supprimer les styles inutilisés'
        ]
      });
    }

    if (metrics.duplicationRate > CONFIG.thresholds.maxDuplication) {
      this.results.optimizations.push({
        type: 'duplication',
        priority: 'medium',
        title: 'Taux de duplication élevé',
        description: `${metrics.duplicationRate}% de règles dupliquées`,
        recommendations: [
          'Extraire les styles communs dans un bundle partagé',
          'Utiliser CSS-in-JS pour éviter les doublons',
          'Optimiser l\'extraction des styles Tailwind'
        ]
      });
    }

    // Recommandations spécifiques aux bundles
    for (const bundle of bundles) {
      if (bundle.size > CONFIG.thresholds.maxBundleSize * 0.5) {
        this.results.optimizations.push({
          type: 'bundle',
          priority: 'medium',
          title: `Bundle volumineux: ${bundle.file}`,
          description: `Taille: ${this.formatBytes(bundle.size)}`,
          recommendations: [
            'Analyser les styles spécifiques à ce bundle',
            'Vérifier l\'utilisation de Tailwind purge',
            'Considérer le lazy loading pour ce bundle'
          ]
        });
      }
    }

    console.log(`   ✓ ${this.results.optimizations.length} optimisations identifiées\n`);
  }

  displayReport() {
    const { metrics, optimizations } = this.results;

    console.log('📋 RAPPORT D\'OPTIMISATION CSS');
    console.log('================================\n');

    // Métriques générales
    console.log('📊 MÉTRIQUES GÉNÉRALES:');
    console.log(`   • Bundles CSS: ${metrics.totalBundles}`);
    console.log(`   • Taille totale: ${this.formatBytes(metrics.totalSize)}`);
    console.log(`   • Taille compressée: ${this.formatBytes(metrics.totalGzipSize)} (${metrics.compressionRatio}% compression)`);
    console.log(`   • Règles CSS: ${metrics.totalRules}`);
    console.log(`   • Sélecteurs: ${metrics.totalSelectors}`);
    console.log(`   • Taux de duplication: ${metrics.duplicationRate}%\n`);

    // Status des seuils
    console.log('🎯 CONFORMITÉ AUX SEUILS:');
    console.log(`   • Taille bundle: ${metrics.totalSize <= CONFIG.thresholds.maxBundleSize ? '✅' : '❌'} ${this.formatBytes(metrics.totalSize)} / ${this.formatBytes(CONFIG.thresholds.maxBundleSize)}`);
    console.log(`   • Duplication: ${metrics.duplicationRate <= CONFIG.thresholds.maxDuplication ? '✅' : '❌'} ${metrics.duplicationRate}% / ${CONFIG.thresholds.maxDuplication}%`);
    console.log(`   • Sélecteurs inutilisés: ${metrics.unusedSelectorsCount <= CONFIG.thresholds.maxUnusedSelectors ? '✅' : '❌'} ${metrics.unusedSelectorsCount} / ${CONFIG.thresholds.maxUnusedSelectors}\n`);

    // Détails des bundles
    console.log('📦 DÉTAILS DES BUNDLES:');
    for (const bundle of this.results.bundles) {
      console.log(`   • ${bundle.file}`);
      console.log(`     - Taille: ${this.formatBytes(bundle.size)} (gzip: ${this.formatBytes(bundle.gzipSize)})`);
      console.log(`     - Règles: ${bundle.rules}, Sélecteurs: ${bundle.selectors.length}`);
    }
    console.log();

    // Optimisations recommandées
    if (optimizations.length > 0) {
      console.log('💡 OPTIMISATIONS RECOMMANDÉES:');
      for (const opt of optimizations) {
        const priorityIcon = opt.priority === 'high' ? '🔴' : opt.priority === 'medium' ? '🟡' : '🟢';
        console.log(`   ${priorityIcon} ${opt.title}`);
        console.log(`     ${opt.description}`);
        for (const rec of opt.recommendations) {
          console.log(`     → ${rec}`);
        }
        console.log();
      }
    } else {
      console.log('✅ Aucune optimisation majeure nécessaire!\n');
    }

    // Score global
    const score = this.calculateOptimizationScore();
    console.log(`🏆 SCORE D'OPTIMISATION: ${score}/100`);
    console.log(`   ${score >= 90 ? '🟢 Excellent' : score >= 70 ? '🟡 Bon' : '🔴 Nécessite des améliorations'}\n`);
  }

  calculateOptimizationScore() {
    let score = 100;
    const { metrics } = this.results;

    // Pénalités basées sur les métriques
    if (metrics.totalSize > CONFIG.thresholds.maxBundleSize) {
      score -= 30;
    }

    if (metrics.duplicationRate > CONFIG.thresholds.maxDuplication) {
      score -= 20;
    }

    if (metrics.unusedSelectorsCount > CONFIG.thresholds.maxUnusedSelectors) {
      score -= 15;
    }

    // Pénalités pour les optimisations critiques
    const highPriorityOpts = this.results.optimizations.filter(opt => opt.priority === 'high');
    score -= highPriorityOpts.length * 10;

    return Math.max(0, Math.min(100, score));
  }

  saveReport() {
    const reportDir = path.dirname(CONFIG.reportFile);
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }

    fs.writeFileSync(CONFIG.reportFile, JSON.stringify(this.results, null, 2));
    console.log(`📄 Rapport sauvegardé: ${CONFIG.reportFile}`);
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

// Exécution principale
async function main() {
  const analyzer = new CSSAnalyzer();
  await analyzer.analyze();
}

// Exécuter si script appelé directement
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Erreur fatale:', error);
    process.exit(1);
  });
}

module.exports = { CSSAnalyzer };
