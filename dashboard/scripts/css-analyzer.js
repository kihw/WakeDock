#!/usr/bin/env node

/**
 * CSS Bundle Analyzer and Optimizer for WakeDock Dashboard
 * TASK-PERF-001: Optimize CSS bundle size from ~60KB to <30KB
 * 
 * This script analyzes the CSS bundle, identifies optimizations,
 * and provides actionable recommendations for size reduction.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BUILD_DIR = path.join(__dirname, '../build');
const SRC_DIR = path.join(__dirname, '../src');
const CSS_EXTENSIONS = ['.css', '.scss', '.sass'];

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
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Get all CSS files recursively
 */
function getAllCSSFiles(dir, files = []) {
  if (!fs.existsSync(dir)) {
    return files;
  }

  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!item.startsWith('.') && item !== 'node_modules') {
        getAllCSSFiles(fullPath, files);
      }
    } else if (CSS_EXTENSIONS.some(ext => item.endsWith(ext))) {
      files.push({
        path: fullPath,
        relativePath: path.relative(SRC_DIR, fullPath),
        size: stat.size,
        content: fs.readFileSync(fullPath, 'utf8')
      });
    }
  }

  return files;
}

/**
 * Analyze CSS content for optimization opportunities
 */
function analyzeCSSContent(content) {
  const analysis = {
    totalLines: content.split('\n').length,
    duplicateSelectors: 0,
    unusedPrefixes: 0,
    largeFontSizes: 0,
    complexSelectors: 0,
    inlineStyles: 0,
    mediaQueries: 0,
    customProperties: 0,
    tailwindClasses: 0
  };

  const lines = content.split('\n');
  const selectors = new Set();

  for (const line of lines) {
    const trimmed = line.trim();

    // Count selectors and detect duplicates
    if (trimmed.includes('{') && !trimmed.startsWith('/*')) {
      const selector = trimmed.split('{')[0].trim();
      if (selectors.has(selector)) {
        analysis.duplicateSelectors++;
      }
      selectors.add(selector);

      // Complex selectors (more than 3 levels)
      if (selector.split(' ').length > 3) {
        analysis.complexSelectors++;
      }
    }

    // Vendor prefixes
    if (trimmed.includes('-webkit-') || trimmed.includes('-moz-') ||
      trimmed.includes('-ms-') || trimmed.includes('-o-')) {
      analysis.unusedPrefixes++;
    }

    // Large font sizes
    if (trimmed.match(/font-size:\s*[5-9]\d+px/) || trimmed.match(/font-size:\s*[1-9]\d+rem/)) {
      analysis.largeFontSizes++;
    }

    // Media queries
    if (trimmed.includes('@media')) {
      analysis.mediaQueries++;
    }

    // CSS custom properties
    if (trimmed.includes('--')) {
      analysis.customProperties++;
    }

    // Tailwind-like utility classes
    if (trimmed.match(/\.(m|p|w|h|text|bg|border|flex|grid)-/)) {
      analysis.tailwindClasses++;
    }
  }

  return analysis;
}

/**
 * Generate optimization recommendations
 */
function generateRecommendations(cssFiles, totalSize) {
  const recommendations = [];
  let potentialSavings = 0;

  // 1. Duplicate removal
  const totalDuplicates = cssFiles.reduce((sum, file) =>
    sum + file.analysis.duplicateSelectors, 0);
  if (totalDuplicates > 10) {
    const savings = Math.floor(totalSize * 0.15); // Estimate 15% savings
    recommendations.push({
      priority: 'HIGH',
      title: 'Remove Duplicate CSS Selectors',
      description: `Found ${totalDuplicates} duplicate selectors across files`,
      action: 'Use PostCSS plugins like postcss-merge-rules',
      estimatedSavings: savings
    });
    potentialSavings += savings;
  }

  // 2. Unused vendor prefixes
  const totalPrefixes = cssFiles.reduce((sum, file) =>
    sum + file.analysis.unusedPrefixes, 0);
  if (totalPrefixes > 20) {
    const savings = Math.floor(totalSize * 0.08); // Estimate 8% savings
    recommendations.push({
      priority: 'MEDIUM',
      title: 'Remove Unnecessary Vendor Prefixes',
      description: `Found ${totalPrefixes} potentially unused vendor prefixes`,
      action: 'Use Autoprefixer with updated browser targets',
      estimatedSavings: savings
    });
    potentialSavings += savings;
  }

  // 3. CSS minification
  const hasMinification = cssFiles.some(file =>
    file.content.includes('\n') && file.content.length > 1000);
  if (hasMinification) {
    const savings = Math.floor(totalSize * 0.25); // Estimate 25% savings
    recommendations.push({
      priority: 'HIGH',
      title: 'Enable CSS Minification',
      description: 'CSS files are not properly minified',
      action: 'Enable CSS minification in Vite/build process',
      estimatedSavings: savings
    });
    potentialSavings += savings;
  }

  // 4. Tailwind CSS purging
  const hasTailwind = cssFiles.some(file =>
    file.analysis.tailwindClasses > 50);
  if (hasTailwind) {
    const savings = Math.floor(totalSize * 0.40); // Estimate 40% savings
    recommendations.push({
      priority: 'CRITICAL',
      title: 'Optimize Tailwind CSS Purging',
      description: 'Tailwind CSS may not be properly purged',
      action: 'Configure Tailwind purge/content settings properly',
      estimatedSavings: savings
    });
    potentialSavings += savings;
  }

  // 5. Critical CSS extraction
  if (totalSize > 50000) { // 50KB+
    const savings = Math.floor(totalSize * 0.30); // Estimate 30% savings
    recommendations.push({
      priority: 'HIGH',
      title: 'Implement Critical CSS',
      description: 'Large CSS bundle should be split into critical/non-critical',
      action: 'Extract above-the-fold CSS inline, lazy load the rest',
      estimatedSavings: savings
    });
    potentialSavings += savings;
  }

  return { recommendations, potentialSavings };
}

/**
 * Main analysis function
 */
function main() {
  console.log(`${colors.cyan}🔍 WakeDock CSS Bundle Analyzer${colors.reset}`);
  console.log(`${colors.cyan}=====================================${colors.reset}\n`);

  // Check if build directory exists
  if (!fs.existsSync(BUILD_DIR)) {
    console.log(`${colors.yellow}⚠️  Build directory not found: ${BUILD_DIR}${colors.reset}`);
    console.log(`${colors.yellow}   Run 'npm run build' first to generate CSS bundles${colors.reset}\n`);

    // Analyze source CSS instead
    console.log(`${colors.blue}📁 Analyzing source CSS files...${colors.reset}`);
    analyzeSources();
    return;
  }

  // Analyze built CSS files
  console.log(`${colors.blue}📁 Scanning build directory: ${BUILD_DIR}${colors.reset}`);
  const buildCSSFiles = getAllCSSFiles(BUILD_DIR);

  if (buildCSSFiles.length === 0) {
    console.log(`${colors.yellow}⚠️  No CSS files found in build directory${colors.reset}`);
    analyzeSources();
    return;
  }

  // Calculate total size
  const totalSize = buildCSSFiles.reduce((sum, file) => sum + file.size, 0);

  console.log(`\n${colors.green}📊 CSS Bundle Analysis Results${colors.reset}`);
  console.log(`${colors.green}===============================${colors.reset}`);
  console.log(`📦 Total CSS files: ${buildCSSFiles.length}`);
  console.log(`📐 Total bundle size: ${colors.yellow}${formatBytes(totalSize)}${colors.reset}`);

  // Check if we're over target
  const targetSize = 30 * 1024; // 30KB
  if (totalSize > targetSize) {
    const excess = totalSize - targetSize;
    console.log(`🎯 Target size: ${formatBytes(targetSize)}`);
    console.log(`❌ Over target by: ${colors.red}${formatBytes(excess)}${colors.reset}`);
  } else {
    console.log(`✅ Under target size of ${formatBytes(targetSize)}`);
  }

  console.log(`\n${colors.blue}📋 Individual File Analysis${colors.reset}`);
  console.log(`${colors.blue}============================${colors.reset}`);

  // Analyze each file
  buildCSSFiles.forEach(file => {
    file.analysis = analyzeCSSContent(file.content);
    console.log(`\n📄 ${path.basename(file.path)}`);
    console.log(`   Size: ${formatBytes(file.size)}`);
    console.log(`   Lines: ${file.analysis.totalLines}`);
    if (file.analysis.duplicateSelectors > 0) {
      console.log(`   ${colors.yellow}⚠️  Duplicate selectors: ${file.analysis.duplicateSelectors}${colors.reset}`);
    }
    if (file.analysis.unusedPrefixes > 0) {
      console.log(`   ${colors.yellow}⚠️  Vendor prefixes: ${file.analysis.unusedPrefixes}${colors.reset}`);
    }
  });

  // Generate recommendations
  const { recommendations, potentialSavings } = generateRecommendations(buildCSSFiles, totalSize);

  console.log(`\n${colors.magenta}💡 Optimization Recommendations${colors.reset}`);
  console.log(`${colors.magenta}================================${colors.reset}`);

  if (recommendations.length === 0) {
    console.log(`${colors.green}✅ No major optimizations needed!${colors.reset}`);
  } else {
    recommendations.forEach((rec, index) => {
      const priorityColor = rec.priority === 'CRITICAL' ? colors.red :
        rec.priority === 'HIGH' ? colors.yellow : colors.blue;
      console.log(`\n${index + 1}. ${priorityColor}[${rec.priority}]${colors.reset} ${rec.title}`);
      console.log(`   📝 ${rec.description}`);
      console.log(`   🔧 ${rec.action}`);
      console.log(`   💾 Potential savings: ${colors.green}${formatBytes(rec.estimatedSavings)}${colors.reset}`);
    });

    console.log(`\n${colors.green}📈 Total Potential Savings: ${formatBytes(potentialSavings)}${colors.reset}`);

    const finalSize = totalSize - potentialSavings;
    console.log(`📦 Projected final size: ${colors.green}${formatBytes(finalSize)}${colors.reset}`);

    if (finalSize <= targetSize) {
      console.log(`🎯 ${colors.green}Will meet target size!${colors.reset}`);
    } else {
      console.log(`🎯 ${colors.yellow}May still be over target by ${formatBytes(finalSize - targetSize)}${colors.reset}`);
    }
  }

  // Implementation commands
  console.log(`\n${colors.cyan}🚀 Next Steps${colors.reset}`);
  console.log(`${colors.cyan}==============${colors.reset}`);
  console.log(`1. Configure Tailwind purging in tailwind.config.js`);
  console.log(`2. Enable CSS minification in vite.config.js`);
  console.log(`3. Run: npm install postcss-merge-rules --save-dev`);
  console.log(`4. Re-run analysis after changes: node scripts/css-analyzer.js`);
}

/**
 * Analyze source files when build not available
 */
function analyzeSources() {
  console.log(`${colors.blue}📁 Analyzing source CSS files...${colors.reset}`);
  const sourceCSSFiles = getAllCSSFiles(SRC_DIR);

  const totalSize = sourceCSSFiles.reduce((sum, file) => sum + file.size, 0);
  console.log(`\n📦 Source CSS files: ${sourceCSSFiles.length}`);
  console.log(`📐 Total source size: ${formatBytes(totalSize)}`);

  console.log(`\n${colors.yellow}ℹ️  This is source analysis only.${colors.reset}`);
  console.log(`${colors.yellow}   Run 'npm run build' for accurate bundle analysis.${colors.reset}`);
}

// Run the analyzer
main();
