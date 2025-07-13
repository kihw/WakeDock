#!/usr/bin/env node

/**
 * Design System Performance Analysis Tool
 * Analyzes the refactored WakeDock design system for improvements and metrics
 */

import globPkg from 'glob';
import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const { glob } = globPkg;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class DesignSystemAnalyzer {
  constructor() {
    this.results = {
      components: {
        atoms: [],
        molecules: [],
        organisms: []
      },
      metrics: {
        totalComponents: 0,
        linesOfCode: 0,
        designTokenUsage: 0,
        testCoverage: 0
      },
      improvements: [],
      violations: []
    };
  }

  async analyze() {
    console.log('🔍 Analyzing WakeDock Design System...\n');

    await this.analyzeComponents();
    await this.analyzeDesignTokens();
    await this.analyzeTests();
    await this.generateReport();

    return this.results;
  }

  async analyzeComponents() {
    console.log('📦 Analyzing Components...');

    // Analyze atoms
    const atomFiles = await glob('src/lib/components/ui/atoms/*.svelte');
    for (const file of atomFiles) {
      const analysis = await this.analyzeComponent(file, 'atom');
      this.results.components.atoms.push(analysis);
    }

    // Analyze molecules  
    const moleculeFiles = await glob('src/lib/components/ui/molecules/*.svelte');
    for (const file of moleculeFiles) {
      const analysis = await this.analyzeComponent(file, 'molecule');
      this.results.components.molecules.push(analysis);
    }

    // Analyze organisms
    const organismFiles = await glob('src/lib/components/ui/organisms/*.svelte');
    for (const file of organismFiles) {
      const analysis = await this.analyzeComponent(file, 'organism');
      this.results.components.organisms.push(analysis);
    }

    this.results.metrics.totalComponents = 
      this.results.components.atoms.length +
      this.results.components.molecules.length +
      this.results.components.organisms.length;

    console.log(`✅ Found ${this.results.metrics.totalComponents} components`);
  }

  async analyzeComponent(filePath, type) {
    const content = await readFile(filePath, 'utf8');
    const fileName = filePath.split('/').pop().replace('.svelte', '');
    
    const analysis = {
      name: fileName,
      path: filePath,
      type,
      linesOfCode: content.split('\n').length,
      hasDesignTokens: content.includes('design-system/tokens'),
      hasTests: await this.hasTests(fileName),
      hasStorybook: await this.hasStorybook(fileName),
      hasTypeScript: content.includes('lang="ts"'),
      violations: []
    };

    // Check atomic design violations
    if (type === 'atom' && analysis.linesOfCode > 200) {
      analysis.violations.push(`Atom component too large: ${analysis.linesOfCode} lines (should be <200)`);
    }

    if (type === 'atom' && !analysis.hasDesignTokens) {
      analysis.violations.push('Atom component should use design tokens');
    }

    this.results.metrics.linesOfCode += analysis.linesOfCode;
    if (analysis.hasDesignTokens) {
      this.results.metrics.designTokenUsage++;
    }

    return analysis;
  }

  async hasTests(componentName) {
    try {
      const testFiles = await glob(`src/lib/components/ui/**/${componentName}.test.{ts,js}`);
      return testFiles.length > 0;
    } catch {
      return false;
    }
  }

  async hasStorybook(componentName) {
    try {
      const storyFiles = await glob(`src/lib/components/ui/**/${componentName}.stories.{ts,js}`);
      return storyFiles.length > 0;
    } catch {
      return false;
    }
  }

  async analyzeDesignTokens() {
    console.log('🎨 Analyzing Design Tokens...');

    try {
      const tokensFile = await readFile('src/lib/design-system/tokens.ts', 'utf8');
      
      // Count different token types
      const colorMatches = tokensFile.match(/colors\s*:\s*{[\s\S]*?}/g);
      const typographyMatches = tokensFile.match(/typography\s*:\s*{[\s\S]*?}/g);
      const spacingMatches = tokensFile.match(/spacing\s*:\s*{[\s\S]*?}/g);
      const variantMatches = tokensFile.match(/variants\s*:\s*{[\s\S]*?}/g);

      this.results.metrics.designTokens = {
        colors: colorMatches ? colorMatches.length : 0,
        typography: typographyMatches ? typographyMatches.length : 0,
        spacing: spacingMatches ? spacingMatches.length : 0,
        variants: variantMatches ? variantMatches.length : 0,
        totalLines: tokensFile.split('\n').length
      };

      console.log('✅ Design tokens analyzed');
    } catch (error) {
      console.log('❌ Could not analyze design tokens:', error.message);
    }
  }

  async analyzeTests() {
    console.log('🧪 Analyzing Tests...');

    const testFiles = await glob('src/lib/components/ui/**/*.test.{ts,js}');
    const totalTests = testFiles.length;
    
    let totalTestLines = 0;
    for (const file of testFiles) {
      const content = await readFile(file, 'utf8');
      totalTestLines += content.split('\n').length;
    }

    this.results.metrics.tests = {
      totalFiles: totalTests,
      totalLines: totalTestLines,
      coverageEstimate: Math.min((totalTests / this.results.metrics.totalComponents) * 100, 100)
    };

    console.log(`✅ Found ${totalTests} test files`);
  }

  async generateReport() {
    console.log('📊 Generating Analysis Report...');

    const report = `# 🎨 WakeDock Design System Analysis Report

**Generated**: ${new Date().toLocaleDateString()}
**Analyzer Version**: 1.0.0

## 📊 Overview Metrics

### Components
- **Total Components**: ${this.results.metrics.totalComponents}
- **Atoms**: ${this.results.components.atoms.length}
- **Molecules**: ${this.results.components.molecules.length}  
- **Organisms**: ${this.results.components.organisms.length}

### Code Quality
- **Total Lines of Code**: ${this.results.metrics.linesOfCode.toLocaleString()}
- **Average Lines per Component**: ${Math.round(this.results.metrics.linesOfCode / this.results.metrics.totalComponents)}
- **Design Token Usage**: ${this.results.metrics.designTokenUsage}/${this.results.metrics.totalComponents} components (${Math.round(this.results.metrics.designTokenUsage / this.results.metrics.totalComponents * 100)}%)

### Testing
- **Test Files**: ${this.results.metrics.tests?.totalFiles || 0}
- **Test Coverage Estimate**: ${Math.round(this.results.metrics.tests?.coverageEstimate || 0)}%
- **Test Lines**: ${this.results.metrics.tests?.totalLines || 0}

## 🏗️ Component Analysis

### ✅ Atomic Components (${this.results.components.atoms.length})
${this.results.components.atoms.map(comp => `
- **${comp.name}**
  - Lines: ${comp.linesOfCode}
  - Design Tokens: ${comp.hasDesignTokens ? '✅' : '❌'}
  - Tests: ${comp.hasTests ? '✅' : '❌'}
  - TypeScript: ${comp.hasTypeScript ? '✅' : '❌'}
  - Storybook: ${comp.hasStorybook ? '✅' : '❌'}
  ${comp.violations.length > 0 ? '  - ⚠️ Violations: ' + comp.violations.join(', ') : ''}
`).join('')}

### 🧩 Molecular Components (${this.results.components.molecules.length})
${this.results.components.molecules.map(comp => `
- **${comp.name}**
  - Lines: ${comp.linesOfCode}
  - Design Tokens: ${comp.hasDesignTokens ? '✅' : '❌'}
  - Tests: ${comp.hasTests ? '✅' : '❌'}
  - TypeScript: ${comp.hasTypeScript ? '✅' : '❌'}
  - Storybook: ${comp.hasStorybook ? '✅' : '❌'}
  ${comp.violations.length > 0 ? '  - ⚠️ Violations: ' + comp.violations.join(', ') : ''}
`).join('')}

### 🏛️ Organism Components (${this.results.components.organisms.length})
${this.results.components.organisms.map(comp => `
- **${comp.name}**
  - Lines: ${comp.linesOfCode}
  - Design Tokens: ${comp.hasDesignTokens ? '✅' : '❌'}
  - Tests: ${comp.hasTests ? '✅' : '❌'}
  - TypeScript: ${comp.hasTypeScript ? '✅' : '❌'}
  - Storybook: ${comp.hasStorybook ? '✅' : '❌'}
  ${comp.violations.length > 0 ? '  - ⚠️ Violations: ' + comp.violations.join(', ') : ''}
`).join('')}

## 🎨 Design Tokens Analysis

${this.results.metrics.designTokens ? `
- **Colors**: ${this.results.metrics.designTokens.colors} palettes
- **Typography**: ${this.results.metrics.designTokens.typography} definitions
- **Spacing**: ${this.results.metrics.designTokens.spacing} scales
- **Variants**: ${this.results.metrics.designTokens.variants} component variants
- **Total Token Lines**: ${this.results.metrics.designTokens.totalLines}
` : '❌ Design tokens file not found'}

## 🎯 Quality Recommendations

### High Priority
${this.getAllViolations().slice(0, 5).map(v => `- ${v}`).join('\n')}

### Design System Health Score
${this.calculateHealthScore()}/100

### Next Steps
1. **Increase Test Coverage**: Target 90%+ coverage for all components
2. **Complete Design Token Migration**: Ensure all components use tokens
3. **Add Missing Storybook Stories**: Document all component variants
4. **Reduce Component Complexity**: Keep atoms under 150 lines
5. **Add TypeScript to All Components**: Ensure type safety

---

*Analysis completed at ${new Date().toISOString()}*
`;

    await writeFile('DESIGN_SYSTEM_ANALYSIS.md', report);
    console.log('✅ Report saved to DESIGN_SYSTEM_ANALYSIS.md');

    return report;
  }

  getAllViolations() {
    const violations = [];
    
    [...this.results.components.atoms, ...this.results.components.molecules, ...this.results.components.organisms]
      .forEach(comp => {
        comp.violations.forEach(violation => {
          violations.push(`${comp.name}: ${violation}`);
        });
        
        if (!comp.hasTests) {
          violations.push(`${comp.name}: Missing test file`);
        }
        
        if (!comp.hasStorybook) {
          violations.push(`${comp.name}: Missing Storybook stories`);
        }
        
        if (!comp.hasTypeScript) {
          violations.push(`${comp.name}: Missing TypeScript`);
        }
      });

    return violations;
  }

  calculateHealthScore() {
    let score = 0;
    
    // Design token usage (25 points)
    score += (this.results.metrics.designTokenUsage / this.results.metrics.totalComponents) * 25;
    
    // Test coverage (25 points)
    score += (this.results.metrics.tests?.coverageEstimate || 0) * 0.25;
    
    // TypeScript usage (20 points)
    const tsComponents = [...this.results.components.atoms, ...this.results.components.molecules, ...this.results.components.organisms]
      .filter(comp => comp.hasTypeScript).length;
    score += (tsComponents / this.results.metrics.totalComponents) * 20;
    
    // Storybook coverage (15 points)
    const storybookComponents = [...this.results.components.atoms, ...this.results.components.molecules, ...this.results.components.organisms]
      .filter(comp => comp.hasStorybook).length;
    score += (storybookComponents / this.results.metrics.totalComponents) * 15;
    
    // Atomic design compliance (15 points)
    const violations = this.getAllViolations().length;
    score += Math.max(0, 15 - violations);
    
    return Math.round(score);
  }
}

// Run analysis if script is called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const analyzer = new DesignSystemAnalyzer();
  
  analyzer.analyze()
    .then(() => {
      console.log('\n🎉 Analysis complete! Check DESIGN_SYSTEM_ANALYSIS.md for full report.');
    })
    .catch(error => {
      console.error('❌ Analysis failed:', error);
      process.exit(1);
    });
}

export default DesignSystemAnalyzer;