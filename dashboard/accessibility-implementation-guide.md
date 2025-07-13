# WakeDock Accessibility Implementation Guide
**WCAG 2.1 AA Compliance Guidelines for Developers**

## Quick Start Checklist

### ✅ Critical Fixes (Implement First)

1. **Remove autofocus usage**
   ```typescript
   // ❌ NEVER do this
   <input autofocus />
   
   // ✅ Use programmatic focus instead
   <input bind:this={inputElement} />
   <script>
     onMount(() => {
       if (shouldFocus) {
         inputElement.focus();
       }
     });
   </script>
   ```

2. **Ensure proper form labeling**
   ```svelte
   <!-- ✅ Proper label association -->
   <label for="email">Email Address</label>
   <input id="email" type="email" aria-describedby="email-help" />
   <div id="email-help">We'll never share your email</div>
   ```

3. **Add ARIA attributes for error states**
   ```svelte
   <input 
     id="password"
     type="password"
     aria-invalid={hasError}
     aria-describedby={hasError ? "password-error" : "password-help"}
   />
   {#if hasError}
     <div id="password-error" role="alert">Password is required</div>
   {/if}
   ```

4. **Fix non-interactive elements with event handlers**
   ```svelte
   <!-- ❌ Bad: div with click handler -->
   <div on:click={handleClick}>Click me</div>
   
   <!-- ✅ Good: proper button or role -->
   <button on:click={handleClick}>Click me</button>
   <!-- OR -->
   <div 
     role="button" 
     tabindex="0"
     on:click={handleClick}
     on:keydown={(e) => e.key === 'Enter' && handleClick()}
   >
     Click me
   </div>
   ```

## Using the New Accessibility Utilities

### 1. Import Accessibility Modules

```typescript
import { 
  accessibleColors, 
  accessibilityTokens 
} from '$lib/design-system/tokens';

import { 
  accessibilityUtils,
  focusManagement,
  keyboardHandlers 
} from '$lib/design-system/accessibility';

import accessibilityTest from '$lib/design-system/accessibility-test';
```

### 2. Use WCAG-Compliant Colors

```typescript
// ✅ Use accessible color tokens
const textClasses = {
  primary: `text-[${accessibleColors.text.primary}]`,     // #1e293b
  secondary: `text-[${accessibleColors.text.secondary}]`, // #475569
  interactive: `text-[${accessibleColors.interactive.primary}]` // #2563eb
};

// ❌ Avoid these non-compliant colors for text
// text-secondary-400 (#94a3b8) - only 2.78:1 contrast
// text-primary-400 (#60a5fa) - only 3.12:1 contrast
```

### 3. Implement Proper Focus Management

```svelte
<script>
  import { focusManagement } from '$lib/design-system/accessibility';
  
  let modalElement;
  let focusManager;
  
  function openModal() {
    focusManager = focusManagement.createFocusManager();
    focusManager.save(); // Save current focus
    modalElement.focus();
  }
  
  function closeModal() {
    focusManager.restore(); // Return focus to previous element
  }
</script>

<div bind:this={modalElement} role="dialog" aria-modal="true">
  <!-- Modal content -->
</div>
```

### 4. Use Touch Target Utilities

```svelte
<script>
  import { accessibilityTokens } from '$lib/design-system/tokens';
</script>

<!-- ✅ Ensure minimum 44px touch targets -->
<button class="px-4 py-2" style="min-height: {accessibilityTokens.touchTarget.minimum}">
  Click me
</button>

<!-- Or use CSS classes -->
<button class="px-4 py-2 touch-target-44">
  Click me
</button>
```

### 5. Generate Unique IDs

```svelte
<script>
  import { accessibilityUtils } from '$lib/design-system/accessibility';
  
  const inputId = accessibilityUtils.generateId('email-input');
  const helperId = `${inputId}-helper`;
  const errorId = `${inputId}-error`;
</script>

<label for={inputId}>Email</label>
<input 
  id={inputId} 
  aria-describedby={accessibilityUtils.buildDescribedBy([helperId, errorId])}
/>
<div id={helperId}>Enter your email address</div>
<div id={errorId}>Email is required</div>
```

## Component Patterns

### 1. Accessible Input Component

```svelte
<!-- InputField.svelte -->
<script lang="ts">
  import { accessibilityUtils } from '$lib/design-system/accessibility';
  import { accessibleColors } from '$lib/design-system/tokens';
  
  export let label: string;
  export let error: string = '';
  export let helper: string = '';
  export let required: boolean = false;
  export let id: string = accessibilityUtils.generateId('input');
  
  $: hasError = !!error;
  $: helperId = helper ? `${id}-helper` : undefined;
  $: errorId = hasError ? `${id}-error` : undefined;
  $: describedBy = accessibilityUtils.buildDescribedBy([helperId, errorId]);
</script>

<div class="form-field">
  <label for={id} class="form-label" class:required>
    {label}
    {#if required}
      <span class="sr-only">(required)</span>
    {/if}
  </label>
  
  <input
    {id}
    aria-invalid={hasError}
    aria-describedby={describedBy}
    aria-required={required}
    class="input-base"
    class:error={hasError}
    {...$$restProps}
  />
  
  {#if helper && !hasError}
    <div id={helperId} class="form-helper">{helper}</div>
  {/if}
  
  {#if hasError}
    <div id={errorId} class="form-error" role="alert">{error}</div>
  {/if}
</div>
```

### 2. Accessible Modal Component

```svelte
<!-- Modal.svelte -->
<script lang="ts">
  import { focusManagement, accessibilityUtils } from '$lib/design-system/accessibility';
  import { onMount } from 'svelte';
  
  export let open: boolean = false;
  export let title: string;
  export let onClose: () => void;
  
  let modalElement: HTMLElement;
  let focusManager: ReturnType<typeof focusManagement.createFocusManager>;
  let cleanup: (() => void) | null = null;
  
  $: if (open) {
    openModal();
  } else {
    closeModal();
  }
  
  function openModal() {
    focusManager = focusManagement.createFocusManager();
    focusManager.save();
    
    setTimeout(() => {
      modalElement?.focus();
      cleanup = accessibilityUtils.trapFocus(modalElement);
    }, 100);
  }
  
  function closeModal() {
    cleanup?.();
    focusManager?.restore();
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      onClose();
    }
  }
</script>

{#if open}
  <div class="modal-overlay" on:click={onClose}>
    <div 
      bind:this={modalElement}
      class="modal-content"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabindex="-1"
      on:click|stopPropagation
      on:keydown={handleKeydown}
    >
      <h2 id="modal-title">{title}</h2>
      <slot />
      <button on:click={onClose} aria-label="Close modal">×</button>
    </div>
  </div>
{/if}
```

### 3. Accessible Navigation Component

```svelte
<!-- Navigation.svelte -->
<script lang="ts">
  import { keyboardHandlers } from '$lib/design-system/accessibility';
  
  export let items: Array<{href: string, label: string}>;
  
  let currentIndex = 0;
  let navItems: HTMLElement[] = [];
  
  function handleKeydown(event: KeyboardEvent) {
    currentIndex = keyboardHandlers.arrowNavigation(
      event,
      navItems,
      currentIndex,
      (index) => {
        // Handle selection
        navItems[index]?.click();
      }
    );
  }
</script>

<nav role="navigation" aria-label="Main navigation">
  <ul on:keydown={handleKeydown}>
    {#each items as item, index}
      <li>
        <a 
          href={item.href}
          bind:this={navItems[index]}
          tabindex={index === 0 ? "0" : "-1"}
        >
          {item.label}
        </a>
      </li>
    {/each}
  </ul>
</nav>
```

## Testing Your Components

### 1. Run Accessibility Tests

```typescript
import accessibilityTest from '$lib/design-system/accessibility-test';

// Test a component
const element = document.querySelector('#my-component');
const result = accessibilityTest.runAccessibilityTest(element);

console.log('Accessibility Score:', result.score);
console.log('Issues:', result.issues);

// Generate report
const report = accessibilityTest.generateAccessibilityReport(result);
console.log(report);
```

### 2. Test Color Contrast

```typescript
import { testColorContrast } from '$lib/design-system/accessibility-test';

// Test a color combination
const issues = testColorContrast('#94a3b8', '#ffffff');
if (issues.length > 0) {
  console.log('Contrast issues:', issues);
}
```

### 3. Manual Testing Checklist

- [ ] **Keyboard Only**: Can you navigate the entire interface using only Tab, Shift+Tab, Enter, Space, and Arrow keys?
- [ ] **Screen Reader**: Test with NVDA (free) or macOS VoiceOver
- [ ] **Focus Indicators**: Are focus rings visible and high contrast?
- [ ] **Error Handling**: Are errors announced to screen readers?
- [ ] **Form Labels**: Are all form controls properly labeled?
- [ ] **Headings**: Is there a logical heading hierarchy (h1, h2, h3)?

## Common Accessibility Patterns

### 1. Skip Links

```svelte
<!-- Add to main layout -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<main id="main-content" tabindex="-1">
  <!-- Main content -->
</main>
```

### 2. Live Regions for Dynamic Content

```svelte
<script>
  import { accessibilityUtils } from '$lib/design-system/accessibility';
  
  function announceSuccess(message: string) {
    accessibilityUtils.announce(message, 'polite');
  }
  
  function announceError(message: string) {
    accessibilityUtils.announce(message, 'assertive');
  }
</script>

<!-- Or use a live region div -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {#if statusMessage}
    {statusMessage}
  {/if}
</div>
```

### 3. Loading States

```svelte
<button disabled={loading} aria-describedby={loading ? 'loading-status' : undefined}>
  Submit
</button>

{#if loading}
  <div id="loading-status" aria-live="polite">
    <span class="sr-only">Loading, please wait...</span>
    <div class="loading-spinner" aria-hidden="true"></div>
  </div>
{/if}
```

## Style Guidelines

### 1. Use Accessibility CSS

```css
/* Import accessibility styles */
@import '$lib/design-system/accessibility.css';

/* Use utility classes */
.my-component {
  @apply touch-target-44 focus-ring;
}
```

### 2. Color Usage

```css
/* ✅ Use accessible color tokens */
.text-primary { color: theme('colors.secondary.800'); }    /* #1e293b */
.text-secondary { color: theme('colors.secondary.600'); }  /* #475569 */
.text-muted { color: theme('colors.secondary.500'); }      /* #64748b - large text only */

/* ❌ Avoid these for body text */
.text-low-contrast { color: theme('colors.secondary.400'); } /* #94a3b8 - fails WCAG */
```

### 3. Focus States

```css
/* Enhanced focus indicators */
.custom-button:focus-visible {
  outline: 2px solid theme('colors.primary.500');
  outline-offset: 2px;
  border-radius: 4px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .custom-button {
    border: 1px solid currentColor;
  }
}
```

## Automated Testing Integration

### 1. Add to Build Process

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    // Add accessibility linting
    {
      name: 'accessibility-check',
      buildStart() {
        // Run accessibility tests during build
      }
    }
  ]
});
```

### 2. Unit Tests

```typescript
// accessibility.test.ts
import { render } from '@testing-library/svelte';
import { axe, toHaveNoViolations } from 'jest-axe';
import MyComponent from './MyComponent.svelte';

expect.extend(toHaveNoViolations);

test('component is accessible', async () => {
  const { container } = render(MyComponent);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Resources

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [axe DevTools Browser Extension](https://www.deque.com/axe/devtools/)

## Support

For accessibility questions or issues:
1. Check this guide for common patterns
2. Use the testing utilities to identify issues
3. Refer to WCAG 2.1 guidelines for detailed requirements
4. Test with actual assistive technology when possible

Remember: Accessibility is not a checklist—it's about creating inclusive experiences for all users.