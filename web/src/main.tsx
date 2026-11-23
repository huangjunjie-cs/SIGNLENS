import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import './index.css'
import { LangProvider } from './lib/i18n'
import Home from './pages/Home'

const Congress = lazy(() => import('./pages/Congress'))
const Polarization = lazy(() => import('./pages/Polarization'))
const Individual = lazy(() => import('./pages/Individual'))
const Temporal = lazy(() => import('./pages/Temporal'))
const Data = lazy(() => import('./pages/Data'))
const Methods = lazy(() => import('./pages/Methods'))

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LangProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading label="" />}>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="congress" element={<Congress />} />
              <Route path="polarization" element={<Polarization />} />
              <Route path="individual" element={<Individual />} />
              <Route path="temporal" element={<Temporal />} />
              <Route path="data" element={<Data />} />
              <Route path="methods" element={<Methods />} />
              <Route path="*" element={<div className="py-24 text-center text-fg-muted">404</div>} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </LangProvider>
  </StrictMode>,
)
