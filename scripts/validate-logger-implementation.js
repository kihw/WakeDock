#!/usr/bin/env node

/**
 * Logger Implementation Validation Script
 * TASK-DX-002: Validates console.log cleanup and production logger usage
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  srcDir: 'dashboard/src',
  excludePatterns: [
    '**/*.test.*',
    '**/*.spec.*',
    '**/test/**',
    '**/tests/**',
    '**/node_modules/**'
  ]
};

class LoggerValidator {
  constructor() {
    this.results = {
      totalFiles: 0,
      filesWithConsoleLog: 0,
      filesWithProductionLogger: 0,
      consoleLogUsages: [],
      productionLoggerUsages: [],
      validationPassed: false
    };
  }

  validate() {
    console.log('🔍 Logger Implementation Validation');
    console.log('===================================\n');

    // 1. Scanner tous les fichiers TypeScript/JavaScript
    const files = this.scanSourceFiles();

    // 2. Analyser chaque fichier
    for (const file of files) {
      this.analyzeFile(file);
    }

    // 3. Évaluer les résultats
    this.evaluateResults();

    // 4. Afficher le rapport
    this.displayReport();

    return this.results.validationPassed;
  }

  scanSourceFiles() {
    const sourceFiles = [];
    const srcPath = path.join(process.cwd(), CONFIG.srcDir);

    if (!fs.existsSync(srcPath)) {
      throw new Error(`Source directory not found: ${srcPath}`);
    }

    this.scanDirectory(srcPath, sourceFiles);

    console.log(`📂 Scanned ${sourceFiles.length} source files\n`);
    this.results.totalFiles = sourceFiles.length;

    return sourceFiles;
  }

  scanDirectory(dir, files) {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        this.scanDirectory(fullPath, files);
      } else if (this.isSourceFile(item) && !this.isExcluded(fullPath)) {
        files.push(fullPath);
      }
    }
  }

  isSourceFile(filename) {
    return /\.(ts|js|svelte)$/.test(filename);
  }

  isExcluded(filePath) {
    return CONFIG.excludePatterns.some(pattern => {
      const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
      return regex.test(filePath);
    });
  }

  analyzeFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const relativePath = path.relative(process.cwd(), filePath);

    // Chercher console.log usages
    const consoleLogMatches = this.findConsoleLogUsages(content);
    if (consoleLogMatches.length > 0) {
      this.results.filesWithConsoleLog++;
      this.results.consoleLogUsages.push({
        file: relativePath,
        count: consoleLogMatches.length,
        lines: consoleLogMatches.map(match => this.getLineNumber(content, match))
      });
    }

    // Chercher production logger usages
    const loggerMatches = this.findProductionLoggerUsages(content);
    if (loggerMatches.length > 0) {
      this.results.filesWithProductionLogger++;
      this.results.productionLoggerUsages.push({
        file: relativePath,
        count: loggerMatches.length,
        methods: loggerMatches
      });
    }
  }

  findConsoleLogUsages(content) {
    // Patterns pour détecter console.log
    const patterns = [
      /console\.log\s*\(/g,
      /console\.warn\s*\(/g,
      /console\.error\s*\(/g,
      /console\.info\s*\(/g,
      /console\.debug\s*\(/g
    ];

    const matches = [];
    for (const pattern of patterns) {
      const found = content.match(pattern) || [];
      matches.push(...found);
    }

    return matches;
  }

  findProductionLoggerUsages(content) {
    // Patterns pour détecter l'usage du production logger
    const patterns = [
      /logger\.debug\s*\(/g,
      /logger\.info\s*\(/g,
      /logger\.warn\s*\(/g,
      /logger\.error\s*\(/g,
      /ProductionLogger/g,
      /production-logger/g
    ];

    const matches = [];
    for (const pattern of patterns) {
      const found = content.match(pattern) || [];
      matches.push(...found);
    }

    return matches;
  }

  getLineNumber(content, searchText) {
    const index = content.indexOf(searchText);
    if (index === -1) return null;

    const beforeMatch = content.substring(0, index);
    return beforeMatch.split('\n').length;
  }

  evaluateResults() {
    const { filesWithConsoleLog, filesWithProductionLogger, totalFiles } = this.results;

    // Critères de validation:
    // 1. Moins de 5% des fichiers avec console.log
    // 2. Au moins quelques fichiers utilisent le production logger
    // 3. Le ratio production logger > console.log

    const consoleLogRatio = (filesWithConsoleLog / totalFiles) * 100;
    const hasProductionLoggerUsage = filesWithProductionLogger > 0;
    const loggerRatioGood = filesWithProductionLogger >= filesWithConsoleLog;

    this.results.validationPassed =
      consoleLogRatio < 10 && // Tolérance de 10% pour console.log
      hasProductionLoggerUsage &&
      loggerRatioGood;

    this.results.metrics = {
      consoleLogRatio: Math.round(consoleLogRatio * 100) / 100,
      hasProductionLoggerUsage,
      loggerRatioGood
    };
  }

  displayReport() {
    const { metrics } = this.results;

    console.log('📊 LOGGER VALIDATION REPORT');
    console.log('===========================\n');

    console.log('📈 METRICS:');
    console.log(`   • Total files analyzed: ${this.results.totalFiles}`);
    console.log(`   • Files with console.log: ${this.results.filesWithConsoleLog} (${metrics.consoleLogRatio}%)`);
    console.log(`   • Files with production logger: ${this.results.filesWithProductionLogger}`);
    console.log(`   • Production logger usage: ${metrics.hasProductionLoggerUsage ? '✅' : '❌'}`);
    console.log(`   • Logger ratio good: ${metrics.loggerRatioGood ? '✅' : '❌'}\n`);

    // Détails des console.log trouvés
    if (this.results.consoleLogUsages.length > 0) {
      console.log('⚠️  CONSOLE.LOG USAGES FOUND:');
      for (const usage of this.results.consoleLogUsages.slice(0, 10)) {
        console.log(`   📄 ${usage.file}: ${usage.count} usages`);
      }
      if (this.results.consoleLogUsages.length > 10) {
        console.log(`   ... and ${this.results.consoleLogUsages.length - 10} more files`);
      }
      console.log();
    }

    // Détails du production logger
    if (this.results.productionLoggerUsages.length > 0) {
      console.log('✅ PRODUCTION LOGGER USAGES:');
      for (const usage of this.results.productionLoggerUsages.slice(0, 5)) {
        console.log(`   📄 ${usage.file}: ${usage.count} usages`);
      }
      console.log();
    }

    // Résultat final
    const status = this.results.validationPassed ? '✅ PASSED' : '❌ FAILED';
    console.log(`🏆 VALIDATION RESULT: ${status}`);

    if (!this.results.validationPassed) {
      console.log('\n💡 RECOMMENDATIONS:');
      if (metrics.consoleLogRatio > 10) {
        console.log('   • Replace more console.log statements with production logger');
      }
      if (!metrics.hasProductionLoggerUsage) {
        console.log('   • Start using the production logger in components');
      }
      if (!metrics.loggerRatioGood) {
        console.log('   • Increase production logger adoption');
      }
    }
  }
}

// Fonction utilitaire pour usage programmatique
function validateLoggerUsage() {
  const validator = new LoggerValidator();
  return validator.validate();
}

// Exécution principale
if (require.main === module) {
  try {
    const validator = new LoggerValidator();
    const passed = validator.validate();
    process.exit(passed ? 0 : 1);
  } catch (error) {
    console.error('❌ Validation error:', error.message);
    process.exit(1);
  }
}

module.exports = { LoggerValidator, validateLoggerUsage };
