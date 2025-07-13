#!/usr/bin/env node

/**
 * WakeDock Accessibility Audit Tool
 * TASK-A11Y-001: Comprehensive accessibility compliance checking
 * 
 * Conformément aux règles strictes WakeDock:
 * - Analyse statique des composants Svelte
 * - Vérification WCAG 2.1 AA
 * - Pas d'exécution de serveur local
 * - Focus sur la conformité production
 */

const fs = require('fs');
const path = require('path');

// Configuration de l'audit
const CONFIG = {
  srcDir: 'dashboard/src',
  reportFile: 'reports/accessibility-audit-report.json',
  wcagLevel: 'AA',
  wcagVersion: '2.1',
  excludePatterns: [
    '**/*.test.*',
    '**/*.spec.*',
    '**/test/**',
    '**/tests/**'
  ]
};

// Règles WCAG 2.1 AA critiques
const WCAG_RULES = {
  // Perceptible
  'color-contrast': {
    level: 'AA',
    principle: 'Perceptible',
    guideline: '1.4.3',
    description: 'Color contrast ratio must be at least 4.5:1'
  },
  'non-text-contrast': {
    level: 'AA',
    principle: 'Perceptible',
    guideline: '1.4.11',
    description: 'Non-text elements must have sufficient contrast'
  },
  'images-alt': {
    level: 'A',
    principle: 'Perceptible',
    guideline: '1.1.1',
    description: 'All images must have alternative text'
  },
  'heading-structure': {
    level: 'AA',
    principle: 'Perceptible',
    guideline: '1.3.1',
    description: 'Heading structure must be logical and sequential'
  },

  // Operable
  'keyboard-accessible': {
    level: 'A',
    principle: 'Operable',
    guideline: '2.1.1',
    description: 'All functionality must be available via keyboard'
  },
  'focus-visible': {
    level: 'AA',
    principle: 'Operable',
    guideline: '2.4.7',
    description: 'Focus indicators must be clearly visible'
  },
  'link-purpose': {
    level: 'AA',
    principle: 'Operable',
    guideline: '2.4.4',
    description: 'Link purpose must be clear from context'
  },

  // Understandable
  'form-labels': {
    level: 'A',
    principle: 'Understandable',
    guideline: '3.3.2',
    description: 'Form inputs must have associated labels'
  },
  'error-identification': {
    level: 'A',
    principle: 'Understandable',
    guideline: '3.3.1',
    description: 'Input errors must be clearly identified'
  },

  // Robust
  'valid-markup': {
    level: 'A',
    principle: 'Robust',
    guideline: '4.1.1',
    description: 'Markup must be valid and semantic'
  },
  'aria-compliance': {
    level: 'A',
    principle: 'Robust',
    guideline: '4.1.2',
    description: 'ARIA attributes must be valid and appropriate'
  }
};

class AccessibilityAuditor {
  constructor() {
    this.results = {
      timestamp: new Date().toISOString(),
      wcagLevel: CONFIG.wcagLevel,
      wcagVersion: CONFIG.wcagVersion,
      summary: {
        totalFiles: 0,
        totalIssues: 0,
        criticalIssues: 0,
        warningIssues: 0,
        passedRules: 0,
        failedRules: 0
      },
      files: [],
      ruleResults: {},
      recommendations: []
    };
  }

  async audit() {
    console.log('♿ WakeDock Accessibility Audit - WCAG 2.1 AA');
    console.log('==============================================\n');

    try {
      // 1. Scanner les fichiers Svelte
      const files = await this.scanSvelteFiles();

      // 2. Analyser chaque fichier
      for (const file of files) {
        await this.analyzeFile(file);
      }

      // 3. Évaluer la conformité globale
      this.evaluateCompliance();

      // 4. Générer les recommandations
      this.generateRecommendations();

      // 5. Afficher le rapport
      this.displayReport();

      // 6. Sauvegarder les résultats
      this.saveReport();

    } catch (error) {
      console.error('❌ Erreur lors de l\'audit d\'accessibilité:', error.message);
      process.exit(1);
    }
  }

  async scanSvelteFiles() {
    console.log('🔍 Scanning Svelte components...');

    const svelteFiles = [];
    const srcPath = path.join(process.cwd(), CONFIG.srcDir);

    if (!fs.existsSync(srcPath)) {
      throw new Error(`Source directory not found: ${srcPath}`);
    }

    this.scanDirectory(srcPath, svelteFiles);

    console.log(`   ✓ Found ${svelteFiles.length} Svelte files\n`);
    this.results.summary.totalFiles = svelteFiles.length;

    return svelteFiles;
  }

  scanDirectory(dir, files) {
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        this.scanDirectory(fullPath, files);
      } else if (item.endsWith('.svelte') && !this.isExcluded(fullPath)) {
        files.push(fullPath);
      }
    }
  }

  isExcluded(filePath) {
    return CONFIG.excludePatterns.some(pattern => {
      const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
      return regex.test(filePath);
    });
  }

  async analyzeFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const relativePath = path.relative(process.cwd(), filePath);

    console.log(`📄 Analyzing: ${relativePath}`);

    const fileResult = {
      path: relativePath,
      issues: [],
      warnings: [],
      compliance: {}
    };

    // Analyser les différents aspects d'accessibilité
    this.checkColorContrast(content, fileResult);
    this.checkImageAlt(content, fileResult);
    this.checkHeadingStructure(content, fileResult);
    this.checkKeyboardAccessibility(content, fileResult);
    this.checkFormLabels(content, fileResult);
    this.checkAriaCompliance(content, fileResult);
    this.checkFocusManagement(content, fileResult);
    this.checkSemanticMarkup(content, fileResult);
    this.checkErrorHandling(content, fileResult);
    this.checkMotionAccessibility(content, fileResult);

    this.results.files.push(fileResult);

    const issueCount = fileResult.issues.length;
    const warningCount = fileResult.warnings.length;

    if (issueCount > 0 || warningCount > 0) {
      console.log(`   ⚠️  ${issueCount} issues, ${warningCount} warnings`);
    } else {
      console.log(`   ✅ No accessibility issues found`);
    }
  }

  checkColorContrast(content, fileResult) {
    // Rechercher les classes de couleur problématiques
    const problematicPatterns = [
      /class="[^"]*text-gray-400[^"]*"/g,
      /class="[^"]*text-gray-300[^"]*"/g,
      /class="[^"]*bg-gray-100[^"]*text-gray-500[^"]*"/g
    ];

    for (const pattern of problematicPatterns) {
      const matches = content.match(pattern);
      if (matches) {
        fileResult.issues.push({
          rule: 'color-contrast',
          severity: 'critical',
          message: 'Potential color contrast issue detected',
          details: `Found ${matches.length} instances of potentially low contrast colors`,
          wcag: WCAG_RULES['color-contrast'],
          line: this.getLineNumber(content, pattern)
        });
      }
    }
  }

  checkImageAlt(content, fileResult) {
    // Vérifier les images sans attribut alt
    const imgWithoutAlt = /<img(?![^>]*alt=)[^>]*>/g;
    const matches = content.match(imgWithoutAlt);

    if (matches) {
      fileResult.issues.push({
        rule: 'images-alt',
        severity: 'critical',
        message: 'Images without alt text found',
        details: `${matches.length} <img> elements missing alt attribute`,
        wcag: WCAG_RULES['images-alt'],
        line: this.getLineNumber(content, imgWithoutAlt)
      });
    }

    // Vérifier les alt vides inappropriés
    const emptyAlt = /<img[^>]*alt=""[^>]*>/g;
    const emptyMatches = content.match(emptyAlt);

    if (emptyMatches) {
      fileResult.warnings.push({
        rule: 'images-alt',
        severity: 'warning',
        message: 'Images with empty alt text found',
        details: `${emptyMatches.length} images with alt="". Ensure these are decorative.`,
        wcag: WCAG_RULES['images-alt']
      });
    }
  }

  checkHeadingStructure(content, fileResult) {
    // Extraire tous les titres
    const headings = content.match(/<h[1-6][^>]*>/g) || [];

    if (headings.length === 0) return;

    const levels = headings.map(h => parseInt(h.match(/h([1-6])/)[1]));

    // Vérifier la séquence logique
    for (let i = 1; i < levels.length; i++) {
      const current = levels[i];
      const previous = levels[i - 1];

      if (current > previous + 1) {
        fileResult.issues.push({
          rule: 'heading-structure',
          severity: 'critical',
          message: 'Heading level skipped',
          details: `Heading level jumps from h${previous} to h${current}`,
          wcag: WCAG_RULES['heading-structure']
        });
      }
    }
  }

  checkKeyboardAccessibility(content, fileResult) {
    // Vérifier les éléments cliquables non-keyboard
    const problematicPatterns = [
      /on:click(?![^>]*tabindex)/g,
      /<div[^>]*on:click(?![^>]*role=["']button["'])/g
    ];

    for (const pattern of problematicPatterns) {
      const matches = content.match(pattern);
      if (matches) {
        fileResult.issues.push({
          rule: 'keyboard-accessible',
          severity: 'critical',
          message: 'Non-keyboard accessible interactive elements',
          details: `${matches.length} clickable elements may not be keyboard accessible`,
          wcag: WCAG_RULES['keyboard-accessible']
        });
      }
    }
  }

  checkFormLabels(content, fileResult) {
    // Vérifier les inputs sans labels
    const inputsWithoutLabels = /<input(?![^>]*aria-label)(?![^>]*aria-labelledby)(?![^>]*id="[^"]*")(?![^>]*type="hidden")/g;
    const matches = content.match(inputsWithoutLabels);

    if (matches) {
      fileResult.issues.push({
        rule: 'form-labels',
        severity: 'critical',
        message: 'Form inputs without labels',
        details: `${matches.length} input elements lack proper labeling`,
        wcag: WCAG_RULES['form-labels']
      });
    }

    // Vérifier les labels orphelins
    const labelsPattern = /<label[^>]*for="([^"]*)"[^>]*>/g;
    const labels = [...content.matchAll(labelsPattern)];

    for (const [, forId] of labels) {
      const hasMatchingInput = content.includes(`id="${forId}"`);
      if (!hasMatchingInput) {
        fileResult.warnings.push({
          rule: 'form-labels',
          severity: 'warning',
          message: 'Label without matching input',
          details: `Label for="${forId}" has no matching input`,
          wcag: WCAG_RULES['form-labels']
        });
      }
    }
  }

  checkAriaCompliance(content, fileResult) {
    // Vérifier les attributs ARIA invalides
    const ariaAttributes = content.match(/aria-[a-z]+="[^"]*"/g) || [];

    const validAriaAttributes = [
      'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden',
      'aria-expanded', 'aria-pressed', 'aria-checked', 'aria-selected',
      'aria-disabled', 'aria-required', 'aria-invalid', 'aria-live',
      'aria-atomic', 'aria-relevant', 'aria-busy', 'aria-controls',
      'aria-owns', 'aria-flowto', 'aria-haspopup', 'aria-level',
      'aria-multiline', 'aria-multiselectable', 'aria-orientation',
      'aria-readonly', 'aria-setsize', 'aria-sort', 'aria-valuemax',
      'aria-valuemin', 'aria-valuenow', 'aria-valuetext', 'aria-posinset'
    ];

    for (const attr of ariaAttributes) {
      const attrName = attr.split('=')[0];
      if (!validAriaAttributes.includes(attrName)) {
        fileResult.warnings.push({
          rule: 'aria-compliance',
          severity: 'warning',
          message: 'Potentially invalid ARIA attribute',
          details: `${attrName} may not be a valid ARIA attribute`,
          wcag: WCAG_RULES['aria-compliance']
        });
      }
    }

    // Vérifier les rôles ARIA invalides
    const rolePattern = /role="([^"]*)"/g;
    const roles = [...content.matchAll(rolePattern)];

    const validRoles = [
      'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
      'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
      'contentinfo', 'definition', 'dialog', 'directory', 'document',
      'form', 'grid', 'gridcell', 'group', 'heading', 'img', 'link',
      'list', 'listbox', 'listitem', 'log', 'main', 'marquee', 'math',
      'menu', 'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
      'navigation', 'note', 'option', 'presentation', 'progressbar',
      'radio', 'radiogroup', 'region', 'row', 'rowgroup', 'rowheader',
      'scrollbar', 'search', 'separator', 'slider', 'spinbutton',
      'status', 'tab', 'tablist', 'tabpanel', 'textbox', 'timer',
      'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'
    ];

    for (const [, role] of roles) {
      if (!validRoles.includes(role)) {
        fileResult.warnings.push({
          rule: 'aria-compliance',
          severity: 'warning',
          message: 'Invalid ARIA role',
          details: `role="${role}" is not a valid ARIA role`,
          wcag: WCAG_RULES['aria-compliance']
        });
      }
    }
  }

  checkFocusManagement(content, fileResult) {
    // Vérifier la gestion du focus
    const tabindexPattern = /tabindex="(-?\d+)"/g;
    const tabindexMatches = [...content.matchAll(tabindexPattern)];

    for (const [, value] of tabindexMatches) {
      const tabindex = parseInt(value);
      if (tabindex > 0) {
        fileResult.warnings.push({
          rule: 'focus-visible',
          severity: 'warning',
          message: 'Positive tabindex found',
          details: `tabindex="${tabindex}" disrupts natural tab order`,
          wcag: WCAG_RULES['focus-visible']
        });
      }
    }
  }

  checkSemanticMarkup(content, fileResult) {
    // Vérifier l'utilisation d'éléments sémantiques
    const semanticElements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'];
    const hasSemanticElements = semanticElements.some(element =>
      content.includes(`<${element}`) || content.includes(`</${element}>`)
    );

    if (!hasSemanticElements && content.includes('<div')) {
      fileResult.warnings.push({
        rule: 'valid-markup',
        severity: 'warning',
        message: 'Consider using semantic HTML elements',
        details: 'No semantic elements found, consider using header, nav, main, section, etc.',
        wcag: WCAG_RULES['valid-markup']
      });
    }
  }

  checkErrorHandling(content, fileResult) {
    // Vérifier la gestion des erreurs dans les formulaires
    const hasFormValidation = content.includes('error') || content.includes('invalid') || content.includes('required');
    const hasFormInputs = content.includes('<input') || content.includes('<select') || content.includes('<textarea');

    if (hasFormInputs && !hasFormValidation) {
      fileResult.warnings.push({
        rule: 'error-identification',
        severity: 'warning',
        message: 'Form without apparent error handling',
        details: 'Forms should provide clear error identification and instructions',
        wcag: WCAG_RULES['error-identification']
      });
    }
  }

  checkMotionAccessibility(content, fileResult) {
    // Vérifier le respect des préférences de mouvement
    const hasAnimations = content.includes('animate') || content.includes('transition') || content.includes('transform');
    const hasReducedMotion = content.includes('prefers-reduced-motion') || content.includes('reduced-motion');

    if (hasAnimations && !hasReducedMotion) {
      fileResult.warnings.push({
        rule: 'non-text-contrast',
        severity: 'warning',
        message: 'Animations without reduced motion consideration',
        details: 'Consider respecting prefers-reduced-motion for accessibility',
        wcag: WCAG_RULES['non-text-contrast']
      });
    }
  }

  getLineNumber(content, pattern) {
    const match = content.match(pattern);
    if (!match) return null;

    const beforeMatch = content.substring(0, content.indexOf(match[0]));
    return beforeMatch.split('\n').length;
  }

  evaluateCompliance() {
    console.log('\n📊 Evaluating WCAG compliance...');

    let totalIssues = 0;
    let criticalIssues = 0;
    let warningIssues = 0;

    for (const file of this.results.files) {
      totalIssues += file.issues.length + file.warnings.length;
      criticalIssues += file.issues.length;
      warningIssues += file.warnings.length;
    }

    this.results.summary.totalIssues = totalIssues;
    this.results.summary.criticalIssues = criticalIssues;
    this.results.summary.warningIssues = warningIssues;

    // Évaluer chaque règle WCAG
    for (const [ruleId, rule] of Object.entries(WCAG_RULES)) {
      const ruleIssues = this.results.files.flatMap(file =>
        [...file.issues, ...file.warnings].filter(issue => issue.rule === ruleId)
      );

      this.results.ruleResults[ruleId] = {
        rule,
        status: ruleIssues.length === 0 ? 'passed' : 'failed',
        issueCount: ruleIssues.length,
        issues: ruleIssues
      };

      if (ruleIssues.length === 0) {
        this.results.summary.passedRules++;
      } else {
        this.results.summary.failedRules++;
      }
    }

    console.log(`   ✓ Compliance evaluation complete\n`);
  }

  generateRecommendations() {
    const { criticalIssues, warningIssues } = this.results.summary;

    // Recommandations basées sur les issues critiques
    if (criticalIssues > 0) {
      this.results.recommendations.push({
        priority: 'high',
        category: 'Critical Issues',
        title: 'Address Critical Accessibility Issues',
        description: `${criticalIssues} critical accessibility issues must be resolved`,
        actions: [
          'Review all critical issues identified in the detailed report',
          'Prioritize keyboard accessibility and form labeling fixes',
          'Implement proper ARIA attributes where needed',
          'Test with screen readers after fixes'
        ]
      });
    }

    // Recommandations pour les warnings
    if (warningIssues > 0) {
      this.results.recommendations.push({
        priority: 'medium',
        category: 'Improvements',
        title: 'Enhance Accessibility Features',
        description: `${warningIssues} accessibility improvements identified`,
        actions: [
          'Review warning-level issues for enhancement opportunities',
          'Consider implementing semantic HTML elements',
          'Add motion preference handling for animations',
          'Improve color contrast where possible'
        ]
      });
    }

    // Recommandations générales
    this.results.recommendations.push({
      priority: 'low',
      category: 'Best Practices',
      title: 'Implement Accessibility Testing Strategy',
      description: 'Establish ongoing accessibility compliance',
      actions: [
        'Integrate accessibility testing into CI/CD pipeline',
        'Train development team on WCAG guidelines',
        'Conduct regular manual testing with assistive technologies',
        'Consider automated accessibility testing tools'
      ]
    });
  }

  displayReport() {
    const { summary, ruleResults } = this.results;

    console.log('♿ ACCESSIBILITY AUDIT REPORT');
    console.log('==============================\n');

    // Résumé exécutif
    console.log('📋 EXECUTIVE SUMMARY:');
    console.log(`   • Files analyzed: ${summary.totalFiles}`);
    console.log(`   • Total issues: ${summary.totalIssues}`);
    console.log(`   • Critical issues: ${summary.criticalIssues}`);
    console.log(`   • Warning issues: ${summary.warningIssues}`);
    console.log(`   • WCAG rules passed: ${summary.passedRules}/${summary.passedRules + summary.failedRules}\n`);

    // Score de conformité
    const complianceScore = this.calculateComplianceScore();
    console.log(`🎯 WCAG ${CONFIG.wcagVersion} ${CONFIG.wcagLevel} COMPLIANCE: ${complianceScore}%`);
    console.log(`   ${complianceScore >= 95 ? '🟢 Excellent' : complianceScore >= 80 ? '🟡 Good' : '🔴 Needs Improvement'}\n`);

    // Détails par règle
    console.log('📏 WCAG RULES EVALUATION:');
    for (const [ruleId, result] of Object.entries(ruleResults)) {
      const status = result.status === 'passed' ? '✅' : '❌';
      console.log(`   ${status} ${ruleId}: ${result.rule.description}`);
      if (result.issueCount > 0) {
        console.log(`      → ${result.issueCount} issues found`);
      }
    }
    console.log();

    // Top issues par fichier
    if (summary.totalIssues > 0) {
      console.log('📁 FILES WITH ISSUES:');
      const filesWithIssues = this.results.files
        .filter(file => file.issues.length > 0 || file.warnings.length > 0)
        .sort((a, b) => (b.issues.length + b.warnings.length) - (a.issues.length + a.warnings.length))
        .slice(0, 10);

      for (const file of filesWithIssues) {
        console.log(`   📄 ${file.path}`);
        console.log(`      🔴 ${file.issues.length} critical, 🟡 ${file.warnings.length} warnings`);

        // Afficher les 3 premiers issues
        const topIssues = [...file.issues, ...file.warnings].slice(0, 3);
        for (const issue of topIssues) {
          const icon = issue.severity === 'critical' ? '🔴' : '🟡';
          console.log(`      ${icon} ${issue.message}`);
        }
        console.log();
      }
    }

    // Recommandations
    console.log('💡 RECOMMENDATIONS:');
    for (const rec of this.results.recommendations) {
      const priorityIcon = rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢';
      console.log(`   ${priorityIcon} ${rec.title}`);
      console.log(`      ${rec.description}`);
      for (const action of rec.actions) {
        console.log(`      → ${action}`);
      }
      console.log();
    }
  }

  calculateComplianceScore() {
    const { passedRules, failedRules } = this.results.summary;
    const totalRules = passedRules + failedRules;

    if (totalRules === 0) return 100;

    return Math.round((passedRules / totalRules) * 100);
  }

  saveReport() {
    const reportDir = path.dirname(CONFIG.reportFile);
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }

    fs.writeFileSync(CONFIG.reportFile, JSON.stringify(this.results, null, 2));
    console.log(`📄 Detailed report saved: ${CONFIG.reportFile}`);
  }
}

// Exécution principale
async function main() {
  const auditor = new AccessibilityAuditor();
  await auditor.audit();
}

// Exécuter si script appelé directement
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { AccessibilityAuditor };
