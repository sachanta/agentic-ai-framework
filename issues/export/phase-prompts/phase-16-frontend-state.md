# Phase 16: Frontend State Management

## Goal
Implement global state management for UI preferences and notifications.

---

## Copilot Prompt

```
You are helping implement global state management for a React app using Zustand.

### Context
- UI state: theme, sidebar collapsed state
- Notification state: toast messages
- State should persist across page refreshes where appropriate

### Files to Read First
- frontend/src/store/authStore.ts (existing store pattern)

### Implementation Tasks

1. **Create UI store in `frontend/src/store/uiStore.ts`:**
   ```typescript
   import { create } from 'zustand'
   import { persist } from 'zustand/middleware'

   interface UIState {
     theme: 'light' | 'dark'
     sidebarCollapsed: boolean
     toggleTheme: () => void
     toggleSidebar: () => void
   }

   export const useUIStore = create<UIState>()(
     persist(
       (set) => ({
         theme: 'light',
         sidebarCollapsed: false,

         toggleTheme: () => set((state) => ({
           theme: state.theme === 'light' ? 'dark' : 'light'
         })),

         toggleSidebar: () => set((state) => ({
           sidebarCollapsed: !state.sidebarCollapsed
         })),
       }),
       { name: 'ui-storage' }
     )
   )
   ```

2. **Create notification store in `frontend/src/store/notificationStore.ts`:**
   ```typescript
   import { create } from 'zustand'

   interface Notification {
     id: string
     type: 'success' | 'error' | 'info' | 'warning'
     message: string
   }

   interface NotificationState {
     notifications: Notification[]
     addNotification: (type: Notification['type'], message: string) => void
     removeNotification: (id: string) => void
   }

   export const useNotificationStore = create<NotificationState>((set) => ({
     notifications: [],

     addNotification: (type, message) => {
       const id = Date.now().toString()
       set((state) => ({
         notifications: [...state.notifications, { id, type, message }]
       }))
       // Auto-remove after 5 seconds
       setTimeout(() => {
         set((state) => ({
           notifications: state.notifications.filter((n) => n.id !== id)
         }))
       }, 5000)
     },

     removeNotification: (id) => set((state) => ({
       notifications: state.notifications.filter((n) => n.id !== id)
     })),
   }))
   ```

3. **Create toast component in `frontend/src/components/Toast.tsx`:**
   ```typescript
   import { useNotificationStore } from '@/store/notificationStore'

   const COLORS = {
     success: 'bg-green-500',
     error: 'bg-red-500',
     info: 'bg-blue-500',
     warning: 'bg-yellow-500',
   }

   export function ToastContainer() {
     const { notifications, removeNotification } = useNotificationStore()

     return (
       <div className="fixed bottom-4 right-4 space-y-2">
         {notifications.map((n) => (
           <div
             key={n.id}
             className={`${COLORS[n.type]} text-white px-4 py-2 rounded shadow-lg flex items-center gap-2`}
           >
             <span>{n.message}</span>
             <button onClick={() => removeNotification(n.id)} className="ml-2">
               ×
             </button>
           </div>
         ))}
       </div>
     )
   }
   ```

4. **Add ToastContainer to App.tsx:**
   ```typescript
   import { ToastContainer } from '@/components/Toast'

   // In App component, add before closing </BrowserRouter>:
   <ToastContainer />
   ```

### Output
After implementing, provide:
1. Files created
2. How to trigger notifications
3. Example usage in components
```

---

## Human Checklist
- [ ] Test theme toggle persists
- [ ] Test notifications appear and auto-dismiss
- [ ] Test notification can be manually dismissed
