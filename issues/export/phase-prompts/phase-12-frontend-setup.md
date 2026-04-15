# Phase 12: Frontend Project Setup

## Goal
Initialize the React frontend with Vite, TypeScript, and Tailwind CSS.

---

## Copilot Prompt

```
You are helping set up a React frontend for a multi-agent AI framework.

### Context
- Using Vite as build tool (fast dev server, optimized builds)
- React 18 with TypeScript
- Tailwind CSS for styling
- The frontend talks to a FastAPI backend at http://localhost:8000

### Files to Read First
- frontend/package.json (if exists)
- frontend/vite.config.ts (if exists)
- frontend/src/ (existing code)

### Implementation Tasks

1. **Verify/Create `frontend/package.json` dependencies:**
   ```json
   {
     "dependencies": {
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "react-router-dom": "^6.22.0",
       "@tanstack/react-query": "^5.17.0",
       "axios": "^1.6.0",
       "zustand": "^4.5.0"
     },
     "devDependencies": {
       "typescript": "^5.3.0",
       "vite": "^5.1.0",
       "@vitejs/plugin-react": "^4.2.0",
       "tailwindcss": "^3.4.0",
       "autoprefixer": "^10.4.0",
       "postcss": "^8.4.0"
     }
   }
   ```

2. **Configure Vite in `frontend/vite.config.ts`:**
   ```typescript
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import path from 'path'

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       },
     },
     server: {
       port: 5173,
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         },
       },
     },
   })
   ```

3. **Configure Tailwind in `frontend/tailwind.config.js`:**
   ```javascript
   /** @type {import('tailwindcss').Config} */
   export default {
     content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
     theme: {
       extend: {},
     },
     plugins: [],
   }
   ```

4. **Create base styles in `frontend/src/index.css`:**
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

5. **Create entry point `frontend/src/main.tsx`:**
   ```typescript
   import React from 'react'
   import ReactDOM from 'react-dom/client'
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   import App from './App'
   import './index.css'

   const queryClient = new QueryClient()

   ReactDOM.createRoot(document.getElementById('root')!).render(
     <React.StrictMode>
       <QueryClientProvider client={queryClient}>
         <App />
       </QueryClientProvider>
     </React.StrictMode>,
   )
   ```

6. **Create basic App component `frontend/src/App.tsx`:**
   ```typescript
   import { BrowserRouter, Routes, Route } from 'react-router-dom'

   function App() {
     return (
       <BrowserRouter>
         <div className="min-h-screen bg-gray-100">
           <Routes>
             <Route path="/" element={<div className="p-4">Hello World App</div>} />
           </Routes>
         </div>
       </BrowserRouter>
     )
   }

   export default App
   ```

### Commands
```bash
cd frontend
npm install
npm run dev
```

### Output
After implementing, provide:
1. Files created/updated
2. Commands to run the dev server
3. URL to access the app (http://localhost:5173)
```

---

## Human Checklist
- [ ] Run `npm install` and verify no errors
- [ ] Run `npm run dev` and verify dev server starts
- [ ] Open http://localhost:5173 and verify app loads
