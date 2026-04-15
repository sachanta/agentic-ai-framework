# Phase 14: Frontend API Client Layer

## Goal
Create typed API clients with Axios and React Query hooks for data fetching.

---

## Copilot Prompt

```
You are helping create API client layer for a React frontend.

### Context
- Use Axios for HTTP requests with auth token injection
- Use React Query for caching and state management
- API base URL is /api/v1

### Files to Read First
- frontend/src/store/authStore.ts (for auth token)
- backend/app/platforms/hello_world/schemas/ (API types)

### Implementation Tasks

1. **Create Axios client in `frontend/src/api/client.ts`:**
   ```typescript
   import axios from 'axios'
   import { useAuthStore } from '@/store/authStore'

   export const apiClient = axios.create({
     baseURL: '/api/v1',
     headers: { 'Content-Type': 'application/json' },
   })

   // Add auth token to requests
   apiClient.interceptors.request.use((config) => {
     const token = useAuthStore.getState().token
     if (token) {
       config.headers.Authorization = `Bearer ${token}`
     }
     return config
   })

   // Handle 401 errors
   apiClient.interceptors.response.use(
     (response) => response,
     (error) => {
       if (error.response?.status === 401) {
         useAuthStore.getState().logout()
       }
       return Promise.reject(error)
     }
   )
   ```

2. **Create types in `frontend/src/types/helloWorld.ts`:**
   ```typescript
   export interface GreetingRequest {
     name: string
     style: 'friendly' | 'formal' | 'casual' | 'enthusiastic'
   }

   export interface GreetingResponse {
     success: boolean
     greeting: string
     style: string
     used_fallback: boolean
     timestamp: string
   }

   export interface PlatformStatus {
     platform: string
     status: string
     agents: string[]
   }
   ```

3. **Create API functions in `frontend/src/api/helloWorld.ts`:**
   ```typescript
   import { apiClient } from './client'
   import { GreetingRequest, GreetingResponse, PlatformStatus } from '@/types/helloWorld'

   export const helloWorldApi = {
     execute: async (request: GreetingRequest): Promise<GreetingResponse> => {
       const { data } = await apiClient.post('/platforms/hello-world/execute', request)
       return data
     },

     getStatus: async (): Promise<PlatformStatus> => {
       const { data } = await apiClient.get('/platforms/hello-world/status')
       return data
     },

     getHealth: async () => {
       const { data } = await apiClient.get('/platforms/hello-world/health')
       return data
     },
   }
   ```

4. **Create React Query hooks in `frontend/src/hooks/useHelloWorld.ts`:**
   ```typescript
   import { useMutation, useQuery } from '@tanstack/react-query'
   import { helloWorldApi } from '@/api/helloWorld'
   import { GreetingRequest } from '@/types/helloWorld'

   export function useExecuteGreeting() {
     return useMutation({
       mutationFn: (request: GreetingRequest) => helloWorldApi.execute(request),
     })
   }

   export function usePlatformStatus() {
     return useQuery({
       queryKey: ['hello-world', 'status'],
       queryFn: helloWorldApi.getStatus,
     })
   }

   export function usePlatformHealth() {
     return useQuery({
       queryKey: ['hello-world', 'health'],
       queryFn: helloWorldApi.getHealth,
       refetchInterval: 30000, // Refresh every 30s
     })
   }
   ```

### Output
After implementing, provide:
1. Files created
2. How to use the hooks in components
3. Example usage
```

---

## Human Checklist
- [ ] Test API client with real backend
- [ ] Verify auth token is included in requests
- [ ] Test error handling on 401
