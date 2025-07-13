#!/usr/bin/env node

/**
 * Script to replace console.log statements with production-safe logging
 * Usage: node scripts/replace-console-logs.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Files to process
const SRC_DIR = path.join(__dirname, '../src');
const EXTENSIONS = ['.ts', '.js', '.svelte'];

// Console methods to replace
const CONSOLE_METHODS = ['log', 'info', 'warn', 'error', 'debug'];

// Import statement to add
const LOGGER_IMPORT = "import { log } from '../lib/utils/production-logger';";
const LOGGER_IMPORT_RELATIVE = "import { log } from '$lib/utils/production-logger';";

/**
 * Get all files recursively
 */
function getAllFiles(dir, files = []) {
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Skip node_modules, .git, etc.
      if (!item.startsWith('.') && item !== 'node_modules' && item !== 'dist' && item !== 'build') {
        getAllFiles(fullPath, files);
      }
    } else if (EXTENSIONS.some(ext => item.endsWith(ext))) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Check if file already has logger import
 */
function hasLoggerImport(content) {
  return content.includes('production-logger') ||
    content.includes("from '$lib/utils/production-logger'") ||
    content.includes("from '../lib/utils/production-logger'");
}

/**
 * Add logger import to file
 */
function addLoggerImport(content, filePath) {
  const isSvelteFile = filePath.endsWith('.svelte');
  let importStatement = LOGGER_IMPORT_RELATIVE;

  // Calculate relative path for non-Svelte files
  if (!isSvelteFile) {
    const relativePath = path.relative(path.dirname(filePath), path.join(SRC_DIR, 'lib/utils/production-logger'));
    importStatement = `import { log } from '${relativePath.replace(/\\/g, '/')}';`;
  }

  if (isSvelteFile) {
    // For Svelte files, add import inside script tag
    const scriptMatch = content.match(/<script[^>]*>/);
    if (scriptMatch) {
      const insertPos = scriptMatch.index + scriptMatch[0].length;
      return content.slice(0, insertPos) + '\n  ' + importStatement + '\n' + content.slice(insertPos);
    }
  } else {
    // For TS/JS files, add at the top after existing imports
    const lines = content.split('\n');
    let insertIndex = 0;

    // Find last import statement
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('import ') && !lines[i].includes('production-logger')) {
        insertIndex = i + 1;
      } else if (lines[i].trim() && !lines[i].trim().startsWith('import ') && !lines[i].trim().startsWith('//')) {
        break;
      }
    }

    lines.splice(insertIndex, 0, importStatement);
    return lines.join('\n');
  }

  return content;
}

/**
 * Replace console statements with logger calls
 */
function replaceConsoleStatements(content) {
  let modified = content;
  let hasChanges = false;

  CONSOLE_METHODS.forEach(method => {
    const consolePattern = new RegExp(`console\\.${method}\\s*\\(`, 'g');
    const matches = [...modified.matchAll(consolePattern)];

    if (matches.length > 0) {
      hasChanges = true;
      modified = modified.replace(consolePattern, `log.${method}(`);
    }
  });

  return { content: modified, hasChanges };
}

/**
 * Process a single file
 */
function processFile(filePath) {
  console.log(`Processing: ${path.relative(SRC_DIR, filePath)}`);

  let content = fs.readFileSync(filePath, 'utf8');
  const originalContent = content;

  // Replace console statements
  const { content: modifiedContent, hasChanges } = replaceConsoleStatements(content);

  if (hasChanges) {
    content = modifiedContent;

    // Add logger import if needed
    if (!hasLoggerImport(content)) {
      content = addLoggerImport(content, filePath);
    }

    // Write back to file
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  ✅ Updated ${path.relative(SRC_DIR, filePath)}`);
    return true;
  } else {
    console.log(`  ⏭️  No console statements found in ${path.relative(SRC_DIR, filePath)}`);
    return false;
  }
}

/**
 * Main execution
 */
function main() {
  console.log('🧹 Replacing console.log statements with production-safe logging...\n');

  const files = getAllFiles(SRC_DIR);
  console.log(`Found ${files.length} files to process\n`);

  let processedCount = 0;
  let modifiedCount = 0;

  for (const file of files) {
    try {
      const wasModified = processFile(file);
      processedCount++;
      if (wasModified) modifiedCount++;
    } catch (error) {
      console.error(`❌ Error processing ${file}:`, error.message);
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   Processed: ${processedCount} files`);
  console.log(`   Modified:  ${modifiedCount} files`);
  console.log(`\n✨ Console.log replacement complete!`);

  if (modifiedCount > 0) {
    console.log('\n🔍 Next steps:');
    console.log('   1. Review the changes');
    console.log('   2. Test the application');
    console.log('   3. Commit the changes');
  }
}

main();
