/**
 * Migration utility for consolidating Button components
 * TASK-UI-001: Unification des Composants Button
 * 
 * This script helps migrate from fragmented button components to UnifiedButton
 */

import type { UnifiedButtonProps, LegacyButtonProps } from './UnifiedButton.types';

// Migration mappings for each legacy component
export const migrationMappings = {
  BaseButton: {
    componentName: 'BaseButton',
    newComponent: 'UnifiedButton',
    propsMapping: (props: any): UnifiedButtonProps => ({
      disabled: props.disabled,
      loading: props.loading,
      type: props.type,
      href: props.href,
      target: props.target,
      rel: props.rel,
      ariaLabel: props.ariaLabel,
      testId: props.testId,
      className: props.className
    })
  },

  PrimaryButton: {
    componentName: 'PrimaryButton',
    newComponent: 'UnifiedButton',
    propsMapping: (props: any): UnifiedButtonProps => ({
      variant: 'primary',
      size: props.size || 'md',
      fullWidth: props.fullWidth,
      disabled: props.disabled,
      loading: props.loading,
      type: props.type,
      href: props.href,
      target: props.target,
      rel: props.rel,
      ariaLabel: props.ariaLabel,
      testId: props.testId
    })
  },

  SecondaryButton: {
    componentName: 'SecondaryButton', 
    newComponent: 'UnifiedButton',
    propsMapping: (props: any): UnifiedButtonProps => ({
      variant: 'secondary',
      size: props.size || 'md',
      fullWidth: props.fullWidth,
      disabled: props.disabled,
      loading: props.loading,
      type: props.type,
      href: props.href,
      target: props.target,
      rel: props.rel,
      ariaLabel: props.ariaLabel,
      testId: props.testId
    })
  },

  IconButton: {
    componentName: 'IconButton',
    newComponent: 'UnifiedButton',
    propsMapping: (props: any): UnifiedButtonProps => ({
      variant: props.variant || 'ghost',
      size: props.size || 'md',
      iconOnly: true,
      disabled: props.disabled,
      loading: props.loading,
      type: props.type,
      href: props.href,
      target: props.target,
      rel: props.rel,
      ariaLabel: props.ariaLabel,
      testId: props.testId
    })
  },

  Button: {
    componentName: 'Button',
    newComponent: 'UnifiedButton',
    propsMapping: (props: any): UnifiedButtonProps => ({
      variant: props.variant || 'primary',
      size: props.size || 'md',
      iconOnly: props.iconOnly,
      fullWidth: props.fullWidth,
      disabled: props.disabled,
      loading: props.loading,
      type: props.type,
      href: props.href,
      target: props.target,
      rel: props.rel,
      ariaLabel: props.ariaLabel,
      testId: props.testId
    })
  }
};

// Component usage finder
export const legacyComponentPatterns = {
  imports: [
    /import\s+(\w+)\s+from\s+['"].*\/BaseButton\.svelte['"];?/g,
    /import\s+(\w+)\s+from\s+['"].*\/PrimaryButton\.svelte['"];?/g,
    /import\s+(\w+)\s+from\s+['"].*\/SecondaryButton\.svelte['"];?/g,
    /import\s+(\w+)\s+from\s+['"].*\/IconButton\.svelte['"];?/g,
    /import\s+(\w+)\s+from\s+['"].*\/Button\.svelte['"];?/g
  ],
  usage: [
    /<BaseButton[\s\S]*?<\/BaseButton>/g,
    /<PrimaryButton[\s\S]*?<\/PrimaryButton>/g,
    /<SecondaryButton[\s\S]*?<\/SecondaryButton>/g,
    /<IconButton[\s\S]*?<\/IconButton>/g,
    /<Button[\s\S]*?(?:\/|<\/Button)>/g
  ]
};

// Migration functions
export function generateMigrationReport(fileContent: string): {
  foundComponents: string[];
  migrationCount: number;
  suggestions: string[];
} {
  const foundComponents: string[] = [];
  const suggestions: string[] = [];
  let migrationCount = 0;

  Object.entries(legacyComponentPatterns.imports).forEach(([index, pattern]) => {
    const matches = fileContent.match(pattern);
    if (matches) {
      const componentNames = Object.keys(migrationMappings);
      const componentName = componentNames[parseInt(index)];
      foundComponents.push(componentName);
      migrationCount += matches.length;
      
      suggestions.push(
        `Replace ${componentName} import with: import UnifiedButton from './UnifiedButton.svelte';`
      );
    }
  });

  return {
    foundComponents,
    migrationCount,
    suggestions
  };
}

export function migrateComponentUsage(
  fileContent: string,
  componentType: keyof typeof migrationMappings
): string {
  const mapping = migrationMappings[componentType];
  if (!mapping) {
    throw new Error(`Unknown component type: ${componentType}`);
  }

  // Replace import statement
  const importPattern = new RegExp(
    `import\\s+(\\w+)\\s+from\\s+['"].*\\/${componentType}\\.svelte['"];?`,
    'g'
  );
  
  let migratedContent = fileContent.replace(
    importPattern,
    `import UnifiedButton from './UnifiedButton.svelte';`
  );

  // Replace component usage (simplified - would need more sophisticated parsing for real implementation)
  const usagePattern = new RegExp(
    `<${componentType}([^>]*?)(?:/>|>([\\s\\S]*?)<\\/${componentType}>)`,
    'g'
  );

  migratedContent = migratedContent.replace(usagePattern, (match, props, content) => {
    // Parse props (simplified)
    const propsObj = parseProps(props || '');
    const migratedProps = mapping.propsMapping(propsObj);
    
    // Generate new props string
    const newPropsString = Object.entries(migratedProps)
      .filter(([, value]) => value !== undefined && value !== false)
      .map(([key, value]) => {
        if (value === true) return key;
        if (typeof value === 'string') return `${key}="${value}"`;
        return `${key}={${JSON.stringify(value)}}`;
      })
      .join(' ');

    // Return migrated component
    if (content) {
      return `<UnifiedButton ${newPropsString}>${content}</UnifiedButton>`;
    } else {
      return `<UnifiedButton ${newPropsString} />`;
    }
  });

  return migratedContent;
}

// Helper function to parse props from string (simplified)
function parseProps(propsString: string): Record<string, any> {
  const props: Record<string, any> = {};
  
  // Simple regex-based prop parsing (in real implementation, use proper parser)
  const propMatches = propsString.matchAll(/(\w+)(?:=(?:"([^"]*)"|{([^}]*)}|(\w+)))?/g);
  
  for (const match of propMatches) {
    const [, key, stringValue, objectValue, booleanValue] = match;
    
    if (stringValue !== undefined) {
      props[key] = stringValue;
    } else if (objectValue !== undefined) {
      try {
        props[key] = JSON.parse(objectValue);
      } catch {
        props[key] = objectValue;
      }
    } else if (booleanValue !== undefined) {
      props[key] = booleanValue === 'true';
    } else {
      props[key] = true; // Boolean prop
    }
  }
  
  return props;
}

// Migration validation
export function validateMigration(
  originalContent: string,
  migratedContent: string
): {
  isValid: boolean;
  issues: string[];
  suggestions: string[];
} {
  const issues: string[] = [];
  const suggestions: string[] = [];

  // Check if all legacy imports were replaced
  const legacyImports = legacyComponentPatterns.imports.some(pattern => 
    originalContent.match(pattern)
  );
  
  if (legacyImports && !migratedContent.includes('UnifiedButton')) {
    issues.push('Legacy button imports found but UnifiedButton import missing');
  }

  // Check for leftover legacy component usage
  Object.keys(migrationMappings).forEach(componentName => {
    const pattern = new RegExp(`<${componentName}[\\s\\S]*?>`, 'g');
    if (migratedContent.match(pattern)) {
      issues.push(`Legacy ${componentName} usage still found in migrated content`);
    }
  });

  // Provide suggestions
  if (issues.length === 0) {
    suggestions.push('Migration completed successfully!');
    suggestions.push('Consider running tests to ensure functionality is preserved');
    suggestions.push('Update any component documentation or stories');
  }

  return {
    isValid: issues.length === 0,
    issues,
    suggestions
  };
}

// Batch migration utility
export async function migrateBatchFiles(
  filePaths: string[],
  fileReader: (path: string) => Promise<string>,
  fileWriter: (path: string, content: string) => Promise<void>
): Promise<{
  successful: string[];
  failed: { path: string; error: string }[];
  totalMigrations: number;
}> {
  const successful: string[] = [];
  const failed: { path: string; error: string }[] = [];
  let totalMigrations = 0;

  for (const filePath of filePaths) {
    try {
      const originalContent = await fileReader(filePath);
      const report = generateMigrationReport(originalContent);
      
      if (report.migrationCount === 0) {
        continue; // Skip files with no legacy components
      }

      let migratedContent = originalContent;
      
      // Apply migrations for each found component type
      for (const componentType of report.foundComponents) {
        migratedContent = migrateComponentUsage(
          migratedContent,
          componentType as keyof typeof migrationMappings
        );
      }

      // Validate migration
      const validation = validateMigration(originalContent, migratedContent);
      
      if (!validation.isValid) {
        failed.push({
          path: filePath,
          error: validation.issues.join(', ')
        });
        continue;
      }

      // Write migrated file
      await fileWriter(filePath, migratedContent);
      successful.push(filePath);
      totalMigrations += report.migrationCount;

    } catch (error) {
      failed.push({
        path: filePath,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  return {
    successful,
    failed,
    totalMigrations
  };
}

// CLI-style migration report
export function generateMigrationSummary(
  successful: string[],
  failed: { path: string; error: string }[],
  totalMigrations: number
): string {
  return `
📊 Button Component Migration Report
=====================================

✅ Successfully migrated: ${successful.length} files
❌ Failed migrations: ${failed.length} files
🔄 Total component replacements: ${totalMigrations}

${successful.length > 0 ? `
Successful migrations:
${successful.map(file => `  ✓ ${file}`).join('\n')}
` : ''}

${failed.length > 0 ? `
Failed migrations:
${failed.map(f => `  ✗ ${f.path}: ${f.error}`).join('\n')}
` : ''}

Next steps:
1. Run tests to verify functionality
2. Update component documentation
3. Remove legacy component files
4. Update import statements in index files
`;
}

// Export all utilities
export default {
  migrationMappings,
  legacyComponentPatterns,
  generateMigrationReport,
  migrateComponentUsage,
  validateMigration,
  migrateBatchFiles,
  generateMigrationSummary
};