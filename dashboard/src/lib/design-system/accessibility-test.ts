/**
 * Accessibility Testing Utilities
 * Runtime accessibility validation and testing helpers
 */

import { getContrastRatio, meetsContrastRequirement } from './accessibility';
import { colors } from './tokens';

export interface AccessibilityIssue {
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: string;
  message: string;
  element?: HTMLElement;
  recommendation: string;
}

export interface AccessibilityTestResult {
  passed: boolean;
  issues: AccessibilityIssue[];
  score: number; // 0-100
}

/**
 * Test color contrast compliance
 */
export function testColorContrast(
  foreground: string,
  background: string,
  fontSize?: number,
  fontWeight?: number
): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const ratio = getContrastRatio(foreground, background);
  
  // Determine if text is large (18pt+ or 14pt+ bold)
  const isLargeText = 
    (fontSize && fontSize >= 18) || 
    (fontSize && fontSize >= 14 && fontWeight && fontWeight >= 700);
  
  const meetsAA = meetsContrastRequirement(foreground, background, 'AA', isLargeText);
  const meetsAAA = meetsContrastRequirement(foreground, background, 'AAA', isLargeText);
  
  if (!meetsAA) {
    issues.push({
      severity: 'critical',
      type: 'color-contrast',
      message: `Color contrast ratio ${ratio.toFixed(2)}:1 fails WCAG AA requirements`,
      recommendation: `Increase contrast ratio to at least ${isLargeText ? '3:1' : '4.5:1'}`
    });
  } else if (!meetsAAA) {
    issues.push({
      severity: 'medium',
      type: 'color-contrast',
      message: `Color contrast ratio ${ratio.toFixed(2)}:1 fails WCAG AAA requirements`,
      recommendation: `Increase contrast ratio to at least ${isLargeText ? '4.5:1' : '7:1'} for AAA compliance`
    });
  }
  
  return issues;
}

/**
 * Test element for proper labeling
 */
export function testElementLabeling(element: HTMLElement): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const tagName = element.tagName.toLowerCase();
  
  // Interactive elements that need labels
  const interactiveElements = ['button', 'input', 'select', 'textarea', 'a'];
  const hasClick = element.onclick || element.addEventListener;
  
  if (interactiveElements.includes(tagName) || hasClick) {
    const hasAriaLabel = element.hasAttribute('aria-label');
    const hasAriaLabelledBy = element.hasAttribute('aria-labelledby');
    const hasAssociatedLabel = element.id && document.querySelector(`label[for="${element.id}"]`);
    const hasTextContent = element.textContent?.trim();
    
    if (!hasAriaLabel && !hasAriaLabelledBy && !hasAssociatedLabel && !hasTextContent) {
      issues.push({
        severity: 'critical',
        type: 'missing-label',
        message: 'Interactive element lacks accessible name',
        element,
        recommendation: 'Add aria-label, aria-labelledby, associated label, or descriptive text content'
      });
    }
  }
  
  return issues;
}

/**
 * Test focus management
 */
export function testFocusManagement(container: HTMLElement): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  
  // Check for elements with tabindex
  const tabindexElements = container.querySelectorAll('[tabindex]');
  tabindexElements.forEach((element) => {
    const tabindex = element.getAttribute('tabindex');
    const isInteractive = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName);
    
    if (tabindex && parseInt(tabindex) > 0) {
      issues.push({
        severity: 'high',
        type: 'positive-tabindex',
        message: 'Positive tabindex values disrupt natural tab order',
        element: element as HTMLElement,
        recommendation: 'Use tabindex="0" for focusable elements or tabindex="-1" for programmatically focused elements'
      });
    }
    
    if (tabindex === '0' && !isInteractive) {
      const hasRole = element.hasAttribute('role');
      const hasEventHandler = element.onclick || element.onkeydown;
      
      if (!hasRole && !hasEventHandler) {
        issues.push({
          severity: 'medium',
          type: 'unnecessary-tabindex',
          message: 'Non-interactive element made focusable without proper role or event handlers',
          element: element as HTMLElement,
          recommendation: 'Add appropriate ARIA role and keyboard event handlers'
        });
      }
    }
  });
  
  return issues;
}

/**
 * Test form accessibility
 */
export function testFormAccessibility(form: HTMLFormElement): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  
  const formControls = form.querySelectorAll('input, select, textarea');
  
  formControls.forEach((control) => {
    const element = control as HTMLElement;
    
    // Check for labels
    const hasLabel = element.id && form.querySelector(`label[for="${element.id}"]`);
    const hasAriaLabel = element.hasAttribute('aria-label');
    const hasAriaLabelledBy = element.hasAttribute('aria-labelledby');
    
    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
      issues.push({
        severity: 'critical',
        type: 'form-missing-label',
        message: 'Form control missing accessible label',
        element,
        recommendation: 'Add a label element with for attribute, aria-label, or aria-labelledby'
      });
    }
    
    // Check for error handling
    const hasAriaInvalid = element.hasAttribute('aria-invalid');
    const hasAriaDescribedBy = element.hasAttribute('aria-describedby');
    
    if (element.classList.contains('error') || element.getAttribute('aria-invalid') === 'true') {
      if (!hasAriaDescribedBy) {
        issues.push({
          severity: 'high',
          type: 'form-missing-error-description',
          message: 'Invalid form control missing error description',
          element,
          recommendation: 'Add aria-describedby pointing to error message element'
        });
      }
    }
  });
  
  return issues;
}

/**
 * Test heading hierarchy
 */
export function testHeadingHierarchy(container: HTMLElement): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
  
  let previousLevel = 0;
  
  headings.forEach((heading, index) => {
    const level = parseInt(heading.tagName.charAt(1));
    
    if (index === 0 && level !== 1) {
      issues.push({
        severity: 'medium',
        type: 'heading-hierarchy',
        message: 'Page should start with h1',
        element: heading as HTMLElement,
        recommendation: 'Use h1 for the main page heading'
      });
    }
    
    if (level > previousLevel + 1) {
      issues.push({
        severity: 'medium',
        type: 'heading-hierarchy',
        message: `Heading level ${level} skips levels (previous was h${previousLevel})`,
        element: heading as HTMLElement,
        recommendation: 'Use heading levels in sequential order'
      });
    }
    
    previousLevel = level;
  });
  
  return issues;
}

/**
 * Test keyboard accessibility
 */
export function testKeyboardAccessibility(container: HTMLElement): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  
  // Find elements with click handlers but no keyboard handlers
  const clickableElements = container.querySelectorAll('*');
  
  clickableElements.forEach((element) => {
    const htmlElement = element as HTMLElement;
    
    if (htmlElement.onclick && !['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(htmlElement.tagName)) {
      const hasKeyHandler = htmlElement.onkeydown || htmlElement.onkeyup || htmlElement.onkeypress;
      const hasRole = htmlElement.hasAttribute('role');
      const hasTabindex = htmlElement.hasAttribute('tabindex');
      
      if (!hasKeyHandler) {
        issues.push({
          severity: 'high',
          type: 'missing-keyboard-handler',
          message: 'Clickable element missing keyboard event handler',
          element: htmlElement,
          recommendation: 'Add keyboard event handler for Enter and Space keys'
        });
      }
      
      if (!hasRole) {
        issues.push({
          severity: 'high',
          type: 'missing-role',
          message: 'Interactive element missing ARIA role',
          element: htmlElement,
          recommendation: 'Add role="button" for clickable elements'
        });
      }
      
      if (!hasTabindex) {
        issues.push({
          severity: 'high',
          type: 'missing-tabindex',
          message: 'Interactive element not keyboard focusable',
          element: htmlElement,
          recommendation: 'Add tabindex="0" to make element focusable'
        });
      }
    }
  });
  
  return issues;
}

/**
 * Run comprehensive accessibility test on element
 */
export function runAccessibilityTest(element: HTMLElement): AccessibilityTestResult {
  const issues: AccessibilityIssue[] = [];
  
  // Test element and its children
  issues.push(...testElementLabeling(element));
  issues.push(...testFocusManagement(element));
  issues.push(...testHeadingHierarchy(element));
  issues.push(...testKeyboardAccessibility(element));
  
  // Test forms if present
  const forms = element.querySelectorAll('form');
  forms.forEach(form => {
    issues.push(...testFormAccessibility(form));
  });
  
  // Calculate score based on issues
  const criticalCount = issues.filter(i => i.severity === 'critical').length;
  const highCount = issues.filter(i => i.severity === 'high').length;
  const mediumCount = issues.filter(i => i.severity === 'medium').length;
  const lowCount = issues.filter(i => i.severity === 'low').length;
  
  // Scoring: start at 100, deduct points for issues
  let score = 100;
  score -= criticalCount * 25; // Critical issues: -25 points each
  score -= highCount * 15;     // High issues: -15 points each
  score -= mediumCount * 10;   // Medium issues: -10 points each
  score -= lowCount * 5;       // Low issues: -5 points each
  
  score = Math.max(0, score); // Don't go below 0
  
  return {
    passed: criticalCount === 0 && highCount === 0,
    issues,
    score
  };
}

/**
 * Generate accessibility report
 */
export function generateAccessibilityReport(result: AccessibilityTestResult): string {
  const { passed, issues, score } = result;
  
  let report = `# Accessibility Test Report\n\n`;
  report += `**Score**: ${score}/100\n`;
  report += `**Status**: ${passed ? '✅ PASSED' : '❌ FAILED'}\n\n`;
  
  if (issues.length === 0) {
    report += `No accessibility issues found! 🎉\n`;
    return report;
  }
  
  const groupedIssues = issues.reduce((acc, issue) => {
    if (!acc[issue.severity]) acc[issue.severity] = [];
    acc[issue.severity].push(issue);
    return acc;
  }, {} as Record<string, AccessibilityIssue[]>);
  
  ['critical', 'high', 'medium', 'low'].forEach(severity => {
    const severityIssues = groupedIssues[severity];
    if (severityIssues && severityIssues.length > 0) {
      report += `## ${severity.toUpperCase()} Issues (${severityIssues.length})\n\n`;
      
      severityIssues.forEach((issue, index) => {
        report += `### ${index + 1}. ${issue.type}\n`;
        report += `**Message**: ${issue.message}\n`;
        report += `**Recommendation**: ${issue.recommendation}\n`;
        if (issue.element) {
          report += `**Element**: \`${issue.element.tagName.toLowerCase()}\`\n`;
        }
        report += `\n`;
      });
    }
  });
  
  return report;
}

/**
 * Color palette accessibility testing
 */
export function testColorPalette(): AccessibilityTestResult {
  const issues: AccessibilityIssue[] = [];
  
  // Test common color combinations
  const textColors = [
    { name: 'secondary-400', value: '#94a3b8' },
    { name: 'secondary-500', value: '#64748b' },
    { name: 'secondary-600', value: '#475569' },
    { name: 'primary-400', value: '#60a5fa' },
    { name: 'primary-500', value: '#3b82f6' },
    { name: 'primary-600', value: '#2563eb' },
  ];
  
  const backgroundColor = '#ffffff';
  
  textColors.forEach(color => {
    const contrastIssues = testColorContrast(color.value, backgroundColor);
    contrastIssues.forEach(issue => {
      issue.message = `${color.name} on white: ${issue.message}`;
      issues.push(issue);
    });
  });
  
  // Calculate score
  const criticalCount = issues.filter(i => i.severity === 'critical').length;
  const mediumCount = issues.filter(i => i.severity === 'medium').length;
  
  let score = 100;
  score -= criticalCount * 20;
  score -= mediumCount * 10;
  score = Math.max(0, score);
  
  return {
    passed: criticalCount === 0,
    issues,
    score
  };
}

export default {
  testColorContrast,
  testElementLabeling,
  testFocusManagement,
  testFormAccessibility,
  testHeadingHierarchy,
  testKeyboardAccessibility,
  runAccessibilityTest,
  generateAccessibilityReport,
  testColorPalette
};