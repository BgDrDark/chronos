# Error Handling Guide

## Type-Safe Error Handling with `getErrorMessage`

This project uses a type-safe approach to error handling to eliminate `any` types and improve type safety.

### The Problem

Traditional error handling uses `any`:
```typescript
try {
  await apiCall();
} catch (err: any) {
  setError(err.message); // ❌ Bad - loses type safety
}
```

### The Solution

We use a type-safe `getErrorMessage` function that handles different error types:

```typescript
try {
  await apiCall();
} catch (err) {
  setError(getErrorMessage(err)); // ✅ Good - type-safe
}
```

### The Function

Located in `frontend/src/types.ts`:

```typescript
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  
  if (typeof error === 'object' && error !== null) {
    const err = error as { 
      response?: { 
        data?: { 
          detail?: string | { message?: string } 
        } 
      }; 
      message?: string 
    };
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') 
        return err.response.data.detail;
      if (err.response.data.detail.message) 
        return err.response.data.detail.message;
    }
    if (err.message) return err.message;
  }
  
  return 'Неизвестна грешка';
}
```

### Supported Error Types

1. **Standard Error**: `throw new Error('message')`
2. **String Error**: `throw 'message'`
3. **Fetch Error**: `response.json()` errors with `detail`
4. **Axios Error**: `axios` errors with `response.data.detail`
5. **GraphQL Error**: Apollo errors

### Usage

Import and use in any component:

```typescript
import { getErrorMessage } from '../types';

// In catch block:
} catch (err) {
  alert(getErrorMessage(err));
}

// Or for setting state:
} catch (err) {
  setError(getErrorMessage(err));
}
```

### Benefits

- **No `any` types** - Eliminates TypeScript `@typescript-eslint/no-explicit-any` errors
- **Type-safe** - Uses `unknown` instead of `any`
- **Consistent** - Single function handles all error types
- **Easy to extend** - Add new error type handling in one place

### Files Using This Pattern

- LoginPage.tsx
- ForgotPasswordPage.tsx
- ResetPasswordPage.tsx
- DashboardPage.tsx
- ProfilePage.tsx
- KioskAdminPage.tsx
- LeavesPage.tsx
- MySchedulePage.tsx
- biometricService.ts
- And more...
