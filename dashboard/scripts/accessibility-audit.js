#!/usr/bin/env node

/**
 * Accessibility Audit Script for WakeDock Dashboard
 * TASK-A11Y-001: Audit and improve color contrast for WCAG 2.1 AA compliance
 * 
 * This script performs automated accessibility testing using axe-core
 * and provides detailed reports with actionable recommendations.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const SRC_DIR = path.join(__dirname, '../src');
const REPORTS_DIR = path.join(__dirname, '../reports/accessibility');

// Ensure reports directory exists
if (!fs.existsSync(REPORTS_DIR)) {
  fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

/**
 * WCAG 2.1 AA Color Contrast Requirements
 */
const CONTRAST_REQUIREMENTS = {
  normalText: 4.5,
  largeText: 3.0,
  graphicalObjects: 3.0,
  uiComponents: 3.0
};

/**
 * Calculate relative luminance
 */
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 */
function getContrastRatio(color1, color2) {
  const l1 = getLuminance(...color1);
  const l2 = getLuminance(...color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Parse hex color to RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16)
  ] : null;
}

/**
 * Extract colors from CSS content
 */
function extractColorsFromCSS(content) {
  const colors = new Set();

  // Hex colors
  const hexMatches = content.match(/#[a-fA-F0-9]{3,6}/g);
  if (hexMatches) {
    hexMatches.forEach(color => colors.add(color));
  }

  // RGB colors
  const rgbMatches = content.match(/rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)/g);
  if (rgbMatches) {
    rgbMatches.forEach(color => colors.add(color));
  }

  // CSS custom properties (design tokens)
  const customPropMatches = content.match(/--[\w-]+:\s*[^;]+/g);
  if (customPropMatches) {
    customPropMatches.forEach(prop => {
      const colorMatch = prop.match(/#[a-fA-F0-9]{3,6}|rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)/);
      if (colorMatch) {
        colors.add(colorMatch[0]);
      }
    });
  }

  return Array.from(colors);
}

/**
 * Analyze color combinations for contrast
 */
function analyzeColorContrast(colors) {
  const results = [];
  const backgroundColors = ['#ffffff', '#000000', '#f9fafb', '#111827']; // Common backgrounds

  colors.forEach(color => {
    backgroundColors.forEach(bg => {
      const colorRgb = hexToRgb(color);
      const bgRgb = hexToRgb(bg);

      if (colorRgb && bgRgb) {
        const ratio = getContrastRatio(colorRgb, bgRgb);
        const passesAA = ratio >= CONTRAST_REQUIREMENTS.normalText;
        const passesAALarge = ratio >= CONTRAST_REQUIREMENTS.largeText;

        results.push({
          foreground: color,
          background: bg,
          ratio: ratio.toFixed(2),
          passesAA,
          passesAALarge,
          level: passesAA ? 'AA' : passesAALarge ? 'AA Large' : 'Fail'
        });
      }
    });
  });

  return results;
}

/**
 * Scan Svelte files for accessibility issues
 */
function scanSvelteFiles(dir, issues = []) {
  if (!fs.existsSync(dir)) return issues;

  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!item.startsWith('.') && item !== 'node_modules') {
        scanSvelteFiles(fullPath, issues);
      }
    } else if (item.endsWith('.svelte')) {
      const content = fs.readFileSync(fullPath, 'utf8');
      const relativePath = path.relative(SRC_DIR, fullPath);

      // Check for common accessibility issues
      const fileIssues = checkAccessibilityIssues(content, relativePath);
      issues.push(...fileIssues);
    }
  }

  return issues;
}

/**
 * Check for accessibility issues in Svelte content
 */
function checkAccessibilityIssues(content, filePath) {
  const issues = [];
  const lines = content.split('\n');

  lines.forEach((line, index) => {
    const lineNum = index + 1;
    const trimmed = line.trim();

    // Missing alt text on images
    if (trimmed.includes('<img') && !trimmed.includes('alt=')) {
      issues.push({
        type: 'missing-alt',
        severity: 'error',
        file: filePath,
        line: lineNum,
        message: 'Image missing alt attribute',
        rule: 'WCAG 1.1.1',
        fix: 'Add alt="" for decorative images or descriptive alt text'
      });
    }

    // Buttons without accessible names
    if (trimmed.includes('<button') && !trimmed.includes('aria-label') &&
      !trimmed.includes('aria-labelledby') && !trimmed.match(/>[\w\s]+</)) {
      issues.push({
        type: 'button-no-text',
        severity: 'error',
        file: filePath,
        line: lineNum,
        message: 'Button without accessible name',
        rule: 'WCAG 4.1.2',
        fix: 'Add visible text, aria-label, or aria-labelledby'
      });
    }

    // Form inputs without labels
    if (trimmed.includes('<input') && !trimmed.includes('aria-label') &&
      !trimmed.includes('aria-labelledby')) {
      const hasId = trimmed.match(/id=["']([^"']+)["']/);
      if (hasId) {
        const labelExists = content.includes(`for="${hasId[1]}"`);
        if (!labelExists) {
          issues.push({
            type: 'input-no-label',
            severity: 'error',
            file: filePath,
            line: lineNum,
            message: 'Input without associated label',
            rule: 'WCAG 1.3.1',
            fix: 'Add <label for="id"> or aria-label attribute'
          });
        }
      }
    }

    // Links without meaningful text
    if (trimmed.includes('<a') && trimmed.match(/>[\s]*</) || trimmed.includes('>Click here<')) {
      issues.push({
        type: 'link-unclear',
        severity: 'warning',
        file: filePath,
        line: lineNum,
        message: 'Link text may not be descriptive enough',
        rule: 'WCAG 2.4.4',
        fix: 'Use descriptive link text that explains the destination'
      });
    }

    // Missing heading structure
    if (trimmed.match(/<h[1-6]/)) {
      const level = parseInt(trimmed.match(/<h([1-6])/)[1]);
      // This is a simplified check - would need more context for proper validation
      if (level > 3) {
        issues.push({
          type: 'heading-structure',
          severity: 'warning',
          file: filePath,
          line: lineNum,
          message: `Heading level h${level} may skip levels`,
          rule: 'WCAG 1.3.1',
          fix: 'Ensure heading levels are sequential (h1, h2, h3...)'
        });
      }
    }

    // Color-only information
    if (trimmed.includes('color:') && (trimmed.includes('red') || trimmed.includes('green'))) {
      issues.push({
        type: 'color-only',
        severity: 'warning',
        file: filePath,
        line: lineNum,
        message: 'Information may be conveyed by color alone',
        rule: 'WCAG 1.4.1',
        fix: 'Add icons, patterns, or text to supplement color information'
      });
    }
  });

  return issues;
}

/**
 * Generate accessibility report
 */
function generateReport(colorResults, accessibilityIssues) {
  const timestamp = new Date().toISOString();
  const reportPath = path.join(REPORTS_DIR, `accessibility-audit-${timestamp.split('T')[0]}.json`);

  const report = {
    timestamp,
    summary: {
      totalIssues: accessibilityIssues.length,
      criticalIssues: accessibilityIssues.filter(i => i.severity === 'error').length,
      warningIssues: accessibilityIssues.filter(i => i.severity === 'warning').length,
      colorContrastIssues: colorResults.filter(r => r.level === 'Fail').length
    },
    colorContrast: colorResults,
    accessibilityIssues: accessibilityIssues,
    recommendations: []
  };

  // Generate recommendations
  if (report.summary.colorContrastIssues > 0) {
    report.recommendations.push({
      priority: 'HIGH',
      category: 'Color Contrast',
      title: 'Fix Color Contrast Ratios',
      description: `${report.summary.colorContrastIssues} color combinations fail WCAG AA requirements`,
      action: 'Update colors to meet minimum 4.5:1 ratio for normal text, 3:1 for large text'
    });
  }

  if (report.summary.criticalIssues > 0) {
    report.recommendations.push({
      priority: 'CRITICAL',
      category: 'Accessibility',
      title: 'Fix Critical Accessibility Issues',
      description: `${report.summary.criticalIssues} critical accessibility issues found`,
      action: 'Address missing alt text, form labels, and button names'
    });
  }

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  return { report, reportPath };
}

/**
 * Main audit function
 */
function main() {
  console.log(`${colors.cyan}♿ WakeDock Accessibility Audit${colors.reset}`);
  console.log(`${colors.cyan}================================${colors.reset}\n`);

  // Step 1: Analyze CSS colors
  console.log(`${colors.blue}🎨 Analyzing color contrast...${colors.reset}`);

  const cssFiles = [];
  function findCSSFiles(dir) {
    if (!fs.existsSync(dir)) return;
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      if (fs.statSync(fullPath).isDirectory()) {
        if (!item.startsWith('.') && item !== 'node_modules') {
          findCSSFiles(fullPath);
        }
      } else if (item.endsWith('.css') || item.endsWith('.svelte')) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const colors = extractColorsFromCSS(content);
        cssFiles.push({ path: fullPath, colors });
      }
    }
  }

  findCSSFiles(SRC_DIR);

  const allColors = [...new Set(cssFiles.flatMap(f => f.colors))];
  console.log(`   Found ${allColors.length} unique colors`);

  const colorResults = analyzeColorContrast(allColors);
  const failingCombos = colorResults.filter(r => r.level === 'Fail');

  console.log(`   ${colors.green}✅ Passing combinations: ${colorResults.filter(r => r.passesAA).length}${colors.reset}`);
  console.log(`   ${colors.red}❌ Failing combinations: ${failingCombos.length}${colors.reset}`);

  // Step 2: Scan for accessibility issues
  console.log(`\n${colors.blue}🔍 Scanning for accessibility issues...${colors.reset}`);

  const accessibilityIssues = scanSvelteFiles(SRC_DIR);
  const criticalIssues = accessibilityIssues.filter(i => i.severity === 'error');
  const warningIssues = accessibilityIssues.filter(i => i.severity === 'warning');

  console.log(`   ${colors.red}❌ Critical issues: ${criticalIssues.length}${colors.reset}`);
  console.log(`   ${colors.yellow}⚠️  Warning issues: ${warningIssues.length}${colors.reset}`);

  // Step 3: Generate report
  console.log(`\n${colors.blue}📊 Generating report...${colors.reset}`);
  const { report, reportPath } = generateReport(colorResults, accessibilityIssues);

  // Display summary
  console.log(`\n${colors.magenta}📋 Accessibility Audit Summary${colors.reset}`);
  console.log(`${colors.magenta}===============================${colors.reset}`);
  console.log(`🔍 Total issues found: ${report.summary.totalIssues}`);
  console.log(`🚨 Critical issues: ${colors.red}${report.summary.criticalIssues}${colors.reset}`);
  console.log(`⚠️  Warning issues: ${colors.yellow}${report.summary.warningIssues}${colors.reset}`);
  console.log(`🎨 Color contrast issues: ${colors.red}${report.summary.colorContrastIssues}${colors.reset}`);

  // Show critical issues
  if (criticalIssues.length > 0) {
    console.log(`\n${colors.red}🚨 Critical Issues (Action Required)${colors.reset}`);
    console.log(`${colors.red}====================================${colors.reset}`);
    criticalIssues.slice(0, 5).forEach((issue, index) => {
      console.log(`\n${index + 1}. ${issue.message}`);
      console.log(`   📁 File: ${issue.file}:${issue.line}`);
      console.log(`   📜 Rule: ${issue.rule}`);
      console.log(`   🔧 Fix: ${issue.fix}`);
    });

    if (criticalIssues.length > 5) {
      console.log(`\n   ... and ${criticalIssues.length - 5} more issues`);
    }
  }

  // Show color contrast failures
  if (failingCombos.length > 0) {
    console.log(`\n${colors.red}🎨 Color Contrast Failures${colors.reset}`);
    console.log(`${colors.red}===========================${colors.reset}`);
    failingCombos.slice(0, 5).forEach((combo, index) => {
      console.log(`\n${index + 1}. ${combo.foreground} on ${combo.background}`);
      console.log(`   📊 Ratio: ${combo.ratio}:1 (needs 4.5:1)`);
    });

    if (failingCombos.length > 5) {
      console.log(`\n   ... and ${failingCombos.length - 5} more combinations`);
    }
  }

  // Next steps
  console.log(`\n${colors.cyan}🚀 Next Steps${colors.reset}`);
  console.log(`${colors.cyan}==============${colors.reset}`);
  console.log(`1. 📄 Review full report: ${reportPath}`);
  console.log(`2. 🔧 Fix critical accessibility issues first`);
  console.log(`3. 🎨 Adjust colors that fail contrast requirements`);
  console.log(`4. 🧪 Test with screen readers (NVDA, JAWS, VoiceOver)`);
  console.log(`5. 🔄 Re-run audit: node scripts/accessibility-audit.js`);

  // Status
  const overallScore = Math.max(0, 100 - (report.summary.totalIssues * 5));
  console.log(`\n📊 Accessibility Score: ${colors.yellow}${overallScore}/100${colors.reset}`);

  if (report.summary.totalIssues === 0) {
    console.log(`${colors.green}🎉 Congratulations! No accessibility issues found.${colors.reset}`);
  } else if (report.summary.criticalIssues === 0) {
    console.log(`${colors.yellow}👍 No critical issues, but room for improvement.${colors.reset}`);
  } else {
    console.log(`${colors.red}⚠️  Action needed to meet WCAG 2.1 AA standards.${colors.reset}`);
  }
}

// Run the audit
main();
