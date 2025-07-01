/**
 * Axe Accessibility Test Helpers
 * Provides utilities for running axe-core accessibility tests on components
 */

import axe from 'axe-core';
import { render, RenderResult } from '@testing-library/svelte';
import type { ComponentType } from 'svelte';

/**
 * Options for accessibility testing
 */
export interface A11yTestOptions {
  /** Rules to include in the accessibility tests */
  rules?: string[];
  /** Rules to exclude from the accessibility tests */
  disabledRules?: string[];
  /** The context to test (defaults to document) */
  context?: axe.ElementContext;
  /** Additional configuration for axe-core */
  config?: axe.RunOptions;
}

/**
 * Run accessibility tests on a rendered component
 * @param component Rendered component from testing-library
 * @param options Accessibility test options
 * @returns Promise resolving to axe test results
 */
export async function runA11yTest(
  component: { container: HTMLElement },
  options: A11yTestOptions = {}
): Promise<axe.AxeResults> {
  const { rules, disabledRules, context, config } = options;

  // Configure axe
  const axeConfig: axe.RunOptions = {
    ...config
  };

  // Add rule configurations if provided
  if (rules?.length || disabledRules?.length) {
    axeConfig.rules = {};

    rules?.forEach(rule => {
      if (!axeConfig.rules) axeConfig.rules = {};
      axeConfig.rules[rule] = { enabled: true };
    });

    disabledRules?.forEach(rule => {
      if (!axeConfig.rules) axeConfig.rules = {};
      axeConfig.rules[rule] = { enabled: false };
    });
  }

  // Run axe on the component's container
  return await axe.run(
    context || component.container,
    axeConfig
  );
}

/**
 * Test a component for accessibility
 * @param Component Svelte component to test
 * @param props Props to pass to the component
 * @param options Accessibility test options
 * @returns Promise resolving to axe test results
 */
export async function testComponentA11y(
  Component: ComponentType,
  props?: Record<string, any>,
  options: A11yTestOptions = {}
): Promise<axe.AxeResults> {
  const component = render(Component, { props });
  return await runA11yTest(component, options);
}

/**
 * Verify if accessibility test results have no violations
 * @param results Results from axe-core test
 * @returns True if no violations were found
 */
export function hasNoViolations(results: axe.AxeResults): boolean {
  return results.violations.length === 0;
}

/**
 * Format accessibility violations for easier debugging
 * @param results Results from axe-core test
 * @returns Formatted string with violation details
 */
export function formatViolations(results: axe.AxeResults): string {
  if (results.violations.length === 0) {
    return 'No accessibility violations found';
  }

  return results.violations
    .map(violation => {
      const nodes = violation.nodes
        .map(node => `  - ${node.html}\n    ${node.failureSummary}`)
        .join('\n');

      return `Rule violated: ${violation.id} - ${violation.help}\nImpact: ${violation.impact}\nDescription: ${violation.description}\nElements:\n${nodes}`;
    })
    .join('\n\n');
}
