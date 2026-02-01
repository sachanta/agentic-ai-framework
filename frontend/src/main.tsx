import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

async function enableMocking() {
  const enableMocks = import.meta.env.VITE_ENABLE_MOCKS === 'true';

  console.log('[MSW] Environment:', {
    DEV: import.meta.env.DEV,
    VITE_ENABLE_MOCKS: import.meta.env.VITE_ENABLE_MOCKS,
    enableMocks,
  });

  if (enableMocks) {
    console.log('[MSW] Starting mock service worker...');
    try {
      const { worker } = await import('./mocks/browser');
      await worker.start({
        onUnhandledRequest: 'bypass',
        serviceWorker: {
          url: '/mockServiceWorker.js',
        },
      });
      console.log('[MSW] Mock service worker started successfully');
    } catch (error) {
      console.error('[MSW] Failed to start mock service worker:', error);
    }
  }
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
