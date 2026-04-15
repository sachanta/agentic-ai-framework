# Phase 15: Hello World UI Components

## Goal
Build the user interface for generating greetings with the Hello World platform.

---

## Copilot Prompt

```
You are helping build UI components for a greeting generator app in React.

### Context
- User enters their name and selects a greeting style
- Form submits to API and displays the generated greeting
- Use Tailwind CSS for styling
- Use the React Query hooks from Phase 14

### Files to Read First
- frontend/src/hooks/useHelloWorld.ts (API hooks)
- frontend/src/types/helloWorld.ts (types)

### Implementation Tasks

1. **Create greeting form in `frontend/src/components/GreetingForm.tsx`:**
   ```typescript
   import { useState } from 'react'

   interface GreetingFormProps {
     onSubmit: (name: string, style: string) => void
     isLoading: boolean
   }

   const STYLES = [
     { value: 'friendly', label: 'Friendly' },
     { value: 'formal', label: 'Formal' },
     { value: 'casual', label: 'Casual' },
     { value: 'enthusiastic', label: 'Enthusiastic' },
   ]

   export function GreetingForm({ onSubmit, isLoading }: GreetingFormProps) {
     const [name, setName] = useState('')
     const [style, setStyle] = useState('friendly')

     const handleSubmit = (e: React.FormEvent) => {
       e.preventDefault()
       if (name.trim()) {
         onSubmit(name, style)
       }
     }

     return (
       <form onSubmit={handleSubmit} className="space-y-4">
         <div>
           <label className="block text-sm font-medium mb-1">Your Name</label>
           <input
             type="text"
             value={name}
             onChange={(e) => setName(e.target.value)}
             placeholder="Enter your name"
             className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
             required
           />
         </div>

         <div>
           <label className="block text-sm font-medium mb-1">Greeting Style</label>
           <select
             value={style}
             onChange={(e) => setStyle(e.target.value)}
             className="w-full p-2 border rounded"
           >
             {STYLES.map((s) => (
               <option key={s.value} value={s.value}>{s.label}</option>
             ))}
           </select>
         </div>

         <button
           type="submit"
           disabled={isLoading}
           className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 disabled:opacity-50"
         >
           {isLoading ? 'Generating...' : 'Generate Greeting'}
         </button>
       </form>
     )
   }
   ```

2. **Create result display in `frontend/src/components/GreetingResult.tsx`:**
   ```typescript
   import { GreetingResponse } from '@/types/helloWorld'

   interface GreetingResultProps {
     result: GreetingResponse | null
     error: Error | null
   }

   export function GreetingResult({ result, error }: GreetingResultProps) {
     if (error) {
       return (
         <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded">
           Error: {error.message}
         </div>
       )
     }

     if (!result) return null

     return (
       <div className="bg-green-50 border border-green-200 p-4 rounded">
         <p className="text-xl font-medium">{result.greeting}</p>
         <p className="text-sm text-gray-500 mt-2">
           Style: {result.style}
           {result.used_fallback && ' (fallback)'}
         </p>
       </div>
     )
   }
   ```

3. **Create page in `frontend/src/pages/HelloWorldPage.tsx`:**
   ```typescript
   import { GreetingForm } from '@/components/GreetingForm'
   import { GreetingResult } from '@/components/GreetingResult'
   import { useExecuteGreeting, usePlatformHealth } from '@/hooks/useHelloWorld'

   export function HelloWorldPage() {
     const mutation = useExecuteGreeting()
     const { data: health } = usePlatformHealth()

     const handleSubmit = (name: string, style: string) => {
       mutation.mutate({ name, style: style as any })
     }

     return (
       <div className="max-w-md mx-auto p-6">
         <h1 className="text-2xl font-bold mb-6">Hello World Greeting Generator</h1>

         {health && (
           <div className={`mb-4 p-2 rounded text-sm ${
             health.llm_available ? 'bg-green-100' : 'bg-yellow-100'
           }`}>
             LLM: {health.llm_available ? 'Available' : 'Unavailable (using fallback)'}
           </div>
         )}

         <GreetingForm
           onSubmit={handleSubmit}
           isLoading={mutation.isPending}
         />

         <div className="mt-6">
           <GreetingResult
             result={mutation.data ?? null}
             error={mutation.error}
           />
         </div>
       </div>
     )
   }
   ```

4. **Add route in App.tsx:**
   ```typescript
   import { HelloWorldPage } from '@/pages/HelloWorldPage'

   // Add to routes:
   <Route path="/hello-world" element={
     <ProtectedRoute>
       <HelloWorldPage />
     </ProtectedRoute>
   } />
   ```

### Output
After implementing, provide:
1. Files created
2. How to test the UI
3. Screenshot description of the interface
```

---

## Human Checklist
- [ ] Test form submission
- [ ] Test all greeting styles
- [ ] Test error display
- [ ] Verify loading state shows correctly
