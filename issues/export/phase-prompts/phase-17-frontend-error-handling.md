# Phase 17: Frontend Error Handling & Loading

## Goal
Implement error boundaries, loading states, and graceful error handling.

---

## Copilot Prompt

```
You are helping implement error handling for a React app.

### Context
- Error boundaries catch rendering errors
- Loading skeletons show during data fetching
- API errors display user-friendly messages
- Retry mechanisms for failed requests

### Files to Read First
- frontend/src/components/ (existing components)
- frontend/src/hooks/useHelloWorld.ts (API hooks)

### Implementation Tasks

1. **Create error boundary in `frontend/src/components/ErrorBoundary.tsx`:**
   ```typescript
   import { Component, ReactNode } from 'react'

   interface Props {
     children: ReactNode
     fallback?: ReactNode
   }

   interface State {
     hasError: boolean
     error: Error | null
   }

   export class ErrorBoundary extends Component<Props, State> {
     state: State = { hasError: false, error: null }

     static getDerivedStateFromError(error: Error): State {
       return { hasError: true, error }
     }

     render() {
       if (this.state.hasError) {
         return this.props.fallback || (
           <div className="p-4 bg-red-50 border border-red-200 rounded">
             <h2 className="text-lg font-bold text-red-700">Something went wrong</h2>
             <p className="text-red-600">{this.state.error?.message}</p>
             <button
               onClick={() => this.setState({ hasError: false, error: null })}
               className="mt-2 bg-red-500 text-white px-4 py-2 rounded"
             >
               Try Again
             </button>
           </div>
         )
       }
       return this.props.children
     }
   }
   ```

2. **Create loading skeleton in `frontend/src/components/Skeleton.tsx`:**
   ```typescript
   interface SkeletonProps {
     className?: string
   }

   export function Skeleton({ className = '' }: SkeletonProps) {
     return (
       <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
     )
   }

   export function CardSkeleton() {
     return (
       <div className="border rounded p-4 space-y-3">
         <Skeleton className="h-4 w-3/4" />
         <Skeleton className="h-4 w-1/2" />
         <Skeleton className="h-8 w-full" />
       </div>
     )
   }
   ```

3. **Create API error component in `frontend/src/components/ApiError.tsx`:**
   ```typescript
   interface ApiErrorProps {
     error: Error
     onRetry?: () => void
   }

   export function ApiError({ error, onRetry }: ApiErrorProps) {
     const message = error.message || 'An unexpected error occurred'

     return (
       <div className="bg-red-50 border border-red-200 rounded p-4">
         <p className="text-red-700">{message}</p>
         {onRetry && (
           <button
             onClick={onRetry}
             className="mt-2 text-red-600 underline hover:text-red-800"
           >
             Retry
           </button>
         )}
       </div>
     )
   }
   ```

4. **Update HelloWorldPage with loading and error states:**
   ```typescript
   import { CardSkeleton } from '@/components/Skeleton'
   import { ApiError } from '@/components/ApiError'
   import { ErrorBoundary } from '@/components/ErrorBoundary'

   export function HelloWorldPage() {
     const { data: health, isLoading, error, refetch } = usePlatformHealth()

     return (
       <ErrorBoundary>
         <div className="max-w-md mx-auto p-6">
           {isLoading && <CardSkeleton />}
           {error && <ApiError error={error} onRetry={() => refetch()} />}
           {health && (
             // ... existing content
           )}
         </div>
       </ErrorBoundary>
     )
   }
   ```

5. **Wrap App with ErrorBoundary:**
   ```typescript
   // In App.tsx:
   <ErrorBoundary>
     <BrowserRouter>
       {/* ... routes */}
     </BrowserRouter>
   </ErrorBoundary>
   ```

### Output
After implementing, provide:
1. Files created
2. How to test error boundary
3. How to test loading states
```

---

## Human Checklist
- [ ] Test error boundary catches errors
- [ ] Test skeleton shows during loading
- [ ] Test retry button works
- [ ] Verify errors don't crash the app
