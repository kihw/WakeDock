# API URL Issues Fix Summary

## Issues Identified

1. **CSP (Content Security Policy) Invalid Sources**
   - Error: "The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '/api/v1'"
   - Error: "The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '/api/v1/ws'"

2. **Double API Path Issue**
   - Error: `POST http://195.201.199.226:3001/api/v1/api/v1/auth/login 403 (Forbidden)`
   - The URL construction was creating duplicate `/api/v1` in the path

3. **403 Forbidden Error**
   - Caused by invalid URLs due to the double path issue
   - CORS might also be affected

## Root Causes

### 1. CSP Configuration
The Content Security Policy was trying to use relative paths `/api/v1` and `/api/v1/ws` as origins, but CSP `connect-src` directive expects origins (schemes + domains) not just paths.

### 2. API URL Construction
- `baseUrl` was set to `/api/v1` in production
- `API_ENDPOINTS` already included `/api/v1` prefix
- URL construction: `${baseUrl}${path}` resulted in `/api/v1/api/v1/auth/login`

### 3. Environment Configuration
- Production environment was using an empty string for `apiUrl` instead of the correct `/api/v1`
- WebSocket URL was incorrectly constructed for production

## Fixes Applied

### 1. Fixed CSP Configuration (`dashboard/src/hooks.server.ts`)
```typescript
// BEFORE:
connect-src 'self' ${wakedockApiUrl} ${wsUrl}

// AFTER: 
connect-src 'self' // Production: only allow same-origin connections
// (Removed the invalid path-based sources)
```

### 2. Fixed API URL Configuration (`dashboard/src/lib/config/environment.ts`)
```typescript
// BEFORE:
apiUrl: typeof window !== 'undefined' && window.location.port === '3001'
  ? 'http://195.201.199.226:8000'
  : '',  // Empty string caused issues

// AFTER:
apiUrl: typeof window !== 'undefined' && window.location.port === '3001'
  ? 'http://195.201.199.226:8000'
  : '/api/v1',  // Correct relative URL
```

### 3. Fixed API Endpoints (`dashboard/src/lib/config/api.ts`)
Removed the `/api/v1` prefix from all endpoints since the baseUrl already includes it:

```typescript
// BEFORE:
AUTH: {
  LOGIN: '/api/v1/auth/login',
  // ...
}

// AFTER:
AUTH: {
  LOGIN: '/auth/login',
  // ...
}
```

### 4. Fixed WebSocket URL (`dashboard/src/lib/config/environment.ts`)
```typescript
// BEFORE:
wsUrl: `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost'}/api/ws`

// AFTER:
wsUrl: `/api/v1/ws`  // Relative WebSocket through proxy
```

## Expected Results

After these fixes:

1. **CSP Errors Resolved**: No more invalid source warnings in browser console
2. **Correct API URLs**: 
   - Development: `http://195.201.199.226:8000/auth/login`
   - Production: `/api/v1/auth/login` (relative, through proxy)
3. **No More 403 Errors**: URLs will hit the correct endpoints
4. **Proper CORS**: Requests go through the correct proxy setup

## Testing

1. **Development Environment**:
   - URLs should be absolute: `http://195.201.199.226:8000/auth/login`
   - Direct backend communication

2. **Production Environment**:
   - URLs should be relative: `/api/v1/auth/login`
   - Requests go through Caddy proxy

3. **Browser Console**:
   - No CSP violation errors
   - Network tab should show correct URLs
   - Login should work without 403 errors

## Files Modified

1. `dashboard/src/hooks.server.ts` - Fixed CSP configuration
2. `dashboard/src/lib/config/environment.ts` - Fixed API and WebSocket URLs
3. `dashboard/src/lib/config/api.ts` - Removed duplicate `/api/v1` prefix from endpoints

## Additional Notes

- The build completed successfully with only minor accessibility warnings (not breaking)
- All TypeScript compilation passed
- Environment detection works correctly (port 3001 = development)
- Runtime configuration API endpoint correctly provides environment-specific URLs

## Test File Created

Created `test-api-fix.html` to verify the fixes work correctly in both development and production environments.
