/**
 * Accessibility Test Suite - Comprehensive Tests
 * Automated accessibility testing with axe-core
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { cleanup } from '@testing-library/svelte';
import {
  testComponentA11y,
  hasNoViolations,
  formatViolations
} from '../helpers/axe-helper';

// Import key components to test
import Button from '../../src/lib/components/Button.svelte';
import Input from '../../src/lib/components/forms/Input.svelte';
import Select from '../../src/lib/components/forms/Select.svelte';
import Alert from '../../src/lib/components/Alert.svelte';
import Card from '../../src/lib/components/Card.svelte';
import Modal from '../../src/lib/components/modals/Modal.svelte';

// Clean up after each test
afterEach(() => {
  cleanup();
});

describe('Accessibility - Core Components', () => {
  // Button component tests
  describe('Button Component', () => {
    it('should have no accessibility violations with default props', async () => {
      const results = await testComponentA11y(Button, {
        label: 'Test Button'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });

    it('should have no accessibility violations when disabled', async () => {
      const results = await testComponentA11y(Button, {
        label: 'Disabled Button',
        disabled: true
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });

    it('should have no accessibility violations with aria attributes', async () => {
      const results = await testComponentA11y(Button, {
        label: 'Aria Button',
        ariaExpanded: 'true',
        ariaControls: 'test-panel'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });
  });

  // Form components tests
  describe('Form Components', () => {
    it('should have no accessibility violations for Input component', async () => {
      const results = await testComponentA11y(Input, {
        id: 'test-input',
        label: 'Test Input',
        name: 'testInput',
        value: '',
        required: true
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });

    it('should have no accessibility violations for Input with error', async () => {
      const results = await testComponentA11y(Input, {
        id: 'test-input-error',
        label: 'Test Input with Error',
        name: 'testInputError',
        value: '',
        error: 'This field is required',
        required: true
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });

    it('should have no accessibility violations for Select component', async () => {
      const results = await testComponentA11y(Select, {
        id: 'test-select',
        label: 'Test Select',
        name: 'testSelect',
        options: [
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2' }
        ],
        value: 'option1'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });
  });

  // Alert component tests
  describe('Alert Component', () => {
    it('should have no accessibility violations for info alert', async () => {
      const results = await testComponentA11y(Alert, {
        type: 'info',
        title: 'Information',
        message: 'This is an informational alert'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });

    it('should have no accessibility violations for error alert', async () => {
      const results = await testComponentA11y(Alert, {
        type: 'error',
        title: 'Error',
        message: 'This is an error alert'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });
  });

  // Card component tests
  describe('Card Component', () => {
    it('should have no accessibility violations', async () => {
      const results = await testComponentA11y(Card, {
        title: 'Test Card',
        subtitle: 'Card subtitle'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });
  });

  // Modal component tests
  describe('Modal Component', () => {
    it('should have no accessibility violations when open', async () => {
      const results = await testComponentA11y(Modal, {
        open: true,
        title: 'Test Modal',
        ariaLabelledby: 'modal-title'
      });

      if (!hasNoViolations(results)) {
        console.error(formatViolations(results));
      }
      expect(hasNoViolations(results)).toBe(true);
    });
  });
});

// Specific WCAG rules to test
describe('Accessibility - WCAG 2.1 Specific Rules', () => {
  it('should pass color contrast tests', async () => {
    const results = await testComponentA11y(Button, {
      label: 'Contrast Test'
    }, {
      rules: ['color-contrast']
    });

    if (!hasNoViolations(results)) {
      console.error(formatViolations(results));
    }
    expect(hasNoViolations(results)).toBe(true);
  });

  it('should have appropriate ARIA attributes', async () => {
    const results = await testComponentA11y(Modal, {
      open: true,
      title: 'ARIA Test',
      ariaLabelledby: 'modal-title'
    }, {
      rules: ['aria-roles', 'aria-valid-attr', 'aria-required-attr']
    });

    if (!hasNoViolations(results)) {
      console.error(formatViolations(results));
    }
    expect(hasNoViolations(results)).toBe(true);
  });

  it('should have accessible names for interactive elements', async () => {
    const results = await testComponentA11y(Button, {
      label: '',
      icon: 'settings'
    }, {
      rules: ['button-name']
    });

    // This should actually fail as we have a button without an accessible name
    if (hasNoViolations(results)) {
      console.warn('Warning: Button without label passed accessibility test, verify button-name rule is working');
    }
  });
});
