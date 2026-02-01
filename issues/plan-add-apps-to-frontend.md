# Plan: Add Apps Feature to Frontend

## Overview
Add an "Apps" section to the frontend that displays available multi-agent platforms (apps). Initially, this will show the "Hello World" app from the backend.

---

## Changes Required

### 1. Types (`src/types/`)

**New File: `src/types/app.ts`**
```typescript
// App/Platform types
export interface App {
  id: string;
  name: string;
  description: string;
  version: string;
  status: 'active' | 'inactive' | 'error';
  icon?: string;
  agents: string[];
  config?: Record<string, unknown>;
}

export interface AppAgent {
  id: string;
  name: string;
  description: string;
  status: string;
}

export interface AppExecuteRequest {
  input: Record<string, unknown>;
}

export interface AppExecuteResponse {
  result: Record<string, unknown>;
  agent: string;
  metadata?: Record<string, unknown>;
}

// Hello World specific
export interface HelloWorldRequest {
  name: string;
  style?: 'friendly' | 'formal' | 'casual' | 'enthusiastic';
}

export interface HelloWorldResponse {
  greeting: string;
  agent: string;
  metadata?: Record<string, unknown>;
}
```

**Update: `src/types/index.ts`**
- Export new app types

---

### 2. API Service (`src/api/`)

**New File: `src/api/apps.ts`**
```typescript
// API endpoints for apps/platforms
- list(): GET /api/v1/platforms - List all available apps
- get(appId): GET /api/v1/platforms/{appId} - Get app details
- getAgents(appId): GET /api/v1/platforms/{appId}/agents - List app agents
- execute(appId, request): POST /api/v1/platforms/{appId}/execute - Execute app
- getStatus(appId): GET /api/v1/platforms/{appId}/status - Get app status
```

**Hello World specific:**
```typescript
// Hello World app specific endpoints
- helloWorld.execute(request): POST /api/v1/platforms/hello-world/execute
- helloWorld.getStatus(): GET /api/v1/platforms/hello-world/status
- helloWorld.getAgents(): GET /api/v1/platforms/hello-world/agents
```

---

### 3. React Query Hooks (`src/hooks/`)

**New File: `src/hooks/useApps.ts`**
```typescript
// Hooks for apps data fetching
- useApps() - List all apps with caching
- useApp(appId) - Get single app details
- useAppAgents(appId) - Get app's agents
- useAppStatus(appId) - Get app status with polling
- useExecuteApp() - Mutation for executing an app
```

**New File: `src/hooks/useHelloWorld.ts`**
```typescript
// Hello World specific hooks
- useHelloWorldStatus() - Get Hello World status
- useExecuteHelloWorld() - Execute greeting generation
```

---

### 4. UI Components (`src/components/`)

**New Directory: `src/components/apps/`**

| File | Description |
|------|-------------|
| `AppList.tsx` | Grid/list of all available apps with cards |
| `AppCard.tsx` | Individual app card with icon, name, description, status badge |
| `AppDetail.tsx` | Full app detail view with agents list and execute button |
| `AppStatusBadge.tsx` | Status indicator for app (active/inactive/error) |

**New Directory: `src/components/apps/hello-world/`**

| File | Description |
|------|-------------|
| `HelloWorldApp.tsx` | Main Hello World app component |
| `GreetingForm.tsx` | Form to input name and select greeting style |
| `GreetingResult.tsx` | Display generated greeting result |

---

### 5. Pages (`src/pages/`)

**New File: `src/pages/AppsPage.tsx`**
- Main apps listing page
- Shows grid of available apps as cards
- Each card links to app detail page
- Filter by status (active/inactive)

**New File: `src/pages/AppDetailPage.tsx`**
- App detail view with:
  - App info (name, description, version, status)
  - List of agents in the app
  - Execute button (redirects to app-specific page)

**New File: `src/pages/apps/HelloWorldPage.tsx`**
- Hello World app interactive page
- Input form for name and style selection
- Execute button
- Display greeting result
- Show agent information

---

### 6. Routing (`src/App.tsx`)

**Add new routes:**
```typescript
// Apps routes
<Route path="/apps" element={<AppsPage />} />
<Route path="/apps/:appId" element={<AppDetailPage />} />

// App-specific routes
<Route path="/apps/hello-world" element={<HelloWorldPage />} />
```

**Update constants:** `src/utils/constants.ts`
```typescript
export const ROUTES = {
  // ... existing routes
  APPS: '/apps',
  APP_DETAIL: '/apps/:appId',
  HELLO_WORLD_APP: '/apps/hello-world',
};
```

---

### 7. Layout Updates

**Update: `src/components/layout/Header.tsx`**
- Add "Apps" button in the top-right area (before notifications/user menu)
- Button with grid/apps icon from lucide-react
- Clicking opens a dropdown or navigates to /apps page

```tsx
// Add to Header.tsx (right side, before notifications)
<Button variant="ghost" size="icon" onClick={() => navigate('/apps')}>
  <LayoutGrid className="h-5 w-5" />
</Button>
// Or with tooltip:
<Tooltip>
  <TooltipTrigger asChild>
    <Button variant="ghost" size="icon" asChild>
      <Link to="/apps">
        <LayoutGrid className="h-5 w-5" />
      </Link>
    </Button>
  </TooltipTrigger>
  <TooltipContent>Apps</TooltipContent>
</Tooltip>
```

**Update: `src/components/layout/Sidebar.tsx`**
- Add "Apps" navigation item to sidebar
- Position: After "Dashboard" or as a prominent item
- Icon: `LayoutGrid` or `Boxes` from lucide-react

```tsx
// Add to navigation items
{
  name: 'Apps',
  href: '/apps',
  icon: LayoutGrid,
}
```

---

### 8. Dashboard Integration

**Update: `src/pages/DashboardPage.tsx`**
- Add "Apps" section or card showing available apps count
- Quick link to apps page

**Update: `src/components/dashboard/QuickActions.tsx`**
- Add "Launch App" quick action button

---

### 9. MSW Mock Handlers (`src/mocks/handlers/`)

**New File: `src/mocks/handlers/apps.ts`**
```typescript
// Mock handlers for apps endpoints
- GET /api/v1/platforms - Return list of mock apps
- GET /api/v1/platforms/:id - Return single app
- GET /api/v1/platforms/:id/agents - Return app agents
- GET /api/v1/platforms/:id/status - Return app status
- POST /api/v1/platforms/:id/execute - Execute app

// Hello World specific
- GET /api/v1/platforms/hello-world/status
- GET /api/v1/platforms/hello-world/agents
- POST /api/v1/platforms/hello-world/execute
```

**New File: `src/mocks/data/apps.ts`**
```typescript
// Mock data for apps
export const mockApps = [
  {
    id: 'hello-world',
    name: 'Hello World',
    description: 'A sample multi-agent platform for demonstration',
    version: '1.0.0',
    status: 'active',
    icon: 'hand-wave',
    agents: ['greeter'],
  },
];
```

**Update: `src/mocks/handlers/index.ts`**
- Import and include `appsHandlers`

---

## File Summary

### New Files (16 files)

| Category | File Path |
|----------|-----------|
| Types | `src/types/app.ts` |
| API | `src/api/apps.ts` |
| Hooks | `src/hooks/useApps.ts` |
| Hooks | `src/hooks/useHelloWorld.ts` |
| Components | `src/components/apps/AppList.tsx` |
| Components | `src/components/apps/AppCard.tsx` |
| Components | `src/components/apps/AppDetail.tsx` |
| Components | `src/components/apps/AppStatusBadge.tsx` |
| Components | `src/components/apps/hello-world/HelloWorldApp.tsx` |
| Components | `src/components/apps/hello-world/GreetingForm.tsx` |
| Components | `src/components/apps/hello-world/GreetingResult.tsx` |
| Pages | `src/pages/AppsPage.tsx` |
| Pages | `src/pages/AppDetailPage.tsx` |
| Pages | `src/pages/apps/HelloWorldPage.tsx` |
| Mocks | `src/mocks/handlers/apps.ts` |
| Mocks | `src/mocks/data/apps.ts` |

### Modified Files (7 files)

| File Path | Changes |
|-----------|---------|
| `src/types/index.ts` | Export app types |
| `src/App.tsx` | Add apps routes |
| `src/utils/constants.ts` | Add ROUTES constants |
| `src/components/layout/Header.tsx` | Add Apps button |
| `src/components/layout/Sidebar.tsx` | Add Apps nav item |
| `src/pages/DashboardPage.tsx` | Add apps summary (optional) |
| `src/mocks/handlers/index.ts` | Include apps handlers |

---

## Implementation Order

1. **Phase 1: Foundation**
   - Create types (`app.ts`)
   - Create API service (`apps.ts`)
   - Create hooks (`useApps.ts`, `useHelloWorld.ts`)
   - Create mock data and handlers

2. **Phase 2: Components**
   - Create app components (`AppList`, `AppCard`, `AppDetail`, `AppStatusBadge`)
   - Create Hello World components

3. **Phase 3: Pages & Routing**
   - Create pages (`AppsPage`, `AppDetailPage`, `HelloWorldPage`)
   - Update routes in `App.tsx`
   - Update constants

4. **Phase 4: Layout Integration**
   - Update Header with Apps button
   - Update Sidebar with Apps nav item
   - (Optional) Update Dashboard

5. **Phase 5: Testing**
   - Verify MSW mocks work
   - Test navigation flow
   - Test Hello World execution

---

## UI/UX Considerations

### Apps Page Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Apps                                        [Filter ▼]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  👋              │  │  (Future App)   │                  │
│  │  Hello World    │  │                 │                  │
│  │  Sample demo    │  │                 │                  │
│  │  ● Active       │  │                 │                  │
│  │  [Launch]       │  │                 │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Hello World App Page Layout
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back    Hello World                        ● Active      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A sample multi-agent platform for demonstration            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Generate a Greeting                                │   │
│  │                                                     │   │
│  │  Name: [____________________]                       │   │
│  │                                                     │   │
│  │  Style: [Friendly ▼]                                │   │
│  │         • Friendly                                  │   │
│  │         • Formal                                    │   │
│  │         • Casual                                    │   │
│  │         • Enthusiastic                              │   │
│  │                                                     │   │
│  │  [Generate Greeting]                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Result:                                            │   │
│  │  "Hello there, John! Hope you're having a           │   │
│  │   wonderful day!"                                   │   │
│  │                                                     │   │
│  │  Agent: greeter                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Header Apps Button
```
┌─────────────────────────────────────────────────────────────┐
│  [≡] Agentic AI Framework          [🔲] [🔔] [👤 Admin ▼]  │
└─────────────────────────────────────────────────────────────┘
                                      ↑
                                  Apps button
```

---

## Notes

- The "Apps" terminology is used in the frontend to be user-friendly (instead of "Platforms")
- Backend uses "platforms" terminology - the API service will map between them
- Future apps can be added by:
  1. Adding to backend platforms
  2. Creating app-specific components in `src/components/apps/{app-name}/`
  3. Creating app page in `src/pages/apps/{AppName}Page.tsx`
  4. Adding route in `App.tsx`
