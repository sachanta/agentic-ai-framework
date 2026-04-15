# Phase 13: Frontend Authentication

## Goal
Implement user authentication with login page, auth state management, and protected routes.

---

## Copilot Prompt

```
You are helping implement authentication for a React frontend.

### Context
- Backend provides JWT tokens via POST /api/v1/auth/login
- Store token in localStorage via Zustand persist
- Protected routes redirect to login if not authenticated

### Files to Read First
- frontend/src/App.tsx (routing setup)
- frontend/src/store/ (existing stores)
- backend/app/api/v1/ (auth endpoints)

### Implementation Tasks

1. **Create auth store in `frontend/src/store/authStore.ts`:**
   ```typescript
   import { create } from 'zustand'
   import { persist } from 'zustand/middleware'

   interface User {
     id: string
     email: string
     name: string
   }

   interface AuthState {
     user: User | null
     token: string | null
     isAuthenticated: boolean
     login: (email: string, password: string) => Promise<void>
     logout: () => void
   }

   export const useAuthStore = create<AuthState>()(
     persist(
       (set) => ({
         user: null,
         token: null,
         isAuthenticated: false,

         login: async (email, password) => {
           const response = await fetch('/api/v1/auth/login', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ email, password }),
           })
           if (!response.ok) throw new Error('Login failed')
           const data = await response.json()
           set({ user: data.user, token: data.token, isAuthenticated: true })
         },

         logout: () => {
           set({ user: null, token: null, isAuthenticated: false })
         },
       }),
       { name: 'auth-storage' }
     )
   )
   ```

2. **Create login page in `frontend/src/pages/LoginPage.tsx`:**
   ```typescript
   import { useState } from 'react'
   import { useNavigate } from 'react-router-dom'
   import { useAuthStore } from '@/store/authStore'

   export function LoginPage() {
     const [email, setEmail] = useState('')
     const [password, setPassword] = useState('')
     const [error, setError] = useState('')
     const login = useAuthStore((state) => state.login)
     const navigate = useNavigate()

     const handleSubmit = async (e: React.FormEvent) => {
       e.preventDefault()
       try {
         await login(email, password)
         navigate('/')
       } catch (err) {
         setError('Invalid credentials')
       }
     }

     return (
       <div className="min-h-screen flex items-center justify-center">
         <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
           <h1 className="text-2xl font-bold mb-6">Login</h1>
           {error && <p className="text-red-500 mb-4">{error}</p>}
           <input
             type="email"
             placeholder="Email"
             value={email}
             onChange={(e) => setEmail(e.target.value)}
             className="w-full p-2 border rounded mb-4"
           />
           <input
             type="password"
             placeholder="Password"
             value={password}
             onChange={(e) => setPassword(e.target.value)}
             className="w-full p-2 border rounded mb-4"
           />
           <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
             Login
           </button>
         </form>
       </div>
     )
   }
   ```

3. **Create protected route component in `frontend/src/components/ProtectedRoute.tsx`:**
   ```typescript
   import { Navigate } from 'react-router-dom'
   import { useAuthStore } from '@/store/authStore'

   export function ProtectedRoute({ children }: { children: React.ReactNode }) {
     const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

     if (!isAuthenticated) {
       return <Navigate to="/login" replace />
     }

     return <>{children}</>
   }
   ```

4. **Update App.tsx with routes:**
   ```typescript
   import { LoginPage } from '@/pages/LoginPage'
   import { ProtectedRoute } from '@/components/ProtectedRoute'

   // Add routes:
   <Route path="/login" element={<LoginPage />} />
   <Route path="/" element={
     <ProtectedRoute>
       <HomePage />
     </ProtectedRoute>
   } />
   ```

### Output
After implementing, provide:
1. Files created/updated
2. How to test the login flow
3. How auth state persists across refreshes
```

---

## Human Checklist
- [ ] Test login with valid credentials
- [ ] Test redirect to login when not authenticated
- [ ] Test logout clears state
- [ ] Verify token persists in localStorage
