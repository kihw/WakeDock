/**
 * Design System Validation Tool
 * Ensures components follow design token standards and best practices
 */

import { variants, colors } from './tokens';

interface ValidationRule {
  name: string;
  description: string;
  check: (content: string) => ValidationResult;
}

interface ValidationResult {
  passed: boolean;
  issues: string[];
  suggestions?: string[];
}

interface ComponentValidation {
  component: string;
  score: number;
  issues: string[];
  suggestions: string[];
  tokenUsage: number;
  deprecated: string[];
}

// Common anti-patterns and deprecated classes
const DEPRECATED_CLASSES = [
  'bg-blue-', 'bg-green-', 'bg-red-', 'bg-yellow-', 'bg-gray-',
  'text-blue-', 'text-green-', 'text-red-', 'text-yellow-', 'text-gray-',
  'border-blue-', 'border-green-', 'border-red-', 'border-yellow-', 'border-gray-',
  'hover:bg-blue-', 'hover:bg-green-', 'hover:bg-red-', 'hover:bg-yellow-', 'hover:bg-gray-',
  'focus:bg-blue-', 'focus:bg-green-', 'focus:bg-red-', 'focus:bg-yellow-', 'focus:bg-gray-'
];

const DESIGN_TOKEN_PATTERNS = [
  'variants\\.',
  'colors\\.',
  'spacing\\.',
  'var\\(--color-',
  'bg-primary-',
  'bg-secondary-',
  'bg-success-',
  'bg-warning-',
  'bg-error-',
  'text-primary-',
  'text-secondary-',
  'text-success-',
  'text-warning-',
  'text-error-',
  'border-primary-',
  'border-secondary-',
  'border-success-',
  'border-warning-',
  'border-error-'
];

// Validation rules
const validationRules: ValidationRule[] = [
  {
    name: 'No Hardcoded Colors',
    description: 'Components should use design tokens instead of hardcoded color classes',
    check: (content: string): ValidationResult => {
      const issues: string[] = [];
      const suggestions: string[] = [];

      DEPRECATED_CLASSES.forEach(pattern => {
        const regex = new RegExp(pattern + '\\d+', 'g');
        const matches = content.match(regex);
        if (matches) {
          issues.push(`Found deprecated color classes: ${matches.join(', ')}`);
          if (pattern.includes('blue')) {
            suggestions.push('Use bg-primary-, text-primary-, or border-primary- instead of bg-blue-');
          } else if (pattern.includes('green')) {
            suggestions.push('Use bg-success-, text-success-, or border-success- instead of bg-green-');
          } else if (pattern.includes('red')) {
            suggestions.push('Use bg-error-, text-error-, or border-error- instead of bg-red-');
          } else if (pattern.includes('yellow')) {
            suggestions.push('Use bg-warning-, text-warning-, or border-warning- instead of bg-yellow-');
          } else if (pattern.includes('gray')) {
            suggestions.push('Use bg-secondary-, text-secondary-, or border-secondary- instead of bg-gray-');
          }
        }
      });

      return {
        passed: issues.length === 0,
        issues,
        suggestions: [...new Set(suggestions)]
      };
    }
  },

  {
    name: 'Design Token Usage',
    description: 'Components should use design tokens from the tokens file',
    check: (content: string): ValidationResult => {
      const issues: string[] = [];
      const suggestions: string[] = [];

      // Check for imports
      const hasTokenImport = content.includes("from '$lib/design-system/tokens'");
      const hasVariantsImport = content.includes('import { variants') || content.includes('import { colors');

      if (!hasTokenImport && !hasVariantsImport) {
        issues.push('Component does not import design tokens');
        suggestions.push('Add: import { variants, colors } from \'$lib/design-system/tokens\'');
      }

      // Check for token usage patterns
      let tokenUsageCount = 0;
      DESIGN_TOKEN_PATTERNS.forEach(pattern => {
        const regex = new RegExp(pattern, 'g');
        const matches = content.match(regex);
        if (matches) {
          tokenUsageCount += matches.length;
        }
      });

      if (tokenUsageCount === 0 && hasTokenImport) {
        issues.push('Imports design tokens but does not use them');
        suggestions.push('Use variants.button.primary or colors.primary[600] instead of hardcoded classes');
      }

      return {
        passed: tokenUsageCount > 0 || !hasTokenImport,
        issues,
        suggestions
      };
    }
  },

  {
    name: 'CSS Custom Properties',
    description: 'Components using CSS should leverage CSS custom properties from the CSS bridge',
    check: (content: string): ValidationResult => {
      const issues: string[] = [];
      const suggestions: string[] = [];

      const hasCSSSection = content.includes('<style>');
      const usesCustomProperties = content.includes('var(--color-');

      if (hasCSSSection && !usesCustomProperties) {
        // Check if it has hardcoded colors in CSS
        const cssColorPatterns = ['#[0-9a-fA-F]{3,6}', 'rgb\\(', 'rgba\\(', 'hsl\\(', 'hsla\\('];
        let hasHardcodedColors = false;

        cssColorPatterns.forEach(pattern => {
          const regex = new RegExp(pattern, 'g');
          if (content.match(regex)) {
            hasHardcodedColors = true;
          }
        });

        if (hasHardcodedColors) {
          issues.push('Component uses hardcoded colors in CSS');
          suggestions.push('Use CSS custom properties like var(--color-primary) instead');
          suggestions.push('Import cssBridge to ensure custom properties are available');
        }
      }

      return {
        passed: !hasCSSSection || usesCustomProperties || issues.length === 0,
        issues,
        suggestions
      };
    }
  },

  {
    name: 'Consistent Props',
    description: 'Components should use consistent prop patterns (size, variant, etc.)',
    check: (content: string): ValidationResult => {
      const issues: string[] = [];
      const suggestions: string[] = [];

      const hasVariantProp = content.includes('export let variant');
      const hasSizeProp = content.includes('export let size');

      // Check for non-standard prop names
      const nonStandardProps = [
        'color:', 'theme:', 'style:', 'type:.*=.*["\'](?:primary|secondary|success|warning|error)'
      ];

      nonStandardProps.forEach(pattern => {
        const regex = new RegExp(pattern, 'g');
        if (content.match(regex)) {
          issues.push(`Consider using 'variant' prop instead of custom type/color props`);
          suggestions.push('Use variant="primary" instead of type="primary" or color="primary"');
        }
      });

      return {
        passed: issues.length === 0,
        issues,
        suggestions
      };
    }
  }
];

// Component validation function
export function validateComponent(content: string, componentPath: string): ComponentValidation {
  const results = validationRules.map(rule => rule.check(content));
  const passedRules = results.filter(r => r.passed).length;
  const score = Math.round((passedRules / validationRules.length) * 100);

  const allIssues = results.flatMap(r => r.issues);
  const allSuggestions = results.flatMap(r => r.suggestions || []);

  // Calculate token usage percentage
  let tokenUsageCount = 0;
  let totalStyleCount = 0;

  DESIGN_TOKEN_PATTERNS.forEach(pattern => {
    const regex = new RegExp(pattern, 'g');
    const matches = content.match(regex);
    if (matches) {
      tokenUsageCount += matches.length;
    }
  });

  // Count potential style applications (rough estimate)
  const classPatterns = ['class=', 'className=', 'class:'];
  classPatterns.forEach(pattern => {
    const regex = new RegExp(pattern, 'g');
    const matches = content.match(regex);
    if (matches) {
      totalStyleCount += matches.length;
    }
  });

  const tokenUsage = totalStyleCount > 0 ? Math.round((tokenUsageCount / totalStyleCount) * 100) : 0;

  // Find deprecated classes
  const deprecated: string[] = [];
  DEPRECATED_CLASSES.forEach(pattern => {
    const regex = new RegExp(pattern + '\\d+', 'g');
    const matches = content.match(regex);
    if (matches) {
      deprecated.push(...matches);
    }
  });

  return {
    component: componentPath,
    score,
    issues: [...new Set(allIssues)],
    suggestions: [...new Set(allSuggestions)],
    tokenUsage,
    deprecated: [...new Set(deprecated)]
  };
}

// Batch validation function
export function validateDesignSystem(components: { path: string; content: string }[]): {
  overall: {
    score: number;
    tokenUsage: number;
    totalIssues: number;
    componentsValidated: number;
  };
  components: ComponentValidation[];
  recommendations: string[];
} {
  const validations = components.map(comp => validateComponent(comp.content, comp.path));
  
  const overallScore = Math.round(
    validations.reduce((sum, v) => sum + v.score, 0) / validations.length
  );
  
  const overallTokenUsage = Math.round(
    validations.reduce((sum, v) => sum + v.tokenUsage, 0) / validations.length
  );
  
  const totalIssues = validations.reduce((sum, v) => sum + v.issues.length, 0);

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (overallScore < 80) {
    recommendations.push('🔧 Consider refactoring components with low scores to use design tokens');
  }
  
  if (overallTokenUsage < 70) {
    recommendations.push('🎨 Increase design token usage by replacing hardcoded classes');
  }
  
  if (totalIssues > 10) {
    recommendations.push('⚠️ Address validation issues to improve design system consistency');
  }

  const deprecatedCount = validations.reduce((sum, v) => sum + v.deprecated.length, 0);
  if (deprecatedCount > 0) {
    recommendations.push(`🚨 Found ${deprecatedCount} deprecated color classes that should be updated`);
  }

  if (recommendations.length === 0) {
    recommendations.push('✅ Design system is in excellent condition!');
  }

  return {
    overall: {
      score: overallScore,
      tokenUsage: overallTokenUsage,
      totalIssues,
      componentsValidated: validations.length
    },
    components: validations,
    recommendations
  };
}

// Helper functions for specific validations
export const validators = {
  hasDesignTokens: (content: string): boolean => {
    return content.includes("from '$lib/design-system/tokens'");
  },

  usesDeprecatedClasses: (content: string): string[] => {
    const found: string[] = [];
    DEPRECATED_CLASSES.forEach(pattern => {
      const regex = new RegExp(pattern + '\\d+', 'g');
      const matches = content.match(regex);
      if (matches) {
        found.push(...matches);
      }
    });
    return found;
  },

  getTokenUsageScore: (content: string): number => {
    let tokenCount = 0;
    DESIGN_TOKEN_PATTERNS.forEach(pattern => {
      const regex = new RegExp(pattern, 'g');
      const matches = content.match(regex);
      if (matches) {
        tokenCount += matches.length;
      }
    });
    return tokenCount;
  }
};

export default {
  validateComponent,
  validateDesignSystem,
  validators,
  validationRules
};