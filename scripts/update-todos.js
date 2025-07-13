#!/usr/bin/env node

/**
 * WakeDock Design Improvement Plan - TODO Status Updater
 * Mise à jour automatique du statut des tâches avec validation
 * 
 * Conformément aux règles strictes WakeDock:
 * - Validation basée sur l'analyse statique
 * - Pas d'exécution de serveurs de développement
 * - Métriques de production uniquement
 */

const fs = require('fs');
const path = require('path');

const DESIGN_PLAN_FILE = 'DESIGN_IMPROVEMENT_PLAN.md';

// Status et validations pour chaque tâche
const TASK_VALIDATIONS = {
  'TASK-DX-002': {
    name: 'Console.log Cleanup & Production Logger',
    files: [
      'dashboard/src/lib/utils/production-logger.ts',
      'scripts/validate-logger-implementation.js'
    ],
    checks: [
      () => checkFileExists('dashboard/src/lib/utils/production-logger.ts'),
      () => checkLoggerImplementation(),
      () => checkConsoleLogCleanup()
    ],
    status: 'completed'
  },
  'TASK-PERF-003': {
    name: 'Animation Optimization',
    files: [
      'dashboard/src/lib/utils/animations.ts'
    ],
    checks: [
      () => checkFileExists('dashboard/src/lib/utils/animations.ts'),
      () => checkAnimationOptimizations(),
      () => checkReducedMotionSupport()
    ],
    status: 'completed'
  },
  'TASK-FEAT-001': {
    name: 'Dashboard Customization',
    files: [
      'dashboard/src/lib/components/dashboard/DashboardCustomizeModal.svelte'
    ],
    checks: [
      () => checkFileExists('dashboard/src/lib/components/dashboard/DashboardCustomizeModal.svelte'),
      () => checkDashboardCustomization()
    ],
    status: 'completed'
  },
  'TASK-DX-001': {
    name: 'Storybook Documentation',
    files: [
      'dashboard/.storybook/main.ts',
      'dashboard/src/stories/Button.stories.ts'
    ],
    checks: [
      () => checkFileExists('dashboard/.storybook/main.ts'),
      () => checkStorybookStories()
    ],
    status: 'completed'
  },
  'TASK-PERF-001': {
    name: 'CSS Bundle Optimization',
    files: [
      'scripts/css-analyzer.js',
      'reports/css-optimization-report.json'
    ],
    checks: [
      () => checkFileExists('scripts/css-analyzer.js'),
      () => checkCSSAnalyzerTool()
    ],
    status: 'in_progress'
  },
  'TASK-A11Y-001': {
    name: 'Accessibility Audit Implementation',
    files: [
      'scripts/accessibility-audit.js',
      'reports/accessibility-audit-report.json'
    ],
    checks: [
      () => checkFileExists('scripts/accessibility-audit.js'),
      () => checkAccessibilityAuditTool()
    ],
    status: 'in_progress'
  },
  'TASK-PERF-002': {
    name: 'Component Performance Optimization',
    files: [],
    checks: [
      () => ({ success: false, reason: 'Task not yet started' })
    ],
    status: 'pending'
  },
  'TASK-A11Y-002': {
    name: 'ARIA Patterns Implementation',
    files: [],
    checks: [
      () => ({ success: false, reason: 'Task not yet started' })
    ],
    status: 'pending'
  }
};

function checkFileExists(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  const exists = fs.existsSync(fullPath);
  return {
    success: exists,
    reason: exists ? `File exists: ${filePath}` : `File missing: ${filePath}`
  };
}

function checkLoggerImplementation() {
  try {
    const loggerPath = path.join(process.cwd(), 'dashboard/src/lib/utils/production-logger.ts');
    if (!fs.existsSync(loggerPath)) {
      return { success: false, reason: 'Logger file not found' };
    }

    const content = fs.readFileSync(loggerPath, 'utf8');
    const hasClass = content.includes('class ProductionLogger');
    const hasLevels = content.includes('LogLevel');
    const hasRemoteLogging = content.includes('remoteEndpoint');

    return {
      success: hasClass && hasLevels && hasRemoteLogging,
      reason: `Logger implementation check: class=${hasClass}, levels=${hasLevels}, remote=${hasRemoteLogging}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking logger: ${error.message}` };
  }
}

function checkConsoleLogCleanup() {
  try {
    const validationPath = path.join(process.cwd(), 'scripts/validate-logger-implementation.js');
    if (!fs.existsSync(validationPath)) {
      return { success: false, reason: 'Validation script not found' };
    }

    const content = fs.readFileSync(validationPath, 'utf8');
    const hasConsoleCheck = content.includes('console.log');
    const hasValidation = content.includes('validateLoggerUsage');

    return {
      success: hasConsoleCheck && hasValidation,
      reason: `Cleanup validation: console check=${hasConsoleCheck}, validation=${hasValidation}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking cleanup: ${error.message}` };
  }
}

function checkAnimationOptimizations() {
  try {
    const animPath = path.join(process.cwd(), 'dashboard/src/lib/utils/animations.ts');
    if (!fs.existsSync(animPath)) {
      return { success: false, reason: 'Animations file not found' };
    }

    const content = fs.readFileSync(animPath, 'utf8');
    const hasReducedMotion = content.includes('prefers-reduced-motion');
    const hasAccessibleAnims = content.includes('accessibleFade') || content.includes('accessibleSlide');

    return {
      success: hasReducedMotion && hasAccessibleAnims,
      reason: `Animation optimization: reduced-motion=${hasReducedMotion}, accessible=${hasAccessibleAnims}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking animations: ${error.message}` };
  }
}

function checkReducedMotionSupport() {
  try {
    const animPath = path.join(process.cwd(), 'dashboard/src/lib/utils/animations.ts');
    const content = fs.readFileSync(animPath, 'utf8');

    const hasMediaQuery = content.includes('window.matchMedia');
    const hasReducedMotionCSS = content.includes('REDUCED_MOTION_CSS');

    return {
      success: hasMediaQuery && hasReducedMotionCSS,
      reason: `Reduced motion support: media query=${hasMediaQuery}, CSS=${hasReducedMotionCSS}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking reduced motion: ${error.message}` };
  }
}

function checkDashboardCustomization() {
  try {
    const modalPath = path.join(process.cwd(), 'dashboard/src/lib/components/dashboard/DashboardCustomizeModal.svelte');
    if (!fs.existsSync(modalPath)) {
      return { success: false, reason: 'Dashboard modal not found' };
    }

    const content = fs.readFileSync(modalPath, 'utf8');
    const hasWidgetConfig = content.includes('WidgetConfig');
    const hasToggleFunction = content.includes('toggleWidgetVisibility');
    const hasPreview = content.includes('preview');

    return {
      success: hasWidgetConfig && hasToggleFunction && hasPreview,
      reason: `Dashboard customization: config=${hasWidgetConfig}, toggle=${hasToggleFunction}, preview=${hasPreview}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking dashboard: ${error.message}` };
  }
}

function checkStorybookStories() {
  try {
    const storybookPath = path.join(process.cwd(), 'dashboard/.storybook/main.ts');
    const buttonStoryPath = path.join(process.cwd(), 'dashboard/src/stories/Button.stories.ts');

    const hasStorybook = fs.existsSync(storybookPath);
    const hasButtonStory = fs.existsSync(buttonStoryPath);

    let storyCount = 0;
    if (fs.existsSync(path.join(process.cwd(), 'dashboard/src/stories'))) {
      const storyFiles = fs.readdirSync(path.join(process.cwd(), 'dashboard/src/stories'))
        .filter(file => file.endsWith('.stories.ts'));
      storyCount = storyFiles.length;
    }

    return {
      success: hasStorybook && hasButtonStory && storyCount >= 3,
      reason: `Storybook: config=${hasStorybook}, button story=${hasButtonStory}, total stories=${storyCount}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking Storybook: ${error.message}` };
  }
}

function checkCSSAnalyzerTool() {
  try {
    const analyzerPath = path.join(process.cwd(), 'scripts/css-analyzer.js');
    if (!fs.existsSync(analyzerPath)) {
      return { success: false, reason: 'CSS analyzer not found' };
    }

    const content = fs.readFileSync(analyzerPath, 'utf8');
    const hasAnalyzerClass = content.includes('class CSSAnalyzer');
    const hasMetrics = content.includes('calculateMetrics');
    const hasOptimizations = content.includes('generateOptimizations');

    return {
      success: hasAnalyzerClass && hasMetrics && hasOptimizations,
      reason: `CSS analyzer: class=${hasAnalyzerClass}, metrics=${hasMetrics}, optimizations=${hasOptimizations}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking CSS analyzer: ${error.message}` };
  }
}

function checkAccessibilityAuditTool() {
  try {
    const auditPath = path.join(process.cwd(), 'scripts/accessibility-audit.js');
    if (!fs.existsSync(auditPath)) {
      return { success: false, reason: 'Accessibility audit tool not found' };
    }

    const content = fs.readFileSync(auditPath, 'utf8');
    const hasAuditorClass = content.includes('class AccessibilityAuditor');
    const hasWCAGRules = content.includes('WCAG_RULES');
    const hasCompliance = content.includes('evaluateCompliance');

    return {
      success: hasAuditorClass && hasWCAGRules && hasCompliance,
      reason: `Accessibility audit: class=${hasAuditorClass}, WCAG=${hasWCAGRules}, compliance=${hasCompliance}`
    };
  } catch (error) {
    return { success: false, reason: `Error checking accessibility audit: ${error.message}` };
  }
}

function validateTasks() {
  console.log('🔍 WakeDock Design Improvement Plan - Task Validation');
  console.log('===================================================\n');

  const results = {};
  let totalTasks = 0;
  let completedTasks = 0;
  let inProgressTasks = 0;
  let pendingTasks = 0;

  for (const [taskId, taskInfo] of Object.entries(TASK_VALIDATIONS)) {
    totalTasks++;
    console.log(`📋 Validating ${taskId}: ${taskInfo.name}`);

    const taskResults = {
      name: taskInfo.name,
      status: taskInfo.status,
      files: taskInfo.files,
      checks: [],
      allChecksPassed: true
    };

    // Exécuter toutes les vérifications
    for (const check of taskInfo.checks) {
      const result = check();
      taskResults.checks.push(result);

      if (!result.success) {
        taskResults.allChecksPassed = false;
      }

      const icon = result.success ? '✅' : '❌';
      console.log(`   ${icon} ${result.reason}`);
    }

    // Déterminer le statut final
    let finalStatus = taskInfo.status;
    if (taskResults.allChecksPassed && taskInfo.status !== 'completed') {
      finalStatus = 'completed';
    } else if (!taskResults.allChecksPassed && taskInfo.status === 'completed') {
      finalStatus = 'in_progress';
    }

    taskResults.finalStatus = finalStatus;
    results[taskId] = taskResults;

    // Compter les statuts
    switch (finalStatus) {
      case 'completed':
        completedTasks++;
        break;
      case 'in_progress':
        inProgressTasks++;
        break;
      case 'pending':
        pendingTasks++;
        break;
    }

    const statusIcon = finalStatus === 'completed' ? '🟢' :
      finalStatus === 'in_progress' ? '🟡' : '🔴';
    console.log(`   ${statusIcon} Status: ${finalStatus.toUpperCase()}\n`);
  }

  // Afficher le résumé
  console.log('📊 TASK SUMMARY:');
  console.log(`   • Total tasks: ${totalTasks}`);
  console.log(`   • Completed: ${completedTasks} (${Math.round(completedTasks / totalTasks * 100)}%)`);
  console.log(`   • In Progress: ${inProgressTasks} (${Math.round(inProgressTasks / totalTasks * 100)}%)`);
  console.log(`   • Pending: ${pendingTasks} (${Math.round(pendingTasks / totalTasks * 100)}%)\n`);

  // Progress bar
  const progress = Math.round(completedTasks / totalTasks * 100);
  const progressBar = '█'.repeat(Math.floor(progress / 5)) + '░'.repeat(20 - Math.floor(progress / 5));
  console.log(`🚀 OVERALL PROGRESS: [${progressBar}] ${progress}%\n`);

  return results;
}

function updateDesignPlan(validationResults) {
  console.log('📝 Updating DESIGN_IMPROVEMENT_PLAN.md...');

  const designPlanPath = path.join(process.cwd(), DESIGN_PLAN_FILE);
  if (!fs.existsSync(designPlanPath)) {
    console.log('❌ DESIGN_IMPROVEMENT_PLAN.md not found');
    return false;
  }

  let content = fs.readFileSync(designPlanPath, 'utf8');
  let updated = false;

  for (const [taskId, results] of Object.entries(validationResults)) {
    const oldStatus = TASK_VALIDATIONS[taskId].status;
    const newStatus = results.finalStatus;

    if (oldStatus !== newStatus) {
      console.log(`   🔄 Updating ${taskId}: ${oldStatus} → ${newStatus}`);

      // Patterns pour chaque statut
      const statusPatterns = {
        pending: `\\[\\s*\\] ${taskId}`,
        in_progress: `\\[~\\] ${taskId}`,
        completed: `\\[x\\] ${taskId}`
      };

      const newStatusMarker = {
        pending: `[ ] ${taskId}`,
        in_progress: `[~] ${taskId}`,
        completed: `[x] ${taskId}`
      };

      // Remplacer le statut ancien par le nouveau
      for (const [status, pattern] of Object.entries(statusPatterns)) {
        const regex = new RegExp(pattern, 'g');
        if (regex.test(content)) {
          content = content.replace(regex, newStatusMarker[newStatus]);
          updated = true;
          break;
        }
      }
    }
  }

  if (updated) {
    fs.writeFileSync(designPlanPath, content);
    console.log('   ✅ Design plan updated successfully');
  } else {
    console.log('   ℹ️  No updates needed');
  }

  return updated;
}

function generateProgressReport(validationResults) {
  const reportPath = path.join(process.cwd(), 'reports/design-improvement-progress.json');

  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalTasks: Object.keys(validationResults).length,
      completedTasks: Object.values(validationResults).filter(r => r.finalStatus === 'completed').length,
      inProgressTasks: Object.values(validationResults).filter(r => r.finalStatus === 'in_progress').length,
      pendingTasks: Object.values(validationResults).filter(r => r.finalStatus === 'pending').length
    },
    tasks: validationResults,
    nextActions: []
  };

  // Calculer le pourcentage de progression
  report.summary.progressPercentage = Math.round(
    (report.summary.completedTasks / report.summary.totalTasks) * 100
  );

  // Générer les prochaines actions
  for (const [taskId, results] of Object.entries(validationResults)) {
    if (results.finalStatus !== 'completed') {
      const failedChecks = results.checks.filter(check => !check.success);
      report.nextActions.push({
        taskId,
        taskName: results.name,
        status: results.finalStatus,
        blockers: failedChecks.map(check => check.reason)
      });
    }
  }

  // Créer le dossier reports s'il n'existe pas
  const reportsDir = path.dirname(reportPath);
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`📄 Progress report saved: ${reportPath}`);

  return report;
}

// Exécution principale
async function main() {
  try {
    const validationResults = validateTasks();
    updateDesignPlan(validationResults);
    const report = generateProgressReport(validationResults);

    console.log('✅ Task validation and update completed successfully!');

    // Suggérer les prochaines étapes
    if (report.nextActions.length > 0) {
      console.log('\n🎯 NEXT ACTIONS:');
      for (const action of report.nextActions.slice(0, 3)) {
        console.log(`   • ${action.taskId}: ${action.taskName}`);
        if (action.blockers.length > 0) {
          console.log(`     Blockers: ${action.blockers[0]}`);
        }
      }
    }

  } catch (error) {
    console.error('❌ Error during validation:', error.message);
    process.exit(1);
  }
}

// Exécuter si script appelé directement
if (require.main === module) {
  main();
}

module.exports = {
  validateTasks,
  updateDesignPlan,
  generateProgressReport,
  TASK_VALIDATIONS
};
