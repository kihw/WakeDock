// Quick test to verify component exports
import { Button } from '$lib/components/ui/atoms';
import { tokens } from '$lib/components/ui';

console.log('Button component:', Button);
console.log('Design tokens:', tokens);
console.log('Test successful - components are properly exported');
