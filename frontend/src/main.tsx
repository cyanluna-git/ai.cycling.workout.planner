import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { queryClient } from './lib/queryClient'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <SpeedInsights />
    </QueryClientProvider>
  </StrictMode>,
)
