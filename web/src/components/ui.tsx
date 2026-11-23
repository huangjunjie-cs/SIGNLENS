import { motion } from 'motion/react'
import { useState, type ReactNode } from 'react'
import { api, useAsync, type DatasetMeta } from '../lib/api'
import { useLabels, useT } from '../lib/i18n'

export function PageHeader({ kicker, title, children }: { kicker: string; title: string; children?: ReactNode }) {
  return (
    <motion.header initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-8">
      <div className="label mb-2 text-accent!">{kicker}</div>
      <h1 className="font-display text-3xl font-semibold tracking-tight text-fg md:text-4xl">{title}</h1>
      {children && <div className="mt-3 max-w-3xl text-[15px] leading-relaxed text-fg-muted">{children}</div>}
    </motion.header>
  )
}

export function Card({ title, subtitle, right, children, className = '' }: {
  title?: ReactNode
  subtitle?: ReactNode
  right?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || right) && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-fg">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs leading-relaxed text-fg-subtle">{subtitle}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

export function InfoTip({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <span className="relative inline-block" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <span className="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-white/15 text-[10px] text-fg-subtle">
        ?
      </span>
      {open && (
        <span className="absolute left-1/2 top-6 z-30 w-64 -translate-x-1/2 rounded-lg border border-white/10 bg-ink-800 p-3 text-xs font-normal normal-case leading-relaxed tracking-normal text-fg-muted shadow-2xl">
          {children}
        </span>
      )}
    </span>
  )
}

/** A metric with a meter whose length always reads "how polarized": `polar` says which end of
 *  the value range is the polarized one (`low` = small values are polarized, the bar is inverted). */
export function Metric({
  label,
  value,
  display,
  help,
  min = 0,
  max = 1,
  polar = 'high',
  hint,
  delay = 0,
}: {
  label: string
  value: number | null | undefined
  display?: string
  help?: ReactNode
  min?: number
  max?: number
  polar?: 'high' | 'low' | 'none'
  hint?: string
  delay?: number
}) {
  const v = value ?? null
  const frac = v === null ? 0 : Math.max(0, Math.min(1, (v - min) / (max - min)))
  const intensity = polar === 'high' ? frac : polar === 'low' ? 1 - frac : 0.5
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="rounded-xl border border-white/[0.06] bg-ink-900/60 p-4"
    >
      <div className="flex items-center text-xs text-fg-muted">
        {label}
        {help && <InfoTip>{help}</InfoTip>}
      </div>
      <div className="tabular mt-1.5 font-mono text-2xl font-medium text-fg">
        {display ?? (v === null ? '—' : +v.toFixed(3))}
      </div>
      {polar !== 'none' && (
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(90deg, #6b7280, color-mix(in oklab, #f0506e ${Math.round(intensity * 100)}%, #8b7cf6))`,
            }}
            initial={{ width: 0 }}
            animate={{ width: `${intensity * 100}%` }}
            transition={{ duration: 0.9, delay: delay + 0.1, ease: 'easeOut' }}
          />
        </div>
      )}
      {hint && <div className="mt-2 text-[11px] text-fg-subtle">{hint}</div>}
    </motion.div>
  )
}

export function Loading({ label }: { label?: string }) {
  const t = useT()
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-sm text-fg-subtle">
      <span className="relative flex h-3 w-6">
        <motion.span className="absolute h-3 w-3 rounded-full bg-camp-a" animate={{ x: [0, 12, 0] }} transition={{ repeat: Infinity, duration: 1.2 }} />
        <motion.span className="absolute h-3 w-3 rounded-full bg-camp-b" animate={{ x: [12, 0, 12] }} transition={{ repeat: Infinity, duration: 1.2 }} />
      </span>
      {label ?? t('Computing…', '计算中…')}
    </div>
  )
}

export function ErrorBox({ error }: { error: string }) {
  return <div className="rounded-xl border border-neg/30 bg-neg/10 px-4 py-3 text-sm text-neg">{error}</div>
}

export function Segmented<T extends string>({ value, options, onChange }: {
  value: T
  options: { value: T; label: string }[]
  onChange: (v: T) => void
}) {
  return (
    <div className="inline-flex rounded-lg border border-white/10 bg-ink-900 p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={`relative rounded-md px-3 py-1.5 text-xs font-medium transition ${value === o.value ? 'text-fg' : 'text-fg-subtle hover:text-fg-muted'}`}
        >
          {value === o.value && (
            <motion.span layoutId={`seg-${options.map((x) => x.value).join()}`} className="absolute inset-0 rounded-md bg-white/[0.08]" />
          )}
          <span className="relative">{o.label}</span>
        </button>
      ))}
    </div>
  )
}

export function DatasetPicker({
  value,
  onChange,
  filter,
}: {
  value: string
  onChange: (id: string, meta?: DatasetMeta) => void
  filter?: (d: DatasetMeta) => boolean
}) {
  const t = useT()
  const L = useLabels()
  const { data } = useAsync(() => api.datasets(), [])
  const list = (data ?? []).filter((d) => !filter || filter(d))
  return (
    <label className="flex min-w-72 flex-col gap-1.5">
      <span className="label">{t('Dataset', '数据集')}</span>
      <select className="input" value={value} onChange={(e) => onChange(e.target.value, list.find((d) => d.id === e.target.value))}>
        {list.map((d) => (
          <option key={d.id} value={d.id}>
            {L.dataset(d)}
          </option>
        ))}
      </select>
    </label>
  )
}

export function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="tabular mt-1 font-mono text-xl text-fg">{value}</div>
      {sub && <div className="text-xs text-fg-subtle">{sub}</div>}
    </div>
  )
}

export function SignKey() {
  const t = useT()
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-fg-muted">
      <span className="inline-flex items-center gap-1.5">
        <svg width="22" height="6"><line x1="1" x2="21" y1="3" y2="3" stroke="#9fb3d1" strokeWidth="2" /></svg>
        {t('positive tie', '正向关系')}
      </span>
      <span className="inline-flex items-center gap-1.5">
        <svg width="22" height="6"><line x1="1" x2="21" y1="3" y2="3" stroke="#f0506e" strokeWidth="2" strokeDasharray="4 3" /></svg>
        {t('negative tie', '负向关系')}
      </span>
    </div>
  )
}
