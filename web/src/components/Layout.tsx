import { motion } from 'motion/react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useLang, useT } from '../lib/i18n'

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <circle cx="12" cy="16" r="7.5" fill="#4f8ef7" fillOpacity="0.9" />
      <circle cx="20" cy="16" r="7.5" fill="#f59e42" fillOpacity="0.85" style={{ mixBlendMode: 'screen' }} />
      <path d="M16 10.2a7.5 7.5 0 0 1 0 11.6a7.5 7.5 0 0 1 0-11.6z" fill="#0b0f17" fillOpacity="0.55" />
    </svg>
  )
}

export default function Layout() {
  const t = useT()
  const { lang, setLang } = useLang()
  const loc = useLocation()
  const links = [
    { to: '/congress', label: t('Congress', '美国国会') },
    { to: '/polarization', label: t('Polarization Lab', '极化实验室') },
    { to: '/individual', label: t('Individuals', '个体分析') },
    { to: '/temporal', label: t('Over Time', '群体演化') },
    { to: '/data', label: t('Data', '数据') },
    { to: '/methods', label: t('Methods', '方法') },
  ]
  const home = loc.pathname === '/'
  return (
    <div className="min-h-screen">
      <nav className={`sticky top-0 z-40 border-b transition ${home ? 'border-transparent bg-ink-900/40' : 'border-white/[0.06] bg-ink-900/80'} backdrop-blur-xl`}>
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-5">
          <NavLink to="/" className="flex items-center gap-2.5">
            <Logo />
            <span className="font-display text-lg font-semibold tracking-tight">SIGNLENS</span>
          </NavLink>
          <div className="hidden flex-1 items-center gap-1 md:flex">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} className="relative rounded-md px-3 py-1.5 text-sm">
                {({ isActive }) => (
                  <>
                    {isActive && <motion.span layoutId="nav-pill" className="absolute inset-0 rounded-md bg-white/[0.07]" />}
                    <span className={`relative ${isActive ? 'text-fg' : 'text-fg-muted hover:text-fg'}`}>{l.label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button className="btn-ghost px-2.5! py-1! text-xs" onClick={() => setLang(lang === 'en' ? 'zh' : 'en')}>
              {lang === 'en' ? '中文' : 'EN'}
            </button>
            <a className="btn-ghost px-2.5! py-1! text-xs" href="/api/docs" target="_blank" rel="noreferrer">API</a>
          </div>
        </div>
        <div className="flex gap-1 overflow-x-auto px-4 pb-2 md:hidden">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={({ isActive }) => `shrink-0 rounded-md px-2.5 py-1 text-xs ${isActive ? 'bg-white/10 text-fg' : 'text-fg-muted'}`}>
              {l.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <main className={home ? '' : 'mx-auto max-w-7xl px-5 py-10'}>
        <Outlet />
      </main>
      <footer className="border-t border-white/[0.06] py-8 text-center text-xs text-fg-subtle">
        SIGNLENS · {t('A lens on polarized social relationships through signed graphs', '以符号网络透视极化的社会关系')} ·{' '}
        <a className="underline decoration-white/20 underline-offset-2 hover:text-fg-muted" href="https://ojs.aaai.org/index.php/ICWSM/article/view/18136" target="_blank" rel="noreferrer">
          ICWSM 2021
        </a>
      </footer>
    </div>
  )
}
