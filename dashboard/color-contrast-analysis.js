/**
 * Color Contrast Analysis Script
 * Tests WakeDock design tokens for WCAG 2.1 AA compliance
 */

// Color contrast calculation functions
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    const srgb = c / 255;
    return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return 0;
  
  const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  
  return (brightest + 0.05) / (darkest + 0.05);
}

// Design tokens color palette
const colors = {
  primary: {
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
  secondary: {
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
  },
  success: {
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  warning: {
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
  },
  error: {
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  }
};

const backgroundColor = '#ffffff'; // White background

// WCAG requirements
const WCAG_AA_NORMAL = 4.5;
const WCAG_AA_LARGE = 3.0;
const WCAG_AAA_NORMAL = 7.0;
const WCAG_AAA_LARGE = 4.5;

console.log('🎨 WakeDock Color Contrast Analysis');
console.log('=====================================\n');

console.log('Testing against white background (#ffffff)\n');

// Test all color combinations
Object.entries(colors).forEach(([colorName, shades]) => {
  console.log(`📊 ${colorName.toUpperCase()} Colors:`);
  console.log('─'.repeat(50));
  
  Object.entries(shades).forEach(([shade, hex]) => {
    const ratio = getContrastRatio(hex, backgroundColor);
    const passesAA = ratio >= WCAG_AA_NORMAL;
    const passesAALarge = ratio >= WCAG_AA_LARGE;
    const passesAAA = ratio >= WCAG_AAA_NORMAL;
    const passesAAALarge = ratio >= WCAG_AAA_LARGE;
    
    const statusAA = passesAA ? '✅' : '❌';
    const statusAALarge = passesAALarge ? '✅' : '❌';
    const statusAAA = passesAAA ? '✅' : '❌';
    const statusAAALarge = passesAAALarge ? '✅' : '❌';
    
    console.log(`${colorName}-${shade} (${hex})`);
    console.log(`  Ratio: ${ratio.toFixed(2)}:1`);
    console.log(`  WCAG AA Normal (4.5:1):  ${statusAA}`);
    console.log(`  WCAG AA Large (3:1):     ${statusAALarge}`);
    console.log(`  WCAG AAA Normal (7:1):   ${statusAAA}`);
    console.log(`  WCAG AAA Large (4.5:1):  ${statusAAALarge}`);
    console.log('');
  });
  
  console.log('');
});

// Generate recommendations
console.log('🔧 RECOMMENDATIONS');
console.log('==================\n');

const recommendations = [];

// Check each color family
Object.entries(colors).forEach(([colorName, shades]) => {
  Object.entries(shades).forEach(([shade, hex]) => {
    const ratio = getContrastRatio(hex, backgroundColor);
    
    if (ratio < WCAG_AA_NORMAL) {
      const betterShades = Object.entries(shades).filter(([s, h]) => {
        return getContrastRatio(h, backgroundColor) >= WCAG_AA_NORMAL;
      });
      
      if (betterShades.length > 0) {
        const [betterShade, betterHex] = betterShades[0];
        recommendations.push({
          current: `${colorName}-${shade} (${hex})`,
          issue: `Fails WCAG AA (${ratio.toFixed(2)}:1)`,
          suggestion: `Use ${colorName}-${betterShade} (${betterHex}) instead`,
          newRatio: getContrastRatio(betterHex, backgroundColor).toFixed(2)
        });
      }
    }
  });
});

if (recommendations.length > 0) {
  console.log('❌ Colors that need updating for WCAG AA compliance:\n');
  
  recommendations.forEach((rec, index) => {
    console.log(`${index + 1}. ${rec.current}`);
    console.log(`   Issue: ${rec.issue}`);
    console.log(`   Fix: ${rec.suggestion}`);
    console.log(`   New ratio: ${rec.newRatio}:1\n`);
  });
} else {
  console.log('✅ All colors meet WCAG AA requirements!\n');
}

// Summary
const totalColors = Object.values(colors).reduce((acc, shades) => acc + Object.keys(shades).length, 0);
const compliantColors = Object.values(colors).reduce((acc, shades) => {
  return acc + Object.values(shades).filter(hex => getContrastRatio(hex, backgroundColor) >= WCAG_AA_NORMAL).length;
}, 0);

console.log('📈 SUMMARY');
console.log('==========');
console.log(`Total colors tested: ${totalColors}`);
console.log(`WCAG AA compliant: ${compliantColors}`);
console.log(`Compliance rate: ${((compliantColors / totalColors) * 100).toFixed(1)}%`);

if (compliantColors === totalColors) {
  console.log('\n🎉 Congratulations! All colors meet WCAG 2.1 AA standards.');
} else {
  console.log(`\n⚠️  ${totalColors - compliantColors} colors need updating for full compliance.`);
}

console.log('\n💡 Next steps:');
console.log('1. Update design tokens with recommended colors');
console.log('2. Update component variants to use compliant colors');
console.log('3. Test with actual screen readers and assistive technology');
console.log('4. Run automated accessibility tests (axe-core)');
console.log('5. Conduct user testing with people who use assistive technology');

console.log('\n🔗 Resources:');
console.log('- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/');
console.log('- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/');
console.log('- axe DevTools: https://www.deque.com/axe/devtools/');